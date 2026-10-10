"""Offline safeguards only; never connect to or create a test database."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-italy-second-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class ReleaseChecks(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.records=a.records();cls.by={v['decision']['number']:v for v in cls.records};cls.rows={v['number']:v for v in a.m.load(a.RUN/'native-candidates-001.json.gz')['rows']}
 def test_selected_distinct_objects(self):
  self.assertEqual(len(self.records),88);self.assertEqual(len({v['artwork_id'] for v in self.records}),88)
 def test_no_source_conflicts_released(self):
  self.assertTrue(all(not v['decision']['issues'] and not v['decision']['comparison']['source_hits'] for v in self.records))
 def test_unknown_units_remain_unknown(self):
  self.assertIn('(unit not stated)',self.by[533]['facts']['dimensions_text']);self.assertNotIn('cm',self.by[533]['facts']['dimensions_text'])
 def test_explicit_units_and_frame_notes_preserved(self):
  self.assertIn('mm',self.by[332]['facts']['dimensions_text']);self.assertIn('cornice',self.by[42]['facts']['dimensions_text'])
 def test_qualified_makers_and_unknown_inventory(self):
  self.assertIn('attribuito',self.by[70]['facts']['creator_label']);self.assertIn('maniera',self.by[606]['facts']['creator_label']);self.assertIsNone(self.by[606]['facts']['inventory'])
 def test_ambiguous_physical_units_deferred(self):
  self.assertFalse({362,365,366,367,603,604,532,123,124,163,333,488}&set(self.by))
 def test_sitter_is_not_same_physical_work(self):
  x=self.by[147]['facts'];y=self.by[148]['facts'];self.assertEqual(x['title'],y['title']);self.assertNotEqual(x['inventory'],y['inventory']);self.assertNotEqual(x['medium'],y['medium'])
 def test_cutoff_and_ranges(self):
  self.assertIsNone(a.r.f.a.numeric_date('ca 1970'));self.assertIsNone(a.r.f.a.numeric_date('1965-1975'));self.assertEqual(a.r.f.a.numeric_date('post 1750 - ante 1755'),(1750,1755,'range'))
 def test_museum_mismatch_fails_source_parser(self):
  row=self.rows[11];b=a.r.f.validated_batch(a.checked(row['source_reference']));p=next(v for v in b['pages'] if v['number']==11);b['_path']=a.checked(row['source_reference']);bad=copy.deepcopy(row)
  for v in bad['authority_candidates']:v['catalogue_city']='Rome (RM)'
  self.assertIn('unique_museum_and_city_review',a.r.f.parse(bad,b,p)['issues'])
 def test_fresh_identity_guards_relevant_changes(self):
  before={'number':1,'creator_pool_ids':['a'],'hits':[]};unrelated=dict(before,creator_pool_ids=['a','b']);relevant=dict(unrelated,hits=[{'id':'b'}]);self.assertEqual(a.comparable(before),a.comparable(unrelated));self.assertNotEqual(a.comparable(before),a.comparable(relevant))
if __name__=='__main__':unittest.main()
