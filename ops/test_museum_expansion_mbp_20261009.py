"""Offline policy boundaries using captured records, no database fixtures."""
import importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-mbp-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a)
class ReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds=a.r.build();cls.by={d['number']:d for d in cls.ds};cls.news,cls.links=a.records()
 def test_selected_counts(self):self.assertEqual((len(self.news),len(self.links)),(89,0))
 def test_physical_reproduction_date(self):self.assertEqual((self.by[59]['facts']['first'],self.by[59]['facts']['last']),(1950,1950));self.assertIn('issued by',self.by[59]['facts']['creator_label'])
 def test_post1970_impressions_held(self):self.assertTrue({802665,635189,635191}<=set(a.i.f.HOLDS))
 def test_unknown_date_not_invented(self):self.assertEqual((self.by[18]['facts']['first'],self.by[18]['facts']['last'],self.by[18]['facts']['date_precision']),(None,None,'unknown'))
 def test_crossing_dates_preserved(self):self.assertEqual(sum(v['facts']['last']==1999 for v in self.news),5)
 def test_qualified_inscription(self):self.assertEqual(self.by[16]['facts']['date_precision'],'circa');self.assertIn('?',self.by[16]['facts']['date_display'])
 def test_tomb_duplicates_held(self):self.assertTrue(all(self.by[n]['state']=='held_editorial_review'for n in[73,76]))
 def test_two_leaf_door_one_record(self):self.assertEqual(sum(v['facts']['source_id']=='721375'for v in self.news),1);self.assertIn('two painted leaves',self.by[108]['facts']['description_md'])
 def test_fragments_described(self):self.assertTrue(all('cut panel'in self.by[n]['facts']['description_md']for n in[95,111]));self.assertTrue(all('central panel'in self.by[n]['facts']['description_md']for n in[31,36]))
 def test_provider_inventory_namespace(self):self.assertEqual(a.i.f.invkey('NET 004'),a.i.f.invkey('ΝΕΤ 4'));self.assertNotEqual(a.i.f.invkey('ΒΕΙ 95'),a.i.f.invkey('ΒΧΕΙ 95'))
 def test_status_and_no_display(self):self.assertTrue(all(a.expected_art(v)['status']=='review'and a.expected_art(v)['research_candidate']for v in self.news));self.assertEqual(len({v['facts']['source_id']for v in self.news}),89)
 def test_no_false_mosaic_class(self):self.assertTrue(all(self.by[n]['facts']['work_type']=='unknown'and'Floor mosaic'in self.by[n]['facts']['description_md']for n in[65,66,67]))
if __name__=='__main__':unittest.main()
