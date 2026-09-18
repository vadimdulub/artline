"""Synthetic source date, attribution, and exact image safeguards."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('smk',Path(__file__).with_name('overnight-smk-selected-images.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class TestSMKSelection(unittest.TestCase):
 def setUp(self):self.o={'production_date':[{'start':'1800-01-01','end':'1805-12-31','period':'1800-1805'}],'production_dates_notes':['Værkdatering: ca. 1800-1805']}
 def test_source_uncertainty_retained(self):self.assertEqual(m.date_parts(self.o),(1800,1805,'circa_range','ca. 1800-1805'))
 def test_activity_dates_held(self):
  self.o['production_dates_notes'].append('Dateringen følger kunstnerens virkeår, da værket er udateret')
  with self.assertRaises(ValueError):m.date_parts(self.o)
 def test_open_date_held(self):
  self.o['production_dates_notes']=['Værkdatering: efter 1800']
  with self.assertRaises(ValueError):m.date_parts(self.o)
 def test_date_disagreement_held(self):
  self.o['production_date'][0]['period']='1850'
  with self.assertRaises(ValueError):m.date_parts(self.o)
 def test_after_artist_stays_secondary(self):
  primary={'creator':'Synthetic Maker','creator_lref':'42_person'};o={'production':[primary,{'creator':'Earlier Artist','creator_role':'Efter','creator_lref':'43_person'}]}
  self.assertEqual(m.primary_maker(o),primary)
 def test_uncertain_attribution_held(self):
  with self.assertRaises(ValueError):m.primary_maker({'production':[{'creator_lref':'42_person','creator_role':'Tilskrevet'}]})
 def test_multiple_primary_makers_held(self):
  with self.assertRaises(ValueError):m.primary_maker({'production':[{'creator_lref':'42_person'},{'creator_lref':'43_person'}]})
 def test_sculpture_excluded(self):
  with self.assertRaises(ValueError):m.work_type({'object_names':[{'name':'Statue'}]})
 def test_painted_work(self):self.assertEqual(m.work_type({'object_names':[{'name':'Maleri'}]}),'painting')
 def test_lifetime_default_is_not_artwork_date(self):
  self.o['production']=[{'creator_lref':'42_person','creator_date_of_birth':'1785-01-01','creator_date_of_death':'1805-01-01'}]
  with self.assertRaisesRegex(ValueError,'default artist activity span'):m.date_parts(self.o)
 def test_standalone_circa_text_is_preserved(self):
  self.o['production_dates_notes']=['Ca. 1802']
  self.assertEqual(m.date_parts(self.o),(1800,1805,'circa_range','Ca. 1802'))
 def image_fixture(self):
  o={**self.o,'object_number':'TEST-42','id':'synthetic-object','responsible_department':'Synthetic museum department','acquisition_date':['1900'],'frontend_url':'https://open.smk.dk/artwork/image/TEST-42','titles':[{'title':'Synthetic painted landscape'}],'object_names':[{'name':'Maleri'}],'production':[{'creator':'Synthetic Artist','creator_lref':'42_person'}],'public_domain':True,'rights':m.PDM,'has_image':True,'image_iiif_id':'https://iip.smk.dk/iiif/jp2/synthetic.jp2'}
  c={'external_id':'TEST-42','accession_number':'TEST-42','source_api_id':'synthetic-object','title':'Synthetic painted landscape','work_type':'painting','artist_authority':'42_person','roles':['primary'],'creation_year_start':1800,'creation_year_end':1805,'date_precision':'circa_range','date_display':'ca. 1800-1805'}
  return c,o
 def test_exact_image_rights_and_identity(self):
  c,o=self.image_fixture();self.assertEqual(m.source_match(c,o)[0],'https://iip.smk.dk/iiif/jp2/synthetic.jp2/full/!1000,1000/0/default.jpg')
 def test_rights_conflict_is_held(self):
  c,o=self.image_fixture()
  for change in [{'rights':None},{'rights':'https://creativecommons.org/licenses/by-nc/4.0/'},{'copyright_notice':'Photographer rights reserved'},{'public_domain':False}]:
   with self.subTest(change=change),self.assertRaises(ValueError):m.source_match(c,{**o,**change})
 def test_other_native_maker_is_held(self):
  c,o=self.image_fixture();c['artist_authority']='43_person'
  with self.assertRaises(ValueError):m.source_match(c,o)
if __name__=='__main__':unittest.main()
