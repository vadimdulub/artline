#!/usr/bin/env python3
"""Offline chronology, role, identity and source-chain checks; no database fixtures."""
import importlib.util,tempfile,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-belvedere-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);w=a.w;m=a.m
class Dates(unittest.TestCase):
 def test_german_circa(self):self.assertEqual(w.creation('um 1885')['date_precision'],'circa')
 def test_before_unknown_lower_bound(self):self.assertEqual(w.creation('before 1907'),dict(first=None,last=1907,date_precision='before',date_issue=None))
 def test_before1971_eligible(self):self.assertIsNone(w.creation('before 1971')['date_issue'])
 def test_after_unbounded_held(self):self.assertIsNotNone(w.creation('nach 1900')['date_issue'])
 def test_unknown_not_from_acquisition(self):self.assertEqual(w.creation('undatiert')['date_precision'],'unknown')
 def test_life_date_not_creation_statement(self):self.assertIsNotNone(w.creation('(1840 Wien – 1905 Berlin)')['date_issue'])
 def test_slash_envelope(self):self.assertEqual((w.creation('1870/1880')['first'],w.creation('1870/1880')['last']),(1870,1880))
 def test_circa1970_held(self):self.assertIsNotNone(w.creation('um 1970')['date_issue'])
 def test_post_cutoff_held(self):self.assertIsNotNone(w.creation('1973')['date_issue'])
class Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=a.records();cls.byid={r['facts']['source_id']:r for r in cls.records};cls.facts={r['source_id']:r['facts'] for r in m.load(a.CANDIDATES)['rows']};cls.queue=m.load(a.RUN/'native-followup-queue-001.json.gz')
 def test112_checked_source_chains(self):self.assertEqual(len(self.records),112)
 def test_unique_native_ids_and_accessions(self):
  self.assertEqual(len({r['facts']['native_object_id'] for r in self.records}),112);self.assertEqual(len({r['facts']['inventory'] for r in self.records}),112)
 def test_all240_index_objects_accounted(self):self.assertEqual(len(self.records)+len(self.queue['rows'])+len(self.queue['index_unselected']),240)
 def test_explicit_before_bounds_not_fabricated(self):self.assertEqual(sum(r['facts']['first'] is None for r in self.records),4)
 def test_before_bound_projected_as_before(self):
  v=a.expected_art(self.byid['20']);self.assertIsNone(v['creation_year_start']);self.assertEqual(v['creation_year_end'],1907);self.assertEqual(v['date_precision'],'before')
 def test_depicted_emperor_not_artist(self):self.assertEqual(self.byid['8']['facts']['creator_label'],'Ferdinand Georg Waldmüller')
 def test_depicted_general_not_artist(self):self.assertEqual(self.byid['133']['facts']['creator_label'],"Sigmund L'Allemand")
 def test_study_own_material_and_creator(self):
  f=self.byid['193']['facts'];self.assertEqual(f['creator_label'],'Friedrich von Amerling');self.assertEqual(f['medium'],'Oil on paper on canvas');self.assertIn('ENTWURF',f['title'])
 def test_nested_biography_uncertainty(self):
  f=self.byid['105']['facts'];self.assertEqual(f['creator_label'],'Franz Gasser');self.assertIn('1838',f['native_artist_field']);self.assertEqual(f['first'],1826)
 def test_qualified_regional_creator(self):self.assertEqual(self.byid['412']['facts']['creator_label'],'Attributed to Slowakischer Maler')
 def test_former_attribution_not_current(self):
  f=self.facts['528'];self.assertEqual(f['creator_label'],'Attributed to Domenico Antonio Vaccaro');self.assertIn('Anton Kern',f['identity_creator_labels']);self.assertNotIn('Anton Kern',f['creator_label'])
 def test_circle_retains_qualification(self):self.assertEqual(self.facts['493']['creator_label'],'Franz Anton Maulbertsch (Umkreis)')
 def test_source_conflicts_remain_held(self):
  held={r['source_id']:r for r in self.queue['rows']};self.assertEqual(held['39']['review_state'],'source_hold');self.assertEqual(held['483']['review_state'],'source_hold')
 def test_background_contributor_not_dropped(self):
  self.assertIn('(Hintergrund) Theodor von Hörmann',self.facts['611']['creator_label']);self.assertNotIn('611',self.byid)
 def test_only_former_creator_remains_unresolved(self):self.assertIsNone(self.facts['498']['creator_label'])
 def test_portfolio_counts_once(self):
  self.assertEqual(self.byid['97']['facts']['inventory'],'1093a-p');self.assertEqual(self.byid['97']['facts']['work_type'],'unknown')
 def test_unreliable_source_type_not_rewritten(self):
  f=self.byid['7981']['facts'];self.assertEqual(f['source_work_type'],'Blackboard');self.assertEqual(f['work_type'],'unknown')
 def test_caption_translation_is_discovery_only(self):
  self.assertIn('Wolkenschatten',self.byid['25']['facts']['titles']);self.assertNotIn('alternate_title',a.expected_art(self.byid['25']))
 def test_ids_not_accessions(self):self.assertEqual(self.byid['25']['facts']['inventory'],'1023');self.assertEqual(self.byid['25']['facts']['native_object_id'],'25')
 def test_known_duplicate_not_reinserted(self):self.assertTrue({'73','540','471','509','656'}.isdisjoint(self.byid))
 def test_none_of_later_candidates_implicitly_approved(self):self.assertEqual(sum(r['review_state']=='unselected_candidate' for r in self.queue['rows']),80)
 def test_four_source_and_seven_identity_holds(self):
  self.assertEqual(sum(r['review_state']=='source_hold' for r in self.queue['rows']),4);self.assertEqual(sum(r['review_state']=='identity_hold' for r in self.queue['rows']),7)
 def test_source_internal_id_separate(self):self.assertNotEqual(self.byid['8']['facts']['index_internal_id'],self.byid['8']['facts']['native_object_id'])
 def test_german_generation_suffix_identity(self):self.assertIn('sigrist',a.i.search_terms(self.facts['764']))
 def test_current_qualified_and_former_names_searched(self):self.assertTrue({'vaccaro','kern','gran'}.issubset(a.i.search_terms(self.facts['528'])))
 def test_no_image_or_display_projection(self):
  for r in self.records:
   v=a.expected_art(r);self.assertEqual(v['status'],'review');self.assertNotIn('current_location_text',v);self.assertNotIn('primary_media_id',v)
 def test_session_urls_canonicalized(self):self.assertEqual(w.c.cleanurl('/objects/25/wolkenschatten;jsessionid=abcd?idx=3'),a.d.BASE+'/objects/25/wolkenschatten')
 def test_hash_mutation_rejected(self):
  with tempfile.TemporaryDirectory(prefix='artline-belvedere-proof-') as tmp:
   p=Path(tmp)/'record';p.write_bytes(b'changed')
   with self.assertRaises(AssertionError):a.checked_reference(dict(path=str(p),sha256='0'*64))
if __name__=='__main__':unittest.main()
