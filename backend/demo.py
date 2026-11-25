"""Run a reproducible, in-memory synthetic investigation from the repository root."""
import json
from pathlib import Path

from pramaan_core import contact_count_assessment, contacts, ingest, verify

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "datasets" / "synthetic"


def main():
    imports = [ingest((FIXTURES / filename).read_bytes(), kind) for filename, kind in (
        ("operator_a.csv", "cdr_a"), ("operator_b.csv", "cdr_b"), ("ipdr.csv", "ipdr"))]
    result = {
        "notice": "Synthetic data only; in-memory demonstration, not a secure evidence system.",
        "imports": [{"kind": item["kind"], "sha256": item["sha256"],
                     "original_rows": len(item["raw"]), "accepted": len(item["accepted"]),
                     "quarantined": len(item["quarantined"]),
                     "duplicate_candidates": len(item["duplicate_candidates"]),
                     "verification_issues": verify(item)} for item in imports],
        "contacts": contacts(imports),
        "assessment": contact_count_assessment(imports[0], "SYNTH-A", "SYNTH-B"),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
