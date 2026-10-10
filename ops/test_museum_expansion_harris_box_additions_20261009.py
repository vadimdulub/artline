"""Offline source and preservation checks; no database connection or fixtures."""
import collections,copy,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-harris-box-additions-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a)
class ReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ds=a.r.build();cls.by={x['number']:x for x in cls.ds};cls.new=[x for x in cls.ds if x['state']=='approved_review_only_addition'];cls.rs=a.records()[0]
 def test_decisions(self):self.assertEqual(collections.Counter(x['state'] for x in self.ds),{'approved_review_only_addition':71,'editorial_hold':14,'already_catalogued':3,'source_fact_hold':8})
 def test_museum_counts(self):self.assertEqual(collections.Counter(x['institution_id'] for x in self.new),dict(zip(a.IIDS,[49,22])))
 def test_dated_counts(self):self.assertEqual(collections.Counter(x['institution_id'] for x in self.new if x['facts']['first'] is not None),dict(zip(a.IIDS,[8,13])))
 def test_unknown_dates(self):
  unknown=[x['facts'] for x in self.new if x['facts']['first'] is None];self.assertEqual(len(unknown),50);self.assertTrue(all(x['last'] is None and x['date_precision']=='unknown' for x in unknown))
 def test_pre1971(self):self.assertTrue(all(x['facts']['last']<=1970 for x in self.new if x['facts']['last'] is not None))
 def test_1970_included(self):self.assertEqual(self.by[100017]['facts']['first'],1970);self.assertEqual(self.by[100017]['state'],'approved_review_only_addition')
 def test_cast_date(self):self.assertEqual((self.by[15605]['facts']['first'],self.by[15605]['facts']['last']),(1880,1889))
 def test_depicted_year(self):self.assertEqual(self.by[100001]['facts']['first'],1890);self.assertIn('1815',self.by[100001]['facts']['title'])
 def test_commission_not_creation(self):self.assertIsNone(self.by[100005]['facts']['first']);self.assertEqual(self.by[100005]['facts']['source_commission_year'],1777)
 def test_exhibition_not_creation(self):self.assertIsNone(self.by[1788]['facts']['first'])
 def test_letter_not_creation(self):self.assertIsNone(self.by[15765]['facts']['first'])
 def test_cast_and_date_qualification(self):self.assertEqual(self.by[15575]['facts']['date_precision'],'circa_range');self.assertEqual(self.by[16791]['facts']['date_precision'],'circa_range')
 def test_snyders_not_unqualified_master(self):self.assertIn('influenced',self.by[15575]['facts']['creator_label']);self.assertIn('possibly',self.by[15575]['facts']['creator_label'])
 def test_studio_copy(self):self.assertEqual(self.by[100029]['facts']['creator_label'],'Studio of Sir Joshua Reynolds');self.assertIsNone(self.by[100029]['facts']['first'])
 def test_rejected_laroon_attribution(self):self.assertTrue(self.by[100008]['facts']['creator_label'].startswith('Unidentified'));self.assertIn('formerly',self.by[100008]['facts']['creator_label'])
 def test_paper_taxonomy_not_technique(self):self.assertTrue(all(self.by[n]['facts']['work_type']=='unknown' for n in [1809,15675,15689,15696,15777]))
 def test_pastel_explicit(self):self.assertEqual(self.by[15684]['facts']['medium'],'Pastel')
 def test_sketchbook_once(self):self.assertEqual(self.by[100031]['physical_object_count'],1);self.assertEqual(len([x for x in self.new if x['source_id']=='box/2018/sketchbook']),1)
 def test_drawing_after_fresco_separate(self):self.assertEqual({self.by[n]['facts']['inventory'] for n in [15771,15774]},{'P348','P441'})
 def test_group_identity_held(self):self.assertEqual(self.by[15748]['state'],'editorial_hold');self.assertEqual(self.by[15751]['state'],'editorial_hold')
 def test_possible_duplicate_not_added(self):self.assertEqual(self.by[15667]['state'],'editorial_hold');self.assertEqual(self.by[100026]['state'],'editorial_hold')
 def test_existing_records_not_written(self):self.assertEqual({x['number'] for x in self.ds if x['state']=='already_catalogued'},{15623,100002,100019});self.assertEqual(a.HCOUNT,0)
 def test_exhibition_holding_held(self):self.assertEqual(self.by[100028]['state'],'editorial_hold')
 def test_modern_and_manuscript_held(self):self.assertEqual(self.by[1774]['state'],'source_fact_hold');self.assertEqual(self.by[15784]['state'],'source_fact_hold')
 def test_unique_physical_identifiers(self):self.assertEqual(len({v['artwork_id'] for v in self.rs}),71);self.assertEqual(len({v['slug'] for v in self.rs}),71)
 def test_review_only_metadata(self):
  for v in self.rs:
   art=a.expected_art(v);self.assertEqual(art['status'],'review');self.assertTrue(art['research_candidate']);self.assertEqual(art['current_institution_id'],v['institution_id']);self.assertNotIn('primary_media_id',art);self.assertNotIn('published_at',art)
 def test_preservation_rejects_metadata_change(self):
  before={k:[] for k in ['artworks','artists','media','media_assets','identifiers','museums','citations','assertions']};before['artworks']=[dict(id='unchanged',title='Original',current_institution_id=None)];after=copy.deepcopy(before);after['artworks'][0]['title']='Altered'
  with self.assertRaises(AssertionError):a.assert_delta(before,after,[],'digest')
 def test_preservation_rejects_media_change(self):
  before={k:[] for k in ['artworks','artists','media','media_assets','identifiers','museums','citations','assertions']};after=copy.deepcopy(before);after['media']=[dict(artwork_id='unexpected')]
  with self.assertRaises(AssertionError):a.assert_delta(before,after,[],'digest')
 def test_source_namespace_search(self):
  params=a.i.params(a.i.rows());self.assertIn('PRSMG : P1179',params['inventories']);self.assertIn('%snyders%',params['patterns']);self.assertIn('%bibiena%',params['patterns'])
 def test_no_authority_fabrication(self):self.assertEqual(self.by[1809]['facts']['creator_label'],'Nash');self.assertEqual(self.by[15739]['facts']['creator_label'],'Nollekens')
if __name__=='__main__':unittest.main(verbosity=2)
