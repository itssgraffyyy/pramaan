import base64
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from openpyxl import Workbook
from backend.api import app
from backend.workspace import db


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous = os.environ.get('PRAMAAN_DB')
        os.environ['PRAMAAN_DB'] = str(Path(self.temp.name) / 'cases.sqlite3')
        self.client = TestClient(app)
        self.case = self.client.post('/api/v1/cases', json={'name': 'Synthetic test'}).json()['id']
        self.url = '/api/v1/cases/' + self.case

    def tearDown(self):
        if self.previous is None:
            os.environ.pop('PRAMAAN_DB', None)
        else:
            os.environ['PRAMAAN_DB'] = self.previous
        self.temp.cleanup()

    def upload(self, filename, kind, content):
        return self.client.post(self.url + '/evidence', json={'filename': filename, 'kind': kind,
             'content_base64': base64.b64encode(content).decode(), 'synthetic': True})

    def test_csv_mapping_validation_history_and_persistence(self):
        content = b'caller,callee,timestamp,duration\nA,B,2026-01-01T00:00:00Z,4\nA,B,2026-01-01T00:00:00Z,4\nA,B,01/02/2026,\n'
        upload = self.upload('sample.csv', 'cdr', content)
        self.assertEqual(upload.status_code, 201)
        file = upload.json(); path = self.url + '/evidence/' + file['id']
        self.assertEqual(self.upload('again.csv', 'cdr', content).status_code, 409)
        bad = dict(file['suggested_mapping']); bad['caller'] = 'missing'
        self.assertEqual(self.client.post(path + '/imports', json={'mapping': bad}).status_code, 422)
        for version in (1, 2):
            response = self.client.post(path + '/imports', json={'mapping': file['suggested_mapping']})
            self.assertEqual(response.json()['version'], version)
        data = self.client.get(path + '/imports/2').json()
        self.assertEqual(data['counts'], {'original': 3, 'accepted': 2, 'quarantined': 1, 'disputed': 2})
        self.assertEqual(len(data['rows'][2]['issues']), 2)
        self.assertTrue(self.client.get(path + '/imports/2/verify').json()['passed'])
        self.assertEqual(self.client.get(path + '/records/2').json()['fields']['caller'], 'A')
        # A fresh client and database connection must see the committed case and history.
        with TestClient(app) as restarted:
            self.assertEqual(restarted.get(self.url).json()['evidence'][0]['latest_version'], 2)
            self.assertEqual(len(restarted.get(path).json()['versions']), 2)

    def test_xlsx_ipdr_and_heterogeneous_cdr(self):
        workbook = Workbook(); sheet = workbook.active
        sheet.append(['start_time', 'source_ip', 'source_port'])
        sheet.append(['2026-01-01T00:00:00Z', '192.0.2.1', '443'])
        sheet.append(['2026-01-01T00:00:00Z', 'not-an-ip', ''])
        output = io.BytesIO(); workbook.save(output)
        uploaded = self.upload('sample.xlsx', 'ipdr', output.getvalue()).json()
        path = self.url + '/evidence/' + uploaded['id']
        self.assertEqual(self.client.post(path + '/imports', json={'mapping': uploaded['suggested_mapping']}).status_code, 201)
        data = self.client.get(path + '/imports/1').json()
        self.assertEqual(data['counts']['quarantined'], 1)
        self.assertTrue(self.client.get(path + '/imports/1/verify').json()['passed'])
        b = self.upload('b.csv', 'cdr', b'a_number,b_number,start_time,seconds\nA,B,2026-01-01T00:00:00Z,10\n').json()
        self.assertEqual(b['suggested_mapping']['caller'], 'a_number')

    def test_independent_verifier_detects_silent_loss(self):
        f = self.upload('x.csv', 'cdr', b'caller,callee,timestamp,duration\nA,B,2026-01-01T00:00:00Z,1\n').json()
        path = self.url + '/evidence/' + f['id']
        self.client.post(path + '/imports', json={'mapping': f['suggested_mapping']})
        with db() as conn:
            with self.assertRaises(Exception):
                conn.execute('UPDATE evidence SET content=? WHERE id=?', (b'altered', f['id']))
            conn.execute('DROP TRIGGER imports_no_update')
            conn.execute('UPDATE imports SET rows_json=? WHERE evidence_id=?', (json.dumps([]), f['id']))
        result = self.client.get(path + '/imports/1/verify').json()
        self.assertFalse(result['passed'])
        self.assertIn('Row-count conservation', result['issues'][0])

    def test_cross_case_and_filename_rejected(self):
        f = self.upload('x.csv', 'cdr', b'caller,callee,timestamp,duration\nA,B,2026-01-01T00:00:00Z,1\n').json()
        self.assertEqual(self.client.get('/api/v1/cases/other/evidence/' + f['id']).status_code, 404)
        self.assertEqual(self.upload('../x.csv', 'cdr', b'a').status_code, 422)

    def test_wrong_column_assignment_quarantines_invalid_values(self):
        f = self.upload('wrong.csv', 'cdr', b'caller,callee,timestamp,duration\nA,B,2026-01-01T00:00:00Z,1\n').json()
        mapping = dict(f['suggested_mapping'])
        mapping['timestamp'], mapping['caller'] = mapping['caller'], mapping['timestamp']
        path = self.url + '/evidence/' + f['id']
        self.assertEqual(self.client.post(path + '/imports', json={'mapping': mapping}).status_code, 201)
        result = self.client.get(path + '/imports/1').json()
        self.assertEqual(result['counts']['quarantined'], 1)
        self.assertTrue(any('timestamp' in issue for issue in result['rows'][0]['issues']))


if __name__ == '__main__':
    unittest.main()
