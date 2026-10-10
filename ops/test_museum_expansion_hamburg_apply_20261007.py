"""Offline source-conflict, version and selection checks; never connects to a database."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-hamburg-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class HamburgSelection(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records={v['facts']['source_id']:v for v in a.records()};cls.queue={v['source_id']:v for v in a.m.load(a.RUN/'followup-queue-001.json.gz')['rows']}
 def test_coverage_counts_distinct_objects(self):
  self.assertEqual(len(self.records),84);self.assertEqual(len(self.queue),199);self.assertFalse(set(self.records)&set(self.queue))
  self.assertEqual(sum(v['review_state']=='existing_identity_reconciliation' for v in self.queue.values()),19)
 def test_beckmann_dimension_resolution_preserves_discrepancies(self):
  r=self.records['Q114053439'];self.assertEqual(r['facts']['dimensions_text'],'150 × 115.5 cm')
  self.assertIn('+1155',[v['value']['amount'] for v in r['source_facts']['dimension_claims']])
  self.assertIn('official caption50x115.5cm',r['decision']['basis'])
 def test_ree_dimension_resolution_is_sourced(self):
  r=self.records['Q114065058'];self.assertEqual(r['facts']['dimensions_text'],'66 × 53.5 cm')
  self.assertIn('+535',[v['value']['amount'] for v in r['source_facts']['dimension_claims']]);self.assertEqual(r['facts']['date_precision'],'range')
 def test_reworking_date_not_lost(self):
  r=self.records['Q115633284'];self.assertEqual((r['facts']['first'],r['facts']['last']),(1910,1926));self.assertEqual(r['source_facts']['last'],1910)
  self.assertIn('überarbeitet 1926',r['facts']['date_display'])
 def test_impossible_lifespan_date_held(self):
  self.assertNotIn('Q114065635',self.records);self.assertIn('1805–1886',self.queue['Q114065635']['reason'])
 def test_calderon_existing_object_not_reinserted(self):
  self.assertNotIn('Q110125296',self.records);q=self.queue['Q110125296'];self.assertEqual(q['review_state'],'existing_identity_reconciliation')
  self.assertIn('de0f6ce7-ddd0-5fa5-be4f-a9de27e643eb',{x['entity_id'] for x in q['comparison']['source_hits']})
 def test_ambiguous_physical_versions_held(self):
  for qid in ['Q111165249','Q116313643','Q121692307','Q121692311','Q119566360','Q119566362','Q116963188']:
   self.assertNotIn(qid,self.records);self.assertEqual(self.queue[qid]['review_state'],'editorial_hold')
 def test_altarpiece_counting_and_casts_held(self):
  for qid in ['Q121547676','Q121547698','Q121547699','Q121547700','Q121547701','caption-013','caption-021']:self.assertIn(qid,self.queue)
 def test_caption_corroboration_not_double_counted(self):
  for n,qid in a.r.CAPTION_OVERLAPS.items():self.assertIn(qid,self.records);self.assertEqual(self.queue['caption-%03d'%n]['review_state'],'corroborating_caption')
 def test_unknowns_remain_null(self):
  v=self.records['Q123014396']['facts'];self.assertIsNone(v['inventory']);self.assertIsNone(v['medium']);self.assertIsNone(v['dimensions_text'])
  self.assertIsNone(self.records['Q102425731']['facts']['medium'])
 def test_all_review_only_with_no_artist_or_media_claim(self):
  for v in self.records.values():
   expected=a.expected_art(v);self.assertEqual(expected['status'],'review');self.assertTrue(expected['research_candidate']);self.assertEqual(expected['current_institution_id'],a.IID)
   self.assertLessEqual(v['facts']['last'],1970);self.assertIn('No image permission or painter-authority link inferred',v['decision']['limitation'])
 def test_source_physical_qualifiers_not_flattened(self):
  rs=list(self.records.values());self.assertTrue(any('(painting support)' in (v['facts']['medium'] or '') for v in rs))
  labels=a.f.f.sources('wikidata-creator-capture-001.json.gz')|a.f.f.sources('wikidata-extra-label-capture-002.json.gz')
  f=copy.deepcopy(self.records['Q110406866']['source_facts']);f['material_claims'][0]['qualifiers']={'P999999':[]}
  with self.assertRaises(AssertionError):a.r.rendered(f,labels)
if __name__=='__main__':unittest.main()
