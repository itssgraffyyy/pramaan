# Test plan

Run `.venv\Scripts\python.exe -m unittest discover -s backend/tests -v` on this workstation. Existing tests cover synthetic mappings, malformed rows, row accounting, duplicate candidates, source references, a scoped count assessment and an in-memory field modification. Broader integration, authorisation, replay and performance tests remain outstanding.

The FastAPI test client verifies demo totals and resolves every displayed source reference. With both local servers running, the browser test can be run using `$env:PRAMAAN_BROWSER='C:\Program Files\Google\Chrome\Application\chrome.exe'; npx playwright test`. It checks loading the synthetic dashboard and opening and closing a source record. Broader authentication, replay and investigation journeys remain outstanding.
