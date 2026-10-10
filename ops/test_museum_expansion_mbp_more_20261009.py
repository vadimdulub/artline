"""Physical object/date/attribution boundaries using captured sources; no DB fixtures."""
import importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-mbp-more-apply-v2-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a)
class ReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds=a.r.build();cls.by={v['number']:v for v in cls.ds};cls.news,cls.links=a.records()
 def test_counts(self):self.assertEqual((len(self.news),len(self.links)),(107,0))
 def test_physical_dates(self):self.assertTrue({968763,635183}<=set(a.i.f.HOLDS));self.assertNotIn('635183',{v['facts']['source_id']for v in self.news})
 def test_assembly_holds(self):self.assertTrue({698191,698211,754670,805614}<=set(a.i.f.HOLDS))
 def test_plate_impression_conflicts(self):self.assertTrue({802566,1042616}<=set(a.i.f.HOLDS))
 def test_circa(self):self.assertEqual(self.by[247]['facts']['date_precision'],'circa')
 def test_attribution_qualifiers(self):self.assertIn('workshop',self.by[270]['facts']['creator_label']);self.assertIn('not genuine',self.by[379]['facts']['creator_label']);self.assertIn('possibly',self.by[375]['facts']['creator_label'])
 def test_fragments(self):self.assertIn('cut panel',self.by[224]['facts']['description_md']);self.assertIn('side leaves',self.by[351]['facts']['description_md']);self.assertIn('central panel',self.by[361]['facts']['description_md'])
 def test_modern_range_review(self):self.assertEqual((self.by[242]['facts']['first'],self.by[242]['facts']['last']),(1900,1999));self.assertEqual(sum(v['facts']['last']<=1970 for v in self.news),106)
 def test_namespaces(self):self.assertEqual(a.i.f.invkey('NET014'),a.i.f.invkey('ΝΕΤ14'));self.assertNotEqual(a.i.f.invkey('ΒΕΙ58'),a.i.f.invkey('ΒΧΕΙ58'))
 def test_preservation(self):self.assertTrue(all(a.expected_art(v)['status']=='review'for v in self.news));self.assertEqual(len({v['facts']['source_id']for v in self.news}),107)
if __name__=='__main__':unittest.main()
