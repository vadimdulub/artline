import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('mia',Path(__file__).with_name('research-expanded-mia.py'));mia=importlib.util.module_from_spec(s);s.loader.exec_module(mia)
class BiographyTests(unittest.TestCase):
 def test_closed_biography(self):
  m=mia.closed_biography('Japanese, 1779–1846');self.assertEqual(m.groups(),('1779','1846'))
 def test_uncertain_boundaries(self):
  for text in ['Chinese, 1563–1639 or later','Chinese, 1710–1750s','British (active 1879–1890)','French, c. 1800–1850','Chinese, 1630–1703?']:
   with self.subTest(text=text):self.assertIsNone(mia.closed_biography(text))
if __name__=='__main__':unittest.main()
