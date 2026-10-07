import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('import_michelin', ROOT / 'scripts/import_michelin.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'data/michelin_dc_area_2026.snapshot.json').read_text(encoding='utf-8'))

    def test_snapshot_and_csv_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            report = module.export(self.data, Path(folder) / 'test.csv')
        self.assertEqual(report['rows'], 110)
        self.assertEqual(report['star_counts'], {0: 89, 1: 18, 2: 3})

    def test_duplicate_url_is_rejected(self):
        self.data['records'][1]['michelin_url'] = self.data['records'][0]['michelin_url']
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            module.validate(self.data)

    def test_missing_page_is_rejected(self):
        self.data['records'].pop()
        with self.assertRaisesRegex(ValueError, 'Expected'):
            module.validate(self.data)

    def test_unknown_award_is_not_assumed_zero(self):
        self.data['records'][0]['badges'] = []
        with self.assertRaisesRegex(ValueError, 'award-container'):
            module.validate(self.data)

    def test_responsive_badges_must_agree(self):
        self.data['records'][0]['badges'][1] = []
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            module.validate(self.data)

    def test_partial_week_is_rejected(self):
        row = next(r for r in self.data['records'] if r['monday_hours'])
        row['sunday_hours'] = ''
        with self.assertRaisesRegex(ValueError, 'Partial weekly'):
            module.validate(self.data)

    def test_closed_and_unknown_remain_different(self):
        rows = module.validate(self.data)
        self.assertTrue(any(r['monday_hours'] == 'closed' for r in rows))
        self.assertTrue(any(r['monday_hours'] == '' for r in rows))


if __name__ == '__main__':
    unittest.main()
