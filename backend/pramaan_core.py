"""Small, deterministic CSV ingestion core. Not a secure evidence store."""
import csv
import hashlib
import io
from collections import Counter
from datetime import datetime

MAPPINGS = {
    "cdr_a": {"caller": "caller", "callee": "callee", "timestamp": "timestamp", "duration": "duration"},
    "cdr_b": {"caller": "a_number", "callee": "b_number", "timestamp": "start_time", "duration": "seconds"},
    "ipdr": {"timestamp": "start_time", "ip": "source_ip", "port": "source_port"},
}


def ingest(content: bytes, kind: str):
    """Preserve each row and quarantine invalid records; timestamps require offsets."""
    mapping = MAPPINGS[kind]
    digest = hashlib.sha256(content).hexdigest()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline=""))
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError("Missing or duplicate CSV headers")
    missing = sorted(set(mapping.values()) - set(reader.fieldnames))
    if missing:
        raise ValueError("Missing required headers: " + ", ".join(missing))
    accepted, quarantined, raw, seen, candidates = [], [], [], set(), []
    for index, row in enumerate(reader, start=2):
        reference = f"{digest}:{index}"
        raw.append({"reference": reference, "fields": row})
        canonical = {key: row.get(column, "") for key, column in mapping.items()}
        errors = []
        try:
            parsed = datetime.fromisoformat(canonical["timestamp"].replace("Z", "+00:00"))
            if parsed.utcoffset() is None:
                raise ValueError("timezone required")
        except (ValueError, TypeError):
            errors.append("R02: timestamp must be ISO 8601 with an offset")
        if kind.startswith("cdr"):
            if not canonical["caller"] or not canonical["callee"]:
                errors.append("R03: missing endpoint")
            try:
                duration = int(canonical["duration"])
                if duration < 0:
                    raise ValueError()
                canonical["duration"] = duration
            except ValueError:
                errors.append("R03: invalid duration")
        else:
            if not canonical["ip"]:
                errors.append("R03: missing IP address")
            if canonical["port"] and (not canonical["port"].isdigit() or not 0 <= int(canonical["port"]) <= 65535):
                errors.append("R03: invalid source port")
        identity = tuple(row.get(k) for k in reader.fieldnames)
        if identity in seen:
            candidates.append(reference)
        seen.add(identity)
        record = {"reference": reference, "fields": canonical}
        if errors:
            quarantined.append({**record, "errors": errors})
        else:
            accepted.append(record)
    return {"sha256": digest, "mapping_version": "1", "kind": kind, "raw": raw,
            "accepted": accepted, "quarantined": quarantined, "duplicate_candidates": candidates}


def verify(imported):
    """Independently check source-row accounting and mapped values."""
    raw = {r["reference"]: r["fields"] for r in imported["raw"]}
    output = imported["accepted"] + imported["quarantined"]
    refs = [r["reference"] for r in output]
    issues = []
    if len(refs) != len(raw) or len(set(refs)) != len(refs) or set(refs) != set(raw):
        issues.append("Row accounting failed")
    mapping = MAPPINGS[imported["kind"]]
    for record in output:
        source = raw.get(record["reference"])
        if source is None:
            continue
        for field, header in mapping.items():
            if str(record["fields"].get(field, "")) != source.get(header, ""):
                issues.append(f"Field mismatch: {record['reference']} {field}")
    return issues


def contacts(imports):
    counts = Counter()
    evidence = {}
    for imported in imports:
        if not imported["kind"].startswith("cdr"):
            continue
        for row in imported["accepted"]:
            pair = (row["fields"]["caller"], row["fields"]["callee"])
            counts[pair] += 1
            evidence.setdefault(pair, []).append(row["reference"])
    return [{"caller": a, "callee": b, "calls": count, "references": evidence[(a, b)]}
            for (a, b), count in sorted(counts.items())]
