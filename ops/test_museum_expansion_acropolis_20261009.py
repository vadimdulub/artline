"""Captured-source identity and BC/AD date boundary tests; no database fixtures."""
import importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-acropolis-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a)
class ReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds=a.r.build();cls.by={v['number']:v for v in cls.ds};cls.news,cls.links=a.records()
 def test_selection(self):self.assertEqual((len(self.news),len(self.links)),(116,0));self.assertEqual({v['number']for v in self.ds if v['state']=='editorial_component_hold'},{24,43,57,176})
 def test_bc_range_no_false_expansion(self):self.assertEqual(a.i.f.date('200-86 BC')[:3],(-200,-86,'range'))
 def test_short_slash_date(self):self.assertEqual(a.i.f.date('420/19 BC')[:3],(-420,-419,'range'))
 def test_no_year_zero(self):self.assertEqual(a.i.f.date('1st cent. BC')[:2],(-100,-1));self.assertEqual(a.i.f.date('1st cent. AD')[:2],(1,100))
 def test_cross_era(self):self.assertEqual(a.i.f.date('323 BC-AD 267')[:2],(-323,267))
 def test_century_qualifier(self):self.assertEqual(a.i.f.date('Beginning of 4th cent. AD')[:3],(301,400,'century'))
 def test_open_dates(self):self.assertEqual({v['decision']['number']for v in self.news if v['facts']['last']is None},{50,53,112,170,179});self.assertEqual(sum(v['facts']['last']is not None for v in self.news),111)
 def test_physical_copy_date(self):self.assertEqual(self.by[14]['facts']['first'],301);self.assertGreater(self.by[55]['facts']['first'],0);self.assertGreater(self.by[62]['facts']['first'],0)
 def test_namespaces(self):self.assertNotEqual(a.i.f.invkey('Ακρ. 1329'),a.i.f.invkey('ΕΑΜ 1329'));self.assertEqual(a.i.f.invkey('Ακρ. 1329'),a.i.f.invkey('Acr. 1329'))
 def test_named_attribution(self):self.assertIn('Attributed',self.by[53]['facts']['creator_label']);self.assertIn('Possibly',self.by[46]['facts']['creator_label']);self.assertIn('(?)',self.by[177]['facts']['creator_label'])
 def test_parent_assemblies(self):self.assertIn('one carved base',self.by[106]['facts']['description_md']);self.assertIn('counted together once',self.by[170]['facts']['description_md']);self.assertIn('deferred body',self.by[46]['facts']['description_md'])
 def test_depiction_is_not_object(self):self.assertIn('watercolour KAS1793',self.by[167]['facts']['description_md']);self.assertIn('Watercolour',{v['medium_text']for v in self.by[167]['supplementary_comparators']})
 def test_dedicators_not_sculptors(self):self.assertEqual(self.by[169]['facts']['creator_label'],'Antenor');self.assertEqual(self.by[76]['facts']['creator_label'],'Thebades');self.assertIn('dedicator',self.by[78]['facts']['description_md'])
 def test_preservation(self):self.assertTrue(all(a.expected_art(v)['status']=='review'for v in self.news));self.assertEqual(len({v['facts']['source_id']for v in self.news}),116);self.assertEqual(a.SCHEME,'acropolis-museum-object')
if __name__=='__main__':unittest.main()
