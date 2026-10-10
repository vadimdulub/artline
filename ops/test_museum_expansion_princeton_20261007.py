"""Offline date, creator-role, physical-unit and source-integrity regressions."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-princeton-review-20261007.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r);f=r.f
class NativeEvidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows={v['number']:v for v in f.m.load(r.CANDIDATES)['rows']};cls.decisions={v['number']:v for v in r.build()}
 def test_all_captured_objects_reparse(self):
  for row in self.rows.values():self.assertEqual(row,f.parse(f.checked(row['source_reference'])))
 def test_bce_bounds_are_negative_creation_dates(self):
  v=self.rows[14]['facts'];self.assertEqual((v['first'],v['last']),(-300,-201))
 def test_maker_period_is_not_object_date(self):
  v=self.rows[1]['facts'];self.assertEqual((v['first'],v['last']),(600,699));self.assertEqual(v['source_makers'][0]['datebegin'],330)
 def test_missing_literal_date_is_never_auto_eligible(self):
  v=self.rows[8]['facts'];self.assertIsNone(v['date_display']);self.assertIsNotNone(v['date_issue']);self.assertEqual((v['first'],v['last']),(330,1453))
 def test_zero_creation_bounds_stay_unknown(self):
  v=self.rows[12]['facts'];self.assertIsNone(v['first']);self.assertIsNone(v['last'])
 def test_cutoff_and_invalid_bounds(self):
  for first,last,date in [(1971,1971,'1971'),(1960,1980,'1960–1980'),(0,0,None),(1900,1800,'19th century')]:self.assertIsNotNone(f.creation(dict(datebegin=first,dateend=last,displaydate=date))['date_issue'])
  self.assertIsNone(f.creation(dict(datebegin=1970,dateend=1970,displaydate='1970'))['date_issue'])
 def test_source_circa_bounds_are_not_recalculated(self):
  v=self.rows[68]['facts'];self.assertEqual((v['first'],v['last']),(1655,1665));self.assertEqual(v['date_display'],'ca. 1660–65')
 def test_printer_not_promoted_to_artist(self):
  v=self.rows[15]['facts'];self.assertEqual(v['creator_label'],'Arthur Bowen Davies');self.assertTrue(any(x['role']=='Printer' and x['displayname']=='Ernest Haskell' for x in v['source_makers']))
 def test_former_attribution_remains_former(self):
  v=self.rows[126]['facts'];self.assertNotIn('Jacopo',v['creator_label']);self.assertTrue(any(x['role']=='Former Attribution' for x in v['source_makers']))
 def test_manufactory_stays_object_level_qualified_label(self):self.assertEqual(self.rows[58]['facts']['creator_label'],'Manufactory: Imperial Porcelain Manufactory')
 def test_medium_and_specific_type_override_broad_metal(self):
  v=self.rows[77]['facts'];self.assertEqual(v['source_fields']['classification'],'Metal');self.assertEqual(v['work_type'],'painting');self.assertEqual(v['medium'],'Oil on wood panel')
 def test_steatite_relief_is_not_forced_into_pottery(self):
  for n in [37,39]:self.assertEqual(self.rows[n]['facts']['work_type'],'sculpture');self.assertEqual(self.rows[n]['facts']['source_fields']['classification'],'Ceramic')
 def test_glass_and_faience_preserve_unmapped_types(self):
  for n in [2,20,21,31,34]:self.assertEqual(self.rows[n]['facts']['work_type'],'unknown')
 def test_compound_objects_keep_one_native_identity(self):
  for n in [5,35,40,53,62]:self.assertTrue(self.rows[n]['facts']['inventory']);self.assertEqual(self.rows[n]['source_id'],self.rows[n]['facts']['native_object_id'])
 def test_source_capture_integrity(self):
  x=f.m.load(f.checked(self.rows[1]['source_reference']));cap=copy.deepcopy(x['capture']);cap['receipt']['status']=429
  with self.assertRaises(AssertionError):f.n.body(cap)
 def test_known_date_conflict_is_held(self):self.assertIn('gift year',r.HOLDS[92])
 def test_review_protects_unknown_dates_and_components(self):
  ds=self.decisions
  for n in [8,12,25,26,28,29,33,92]:self.assertEqual(ds[n]['state'],'editorial_hold')
 def test_explicit_icons_get_form_without_artist_authority(self):
  ds=self.decisions
  for n in [36,37,39,40,42,43,44,45,46,61]:self.assertEqual(ds[n]['facts']['object_form'],'icon')
  self.assertIsNone(ds[35]['facts']['object_form'])
 def test_existing_holdings_are_reconciliations_not_new_records(self):
  hs=[v for v in self.decisions.values() if v['state']=='approved_existing_holding'];self.assertEqual(len(hs),18);self.assertEqual(len({v['existing_artwork_id'] for v in hs}),18)
 def test_selected_queue_is_unique_and_research_only(self):
  q=f.m.load(f.QUEUE);self.assertEqual(len(q['selected']),256);self.assertEqual(len(q['held']),132);self.assertEqual(len({v['source_id'] for v in q['selected']+q['held']}),388)
if __name__=='__main__':unittest.main()
