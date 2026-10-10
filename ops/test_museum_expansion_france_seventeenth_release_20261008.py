"""Offline safeguards for real-record release; no catalogue fixtures or writes."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-france-seventeenth-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class ReleaseTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=r.m.load(r.CANDIDATES)['rows'];cls.by={v['number']:v for v in cls.rows};cls.native={v['number']:v for v in r.m.load(r.i.OLD/'paris-object-context-checked-001.json.gz')['rows']}
 def test_holds_and_deferred_excluded(self):
  self.assertEqual(len(r.NOTES),125);self.assertFalse(set(r.NOTES)&(set(r.HOLDS)|set(r.n.DEFERRED)))
  self.assertTrue({584,586}<=set(r.HOLDS))
 def test_previously_delivered_not_selected(self):
  old=r.m.load(r.i.prior.REVIEW)['decisions'];ids={v['source_id'] for v in old if v['state']=='approved_review_only_addition'}
  self.assertFalse(ids&{v['source_id'] for v in self.rows});self.assertEqual(len(self.rows),238)
 def test_all_qualified_labels_preserve_literal_export(self):
  for n in r.NOTES:
   v=copy.deepcopy(self.by[n]['facts']);before=copy.deepcopy(v['source_fields']);result=r.derive_creator(v,n,self.native[n]);self.assertEqual(before,v['source_fields'])
   if n in r.old['NATIVE_QUALIFIED']:self.assertEqual(result['derived'],r.old['NATIVE_QUALIFIED'][n])
 def test_alternative_attributions_not_collaboration(self):
  v=copy.deepcopy(self.by[466]['facts']);r.derive_creator(v,466,self.native[466]);self.assertIn('alternatively',v['creator_label']);self.assertIn(' or ',v['creator_label'])
 def test_unknown_executor_is_not_model_author(self):
  v=copy.deepcopy(self.by[431]['facts']);r.derive_creator(v,431,self.native[431]);self.assertTrue(v['creator_label'].startswith('Unknown executing painter'));self.assertIn('after Boilly',v['creator_label'])
 def test_before_dates_keep_unknown_lower_bounds(self):
  for n in [367,485]:
   f=self.by[n]['facts'];self.assertIsNone(f['first']);self.assertEqual(f['date_precision'],'before');self.assertLessEqual(f['last'],1970)
 def test_manufacture_not_model_or_acquisition_year(self):
  self.assertEqual(self.by[389]['facts']['date_display'],'19e siècle');self.assertEqual(self.by[414]['facts']['date_display'],'Vers 1900');self.assertEqual(self.by[473]['facts']['date_display'],'En 1934');self.assertEqual(self.by[483]['facts']['date_display'],'19e siècle')
 def test_missing_comparison_basis_rejected(self):
  saved=r.n.FOLLOWUP.pop(492)
  try:
   with self.assertRaisesRegex(AssertionError,'missing individual comparison basis'):r.coverage(self.rows,r.m.load(r.RUN/'comparison-triage-001.json.gz'))
  finally:r.n.FOLLOWUP[492]=saved
 def test_units_do_not_duplicate_inventory(self):
  rows=[self.by[n] for n in r.NOTES];self.assertEqual(len(rows),len({(v['institution_id'],v['facts']['inventory']) for v in rows}));r.batch_review(self.rows)
 def test_native_inventory_mismatch_rejected(self):
  v=copy.deepcopy(self.by[431]['facts']);native=copy.deepcopy(self.native[431]);native['native_inventory']='J 999999'
  with self.assertRaises(AssertionError):r.derive_creator(v,431,native)
if __name__=='__main__':unittest.main()
