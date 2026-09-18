import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('commons',Path(__file__).with_name('overnight-commons-images.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class CommonsBatchIdentity(unittest.TestCase):
 def setUp(self):
  self.a={'pageid':10,'ns':6,'title':'File:First painting.jpg','imageinfo':[{'url':'https://upload.wikimedia.org/synthetic-first.jpg'}]}
  self.b={'pageid':20,'ns':6,'title':'File:Second painting.jpg','imageinfo':[{'url':'https://upload.wikimedia.org/synthetic-second.jpg'}]}
  self.data={'query':{'normalized':[{'from':'File:First_painting.jpg','to':'File:First painting.jpg'}],'pages':{'20':self.b,'10':self.a}}}
 def test_response_order_never_assigns_another_image(self):self.assertIs(m.page_for_filename(self.data,'First painting.jpg'),self.a)
 def test_explicit_mediawiki_normalization(self):self.assertIs(m.page_for_filename(self.data,'First_painting.jpg'),self.a)
 def test_unrequested_filename_fails(self):
  with self.assertRaises(ValueError):m.page_for_filename(self.data,'Unknown.jpg')
 def test_duplicate_title_response_fails(self):
  self.data['query']['pages']['30']=dict(self.a,pageid=30)
  with self.assertRaises(ValueError):m.page_for_filename(self.data,'First painting.jpg')
 def test_missing_image_fails(self):
  self.a.pop('imageinfo')
  with self.assertRaises(ValueError):m.page_for_filename(self.data,'First painting.jpg')
 def test_non_file_page_fails(self):
  self.a['ns']=0
  with self.assertRaises(ValueError):m.page_for_filename(self.data,'First painting.jpg')
 def test_redirect_requires_review(self):
  self.data['query']['redirects']=[{'from':'File:First painting.jpg','to':'File:Second painting.jpg'}]
  with self.assertRaises(ValueError):m.page_for_filename(self.data,'First painting.jpg')
 def test_nonexistent_page_fails(self):
  self.a['pageid']=-1
  with self.assertRaises(ValueError):m.page_for_filename(self.data,'First painting.jpg')
 def structured(self,*ids):return {'statements':{'P6243':[{'mainsnak':{'snaktype':'value','datavalue':{'value':{'id':q}}}} for q in ids]}}
 def test_conflicting_structured_object_fails(self):
  with self.assertRaises(ValueError):m.verify_structured_object({'qid':'Q1'},self.structured('Q2'))
 def test_multiple_structured_objects_require_review(self):
  with self.assertRaises(ValueError):m.verify_structured_object({'qid':'Q1'},self.structured('Q1','Q2'))
 def test_exact_structured_object_passes(self):m.verify_structured_object({'qid':'Q1'},self.structured('Q1'))
 def test_absent_structured_object_defers_to_other_evidence(self):m.verify_structured_object({'qid':'Q1'},self.structured())
if __name__=='__main__':unittest.main()
