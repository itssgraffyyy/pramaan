"""Synthetic-only SQLite development workspace. Not secure evidence storage."""
import base64
import binascii
import csv
import hashlib
import io
import ipaddress
import json
import os
import re
import sqlite3
import uuid
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from openpyxl import load_workbook
from pydantic import BaseModel, Field

router = APIRouter(prefix='/api/v1/cases', tags=['Synthetic cases'])
ROOT = Path(__file__).resolve().parents[1]
ALIASES = {'caller': ['caller', 'a_number'], 'callee': ['callee', 'b_number'],
           'timestamp': ['timestamp', 'start_time'], 'duration': ['duration', 'seconds'],
           'ip': ['source_ip', 'ip'], 'port': ['source_port', 'port']}
REQUIRED = {'cdr': ('caller', 'callee', 'timestamp', 'duration'), 'ipdr': ('timestamp', 'ip', 'port')}


@contextmanager
def db():
    path = Path(os.environ.get('PRAMAAN_DB', str(ROOT / 'data' / 'pramaan.sqlite3')))
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS cases (id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS evidence (id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id), filename TEXT NOT NULL, kind TEXT NOT NULL, sha256 TEXT NOT NULL, content BLOB NOT NULL, created_at TEXT NOT NULL, UNIQUE(case_id,sha256));
    CREATE TRIGGER IF NOT EXISTS evidence_no_update BEFORE UPDATE ON evidence BEGIN SELECT RAISE(ABORT, 'original evidence is immutable'); END;
    CREATE TRIGGER IF NOT EXISTS evidence_no_delete BEFORE DELETE ON evidence BEGIN SELECT RAISE(ABORT, 'original evidence is immutable'); END;
    CREATE TABLE IF NOT EXISTS imports (id TEXT PRIMARY KEY, evidence_id TEXT NOT NULL REFERENCES evidence(id), version INTEGER NOT NULL, mapping TEXT NOT NULL, rows_json TEXT NOT NULL, ledger_json TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(evidence_id,version));
    CREATE TRIGGER IF NOT EXISTS imports_no_update BEFORE UPDATE ON imports BEGIN SELECT RAISE(ABORT, 'import versions are immutable'); END;
    CREATE TRIGGER IF NOT EXISTS imports_no_delete BEFORE DELETE ON imports BEGIN SELECT RAISE(ABORT, 'import versions are immutable'); END;
    ''')
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def now():
    return datetime.now(timezone.utc).isoformat()


def identifier():
    return uuid.uuid4().hex


def parse(content, filename):
    """Read first worksheet or CSV as text; reject formulas and malformed headers."""
    if filename.lower().endswith('.csv'):
        try:
            reader = csv.reader(io.StringIO(content.decode('utf-8-sig'), newline=''), strict=True)
            matrix = list(reader)
        except (UnicodeError, csv.Error) as exc:
            raise ValueError('Invalid UTF-8 CSV: ' + str(exc)) from exc
    elif filename.lower().endswith('.xlsx'):
        try:
            wb = load_workbook(io.BytesIO(content), read_only=True, data_only=False)
            sheet = wb.worksheets[0]
            matrix = []
            for cells in sheet.iter_rows():
                if any(c.data_type == 'f' for c in cells):
                    raise ValueError('Formula cells are not supported')
                matrix.append(['' if c.value is None else str(c.value) for c in cells])
                if len(matrix) > 10001:
                    raise ValueError('Maximum 10,000 data rows')
            wb.close()
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError('Invalid XLSX file') from exc
    else:
        raise ValueError('Only CSV and XLSX are supported')
    if not matrix or not matrix[0] or any(not str(h).strip() for h in matrix[0]):
        raise ValueError('Non-empty column headers are required')
    headers = [str(h) for h in matrix[0]]
    if len(headers) != len(set(headers)) or len(headers) > 100 or '__extra__' in headers or '__missing__' in headers:
        raise ValueError('Headers must be unique and limited to 100 columns')
    if len(matrix) > 10001:
        raise ValueError('Maximum 10,000 data rows')
    return headers, [dict(zip(headers, row + [''] * max(0, len(headers)-len(row)))) | ({'__extra__': row[len(headers):]} if len(row) > len(headers) else {}) | ({'__missing__': headers[len(row):]} if len(row) < len(headers) else {}) for row in matrix[1:]]


def suggest(headers, kind):
    return {field: next((h for h in headers if h.strip().lower() in ALIASES[field]), '') for field in REQUIRED[kind]}


def validate(fields, kind, raw):
    issues = []
    if '__extra__' in raw:
        issues.append('R03: Extra columns in row')
    if '__missing__' in raw:
        issues.append('R03: Missing columns in row')
    try:
        value = datetime.fromisoformat(fields['timestamp'].replace('Z', '+00:00'))
        if value.utcoffset() is None:
            raise ValueError()
    except ValueError:
        issues.append('R02: Invalid or ambiguous timestamp; ISO 8601 offset required')
    if kind == 'cdr':
        for key in ('caller', 'callee'):
            if not fields[key] or not re.fullmatch(r'[A-Za-z0-9+_-]{1,64}', fields[key]):
                issues.append(f'R03: Missing or invalid {key} identifier')
        if not fields['duration'].isascii() or not fields['duration'].isdigit():
            issues.append('R03: Missing or invalid duration')
    else:
        try:
            ipaddress.ip_address(fields['ip'])
        except ValueError:
            issues.append('R03: Missing or invalid IP address')
        port = fields['port']
        if not port or not port.isascii() or not port.isdigit() or int(port) > 65535:
            issues.append('R03: Missing or invalid source port')
    return issues


def get_case(conn, case_id):
    row = conn.execute('SELECT * FROM cases WHERE id=?', (case_id,)).fetchone()
    if not row:
        raise HTTPException(404, 'Case not found')
    return row


def get_file(conn, case_id, file_id):
    row = conn.execute('SELECT * FROM evidence WHERE case_id=? AND id=?', (case_id, file_id)).fetchone()
    if not row:
        raise HTTPException(404, 'Evidence not found in case')
    return row


class CaseIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class UploadIn(BaseModel):
    filename: str = Field(min_length=1, max_length=200)
    kind: str
    content_base64: str = Field(max_length=8_000_000)
    synthetic: bool


class MappingIn(BaseModel):
    mapping: dict[str, str]


@router.get('')
def cases():
    with db() as conn:
        return [dict(r) for r in conn.execute('SELECT * FROM cases ORDER BY created_at DESC')]


@router.post('', status_code=201)
def create_case(body: CaseIn):
    if not body.name.strip():
        raise HTTPException(422, 'Case name cannot be blank')
    row = {'id': identifier(), 'name': body.name.strip(), 'created_at': now()}
    with db() as conn:
        conn.execute('INSERT INTO cases VALUES (:id,:name,:created_at)', row)
    return row


@router.get('/{case_id}')
def case_detail(case_id: str):
    with db() as conn:
        case = dict(get_case(conn, case_id))
        case['evidence'] = [dict(x) for x in conn.execute('''SELECT id,filename,kind,sha256,created_at,
          (SELECT MAX(version) FROM imports WHERE evidence_id=evidence.id) AS latest_version
          FROM evidence WHERE case_id=? ORDER BY created_at DESC''', (case_id,))]
        return case


@router.post('/{case_id}/evidence', status_code=201)
def upload(case_id: str, body: UploadIn):
    if not body.synthetic or body.kind not in REQUIRED:
        raise HTTPException(422, 'Confirm synthetic data and select CDR or IPDR')
    name = body.filename.replace('\\', '/').split('/')[-1]
    if name != body.filename or name in ('.', '..'):
        raise HTTPException(422, 'Filename must not contain a path')
    try:
        content = base64.b64decode(body.content_base64, validate=True)
        if len(content) > 5_000_000:
            raise ValueError('Maximum file size is 5 MB')
        headers, rows = parse(content, name)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(422, str(exc)) from exc
    digest = hashlib.sha256(content).hexdigest()
    file_id = identifier()
    with db() as conn:
        get_case(conn, case_id)
        try:
            conn.execute('INSERT INTO evidence VALUES (?,?,?,?,?,?,?)', (file_id, case_id, name, body.kind, digest, content, now()))
        except sqlite3.IntegrityError as exc:
            raise HTTPException(409, 'This exact file has already been imported into this case') from exc
    return {'id': file_id, 'filename': name, 'sha256': digest, 'headers': headers,
            'row_count': len(rows), 'suggested_mapping': suggest(headers, body.kind)}


@router.get('/{case_id}/evidence/{file_id}')
def evidence_detail(case_id: str, file_id: str):
    with db() as conn:
        item = get_file(conn, case_id, file_id)
        headers, rows = parse(item['content'], item['filename'])
        versions = [dict(x) for x in conn.execute('SELECT id,version,mapping,created_at FROM imports WHERE evidence_id=? ORDER BY version DESC', (file_id,))]
        return {'id': item['id'], 'filename': item['filename'], 'kind': item['kind'], 'sha256': item['sha256'],
                'headers': headers, 'row_count': len(rows), 'suggested_mapping': suggest(headers, item['kind']), 'versions': versions}


@router.post('/{case_id}/evidence/{file_id}/imports', status_code=201)
def confirm_mapping(case_id: str, file_id: str, body: MappingIn):
    with db() as conn:
        item = get_file(conn, case_id, file_id)
        headers, raw_rows = parse(item['content'], item['filename'])
        mapping = body.mapping
        if set(mapping) != set(REQUIRED[item['kind']]) or any(v not in headers for v in mapping.values()) or len(set(mapping.values())) != len(mapping):
            raise HTTPException(422, 'Map each required field to a different existing column')
        signatures = Counter(json.dumps(row, sort_keys=True) for row in raw_rows)
        rows, ledger = [], []
        for number, raw in enumerate(raw_rows, 2):
            fields = {key: raw[column] for key, column in mapping.items()}
            issues = validate(fields, item['kind'], raw)
            duplicate = signatures[json.dumps(raw, sort_keys=True)] > 1
            rows.append({'row': number, 'reference': f'{item["sha256"]}:{number}', 'fields': fields,
                         'status': 'quarantined' if issues else 'accepted', 'disputed': duplicate, 'issues': issues})
            ledger.extend({'row': number, 'target': key, 'source': column, 'operation': 'copy'} for key, column in mapping.items())
        version = conn.execute('SELECT COALESCE(MAX(version),0)+1 FROM imports WHERE evidence_id=?', (file_id,)).fetchone()[0]
        import_id = identifier()
        conn.execute('INSERT INTO imports VALUES (?,?,?,?,?,?,?)', (import_id, file_id, version, json.dumps(mapping), json.dumps(rows), json.dumps(ledger), now()))
    return {'id': import_id, 'version': version}


@router.get('/{case_id}/evidence/{file_id}/imports/{version}')
def import_detail(case_id: str, file_id: str, version: int):
    with db() as conn:
        item = get_file(conn, case_id, file_id)
        imp = conn.execute('SELECT * FROM imports WHERE evidence_id=? AND version=?', (file_id, version)).fetchone()
        if not imp:
            raise HTTPException(404, 'Import version not found')
        rows = json.loads(imp['rows_json'])
        return {'version': version, 'mapping': json.loads(imp['mapping']), 'rows': rows,
                'ledger': json.loads(imp['ledger_json']), 'sha256': item['sha256'],
                'counts': {'original': len(rows), 'accepted': sum(r['status'] == 'accepted' for r in rows),
                           'quarantined': sum(r['status'] == 'quarantined' for r in rows),
                           'disputed': sum(r['disputed'] for r in rows)}}


@router.get('/{case_id}/evidence/{file_id}/records/{row_number}')
def original_row(case_id: str, file_id: str, row_number: int):
    with db() as conn:
        item = get_file(conn, case_id, file_id)
        _, rows = parse(item['content'], item['filename'])
        if row_number < 2 or row_number - 2 >= len(rows):
            raise HTTPException(404, 'Source row not found')
        return {'file': item['filename'], 'reference': f'{item["sha256"]}:{row_number}', 'fields': rows[row_number-2]}


@router.get('/{case_id}/evidence/{file_id}/imports/{version}/verify')
def verify_import(case_id: str, file_id: str, version: int):
    """Re-read original bytes and compare to persisted output without running normalisation."""
    with db() as conn:
        item = get_file(conn, case_id, file_id)
        imp = conn.execute('SELECT * FROM imports WHERE evidence_id=? AND version=?', (file_id, version)).fetchone()
        if not imp:
            raise HTTPException(404, 'Import version not found')
        headers, raw = parse(item['content'], item['filename'])
        rows, mapping, ledger = json.loads(imp['rows_json']), json.loads(imp['mapping']), json.loads(imp['ledger_json'])
        issues = []
        if hashlib.sha256(item['content']).hexdigest() != item['sha256']:
            issues.append('Original file hash mismatch')
        if len(rows) != len(raw) or [r['row'] for r in rows] != list(range(2, len(raw)+2)):
            issues.append('Row-count conservation or row identity failed')
        if len(ledger) != len(raw) * len(mapping):
            issues.append('Transformation ledger count mismatch')
        ledger_set = {(x['row'], x['target'], x['source'], x['operation']) for x in ledger}
        by_number = {r['row']: r for r in rows}
        raw_signatures = Counter(json.dumps(row, sort_keys=True) for row in raw)
        for index, source in enumerate(raw, 2):
            record = by_number.get(index)
            if record is None:
                continue
            if record['reference'] != f'{item["sha256"]}:{index}':
                issues.append(f'Row {index}: reference mismatch')
            if record.get('status') not in ('accepted', 'quarantined') or (record.get('status') == 'quarantined') != bool(record.get('issues')):
                issues.append(f'Row {index}: quarantine status inconsistent with issues')
            if record.get('disputed') != (raw_signatures[json.dumps(source, sort_keys=True)] > 1):
                issues.append(f'Row {index}: duplicate candidate mismatch')
            for target, column in mapping.items():
                if column not in headers or record['fields'].get(target) != source.get(column):
                    issues.append(f'Row {index}: {target} mismatch')
                if (index, target, column, 'copy') not in ledger_set:
                    issues.append(f'Row {index}: {target} ledger entry missing')
        return {'passed': not issues, 'issues': issues, 'original_rows': len(raw), 'output_rows': len(rows),
                'sha256': item['sha256'], 'mapping_version': version,
                'note': 'Reconciliation does not establish source authenticity or mapping semantic correctness.'}
