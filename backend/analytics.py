"""Case-scoped deterministic analysis of latest confirmed synthetic imports."""
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
import networkx as nx
from backend.workspace import db, get_case

router = APIRouter(prefix='/api/v1/cases', tags=['Synthetic analytics'])


def instant(value, label):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.utcoffset() is None:
            raise ValueError()
        return parsed.astimezone(timezone.utc)
    except ValueError as exc:
        raise HTTPException(422, f'{label} must be ISO 8601 with a timezone offset') from exc


@router.get('/{case_id}/analytics')
def analytics(case_id: str, file_id: list[str] = Query(default=[]), subject: str = '',
              start: str = '', end: str = '', night_start: int = 22, night_end: int = 6):
    """Counts accepted event rows; time filters and night hours use UTC, end is exclusive."""
    start_at, end_at = instant(start, 'start'), instant(end, 'end')
    if start_at and end_at and start_at >= end_at:
        raise HTTPException(422, 'start must be earlier than end')
    if not 0 <= night_start <= 23 or not 0 <= night_end <= 23 or night_start == night_end:
        raise HTTPException(422, 'Night hours must be distinct integers between 0 and 23')
    subject = subject.strip()
    with db() as conn:
        get_case(conn, case_id)
        files = conn.execute('''SELECT e.id,e.filename,e.kind,e.sha256,i.version,i.rows_json
          FROM evidence e JOIN imports i ON i.evidence_id=e.id
          WHERE e.case_id=? AND i.version=(SELECT MAX(v.version) FROM imports v WHERE v.evidence_id=e.id)
          ORDER BY e.created_at,e.id''', (case_id,)).fetchall()
        if file_id:
            allowed = set(file_id)
            if allowed - {f['id'] for f in files}:
                raise HTTPException(422, 'Selected file is unavailable in this case or has no confirmed import')
            files = [f for f in files if f['id'] in allowed]
        events, ipdr, excluded = [], [], 0
        for f in files:
            for row in json.loads(f['rows_json']):
                if row['status'] != 'accepted':
                    excluded += 1
                    continue
                fields = row['fields']
                timestamp = instant(fields['timestamp'], 'record timestamp')
                if (start_at and timestamp < start_at) or (end_at and timestamp >= end_at):
                    continue
                if subject and (f['kind'] != 'cdr' or subject not in (fields['caller'], fields['callee'])):
                    continue
                ref = {'file_id': f['id'], 'filename': f['filename'], 'row': row['row'], 'reference': row['reference'],
                       'disputed': row['disputed'], 'version': f['version']}
                event = {'fields': fields, 'time': timestamp, 'source': ref}
                (events if f['kind'] == 'cdr' else ipdr).append(event)
    pairs, neighbours, daily, hours, nodes = {}, defaultdict(dict), Counter(), Counter(), defaultdict(list)
    total_duration = night_count = 0
    for e in events:
        f, t, ref = e['fields'], e['time'], e['source']
        pair = (f['caller'], f['callee'])
        entry = pairs.setdefault(pair, {'caller': pair[0], 'callee': pair[1], 'calls': 0, 'duration_seconds': 0, 'sources': []})
        entry['calls'] += 1; entry['duration_seconds'] += int(f['duration']); entry['sources'].append(ref)
        for node in set(pair):
            nodes[node].append(ref)
        if subject:
            other = f['callee'] if f['caller'] == subject else f['caller']
            neighbours[ref['file_id']].setdefault(other, []).append(ref)
        total_duration += int(f['duration'])
        daily[t.date().isoformat()] += 1; hours[t.hour] += 1
        night_count += int((night_start <= t.hour or t.hour < night_end) if night_start > night_end else (night_start <= t.hour < night_end))
    edges = sorted(pairs.values(), key=lambda item: (-item['calls'], item['caller'], item['callee']))
    graph = nx.DiGraph()
    graph.add_edges_from((e['caller'], e['callee']) for e in edges)
    selected_cdr = [f for f in files if f['kind'] == 'cdr']
    common = []
    if subject and len(selected_cdr) >= 2:
        shared = set.intersection(*(set(neighbours[f['id']]) for f in selected_cdr))
        common = [{'contact': x, 'sources': [r for f in selected_cdr for r in neighbours[f['id']][x]]} for x in sorted(shared)]
    timestamps = [e['time'] for e in events]
    return {'scope': {'subject': subject or None, 'start': start or None, 'end_exclusive': end or None,
                      'timezone': 'UTC', 'night_start_hour': night_start, 'night_end_hour_exclusive': night_end,
                      'files': [{'id': f['id'], 'filename': f['filename'], 'kind': f['kind'], 'version': f['version']} for f in files]},
            'summary': {'calls': len(events), 'total_duration_seconds': total_duration,
                        'average_duration_seconds': total_duration / len(events) if events else None,
                        'first_utc': min(timestamps).isoformat() if timestamps else None,
                        'last_utc': max(timestamps).isoformat() if timestamps else None,
                        'night_calls': night_count, 'outgoing': sum(e['fields']['caller'] == subject for e in events) if subject else None,
                        'incoming': sum(e['fields']['callee'] == subject for e in events) if subject else None,
                        'quarantined_excluded_in_selected_files': excluded,
                        'disputed_included': sum(e['source']['disputed'] for e in events)},
            'edges': edges, 'nodes': [{'identifier': key, 'in_degree': graph.in_degree(key), 'out_degree': graph.out_degree(key), 'sources': value} for key, value in sorted(nodes.items())],
            'common_contacts': common, 'daily': [{'date': k, 'calls': daily[k]} for k in sorted(daily)],
            'hourly_utc': [{'hour': h, 'calls': hours[h]} for h in range(24)],
            'ipdr_sessions': [{'timestamp_utc': e['time'].isoformat(), 'ip': e['fields']['ip'], 'port': e['fields']['port'], 'source': e['source']} for e in ipdr],
            'limitations': ['Accepted rows are observations, not confirmed unique calls; duplicate candidates remain included.',
                            'Incoming and outgoing are relative to the specified subject and depend on the confirmed mapping.',
                            'Source timestamps are converted to UTC; night hours are UTC, not local time.',
                            'Shared public IP addresses do not establish subscriber identity or app usage.']}
