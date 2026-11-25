"""Synthetic-only web API. No evidence uploads or persistence are provided."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from backend.pramaan_core import contacts, ingest, verify
from backend.workspace import router as workspace_router

app = FastAPI(title="PRAMAAN Synthetic Demo", version="0.1.0")
app.include_router(workspace_router)
FIXTURES = Path(__file__).resolve().parents[1] / "datasets" / "synthetic"
FILES = (("operator_a.csv", "cdr_a"), ("operator_b.csv", "cdr_b"), ("ipdr.csv", "ipdr"))


def load_demo():
    return [(name, ingest((FIXTURES / name).read_bytes(), kind)) for name, kind in FILES]


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "mode": "synthetic-only"}


@app.get("/api/v1/demo")
def demo():
    files = load_demo()
    imports = [item for _, item in files]
    inventory = []
    issues = []
    for name, item in files:
        verification = verify(item)
        inventory.append({"name": name, "kind": item["kind"], "sha256": item["sha256"],
                          "original": len(item["raw"]), "accepted": len(item["accepted"]),
                          "quarantined": len(item["quarantined"]),
                          "duplicate_candidates": len(item["duplicate_candidates"]),
                          "verification_issues": verification})
        for row in item["quarantined"]:
            for message in row["errors"]:
                issues.append({"file": name, "reference": row["reference"], "message": message})
        for reference in item["duplicate_candidates"]:
            issues.append({"file": name, "reference": reference,
                           "message": "R01: Potential duplicate event; repeated rows may be legitimate."})
        for message in verification:
            issues.append({"file": name, "reference": None, "message": message})
    return {"inventory": inventory, "contacts": contacts(imports), "issues": issues,
            "totals": {"files": len(files), "rows": sum(len(x["raw"]) for x in imports),
                       "accepted": sum(len(x["accepted"]) for x in imports),
                       "quarantined": sum(len(x["quarantined"]) for x in imports),
                       "calls": sum(len(x["accepted"]) for x in imports if x["kind"].startswith("cdr"))}}


@app.get("/api/v1/demo/records/{digest}/{row_number}")
def source_record(digest: str, row_number: int):
    reference = f"{digest}:{row_number}"
    for name, item in load_demo():
        for row in item["raw"]:
            if row["reference"] == reference:
                return {"file": name, "reference": reference, "fields": row["fields"]}
    raise HTTPException(status_code=404, detail="Synthetic source record not found")
