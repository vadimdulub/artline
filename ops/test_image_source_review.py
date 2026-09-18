"""Offline evidence counterexamples; no database fixtures."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('prepare-wikimedia-catalogue-images.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def record(death):return {'creator_entity':{'claims':{'P570':[{'rank':'normal','mainsnak':{'snaktype':'value','datavalue':{'value':{'precision':9,'time':f'+{death:04d}-01-01T00:00:00Z'}}}}]}}}
class Review(unittest.TestCase):
 def test_depicted_painter_does_not_replace_photographer(self):
  result=m.image_credit({'Artist':{'value':'Painter Name'},'Credit':{'value':'Self-photographed by <a href="/wiki/User:Photo">Photo Name</a>'}})
  self.assertIn('Painter Name',result);self.assertIn('Photo Name',result)
 def test_explicit_required_credit_is_preserved(self):
  result=m.image_credit({'Artist':{'value':'Painter'},'Attribution':{'value':'Museum / Photographer'}});self.assertIn('Museum / Photographer',result)
 def test_false_old100_tag_is_held(self):
  with self.assertRaises(ValueError):m.check_rights_chronology(record(1959),'Public domain','{{PD-Art|PD-old-100-1923}}')
 def test_old_master_not_held_by_modern_death_check(self):m.check_rights_chronology(record(1659),'Public domain','{{PD-Art|PD-old-100-1923}}')
 def test_explicit_cc_permission_is_not_a_life_expiry_claim(self):m.check_rights_chronology(record(2012),'CC BY-SA 4.0','{{PermissionTicket|id=2016093010020885}}')
if __name__=='__main__':unittest.main()
