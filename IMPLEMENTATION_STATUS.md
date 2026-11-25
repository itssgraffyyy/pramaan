# Implementation status

This is an early foundation, not a deployable investigation system. Do not upload real evidence.

| Requirement | Location | Test | Status | Limitation |
|---|---|---|---|---|
| Two synthetic CDR mappings and one IPDR mapping | backend/pramaan_core.py | backend/tests/test_core.py | In progress | CSV only; mapping fixed, no UI or persistence |
| Row accounting and transformation reconciliation | backend/pramaan_core.py | backend/tests/test_core.py | In progress | In-memory only; no immutable evidence store or independent file hash verification |
| Contact aggregation with source references | backend/pramaan_core.py | backend/tests/test_core.py | In progress | No filters, graph or shared contacts |
| Authentication, RBAC and case isolation | — | — | Not started | No protected backend exists |
| Evidence sufficiency, gaps and robustness | backend/pramaan_core.py | backend/tests/test_core.py | In progress | Only a single-file directed contact count; no full rule catalogue or persisted gaps |
| Finding revalidation and signed replay | — | — | Not started | No versioned findings or signatures |
| Assistant, reports and review | — | — | Not started | No AI, exports or review workflow |
| Deployment and browser tests | — | — | Blocked | Docker unavailable locally; no complete application yet |

Repeated identical rows are candidates only and are never removed. Missing source ports are retained; no IP correlation is performed. The verifier checks the in-memory representation, not authenticity or admissibility.

Run the synthetic in-memory demonstration with `python backend/demo.py`. It imports eight fixture rows across three files; it is not an upload workflow. The count assessment flags all occurrences of identical source rows as disputed. Its exclusion scenario does not determine whether they are duplicates.
