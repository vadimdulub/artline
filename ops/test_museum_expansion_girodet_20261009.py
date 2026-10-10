"""Offline source-boundary tests; no database fixtures or writes."""
import importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-girodet-facts-20261009.py'));f=importlib.util.module_from_spec(z);z.loader.exec_module(f)
class EvidenceBoundaries(unittest.TestCase):
 def test_unknown_is_not_creator_lifetime(self):self.assertEqual(f.dates({'Auteur':'Girodet (1767-1824)'})[:3],(None,None,'unknown'))
 def test_twentieth_century_not_truncated(self):self.assertEqual(f.dates({'Periode_de_creation':'20e siècle'})[:3],(1901,2000,'century'))
 def test_qualified_range_preserved(self):self.assertEqual(f.dates({'Millesime_de_creation':'1823-1824 vers'})[:3],(1823,1824,'circa_range'))
 def test_national_range_syntax(self):self.assertEqual(f.dates({'Millesime_de_creation':'1920 entre,1940 et'})[:3],(1920,1940,'range'))
 def test_before_has_no_invented_start(self):self.assertEqual(f.dates({'Millesime_de_creation':'1819 avant'})[:3],(None,1819,'before'))
 def test_circa_without_year_uses_explicit_period(self):self.assertEqual(f.dates({'Millesime_de_creation':'vers','Periode_de_creation':'4e quart 18e siècle'})[:3],(1776,1800,'range'))
 def test_unrecognized_numeric_qualification_rejected(self):
  with self.assertRaises(ValueError):f.dates({'Millesime_de_creation':'1819 ?'})
 def test_source_date_not_acquisition(self):self.assertEqual(f.dates({'Date_d_acquisition':'1853'})[:3],(None,None,'unknown'))
 def test_missing_object_held(self):self.assertIn('missing',f.MANUAL_HOLDS['M0284002755'].lower())
 def test_parent_and_all_children_held(self):self.assertTrue(all(k in f.MANUAL_HOLDS for k in ['M0284000108']+['M028400'+str(n) for n in range(3963,3971)]))
 def test_matrix_not_paper_print(self):self.assertIn('matrix',f.MANUAL_HOLDS['M0284000960'])
 def test_literals_and_inventory_preserved(self):
  rows,held=f.rows();self.assertEqual(len(rows)+len(held),205)
  for r in rows:
   self.assertEqual(r['facts']['inventory'],r['facts']['source_fields']['Numero_inventaire']);self.assertEqual(r['facts']['title'],r['facts']['source_fields']['Titre'].strip())
if __name__=='__main__':unittest.main()
