"""Offline retained-source checks; no test database or catalogue fixtures."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-next-samples-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class Samples(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows={r['provider']:r for r in a.records()}
 def test_two_sources_are_not_the_unapproved_queues(self):
  self.assertEqual(len(self.rows),2)
  self.assertEqual(len(a.m.load(a.f.a.RUN/'selected-official-queue-001.json')['selected']),172)
  self.assertEqual(len(a.m.load(a.f.d.RUN/'selected-official-queue-001.json')['selected']),118)
 def test_group_portrait_counts_once(self):
  v=self.rows['ago']['facts'];self.assertEqual(v['title'],'The Three Robinson Sisters');self.assertEqual(v['inventory'],'2007/33');self.assertEqual(v['creator_label'],'George Theodore Berthon')
 def test_artist_life_and_gift_dates_do_not_replace_creation(self):
  v=self.rows['ago']['facts'];self.assertEqual((v['first'],v['last']),(1846,1846));self.assertIn('1944',v['credit_line']);self.assertIn('1806 - 1892',v['source_fields']['Creator'])
 def test_native_html_json_agree_on_detroit_identity(self):
  v=self.rows['detroit']['facts'];self.assertEqual(v['native_metadata']['core']['objectNumber'],'2020.15');self.assertEqual(v['inventory'],'2020.15');self.assertEqual(v['first'],1667);self.assertEqual(v['medium'],'Oil on copper')
 def test_actual_rights_and_discrepancies_remain_evidence(self):
  self.assertEqual(self.rows['ago']['facts']['source_rights'],'Photo © AGO');self.assertEqual(self.rows['detroit']['facts']['source_rights'][0]['type'],'Public Domain');self.assertEqual(len(self.rows['detroit']['decision']['source_discrepancies']),2)
 def test_partial_sources_stay_held(self):
  self.assertEqual(a.m.load(a.f.d.RUN/'partial-capture-001.json')['state'],'stopped_on_http429');self.assertEqual(a.m.load(a.f.a.RUN/'partial-capture-001.json')['complete_object_pages'],1)
 def test_creation_cutoff_and_literal_season_years(self):
  self.assertIsNotNone(a.f.a.creation('1971')['date_issue']);self.assertIsNotNone(a.f.a.creation('20th century')['date_issue']);self.assertIsNotNone(a.f.a.creation('unknown')['date_issue']);self.assertEqual(a.f.a.creation('Winter 1916-1917')['last'],1917)
 def test_qualified_detroit_range_retains_uncertainty(self):
  v=a.f.d.creation('probably between 1650 and 1675');self.assertEqual((v['first'],v['last'],v['date_precision']),(1650,1675,'circa_range'))
 def test_review_only_and_no_synthesized_object_form(self):
  for v in self.rows.values():
   e=a.expected_art(v);self.assertEqual(e['status'],'review');self.assertTrue(e['research_candidate']);self.assertEqual(e['current_institution_id'],v['institution_id']);self.assertIsNone(e['object_form']);self.assertNotIn('primary_media_id',e);self.assertNotIn('published_at',e)
 def test_historical_policy_requires_both_exact_versions(self):
  p=a.h.checked_policy(dict(path='AGENTS.md',sha256=a.h.OLD));self.assertEqual(p,a.h.BACKUP)
  with self.assertRaises(AssertionError):a.h.checked_policy(dict(path='AGENTS.md',sha256='0'*64))
 def test_policy_adapter_does_not_accept_other_changed_artifacts(self):
  ref=a.reference(a.REVIEW);ref['sha256']='0'*64
  with self.assertRaises(AssertionError):a.checked_reference(ref)
if __name__=='__main__':unittest.main()
