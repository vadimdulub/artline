"""Further physical version/date safeguards from captured evidence, no DB fixtures."""
import importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-acropolis-more-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a)
class ReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds=a.r.build();cls.by={v['number']:v for v in cls.ds};cls.news,cls.links=a.records()
 def test_selection(self):self.assertEqual((len(self.news),len(self.links)),(75,0));self.assertEqual(len(a.r.HOLDS),9)
 def test_cast_components(self):self.assertIn('Louvre',a.r.HOLDS[185]);self.assertIn('Louvre',a.r.HOLDS[188])
 def test_arm_parent(self):self.assertIn('Acr.665',a.r.HOLDS[231]);self.assertIn('held',self.by[180]['facts']['description_md'])
 def test_possible_group_not_doubled(self):self.assertTrue({215,241}<=set(a.r.HOLDS))
 def test_existing_head_association(self):self.assertIn('already catalogued',a.r.HOLDS[190]);self.assertIn('Acr.658',self.by[197]['facts']['description_md'])
 def test_date_counts(self):self.assertEqual({v['decision']['number']for v in self.news if v['facts']['last']is None},{232,255});self.assertEqual(sum(v['facts']['last']is not None for v in self.news),73)
 def test_physical_copy_dates(self):self.assertEqual((self.by[203]['facts']['first'],self.by[203]['facts']['last']),(150,200));self.assertEqual(self.by[224]['facts']['first'],201);self.assertLess(self.by[201]['facts']['last'],0)
 def test_cross_era_and_unknown_subject(self):self.assertEqual((self.by[223]['facts']['first'],self.by[223]['facts']['last']),(-86,267));self.assertIn('probably depicts Alexander',self.by[218]['facts']['description_md'])
 def test_qualified_authorship(self):self.assertTrue(all('Attributed to'in self.by[n]['facts']['creator_label']for n in [205,211,255]))
 def test_dedicators(self):self.assertEqual(self.by[204]['facts']['creator_label'],'Euenor');self.assertEqual(self.by[233]['facts']['creator_label'],'Endoios');self.assertIn('dedicator, not the sculptor',self.by[232]['facts']['description_md'])
 def test_assemblies(self):self.assertIn('one sculpture',self.by[228]['facts']['description_md']);self.assertIn('count once',self.by[219]['facts']['description_md'])
 def test_namespaces(self):self.assertNotEqual(a.i.f.invkey(self.by[233]['facts']['inventory']),a.i.f.invkey(self.by[237]['facts']['inventory']));self.assertNotEqual(a.i.f.invkey('ΝΜΑ 1868'),a.i.f.invkey('ΝΜΑ 1869'))
 def test_workshop_originals(self):self.assertIn('unfinished',self.by[243]['facts']['description_md']);self.assertIn('left male hand',self.by[247]['facts']['description_md']);self.assertIn('right hand',self.by[248]['facts']['description_md'])
 def test_review_preservation(self):self.assertTrue(all(a.expected_art(v)['status']=='review'for v in self.news));self.assertEqual(a.SCHEME,'acropolis-museum-object');self.assertEqual(len({v['facts']['source_id']for v in self.news}),75)
if __name__=='__main__':unittest.main()
