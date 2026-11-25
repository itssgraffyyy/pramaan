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

Early development. The React page is a starter and is not connected to a backend. A standard-library Python experiment ingests three synthetic CSV formats and produces referenced contact counts and a limited evidence assessment. Run it from the repository root with `python backend/demo.py`, and run its tests with `python -m unittest discover -s backend/tests -v`. See [implementation status](IMPLEMENTATION_STATUS.md) for limitations and outstanding work. This is not a secure evidence system; do not use real records.

Only synthetic datasets will be used for the hackathon. No live interception or unauthorised access to telecom records. All investigative findings require authorised human review.

## Team

**ARC** — Govt. Mahila Engineering College, Ajmer
