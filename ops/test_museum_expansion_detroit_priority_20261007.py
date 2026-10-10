"""Offline checks for Russian/Greek source records and exclusion of missing work."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-detroit-priority-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class DetroitPriority(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows={r['facts']['source_id']:r for r in a.records()};cls.candidates={r['source_id']:r for r in a.m.load(a.f.RUN/'native-candidates-002.json.gz')['rows']}
 def test_missing_since_1951_is_excluded(self):
  row=self.candidates['54994'];self.assertIn('holding_or_custody_requires_review',row['review_flags']);self.assertNotIn('54994',self.rows);self.assertIn('unknown since 1951',' '.join(s['text'] for s in row['facts']['source_sections']))
 def test_unknown_artists_remain_cultural_labels(self):
  for sid,label in [('163','Russian'),('46395','Greek')]:
   v=self.rows[sid]['facts'];self.assertIsNone(v['detail_creator_label']);self.assertEqual(v['creator_label'],label);self.assertEqual(v['creator_label_kind'],'source_cultural_label');self.assertEqual(a.r.e.terms(v),[])
 def test_named_school_is_preserved_and_searched(self):
  v=self.rows['62943']['facts'];self.assertEqual(v['creator_label'],'Stroganov School');self.assertIn('stroganov',a.r.e.terms(v))
 def test_creation_is_not_life_or_acquisition_date(self):
  v=self.rows['54996']['facts'];self.assertEqual((v['first'],v['last'],v['date_precision']),(1501,1600,'century'));self.assertEqual(next(s['value'] for s in v['source_fields'] if s['label']=='Life Dates'),'1500-1600');self.assertIn('1939-present',' '.join(s['text'] for s in v['source_sections']))
 def test_unknown_rights_are_not_public_domain(self):
  for row in self.rows.values():
   v=row['facts'];self.assertIsNone(v['source_rights']);self.assertEqual(next(s['value'] for s in v['source_fields'] if s['label']=='Copyright'),'----------')
 def test_index_abbreviation_does_not_remove_qualification(self):
  row=self.candidates['44747'];self.assertEqual(row['facts']['creator_label'],'School of Fabriano');self.assertIn('index_detail_creator_difference',row['review_flags']);self.assertNotIn('44747',self.rows)
 def test_museum_specific_inventory_collisions_are_retained(self):
  self.assertEqual(len(self.rows['62943']['decision']['comparison']['inventory_hits']),2);self.assertEqual(len(self.rows['46395']['decision']['comparison']['inventory_hits']),2)
 def test_similar_toledo_panel_is_explicitly_distinguished(self):
  self.assertIn('Toledo1943.30',self.rows['55894']['decision']['basis']);self.assertEqual(self.rows['55894']['facts']['inventory'],'38.69')
 def test_not_on_view_remains_evidence_only(self):
  for row in self.rows.values():
   self.assertIn('Not On View',row['facts']['source_hero']);expected=a.expected_art(row);self.assertEqual(expected['status'],'review');self.assertNotIn('display_state',expected);self.assertIsNone(expected['object_form'])
 def test_native_identity_rejects_other_host(self):
  self.assertEqual(a.f.object_id('https://dia.org/collection/intercession-virgin-163'),'163')
  with self.assertRaises(AssertionError):a.f.object_id('https://example.com/collection/intercession-virgin-163')
 def test_body_hash_and_file_hash_are_both_checked(self):
  r=copy.deepcopy(self.rows['163']['decision']['source_reference']);r['sha256']='0'*64
  with self.assertRaises(AssertionError):a.checked_reference(r)
  cap=copy.deepcopy(a.m.load(a.m.ROOT/self.rows['163']['decision']['source_reference']['path'])['capture']);cap['receipt']['sha256']='0'*64
  with self.assertRaises(AssertionError):a.f.d.body(cap)
 def test_cutoff_does_not_invent_eligible_dates(self):
  for value in ['unknown','20th century','c. 1970','1971']:
   self.assertIsNotNone(a.f.d.creation(value)['date_issue'])
if __name__=='__main__':unittest.main()
