"""Offline physical-identity and review-state safeguards on real retained sources."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-nelson-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class NelsonSelection(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows={r['decision']['number']:r for r in a.records()};cls.held={r['number']:r for r in a.m.load(a.REVIEW)['holds']}
 def test_every_selected_object_accounted_once(self):
  self.assertEqual(len(self.rows),149);self.assertEqual(len(self.held),37);self.assertFalse(set(self.rows)&set(self.held));self.assertEqual(set(self.rows)|set(self.held),set(range(1,187)))
 def test_known_existing_work_does_not_become_an_addition(self):
  self.assertNotIn(64,self.rows);self.assertEqual(self.held[64]['state'],'existing_reconciliation');self.assertIn('5c5b1b46',self.held[64]['review_note'])
 def test_artist_lifespan_date_cannot_be_approved(self):
  self.assertNotIn(136,self.rows);self.assertEqual(self.held[136]['facts']['date_display'],'1510-1592');self.assertEqual(self.held[136]['state'],'source_hold')
 def test_close_physical_versions_are_held(self):
  for n in [50,52,55,67,112,120,121,165,171]:self.assertNotIn(n,self.rows);self.assertEqual(self.held[n]['state'],'version_hold')
 def test_current_qualifications_override_shortened_index(self):
  self.assertEqual(self.rows[184]['facts']['creator_label'],'Workshop of Doménikos Theotokópoulos, called El Greco')
  self.assertEqual(self.rows[110]['facts']['creator_label'],'Attributed to Sebastien Bourdon')
  self.assertEqual(self.rows[164]['facts']['creator_label'],'Circle of Jan Wellens de Cock')
  for n in [110,164,184]:self.assertEqual(self.rows[n]['decision']['source_discrepancies'],['Index/detail creator_label differs'])
 def test_anonymous_russian_panels_and_actual_gift_provenance_retained(self):
  self.assertEqual(self.rows[185]['facts']['creator_label'],'Moscow School');self.assertEqual(self.rows[186]['facts']['creator_label'],'Unknown')
  for n in [185,186]:
   v=self.rows[n]['facts'];self.assertEqual((v['first'],v['last']),(1490,1510));self.assertEqual(v['credit_line'],'Gift of Dr. Fred Irwig');self.assertTrue(any('Istanbul' in t for t in v['source_text']))
 def test_ensemble_counting_is_not_multiplied_by_components(self):
  self.assertEqual(self.rows[161]['facts']['inventory'],'38-4 A-C');self.assertEqual(self.rows[179]['facts']['inventory'],'32-207 A-P')
  self.assertIn('One triptych',self.rows[161]['decision']['basis']);self.assertIn('One entire altarpiece',self.rows[179]['decision']['basis']);self.assertEqual(self.held[155]['state'],'group_version_hold')
 def test_companion_panels_have_separate_native_accessions(self):
  self.assertEqual(self.rows[123]['facts']['inventory'],'46-9/1');self.assertEqual(self.rows[124]['facts']['inventory'],'46-9/2');self.assertNotEqual(self.rows[123]['facts']['source_id'],self.rows[124]['facts']['source_id'])
 def test_magdalen_comparison_uses_physical_source_evidence(self):
  self.assertIn('157x121cm',self.rows[183]['decision']['basis']);self.assertIn('101.6x81.92cm',self.rows[183]['decision']['basis']);self.assertEqual(len(a.m.load(a.RUN/'prior-body-verification-001.json.gz')['rows']),3)
 def test_web_extract_limit_and_actual_unknowns_are_preserved(self):
  for r in self.rows.values():
   self.assertIn('not original object HTTP bytes',r['source_format']);self.assertEqual(r['facts'],r['source_facts']);self.assertIsNone(r['facts']['object_form'])
  self.assertTrue(any(r['facts']['source_rights'] is None for r in self.rows.values()))
 def test_review_only_without_media_or_publication(self):
  for r in self.rows.values():
   v=a.expected_art(r);self.assertEqual(v['status'],'review');self.assertEqual(v['current_institution_id'],a.IID);self.assertTrue(v['research_candidate']);self.assertLessEqual(v['creation_year_end'],1970);self.assertNotIn('published_at',v);self.assertNotIn('primary_media_id',v)
 def test_reworked_and_alternative_dates_survive_selection(self):
  self.assertEqual(self.rows[102]['facts']['date_display'],'1892; reworked 1929');self.assertEqual(self.rows[100]['facts']['date_display'],'1773 or 1775')
if __name__=='__main__':unittest.main()
