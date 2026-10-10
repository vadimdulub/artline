"""Offline production safeguards for cutoffs, physical versions and row preservation."""
import copy,hashlib,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-rhodes-more-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);r=a.r;f=r.i.f
class RhodesMoreTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds={v['number']:v for v in r.build()}
 def test_before_keeps_unknown_lower_bound(self):self.assertEqual(f.date('πριν από το 1948'),(None,1948,'before'))
 def test_abbreviated_year_range(self):self.assertEqual(f.date('1935-36'),(1935,1936,'range'))
 def test_circa_range(self):self.assertEqual(f.date('περ. 1939-1941'),(1939,1941,'circa_range'))
 def test_decade_complete(self):self.assertEqual(f.date('δεκαετία 1950'),(1950,1959,'decade'))
 def test_no_unknown_year_invention(self):self.assertEqual(f.date(None),(None,None,'unknown'))
 def test_unreviewed_syntax_fails_closed(self):
  with self.assertRaises(ValueError):f.date('1930 or later')
 def test_circa1970_and_decade1970_held(self):
  for n in [140,142,162]:self.assertEqual(self.ds[n]['state'],'cutoff_date_review_hold')
 def test_exact1970_eligible(self):self.assertEqual(self.ds[274]['state'],'approved_review_only_addition')
 def test_depicted1944_does_not_date1966_painting(self):self.assertEqual(self.ds[143]['facts']['first'],1966)
 def test_edition_range_not_silently_narrowed(self):self.assertEqual((self.ds[232]['facts']['first'],self.ds[232]['facts']['last']),(1841,1842))
 def test_existing_object_never_added(self):self.assertEqual(self.ds[158]['state'],'already_catalogued')
 def test_physical_pair_has_distinct_supports(self):
  self.assertNotEqual(self.ds[131]['source_id'],self.ds[132]['source_id']);self.assertIn('blue shirt',self.ds[131]['basis']);self.assertIn('white shirt',self.ds[132]['basis'])
 def test_single_composite_sheet_and_manuscript_units(self):
  for n in [136,278,279]:self.assertIn('one',self.ds[n]['basis'].lower());self.assertEqual(len(self.ds[n]['facts']['native_page_urls']),2)
 def test_dry_and_water_media_types(self):
  for n in [127,131,132,157,170,171,273]:self.assertEqual(self.ds[n]['facts']['work_type'],'drawing')
  for n in [208,209,213,245,274]:self.assertEqual(self.ds[n]['facts']['work_type'],'watercolor')
 def test_before_record_passes_plan_without_invented_year(self):
  news,holds=a.records();v=next(v for v in news if v['decision']['number']==245);self.assertIsNone(a.expected_art(v)['creation_year_start']);self.assertEqual(a.expected_art(v)['date_precision'],'before')
 def test_visual_comparison_images_pinned(self):
  x=a.m.load(a.RUN/'visual-assessment-001.json');self.assertEqual(len(x['images_seen']),4)
  for v in x['images_seen']:self.assertEqual(hashlib.sha256(Path(v['path']).read_bytes()).hexdigest(),v['sha256'])
 def test_empty_alternate_title_never_matches(self):
  row=dict(number=1,source_id='source',facts=dict(title='Test [Name]',titles=['Test [Name]'],inventory='1',native_page_urls=['https://example.test/item']))
  state=dict(artworks=[dict(id='other',title='Different',alternate_title=None,accession_number=None)],scoped_ids=[],source_hits=[],external_hits=[],native_id_hits=[])
  self.assertEqual(r.i.comparisons([row],state)[0]['hits'],[])
 def test_preserve_existing_status_and_image(self):
  before={k:[]for k in ['artworks','artists','media','media_assets','identifiers','museums','citations','assertions']};before['artworks']=[dict(id='existing',status='review',primary_media_id='image')]
  for key,val in [('status','published'),('primary_media_id',None)]:
   after=copy.deepcopy(before);after['artworks'][0][key]=val
   with self.assertRaises(AssertionError):a.assert_delta(before,after,[],'digest')
 def test_selected_total_and_no_publication_or_media(self):
  news,holds=a.records();self.assertEqual(len(news),65);self.assertEqual(holds,[])
  for v in news:self.assertEqual(a.expected_art(v)['status'],'review');self.assertFalse(v['facts']['image_downloaded'])
if __name__=='__main__':unittest.main()
