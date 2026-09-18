import csv
import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('import_inventory',ROOT/'tools/import_inventory.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ImportTests(unittest.TestCase):
    def test_private_columns_are_never_serialized(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'private-feed.csv'
            row={'Stock Number':'TEST123','Year':'2026','Brand':'Example','Model':'Road','Floorplan':'22','Type':'Class C','Images':'','Price':'100000','Cost':'CONFIDENTIAL_COST_SENTINEL','Dealer ID':'2321','Sleep Capacity':'','Fuel Type':'Gas','Width':'0.00','Height':'0','Description':'A compact RV.','Features':'Theater Seating'}
            with path.open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=row);writer.writeheader();writer.writerow(row)
            catalog,details=module.import_feed(path,'2026-09-17')
            serialized=json.dumps([catalog,details])
            self.assertNotIn('CONFIDENTIAL_COST_SENTINEL',serialized)
            self.assertNotIn('"Cost"',serialized)
            self.assertIsNone(catalog['items'][0]['sleeps'])
            self.assertNotIn('Width',details['TEST123']['specs'])
            self.assertNotIn('Height',details['TEST123']['specs'])

    def test_empty_or_invalid_feed_cannot_replace_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'invalid.csv';p.write_text('Stock Number,Cost\nTEST,123\n')
            with self.assertRaises(ValueError):module.import_feed(p,'2026-09-17')

    def test_non_finite_values_are_not_emitted(self):
        for value in ['NaN','Infinity','-Infinity','']:
            self.assertIsNone(module.number(value))

    def test_public_catalog_matches_detail_records(self):
        catalog=json.loads((ROOT/'inventory.json').read_text())
        stocks=set()
        for u in catalog['items']:
            self.assertNotIn(u['stock'],stocks);stocks.add(u['stock'])
            detail=json.loads((ROOT/'inventory'/(u['stock']+'.json')).read_text())
            for key,value in u.items():self.assertEqual(value,detail[key],(u['stock'],key))
            self.assertEqual(len(detail['photos']),u['photoCount'])
            if detail.get('brochure',{}):
                self.assertEqual(detail['brochure']['sameYear'],detail['brochure']['year']==u['year'])

if __name__=='__main__':unittest.main()
