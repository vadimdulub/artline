import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('direct',Path(__file__).with_name('followup-nga-direct-images.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class SourceResourceRights(unittest.TestCase):
 def record(self):
  return {'external_id':'12','title':'Synthetic painting','accession_number':'S.1','work_type':'painting','creation_year_start':1800,'creation_year_end':1800,'source_image_url':'https://api.nga.gov/iiif/00000000-0000-0000-0000-000000000000/full/!1000,1000/0/default.jpg','artist_authorities':['5'],'policy_url':m.CC0,'rights_status':'cc0','raw':{'nga_object':{'objectid':'12','accessioned':'1','isvirtual':'0','classification':'Painting','title':'Synthetic painting','accessionnum':'S.1','beginyear':'1800','endyear':'1800'},'published_image':{'openaccess':'1','viewtype':'primary','depictstmsobjectid':'12','uuid':'00000000-0000-0000-0000-000000000000','iiifurl':'https://api.nga.gov/iiif/00000000-0000-0000-0000-000000000000'},'artist_relations':[{'objectid':'12','constituentid':'5','roletype':'artist','role':'painter','prefix':'','suffix':''}],'image_policy':{'url':m.POLICY,'open_access_images_cc0':True,'sha256':'synthetic-policy-evidence'}}}
 def test_exact_open_resource(self):m.verify(self.record())
 def test_metadata_cc0_does_not_license_closed_image(self):
  r=self.record();r['raw']['published_image']['openaccess']='0'
  with self.assertRaises(ValueError):m.verify(r)
 def test_other_object_image_held(self):
  r=self.record();r['raw']['published_image']['depictstmsobjectid']='13'
  with self.assertRaises(ValueError):m.verify(r)
 def test_unproven_resource_url_held(self):
  r=self.record();r['source_image_url']=r['source_image_url'].replace('00000000-','11111111-',1)
  with self.assertRaises(ValueError):m.verify(r)
 def test_wrong_catalogue_creator_held(self):
  r=self.record();r['artist_authorities']=['6']
  with self.assertRaises(ValueError):m.verify(r)
 def test_qualified_attribution_held(self):
  r=self.record();r['raw']['artist_relations'][0]['prefix']='after'
  with self.assertRaises(ValueError):m.verify(r)
 def test_policy_missing_held(self):
  r=self.record();r['raw']['image_policy']['open_access_images_cc0']=False
  with self.assertRaises(ValueError):m.verify(r)
 def test_loan_not_permanent_holding(self):
  r=self.record();r['raw']['nga_object']['accessioned']='0'
  with self.assertRaises(ValueError):m.verify(r)
 def redirect(self):
  r=self.record();old=r['source_image_url'];r['source_image_url']=old.replace('/full/','__900/full/');r['raw']['museum_rendition_redirect']={'status':303,'requested_url':old,'location':r['source_image_url'],'retrieved_at':'synthetic'};return r
 def test_same_image_explicit_museum_rendition(self):m.verify(self.redirect())
 def test_redirect_cannot_change_object_image(self):
  r=self.redirect();r['source_image_url']=r['source_image_url'].replace('00000000-','11111111-',1);r['raw']['museum_rendition_redirect']['location']=r['source_image_url']
  with self.assertRaises(ValueError):m.verify(r)
 def test_redirect_cannot_crop_image(self):
  r=self.redirect();r['source_image_url']=r['source_image_url'].replace('/full/','/square/');r['raw']['museum_rendition_redirect']['location']=r['source_image_url']
  with self.assertRaises(ValueError):m.verify(r)
 def test_redirect_requires_explicit_303_evidence(self):
  r=self.redirect();r['raw']['museum_rendition_redirect']['status']=403
  with self.assertRaises(ValueError):m.verify(r)
if __name__=='__main__':unittest.main()
