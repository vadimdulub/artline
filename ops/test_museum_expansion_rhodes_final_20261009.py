"""Offline physical-identity, date and existing-row preservation safeguards."""
import copy,hashlib,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-rhodes-final-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);r=a.r;f=r.i.f
class RhodesFinalTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds={v['number']:v for v in r.build()}
 def test_one_digit_range(self):self.assertEqual(f.date('1986-7'),(1986,1987,'range'))
 def test_circa_short_range(self):self.assertEqual(f.date('περ. 1936-40'),(1936,1940,'circa_range'))
 def test_no_unknown_year_invention(self):self.assertEqual(f.date(None),(None,None,'unknown'))
 def test_unreviewed_syntax_fails_closed(self):
  with self.assertRaises(ValueError):f.date('1930 or later')
 def test_exact1970_eligible_type_from_medium(self):
  d=self.ds[312];self.assertEqual(d['state'],'approved_review_only_addition');self.assertEqual(d['facts']['first'],1970);self.assertEqual(d['facts']['work_type'],'painting')
 def test_exhibition_not_creation(self):
  for n,y in [(300,1946),(343,1930),(344,1952)]:self.assertEqual(self.ds[n]['facts']['first'],y)
 def test_qualified_creator_preserved(self):self.assertEqual(self.ds[298]['facts']['creator_label'],'Σπυρίδων Βικάτος(;)')
 def test_medium_unknown_retained(self):
  for n in [281,282,352,362]:self.assertIsNone(self.ds[n]['facts']['medium'])
 def test_medium_conflicts_explicit(self):
  for n in [301,369]:self.assertIn('narrative',self.ds[n]['basis']);self.assertTrue(self.ds[n]['facts']['medium'])
 def test_existing_translation_link_no_duplicate(self):
  news,holds=a.records();self.assertEqual([v['decision']['number']for v in holds],[291]);self.assertNotIn(291,[v['decision']['number']for v in news])
 def test_double_sided_sheet_one_record(self):
  self.assertEqual(self.ds[326]['facts']['inventory'],'1125');self.assertIn('one1930–1938 double-sided',self.ds[326]['basis']);self.assertIn('not two sides',self.ds[326]['basis'])
 def test_three_models_distinct(self):
  self.assertEqual(len({self.ds[n]['source_id']for n in [360,363,364]}),3)
  for n in [360,363,364]:self.assertEqual(self.ds[n]['facts']['work_type'],'drawing')
 def test_material_based_types(self):
  for n in r.DRAWINGS:self.assertEqual(self.ds[n]['facts']['work_type'],'drawing')
  self.assertEqual(self.ds[320]['facts']['work_type'],'watercolor')
 def test_visual_images_pinned(self):
  vs=a.m.load(a.RUN/'visual-assessment-001.json')['images_seen'];self.assertEqual(len(vs),12)
  for v in vs:self.assertEqual(hashlib.sha256(Path(v['path']).read_bytes()).hexdigest(),v['sha256'])
 def test_empty_alternate_title_never_matches(self):
  row=dict(number=1,source_id='source',facts=dict(title='Test [Name]',titles=['Test [Name]'],inventory='1',native_page_urls=['https://example.test/item']));state=dict(artworks=[dict(id='other',title='Different',alternate_title=None,accession_number=None)],scoped_ids=[],source_hits=[],external_hits=[],native_id_hits=[]);self.assertEqual(r.i.comparisons([row],state)[0]['hits'],[])
 def test_preserve_existing_status_image_and_unknown_date(self):
  before={k:[]for k in ['artworks','artists','media','media_assets','identifiers','museums','citations','assertions']};before['artworks']=[dict(id='existing',status='review',primary_media_id='image',creation_year_start=None,current_institution_id=None)]
  for key,val in [('status','published'),('primary_media_id',None),('creation_year_start',1962)]:
   after=copy.deepcopy(before);after['artworks'][0][key]=val
   with self.assertRaises(AssertionError):a.assert_delta(before,after,[dict(artwork_id='existing',institution_id=a.IID)],'digest')
 def test_no_unknown_or_after_cutoff_added(self):
  news,holds=a.records();self.assertEqual(len(news),43);self.assertEqual(len(holds),1)
  for v in news:self.assertLessEqual(v['facts']['last'],1970);self.assertEqual(a.expected_art(v)['status'],'review');self.assertFalse(v['facts']['image_downloaded'])
 def test_complete_decision_accounting(self):
  self.assertEqual(len(self.ds),100);self.assertEqual(sum(v['state']=='unknown_date_review_deferred'for v in self.ds.values()),41);self.assertEqual(sum(v['state']=='outside_creation_scope'for v in self.ds.values()),15)
if __name__=='__main__':unittest.main()
