"""Verify selected real-source identities and safety invariants without a test database."""
import copy,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-wallace-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class WallaceSelection(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=a.records();cls.byinv={x['facts']['inventory']:x for x in cls.records}
 def test_existing_inventory_and_ambiguous_objects_are_excluded(self):
  self.assertEqual(len(self.records),92)
  for inv in ['P362','P309','P704','P341','P618','M5','M83','M93']:self.assertNotIn(inv,self.byinv)
 def test_attribution_and_copy_date_stay_literal(self):
  for inv,label in [('P319','After Richard Parkes Bonington'),('M163','Imitator of Jacques Charlier'),('M132','Manner of Louis Cournerie')]:self.assertEqual(a.expected_art(self.byinv[inv])['unlinked_creator_label'],label)
  self.assertEqual(self.byinv['M163']['facts']['date_display'],'19th century');self.assertEqual(self.byinv['P319']['facts']['first'],1830)
 def test_same_subject_versions_keep_distinct_objects(self):
  for one,two in [('M94','M95'),('P351','P733'),('P586','P730'),('M66','M163'),('M60','M74')]:
   self.assertNotEqual(self.byinv[one]['artwork_id'],self.byinv[two]['artwork_id']);self.assertNotEqual(self.byinv[one]['facts']['source_url'],self.byinv[two]['facts']['source_url'])
  self.assertEqual(self.byinv['P351']['facts']['medium'],'Oil on canvas');self.assertIn('Watercolour',self.byinv['P733']['facts']['medium'])
 def test_biography_and_incorrect_reverse_labels_retained_as_evidence(self):
  v=self.byinv['M86']['facts'];self.assertEqual(v['creator_label'],'Julie Corneo');self.assertIn('active between',v['creator_extraction']['detail']['original_statement'])
  self.assertIn('M283',self.byinv['M96']['facts']['marks']);self.assertEqual(self.byinv['M96']['facts']['first'],1840)
 def test_source_uncertainty_and_unknowns_survive(self):
  self.assertIsNone(self.byinv['M97']['facts']['provenance']);self.assertIn('may have been added',self.byinv['P678']['facts']['description'])
  for x in self.records:
   v=a.expected_art(x);self.assertEqual(v['status'],'review');self.assertTrue(v['research_candidate']);self.assertIsNone(v['object_form']);self.assertLessEqual(v['creation_year_end'],1970)
 def test_native_and_supplementary_evidence_formats_are_distinguished(self):
  n=json.loads(a.citation_note(self.byinv['M92'],'test-digest'));self.assertIn('native HTML',n['policy']);self.assertIn('separately labelled',n['policy']);self.assertIn('Walters 38.19',n['source_record']['decision']['basis'])
 def test_changed_editorial_facts_are_rejected(self):
  rows=copy.deepcopy(a.decisions());x=next(x for x in rows if x['state']=='approved_review_only_addition');x['facts']['creator_label']='Incorrect replacement'
  with patch.object(a,'decisions',return_value=rows),self.assertRaises(AssertionError):a.records()
if __name__=='__main__':unittest.main()
