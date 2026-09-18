import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('sources',Path(__file__).with_name('research-expanded-sources.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class SourceDateTests(unittest.TestCase):
 def test_uncertain_biography_is_not_exact(self):
  for value in ['American, ca. 1810-1874','Chinese, 1563-1639 or later','British (active 1879-1890)']:
   self.assertEqual(r.closed_bio(value),(None,None))
 def test_smithsonian_biography_separated_from_name(self):
  p=r.saam_person('Mary Vaux Walcott, born Philadelphia, PA 1860-died St. Andrews, New Brunswick, Canada 1940')
  self.assertEqual((p['name'],p['birth'],p['death']),('Mary Vaux Walcott',1860,1940))
 def test_qualified_date_not_invented(self):
  self.assertEqual(r.strict_date('ca. 1510 (Renaissance)')['precision'],'unknown')
  self.assertEqual(r.strict_date('ca. 1887')['precision'],'circa')
 def test_rijks_uncertain_lifespan_boundary(self):
  self.assertIsNone(r.event_year({'timespan':{'identified_by':[{'type':'Name','content':'1606 - 1607'}]}}))
  self.assertEqual(r.event_year({'timespan':{'identified_by':[{'type':'Name','content':'1606-07-15'}]}}),1606)
 def test_multiple_creation_periods_are_held(self):
  a={'identified_by':[{'type':'Name','content':'ca. 1670'}]}
  b={'identified_by':[{'type':'Name','content':'ca. 1740'}]}
  self.assertIsNone(r.single_timespan([a,b]))
  self.assertEqual(r.single_timespan([a]),a)
  self.assertIsNone(r.event_year({'timespan':[a,b]}))
if __name__=='__main__':unittest.main()
