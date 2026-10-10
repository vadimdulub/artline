"""Offline review and preservation checks; no database fixtures or connections."""
import collections,copy,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-box-continuation-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a)
class ReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds=a.r.build();cls.by={v['number']:v for v in cls.ds};cls.rs=a.records()[0]
 def test_decisions(self):self.assertEqual(collections.Counter(v['state'] for v in self.ds),{'approved_review_only_addition':21,'editorial_hold':4,'already_catalogued':2})
 def test_unknown_dates(self):
  vs=[v['facts'] for v in self.rs if v['facts']['first'] is None];self.assertEqual(len(vs),8);self.assertTrue(all(v['last'] is None and v['date_precision']=='unknown' for v in vs))
 def test_nonempty_date_labels(self):self.assertTrue(all(a.expected_art(v)['date_display'] for v in self.rs))
 def test_cutoff(self):self.assertTrue(all(v['facts']['last']<=1970 for v in self.rs if v['facts']['last'] is not None))
 def test_depicted_year_not_creation(self):self.assertEqual(self.by[1915]['facts']['first'],1670);self.assertIn('1666',self.by[1915]['facts']['title']);self.assertIsNone(self.by[1900]['facts']['first'])
 def test_acquisition_not_creation(self):self.assertIsNone(self.by[1947]['facts']['first']);self.assertIsNone(self.by[1966]['facts']['first']);self.assertEqual(self.by[2038]['facts']['last'],1969)
 def test_commission_not_creation(self):self.assertIsNone(self.by[1903]['facts']['first']);self.assertIn('commissioned 1955',self.by[1903]['facts']['date_display'])
 def test_lifespans_not_creation(self):self.assertIsNone(self.by[200001]['facts']['first']);self.assertIsNone(self.by[200003]['facts']['first'])
 def test_qualified_attributions(self):self.assertTrue(all(self.by[n]['facts']['creator_label'].startswith('Attributed to') for n in [1891,1915]))
 def test_qualified_decade(self):self.assertEqual(self.by[1894]['facts']['date_precision'],'circa_range');self.assertIn('believed',self.by[1894]['facts']['date_display'])
 def test_exhibition_not_creation(self):self.assertIsNone(self.by[1881]['facts']['first'])
 def test_similar_version_holds(self):self.assertTrue(all(self.by[n]['state']=='editorial_hold' for n in [1903,1912,1918]))
 def test_traditional_provenance_not_promoted(self):self.assertEqual(self.by[200005]['state'],'editorial_hold')
 def test_existing_not_inserted(self):self.assertTrue(all(self.by[n]['state']=='already_catalogued' for n in [1921,1966]));self.assertEqual(a.HCOUNT,0)
 def test_porteliot_location_explicit(self):self.assertIn('remains in situ at Port Eliot',self.by[2030]['facts']['source_fields']['editorial_note']);self.assertNotIn('current_location_text',a.expected_art(next(v for v in self.rs if v['decision']['number']==2030)))
 def test_two_portraits_distinct(self):self.assertEqual(self.by[2142]['facts']['creator_label'],self.by[92142]['facts']['creator_label']);self.assertNotEqual(self.by[2142]['facts']['title'],self.by[92142]['facts']['title'])
 def test_one_crab_not_collection(self):self.assertEqual(self.by[200004]['physical_object_count'],1);self.assertEqual(self.by[200004]['facts']['work_type'],'sculpture')
 def test_unique_ids(self):self.assertEqual(len({v['artwork_id'] for v in self.rs}),21);self.assertEqual(len({v['slug'] for v in self.rs}),21)
 def test_review_metadata(self):
  for v in self.rs:
   art=a.expected_art(v);self.assertEqual(art['status'],'review');self.assertTrue(art['research_candidate']);self.assertNotIn('published_at',art);self.assertNotIn('primary_media_id',art)
 def test_namespace_sources(self):
  p=a.i.params(a.i.rows());self.assertIn('box/1810/gore',p['source_ids']);self.assertIn('artfund/plymouth-harbour',p['source_ids'])
 def test_preservation_rejects_title_change(self):
  b={k:[] for k in ['artworks','artists','media','media_assets','identifiers','museums','citations','assertions']};b['artworks']=[dict(id='original',title='Original',current_institution_id=None)];c=copy.deepcopy(b);c['artworks'][0]['title']='Changed'
  with self.assertRaises(AssertionError):a.assert_delta(b,c,[],'digest')
 def test_preservation_rejects_media_change(self):
  b={k:[] for k in ['artworks','artists','media','media_assets','identifiers','museums','citations','assertions']};c=copy.deepcopy(b);c['media']=[dict(artwork_id='unexpected')]
  with self.assertRaises(AssertionError):a.assert_delta(b,c,[],'digest')
if __name__=='__main__':unittest.main(verbosity=2)
