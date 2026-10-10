"""Offline date,copy/version,attribution and preservation regressions; no databases."""
import copy,hashlib,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-kazantzakis-more-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);r=a.r;f=r.i.f
class KazantzakisMoreTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds={v['number']:v for v in r.build()}
 def test_unknown_date_not_invented(self):self.assertEqual(f.date(None),(None,None,'unknown'))
 def test_date_range_preserved(self):self.assertEqual(f.date('1927 - 1928'),(1927,1928,'range'))
 def test_unreviewed_date_fails_closed(self):
  with self.assertRaises(ValueError):f.date('1940 production; copy date unknown')
 def test_anonymous_not_overwritten_by_enrichment(self):
  for d in self.ds.values():
   self.assertEqual(d['facts']['creator_label'],'Άγνωστος δημιουργός');self.assertIn('Ανεμογιάννης',d['facts']['semantic_enrichment']['Δημιουργός'][0])
 def test_object_dates_not_lifespans(self):
  self.assertEqual(self.ds[1]['facts']['first'],1940);self.assertEqual(self.ds[83]['facts']['first'],1941)
 def test_copies_not_counted_as_originals(self):
  for n in [15,25,33,80]:self.assertEqual(self.ds[n]['state'],'reproduction_review_hold')
 def test_image_description_mismatch_held(self):self.assertEqual(self.ds[28]['state'],'source_identity_review_hold')
 def test_copy_originals_do_not_inherit_elia_holding(self):
  for n in [4,12]:self.assertEqual(self.ds[n]['state'],'approved_review_only_addition');self.assertIn('ELIA',self.ds[n]['basis']);self.assertEqual(self.ds[n]['institution_id'],a.IID)
 def test_related_designs_preserve_separate_supports(self):
  for n in [4,12,35,49,52,53,54,59,66,79,82]:self.assertEqual(self.ds[n]['state'],'approved_review_only_addition')
 def test_multiple_panels_count_once(self):
  for n in [37,38,39,81,93,108]:self.assertIn('one',self.ds[n]['basis'].lower())
 def test_title_correction_grounded_in_same_object(self):
  for n in [1,91]:
   v=self.ds[n]['facts'];self.assertIn('\ufffd',v['source_title_literal']);self.assertNotIn('\ufffd',v['title']);self.assertIn(v['title'],v['source_narrative']);self.assertEqual(v['source_fields']['Τίτλος'],[v['source_title_literal']])
 def test_mixed_technique_not_assumed_flat_drawing(self):
  v=self.ds[83]['facts'];self.assertEqual(v['work_type'],'unknown');self.assertIn('μικτή τεχνική',v['medium'])
 def test_costume_textile_not_artwork_medium(self):
  for n in [23,70,72]:self.assertIsNone(self.ds[n]['facts']['medium'])
 def test_unknown_dimensions_accessions_preserved(self):
  for d in self.ds.values():
   for key in ['dimensions_text','inventory']:self.assertIsNone(d['facts'][key])
 def test_missing_inventory_not_duplicate_match(self):
  row=dict(number=1,source_id='source',facts=dict(title='Unique title',titles=['Unique title'],inventory=None,native_page_urls=['https://example.test/item']));state=dict(artworks=[dict(id='other',title='Completely different',alternate_title=None,accession_number=None)],scoped_ids=[],source_hits=[],external_hits=[],native_id_hits=[]);self.assertEqual(r.i.comparisons([row],state)[0]['hits'],[])
 def test_reference_evidence_pinned(self):
  x=a.m.load(a.RUN/'visual-reference-captures-001.json');self.assertEqual(len(x['rows']),110);self.assertTrue(all(v['receipt']['available']for v in x['rows']))
  for v in x['rows']:self.assertEqual(hashlib.sha256(Path(v['receipt']['path']).read_bytes()).hexdigest(),v['receipt']['sha256'])
 def test_preserve_existing_image_status_dates(self):
  before={k:[]for k in ['artworks','artists','media','media_assets','identifiers','museums','citations','assertions']};before['artworks']=[dict(id='existing',status='review',primary_media_id='image',creation_year_start=None)]
  for key,val in [('status','published'),('primary_media_id',None),('creation_year_start',1940)]:
   after=copy.deepcopy(before);after['artworks'][0][key]=val
   with self.assertRaises(AssertionError):a.assert_delta(before,after,[],'digest')
 def test_slug_and_source_identity_preserved(self):
  news,holds=a.records();self.assertEqual(len(news),105);self.assertEqual(holds,[])
  for v in news:self.assertNotIn('/',v['slug']);self.assertIn('/',v['facts']['source_id']);self.assertEqual(a.expected_art(v)['status'],'review')
 def test_prior_linked_existing_work_preserved(self):self.assertEqual(len(a.prior_ids()),921)
 def test_all_decisions_accounted(self):
  self.assertEqual(len(self.ds),110);self.assertEqual(sum(v['state']=='approved_review_only_addition'for v in self.ds.values()),105);self.assertEqual(sum(v['state']=='reproduction_review_hold'for v in self.ds.values()),4)
if __name__=='__main__':unittest.main()
