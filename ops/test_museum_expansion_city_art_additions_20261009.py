"""Offline source, identity and preservation invariants; no database fixtures."""
import collections,copy,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-city-art-additions-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a)
class ReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds=a.r.build();cls.by={v['number']:v for v in cls.ds};cls.news,cls.links=a.records()
 def test_decision_accounting(self):self.assertEqual(collections.Counter(v['state'] for v in self.ds),{'approved_review_only_addition':14,'approved_existing_holding':1,'editorial_hold':6})
 def test_unknown_not_eligible(self):
  f=[v['facts'] for v in self.news if v['facts']['first'] is None];self.assertEqual(len(f),3);self.assertTrue(all(v['last'] is None and v['date_precision']=='unknown' for v in f))
 def test_nonempty_date_display(self):self.assertTrue(all(a.expected_art(v)['date_display'] for v in self.news))
 def test_cutoff(self):self.assertTrue(all(v['facts']['last']<=1970 for v in self.news+self.links if v['facts']['last'] is not None))
 def test_bequest_not_creation(self):self.assertIsNone(self.by[5]['facts']['first']);self.assertIn('1989',self.by[5]['facts']['source_fields']['editorial_note'])
 def test_new_acquisition_old_work(self):self.assertEqual(self.by[4]['facts']['first'],1907)
 def test_curator_qualified_range(self):self.assertEqual((self.by[9]['facts']['first'],self.by[9]['facts']['last'],self.by[9]['facts']['date_precision']),(1905,1906,'circa_range'))
 def test_artist_lifespans_not_dates(self):self.assertIsNone(self.by[10]['facts']['first']);self.assertIsNone(self.by[11]['facts']['first'])
 def test_painting_model_not_cast(self):self.assertEqual(self.by[18]['state'],'editorial_hold');self.assertIsNone(self.by[18]['facts']['first'])
 def test_cross_cutoff_exhibition_held(self):self.assertTrue(all(self.by[n]['state']=='editorial_hold' for n in [19,20,21]))
 def test_conflicting_date_held(self):self.assertEqual(self.by[15]['state'],'editorial_hold');self.assertIsNone(self.by[15]['facts']['first'])
 def test_portrait_version_held(self):self.assertEqual(self.by[1]['state'],'editorial_hold');self.assertIn('NGL001.08',self.by[1]['hold_reason'])
 def test_existing_duncan_reused(self):self.assertEqual(len(self.links),1);self.assertEqual(self.links[0]['artwork_id'],'ad501e87-0f8e-5dc0-a5bf-5c2977390991');self.assertNotIn(12,[v['decision']['number'] for v in self.news])
 def test_title_variants_preserved_as_evidence(self):self.assertIn('Tristan and Isolde',self.by[12]['facts']['titles']);self.assertIn('The Tragic Muse',self.by[16]['facts']['titles'])
 def test_drawings_remain_drawings(self):self.assertTrue(all(self.by[n]['facts']['work_type']=='drawing' for n in [4,13,16]))
 def test_lender_boundaries(self):self.assertEqual({v['institution_id'] for v in self.ds},{a.IID});self.assertFalse(any(v['facts']['title'] in ['The Riders of the Sidhe','Unicorns','The Children of Lir'] for v in self.ds))
 def test_funder_not_creation(self):self.assertEqual((self.by[16]['facts']['first'],self.by[16]['facts']['last']),(1930,1932))
 def test_unique_physical_objects(self):self.assertEqual(len({v['artwork_id'] for v in self.news+self.links}),15)
 def test_review_and_no_image_changes(self):
  for v in self.news:
   art=a.expected_art(v);self.assertEqual(art['status'],'review');self.assertNotIn('published_at',art);self.assertNotIn('primary_media_id',art)
 def test_physical_comparator_evidence(self):
  x=a.m.load(a.RUN/'physical-object-review-001.json.gz');self.assertEqual(len(x['images']),10);self.assertTrue(any(v['artwork_id']=='ad501e87-0f8e-5dc0-a5bf-5c2977390991' for v in x['images']))
 def test_reject_existing_title_change(self):
  b={k:[] for k in ['artworks','artists','media','media_assets','identifiers','museums','citations','assertions']};b['artworks']=[dict(id='original',title='Original',current_institution_id=None)];c=copy.deepcopy(b);c['artworks'][0]['title']='Changed'
  with self.assertRaises(AssertionError):a.assert_delta(b,c,[],'digest')
 def test_reject_existing_media_change(self):
  b={k:[] for k in ['artworks','artists','media','media_assets','identifiers','museums','citations','assertions']};c=copy.deepcopy(b);c['media']=[dict(artwork_id='unexpected')]
  with self.assertRaises(AssertionError):a.assert_delta(b,c,[],'digest')
if __name__=='__main__':unittest.main(verbosity=2)
