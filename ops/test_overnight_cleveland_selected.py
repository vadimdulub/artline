"""Synthetic exact-source identity, ownership, date and image-rights checks."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('overnight-cleveland-selected-images.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class TestClevelandSelection(unittest.TestCase):
 def setUp(self):
  self.c={'external_id':'42','accession_number':'1900.1','title':'Synthetic landscape','work_type':'painting','artist':'Ada Example','aliases':[],'artist_authority':'77','roles':['primary'],'creation_year_start':1850,'creation_year_end':1860,'date_precision':'circa_range','date_display':'c. 1855'}
  self.o={'id':42,'accession_number':'1900.1','title':'Synthetic landscape','type':'Painting','legal_status':'accessioned','on_loan':False,'record_type':'object','url':'https://clevelandart.org/art/1900.1','creators':[{'id':77,'role':'artist','description':'Ada Example (Synthetic nationality, 1800–1890)','birth_year':'1800','death_year':'1890'}],'creation_date_earliest':1850,'creation_date_latest':1860,'creation_date':'c. 1855','share_license_status':'CC0','images':{'web':{'url':'https://openaccess-cdn.clevelandart.org/1900.1/1900.1_web.jpg','filename':'1900.1_web.jpg'}}}
 def test_exact_source_image(self):self.assertEqual(m.source_match(self.c,self.o)[0],self.o['images']['web']['url'])
 def test_loan_is_not_museum_ownership(self):
  with self.assertRaises(ValueError):m.source_match(self.c,{**self.o,'legal_status':'long-term loan','on_loan':True})
 def test_component_is_not_silently_top_level(self):
  with self.assertRaises(ValueError):m.source_match(self.c,{**self.o,'record_type':'component','cover_accession_number':'1900.2'})
 def test_copyright_conflict(self):
  for change in [{'share_license_status':'Other'},{'copyright':'Photographer rights reserved'},{'rights_and_reproductions':'Permission required'}]:
   with self.subTest(change=change),self.assertRaises(ValueError):m.source_match(self.c,{**self.o,**change})
 def test_other_image_resource(self):
  o={**self.o,'images':{'web':{'url':'https://openaccess-cdn.clevelandart.org/1900.2/1900.2_web.jpg','filename':'1900.2_web.jpg'}}}
  with self.assertRaises(ValueError):m.source_match(self.c,o)
 def test_scope_crossing_cutoff(self):
  with self.assertRaises(ValueError):m.date_parts({**self.o,'creation_date_earliest':1960,'creation_date_latest':1980})
 def test_artist_lifespan_is_not_creation_interval(self):
  with self.assertRaises(ValueError):m.date_parts({**self.o,'creation_date_earliest':1800,'creation_date_latest':1890})
 def test_qualified_artist_held(self):
  o={**self.o,'creators':[{**self.o['creators'][0],'qualifier':'attributed to'}]}
  with self.assertRaises(ValueError):m.source_match(self.c,o)
 def test_second_artist_held(self):
  with self.assertRaises(ValueError):m.source_match(self.c,{**self.o,'creators':self.o['creators']*2})
 def test_diacritics_normalize_without_changing_source_text(self):self.assertEqual(m.norm('Édouard Example'),m.norm('Edouard Example'))
 def test_publisher_and_after_artist_remain_secondary(self):
  o={**self.o,'creators':self.o['creators']+[{'id':80,'role':'published by','description':'Synthetic Press'},{'id':90,'role':'artist','qualifier':'after','description':'Earlier Example'}]}
  self.assertEqual(m.primary_maker(o)['id'],77)
if __name__=='__main__':unittest.main()
