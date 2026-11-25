# PRAMAAN

**CDR/IPDR Analysis Tool with AI Investigation Assistant**

Team ARC | Rajasthan Police Hackathon 2026 | PS03

PRAMAAN is a proposed local-first telecom forensic investigation platform designed to help authorised investigators analyse uploaded call and internet activity records, identify communication patterns and obtain evidence-linked answers.

## Proposed features

- Multi-operator CDR/IPDR import and standardisation.
- Contact graphs, common-contact analysis, cell-tower timelines and device-change detection.
- AI-assisted queries backed by deterministic analytics and source-record references.
- Case management, officer review, audit logs and PDF/Excel reports.

## Our three differentiators

1. **Forensic Evidence Integrity:** Independently verify data transformations and detect silent errors or information loss.
2. **Evidence Sufficiency, Robustness & Gap Navigation:** Assess whether findings are supported, measure the impact of disputed records and identify missing evidence.
3. **Living Investigation & Forensic Replay:** Revalidate affected findings when evidence changes and enable independent reproduction of analytical results.

## Planned technology stack

React, TypeScript, Python, FastAPI, PostgreSQL, Polars, DuckDB, NetworkX, Cytoscape.js, Leaflet and local Qwen inference through Ollama.

The architecture is designed to operate without mandatory external API dependencies.

## Project status

Early development. The React dashboard connects to a FastAPI synthetic-only backend and shows computed contact counts, validation issues and source records. It has no authentication or protected storage; do not use real records. See [implementation status](IMPLEMENTATION_STATUS.md) for limitations and outstanding work.

From the repository root on Windows, create the environment and install dependencies once:

```powershell
G:\Python313\python.exe -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
npm install
```

Run the following in separate terminals:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
npm run dev
```

Open http://127.0.0.1:5173 and select **Load synthetic demo** or **Case workspace**. In the workspace, create a case, upload a synthetic CSV or XLSX file, confirm the suggested column mappings, and select **Verify integrity**. Select a row to inspect its original values. Case history persists in `data/pramaan.sqlite3`; set `PRAMAAN_DB` to use another SQLite file. SQLite is a temporary local development adapter; the planned PostgreSQL adapter is not implemented. The API has no authentication or real-evidence protections. Only use fictional data. Vite proxies `/api` to the backend. Run tests with `.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v` and build the frontend with `npm run build`.

After importing synthetic records, open **Telecom analytics**, select the case and optionally narrow the files, subject and UTC dates. Results include source-linked communication pairs, a contact network, common contacts and IPDR session rows. Details and limitations are in [analytics semantics](docs/ANALYTICS.md).

Uploads are limited to 5 MB and 10,000 records; XLSX imports read the first sheet and reject formulas. Use text cells for identifiers and ISO 8601 timestamps with offsets. XLSX numeric formatting, including leading-zero display formats, is not preserved in the extracted values; the original file bytes are retained. Mapping confirmation cannot establish that an operator's column semantics are correct. The integrity check compares original bytes, row accounting, mappings and ledger entries; it is not proof of authenticity or legal admissibility.

Only synthetic datasets will be used for the hackathon. No live interception or unauthorised access to telecom records. All investigative findings require authorised human review.

## Team

**ARC** — Govt. Mahila Engineering College, Ajmer
