import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('alternate',Path(__file__).with_name('research-overnight-alternate-commons.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class AlternateIdentity(unittest.TestCase):
 def setUp(self):
  self.c={'qid':'Q1'};self.page={'ns':6,'title':'File:Independent museum photograph.jpg'};self.sd={'statements':{'P6243':[{'mainsnak':{'snaktype':'value','datavalue':{'value':{'id':'Q1'}}}}]}}
 def test_exact_alternate_passes(self):m.valid_alternate(self.c,self.page,self.sd,'Primary.jpg')
 def test_primary_is_not_researched_again(self):
  with self.assertRaises(ValueError):m.valid_alternate(self.c,self.page,self.sd,self.page['title'][5:])
 def test_unlinked_file_fails(self):
  with self.assertRaises(ValueError):m.valid_alternate(self.c,self.page,{},'Primary.jpg')
 def test_another_object_fails(self):
  with self.assertRaises(ValueError):m.valid_alternate({'qid':'Q2'},self.page,self.sd,'Primary.jpg')
 def test_partial_reproduction_fails(self):
  self.page['title']='File:Painting detail.jpg'
  with self.assertRaises(ValueError):m.valid_alternate(self.c,self.page,self.sd,'Primary.jpg')
 def test_multiple_objects_fails(self):
  self.sd['statements']['P6243'].append({'mainsnak':{'snaktype':'value','datavalue':{'value':{'id':'Q2'}}}})
  with self.assertRaises(ValueError):m.valid_alternate(self.c,self.page,self.sd,'Primary.jpg')
if __name__=='__main__':unittest.main()
