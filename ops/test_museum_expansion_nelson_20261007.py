"""Offline source-contract checks using retained real research evidence."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-nelson-facts-20261007.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
class NelsonSources(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.triage=f.m.load(f.RUN/'native-candidates-003.json.gz');cls.rows={r['number']:r for r in cls.triage['rows']}
 def test_all_selected_sources_complete_and_reproducible(self):
  self.assertEqual(len(self.rows),186);self.assertFalse(self.triage['errors'])
  for n,r in self.rows.items():
   _,_,p,refs=f.page(n);self.assertTrue(p['complete']);self.assertEqual(f.facts(p),r['facts']);self.assertEqual(refs,r['source_references'])
 def test_dou_signature_is_separate_from_inventory(self):
  v=self.rows[50]['facts'];self.assertEqual(v['inventory'],'32-77');self.assertIn('G Dou 1663 AE t. 50.',v['source_fields']['Signed'][0]);self.assertEqual(self.rows[50]['state'],'candidate')
 def test_ruysdael_signature_is_separate_from_inventory(self):
  v=self.rows[58]['facts'];self.assertEqual(v['inventory'],'F61-72');self.assertEqual(v['source_fields']['Signed'],['"S V Ruysdael 1644"']);self.assertEqual(self.rows[58]['state'],'candidate')
 def test_repeated_index_is_not_multiple_artworks(self):
  q=f.m.load(f.RUN/'selected-official-queue-001.json');self.assertEqual(len(q['duplicate_indexes']),8)
  self.assertEqual(len({r['inventory'] for r in q['selected']}),len(q['selected']))
 def test_long_source_sections_are_preserved(self):
  _,_,p,refs=f.page(119);self.assertEqual(p['total_lines'],655);self.assertEqual(len(p['lines']),655);self.assertEqual(len(refs),4)
 def test_workshop_qualification_is_not_promoted_to_artist(self):
  r=self.rows[184];self.assertEqual(r['facts']['creator_label'],'Workshop of Doménikos Theotokópoulos, called El Greco');self.assertEqual(r['state'],'source_hold')
 def test_former_attributions_remain_separate(self):
  v=self.rows[67]['facts'];self.assertEqual(v['creator_label'],'Nathaniel Dance-Holland');self.assertEqual(v['historical_creator_labels'],['Francis Cotes']);self.assertIn('Francis Cotes',v['identity_creator_labels'])
 def test_russian_unknown_and_school_labels_are_supported(self):
  self.assertEqual(self.rows[185]['facts']['creator_label'],'Moscow School');self.assertEqual(self.rows[186]['facts']['creator_label'],'Unknown')
  for n in [185,186]:
   v=self.rows[n]['facts'];self.assertEqual(v['credit_line'],'Gift of Dr. Fred Irwig');self.assertEqual((v['first'],v['last']),(1490,1510));self.assertIn('Russian',v['source_terms']);self.assertEqual(self.rows[n]['state'],'candidate')
 def test_artist_lifespan_is_not_approved_creation_evidence(self):
  r=self.rows[136];self.assertEqual(r['state'],'source_hold');self.assertIn('Creation field repeats artist lifespan',r['reasons'])
 def test_alternative_title_is_identity_evidence(self):
  v=self.rows[5]['facts'];self.assertEqual(v['title'],'George and Emma Eastman');self.assertIn('A Fashionable Inn',v['titles'])
 def test_literal_alternative_and_reworked_dates_are_retained(self):
  v=self.rows[100]['facts'];self.assertEqual(v['date_display'],'1773 or 1775');self.assertEqual((v['first'],v['last']),(1773,1775))
  v=self.rows[102]['facts'];self.assertEqual(v['date_display'],'1892; reworked 1929');self.assertEqual((v['first'],v['last']),(1892,1929))
 def test_post_cutoff_and_unmapped_dates_are_held_before_capture(self):
  q=f.m.load(f.RUN/'selected-official-queue-001.json');held={r['title']:r for r in q['held']};self.assertEqual(held['Port-au-Prince Street']['date_display'],'1979');self.assertIn('Saint Luke',held)
 def test_captured_facts_keep_unknown_rights_and_restricted_form(self):
  self.assertTrue(any(r['facts']['source_rights'] is None for r in self.rows.values()))
  for r in self.rows.values():self.assertIsNone(r['facts']['object_form'])
 def test_hash_mismatch_cannot_validate_evidence(self):
  bad=dict(self.rows[1]['source_references'][0],sha256='0'*64)
  with self.assertRaises(AssertionError):f.checked_reference(bad)
if __name__=='__main__':unittest.main()
