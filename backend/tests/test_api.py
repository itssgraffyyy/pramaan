import unittest

from fastapi.testclient import TestClient
from backend.api import app


class DemoAPITests(unittest.TestCase):
    def test_demo_and_all_references_resolve(self):
        client = TestClient(app)
        self.assertEqual(client.get('/api/v1/health').json()['mode'], 'synthetic-only')
        response = client.get('/api/v1/demo')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['totals'], {'files': 3, 'rows': 8, 'accepted': 7, 'quarantined': 1, 'calls': 5})
        self.assertTrue(data['issues'])
        for ref in [r for contact in data['contacts'] for r in contact['references']] + [i['reference'] for i in data['issues'] if i['reference']]:
            digest, row = ref.split(':')
            record = client.get(f'/api/v1/demo/records/{digest}/{row}')
            self.assertEqual(record.status_code, 200)
            self.assertEqual(record.json()['reference'], ref)
        self.assertEqual(client.get('/api/v1/demo/records/missing/1').status_code, 404)


if __name__ == '__main__':
    unittest.main()
