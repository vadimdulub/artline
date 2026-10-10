"""Offline checks of reviewed real-source decisions; no database fixtures."""
import importlib.util,json,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-dulwich-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class DulwichSelection(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=a.records();cls.byinv={r['facts']['inventory']:r for r in cls.records};cls.review=a.m.load(a.REVIEW)
 def test_all_captured_objects_remain_accounted_for(self):
  self.assertEqual(len(self.review['decisions']),336)
  self.assertEqual(self.review['counts'],dict(approved_review_only_addition=125,editorial_review_pending=118,editorial_hold=58,source_hold=35))
 def test_lost_destroyed_wrong_object_and_two_sided_cases_stay_held(self):
  for inv in ['DPG447','DPG483','DPG631','DPG017A']:
   d=next(d for d in self.review['decisions'] if d['inventory']==inv)
   self.assertEqual(d['state'],'editorial_hold');self.assertNotIn(inv,self.byinv)
 def test_later_comparison_withdraws_provisional_approval(self):
  d=next(d for d in self.review['decisions'] if d['inventory']=='DPG114')
  self.assertEqual(d['previous_provisional_state'],'approved_review_only_addition');self.assertEqual(d['state'],'editorial_hold')
 def test_existing_dulwich_inventory_is_not_added(self):
  self.assertNotIn('DPG632',self.byinv)
  self.assertEqual(len(self.byinv),len(self.records))
 def test_copy_keeps_creation_of_copy_and_qualified_creator(self):
  r=self.byinv['DPG403'];v=r['facts'];self.assertEqual(v['creator_label'],'After Sir Peter Paul Rubens');self.assertEqual(v['date_display'],'19th Century')
  self.assertNotEqual(v['first'],1616)
  r=self.byinv['DPG657'];self.assertEqual(r['facts']['first'],1830);self.assertIn('DPG168',r['decision']['basis'])
 def test_source_before_preserves_unknown_lower_bound(self):
  for inv,end in [('DPG356',1686),('DPG499',1844),('DPG291',1832)]:
   v=a.expected_art(self.byinv[inv]);self.assertIsNone(v['creation_year_start']);self.assertEqual(v['creation_year_end'],end);self.assertEqual(v['date_precision'],'before')
 def test_same_size_pendants_are_separately_evidenced(self):
  one,two=self.byinv['DPG106'],self.byinv['DPG110'];self.assertEqual(one['facts']['dimensions_text'],two['facts']['dimensions_text']);self.assertNotEqual(one['facts']['source_url'],two['facts']['source_url']);self.assertNotEqual(one['artwork_id'],two['artwork_id'])
 def test_anonymous_and_joint_creators_are_literal_review_records(self):
  self.assertEqual(a.expected_art(self.byinv['DPG542'])['unlinked_creator_label'],'British School')
  self.assertEqual(a.expected_art(self.byinv['DPG322'])['unlinked_creator_label'],'Daniel Seghers & Erasmus Quellinus')
  for r in self.records:self.assertEqual(a.expected_art(r)['status'],'review');self.assertIsNone(a.expected_art(r)['object_form'])
 def test_citation_discloses_extraction_format_and_retains_uncertainty(self):
  r=self.byinv['DPG582'];note=json.loads(a.citation_note(r,'test-digest'))
  self.assertIn('not original HTTP bytes',note['policy']);self.assertIn('disputes',note['source_record']['decision']['basis']);self.assertIn('not original HTTP bytes',a.holding_note(r,'test-digest'))

if __name__=='__main__':unittest.main()
