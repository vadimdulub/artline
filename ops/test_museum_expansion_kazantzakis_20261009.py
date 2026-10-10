"""Physical units, literal attribution, date scope and row-preservation safeguards."""
import copy,hashlib,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-kazantzakis-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);r=a.r;f=r.i.f
class KazantzakisTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds={v['number']:v for v in r.build()}
 def test_unknown_date_not_invented(self):self.assertEqual(f.date(None),(None,None,'unknown'))
 def test_date_range_preserved(self):self.assertEqual(f.date('1927 - 1928'),(1927,1928,'range'))
 def test_unreviewed_date_fails_closed(self):
  with self.assertRaises(ValueError):f.date('1949 performance, drawing date unknown')
 def test_anonymous_not_overwritten_by_enrichment(self):
  d=self.ds[1];self.assertEqual(d['facts']['creator_label'],'Άγνωστος δημιουργός');self.assertIn('Ανεμογιάννης',d['facts']['semantic_enrichment']['Δημιουργός'][0]);self.assertEqual(d['state'],'approved_review_only_addition')
 def test_no_artist_lifespan_date(self):self.assertEqual(self.ds[1]['facts']['first'],1949)
 def test_reverse_and_annotation_held(self):
  for n in [91,92]:self.assertEqual(self.ds[n]['state'],'physical_unit_review_hold')
 def test_correspondence_not_art(self):
  for n in [104,106,108,115]:self.assertEqual(self.ds[n]['state'],'not_an_artwork')
 def test_post1970_excluded(self):
  self.assertEqual(self.ds[57]['state'],'outside_creation_scope');self.assertEqual(self.ds[101]['state'],'outside_creation_scope')
 def test_several_figures_still_one_sheet(self):
  for n in [1,4,70,99,122,126,127]:self.assertIn('one',self.ds[n]['basis'].lower())
 def test_incomplete_physical_artwork_retained(self):
  for n in [39,93]:self.assertEqual(self.ds[n]['state'],'approved_review_only_addition');self.assertTrue(self.ds[n]['facts']['description_md'])
 def test_missing_image_does_not_remove_artwork(self):self.assertEqual(self.ds[20]['state'],'approved_review_only_addition')
 def test_unknown_medium_dimensions_accessions_preserved(self):
  for n in [1,121,130]:
   for key in ['medium','dimensions_text','inventory']:self.assertIsNone(self.ds[n]['facts'][key])
 def test_one_explicit_medium_supported(self):self.assertIn('pencil',self.ds[68]['facts']['medium'])
 def test_illustration_medium_not_invented(self):
  for n in [130,131,132,133,134]:self.assertEqual(self.ds[n]['facts']['work_type'],'unknown')
 def test_missing_inventory_not_duplicate_match(self):
  row=dict(number=1,source_id='source',facts=dict(title='Unique title',titles=['Unique title'],inventory=None,native_page_urls=['https://example.test/item']));state=dict(artworks=[dict(id='other',title='Completely different',alternate_title=None,accession_number=None)],scoped_ids=[],source_hits=[],external_hits=[],native_id_hits=[]);self.assertEqual(r.i.comparisons([row],state)[0]['hits'],[])
 def test_reference_evidence_pinned(self):
  x=a.m.load(a.RUN/'visual-reference-captures-001.json');self.assertEqual(len(x['rows']),102);self.assertEqual(sum(v['receipt'].get('available',True)for v in x['rows']),101)
  for v in x['rows']:self.assertEqual(hashlib.sha256(Path(v['receipt']['path']).read_bytes()).hexdigest(),v['receipt']['sha256'])
 def test_preserve_existing_image_status_dates(self):
  before={k:[]for k in ['artworks','artists','media','media_assets','identifiers','museums','citations','assertions']};before['artworks']=[dict(id='existing',status='review',primary_media_id='image',creation_year_start=None)]
  for key,val in [('status','published'),('primary_media_id',None),('creation_year_start',1927)]:
   after=copy.deepcopy(before);after['artworks'][0][key]=val
   with self.assertRaises(AssertionError):a.assert_delta(before,after,[],'digest')
 def test_slug_safe_and_source_id_preserved(self):
  news,holds=a.records();self.assertEqual(len(news),100);self.assertEqual(holds,[])
  for v in news:self.assertNotIn('/',v['slug']);self.assertIn('/',v['facts']['source_id']);self.assertEqual(a.expected_art(v)['status'],'review')
 def test_all_decisions_accounted(self):
  self.assertEqual(len(self.ds),134);self.assertEqual(sum(v['state']=='approved_review_only_addition'for v in self.ds.values()),100);self.assertEqual(sum(v['state']=='outside_creation_scope'for v in self.ds.values()),28)
if __name__=='__main__':unittest.main()
