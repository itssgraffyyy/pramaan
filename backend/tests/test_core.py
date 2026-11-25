import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pramaan_core import contacts, ingest, verify


class IngestionTests(unittest.TestCase):
    def test_formats_accounting_and_citations(self):
        a = ingest(b'caller,callee,timestamp,duration\nA,B,2026-01-01T00:00:00+00:00,4\nA,B,2026-01-01T00:00:00+00:00,4\nA,B,unknown,-1\n', 'cdr_a')
        b = ingest(b'a_number,b_number,start_time,seconds\nA,B,2026-01-02T00:00:00Z,3\n', 'cdr_b')
        self.assertEqual((len(a['raw']), len(a['accepted']), len(a['quarantined'])), (3, 2, 1))
        self.assertEqual(len(a['duplicate_candidates']), 1)
        self.assertEqual(verify(a), [])
        self.assertEqual(contacts([a, b])[0]['calls'], 3)
        self.assertEqual(len(contacts([a, b])[0]['references']), 3)

    def test_ipdr_and_tampering(self):
        data = ingest(b'start_time,source_ip,source_port\n2026-01-01T00:00:00Z,192.0.2.1,\n', 'ipdr')
        self.assertEqual(len(data['accepted']), 1)
        data['accepted'][0]['fields']['ip'] = '192.0.2.2'
        self.assertTrue(verify(data))

    def test_bad_headers_rejected(self):
        with self.assertRaises(ValueError):
            ingest(b'caller,caller\na,b\n', 'cdr_a')


if __name__ == '__main__':
    unittest.main()
