import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('lombardia',Path(__file__).with_name('research-expanded-lombardia.py'));l=importlib.util.module_from_spec(s);s.loader.exec_module(l)
class SourcePolicyTests(unittest.TestCase):
 def test_biographies_are_not_activity_or_estimated_years(self):
  self.assertEqual(l.lifespan('1838/ 1920'),(1838,1920))
  for text in ['1597 ca./ 1637','notizie 1951-2008','1710/ 1750s','1630/ 1703 o dopo']:
   with self.subTest(text=text):self.assertEqual(l.lifespan(text),(None,None))
 def test_qualified_work_dates_preserve_uncertainty(self):
  o={'dtsi':'1890','dtsf':'1899','dtsv':'post','dtsl':'ante'};d=l.creation_date(o,'post 1890-ante 1899')
  self.assertIsNone(d['first']);self.assertEqual(d['precision'],'unknown')
 def test_circa_range(self):
  d=l.creation_date({'dtsi':'1900','dtsf':'1907','dtsv':'ca.','dtsl':'ca.'},'ca. 1900-ca. 1907');self.assertEqual((d['first'],d['last'],d['precision']),(1900,1907,'circa_range'))
 def test_building_is_not_an_invented_museum(self):
  self.assertEqual(l.museum_names({'ldcn':'Palazzo Clerici'}),set())
if __name__=='__main__':unittest.main()
