# Implementation status

This is a local synthetic-only development application, not a deployable investigation system. Do not use real evidence.

| Requirement | Location | Test | Status | Limitation |
|---|---|---|---|---|
| Persistent synthetic cases and import history | backend/workspace.py, src/Workspace.jsx | backend/tests/test_workspace.py | In progress | SQLite development adapter only; no auth, PostgreSQL or migrations |
| Two synthetic CDR mappings and one IPDR mapping | backend/workspace.py, src/Workspace.jsx | backend/tests/test_workspace.py | In progress | CSV/XLSX first worksheet; synthetic use is user-attested, not automatically verifiable |
| Row accounting and transformation reconciliation | backend/workspace.py | backend/tests/test_workspace.py | In progress | Original bytes and import versions protected by SQLite triggers; database owner can alter them; verifier does not independently establish semantic mapping correctness or all validation decisions |
| Contact aggregation with source references | backend/pramaan_core.py, backend/api.py, src/main.jsx | backend/tests/test_core.py, backend/tests/test_api.py | In progress | Dashboard displays computed counts and original fixture rows; no filters, graph or shared contacts |
| Case-scoped telecom analytics | backend/analytics.py, src/Analytics.jsx, src/ContactGraph.jsx | backend/tests/test_workspace.py, tests/workspace.spec.js | In progress | Latest versions only; missing tower/device analytics, IPDR correlation, coverage, chart tabs and unusual-activity rules |
| Synthetic web dashboard | backend/api.py, src/main.jsx | backend/tests/test_api.py, tests/synthetic-demo.spec.js | Tested | No authentication or real-data functionality |
| Authentication, RBAC and case isolation | — | — | Not started | No protected backend exists |
| Evidence sufficiency, gaps and robustness | backend/pramaan_core.py | backend/tests/test_core.py | In progress | Only a single-file directed contact count; no full rule catalogue or persisted gaps |
| Finding revalidation and signed replay | — | — | Not started | No versioned findings or signatures |
| Assistant, reports and review | — | — | Not started | No AI, exports or review workflow |
| Deployment and browser tests | vite.config.js | tests/synthetic-demo.spec.js | In progress | Local development servers only; one synthetic demo browser journey passed, no complete deployment |

Repeated identical rows are candidates only and are never removed. In uploaded IPDR, missing source ports are quarantined; no IP correlation is performed. The verifier checks stored bytes and reconciliation, not authenticity or admissibility. The database is local and unencrypted, without authentication. XLSX extraction reads the first sheet; numeric display formatting and original cell types are not represented in normalized values. Files are limited to 5 MB and 10,000 records.

The original synthetic demo remains available. The case workspace accepts user-confirmed synthetic CSV/XLSX and stores versioned mappings and source references. Backend suite: 12 tests passed, including the six original tests. The frontend production build passed. Two browser tests passed separately: the existing demo and case creation, CSV upload, mapping, verification, source inspection and reopening after a page reload. The stored import was also retrieved and verified after an actual backend restart. The integrity engine and Milestone 2 remain partial: no independent semantic validation of every field, comprehensive malformed-file benchmark, full forensic audit trail, or protected immutable evidence store has been demonstrated.

Milestone 3 is **partial**. Case analytics includes scoped directed communication counts and duration, UTC daily/hourly/night counts, NetworkX graph data with Cytoscape display, common contacts across selected files, IPDR session listing and source links. The backend suite passed 13 tests, including one ground-truth analytics test. The production build passed with a warning about a JavaScript chunk exceeding 500 kB. See [analytics semantics](docs/ANALYTICS.md). Tower and device mappings and timelines, IP/port correlation, historical versions, complete visualisations, and remaining Milestones 4–14 are unfinished. The next task is to extend the canonical import schema with provenance-preserving optional tower/device fields and implement time-valid tower metadata and source-linked timeline tests.
