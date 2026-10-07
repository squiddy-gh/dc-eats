import copy
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('enrich',ROOT/'scripts/enrich_cheap_eats.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class EnrichmentTests(unittest.TestCase):
    def test_utf8_repair_preserves_real_accents(self):
        for value in ['Mélange Foods','Jon’s Joint','Bánh Mì Ơi','There isn’t a problem.']:
            self.assertEqual(mod.clean(value),value)
        original='Mélange Foods — Jon’s Joint'
        self.assertEqual(mod.clean(original.encode('utf-8').decode('cp1252')),original)
    def test_bom_and_csv_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'sample.csv'
            rows=[{'name':'Bánh Mì Ơi','narrative':'A "sandwich", with herbs.'}]
            mod.write_csv(path,list(rows[0]),rows)
            self.assertTrue(path.read_bytes().startswith(b'\xef\xbb\xbf'))
            with path.open(encoding='utf-8-sig',newline='') as f:
                self.assertEqual(list(csv.DictReader(f)),rows)
    def test_branch_specific_schedules(self):
        reviewed=json.loads((ROOT/'sources/cheap_eats_2026_enrichment.json').read_text(encoding='utf-8'))['records']
        aj=[r for r in reviewed if r['original_name']=='A&J Restaurant']
        self.assertEqual(aj[0]['hours'][1],'Closed')
        self.assertEqual(aj[1]['hours'][1],'11:30-21:00')
        lighthouse=next(r for r in reviewed if r['original_name'].startswith('Vit Goel'))
        self.assertEqual(lighthouse['phone'],'703-333-3436')
        self.assertEqual(lighthouse['website'],'https://lighthousetofu.com/')
    def test_unmatched_branch_fails_instead_of_guessing(self):
        before={'restaurant_name':'New branch','address':'1 Main St','latitude':'1','longitude':'2'}
        with self.assertRaisesRegex(ValueError,'Unreviewed'):
            mod.enrich([before],[])
    def test_generated_deliverable(self):
        path=ROOT/'data/washingtonian_best_cheap_eats_2026.csv'
        with path.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f);self.assertEqual(reader.fieldnames,mod.FIELDS);rows=list(reader)
        self.assertEqual(len(rows),107)
        self.assertEqual(len({(r['restaurant_name'],r['address']) for r in rows}),107)
        for r in rows:
            self.assertTrue(r['narrative'].endswith('.'))
            self.assertNotIn('…',r['narrative'])
            self.assertNotIn('\ufffd',str(r))
            self.assertTrue(38<float(r['latitude'])<40)
            self.assertTrue(-79<float(r['longitude'])<-76)

if __name__=='__main__':unittest.main()
