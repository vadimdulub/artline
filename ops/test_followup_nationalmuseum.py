import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('nm',Path(__file__).with_name('followup-nationalmuseum-images.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class NationalmuseumEvidence(unittest.TestCase):
 def fixture(self):
  lead={'native_id':'1','accessions':['NM 1'],'people':[{'name':'Synthetic Artist'}],'artist':{'slug':'synthetic','display_name':'Synthetic Artist','birth_year':1800,'death_year':1880,'qid':'Q1','popular':True}}
  capture={'url':m.HOST+'/en/collection/item/1/','rendered_image_paths':['/multimedia/1/multimedia-1.large.jpg'],'item':{
   'Id':'1','ObjCollectionSearchTxt':{'LabelTxt':'Paintings'},'ObjCategoryTxt':'#painting#','ObjInventoryNumberTxt':'NM 1','ObjDonationTxt':'Gift 1900',
   'ObjPersonRef':{'Items':[{'RoleVoc':{'LabelTxt':'Artist'},'LinkLabelTxt':'Synthetic Artist (1800 - 1880)','ReferencedId':'2'}]},
   'ObjFromYearTxt':'1850','ObjToYearTxt':'1850','ObjDateMainTxt':'Signed 1850','ObjTitleMainTxt':'Synthetic painting','ObjExternalIDTxt':'Wikidata: Q2',
   'DefaultImage':'multimedia/1/multimedia-1.large.jpg','ObjMultimediaRef':{'Items':[{'ReferencedId':'1','MulRightsTxt':'Public Domain, '+m.PDM,'MulPhotocreditTxt':'Synthetic photographer','InternetVoc':{'LabelTxt':'Public'},'Multimedia':[{'full':'multimedia/1/multimedia-1.large.jpg','mime':'image/jpeg'}]}]}}}
  return lead,capture
 def test_current_source_and_exact_image(self):
  lead,c=self.fixture();self.assertEqual(m.fact_check(lead,c)['date_precision'],'exact');self.assertEqual(m.exact_image(c)[1],'Synthetic photographer')
 def test_metadata_license_cannot_clear_image(self):
  lead,c=self.fixture();c['metadata_license']=m.CC0;c['item']['ObjMultimediaRef']['Items'][0]['MulRightsTxt']=''
  self.assertEqual(m.fact_check(lead,c)['title'],'Synthetic painting')
  with self.assertRaises(ValueError):m.exact_image(c)
 def test_other_image_rights_cannot_clear_default(self):
  _,c=self.fixture();extra=copy.deepcopy(c['item']['ObjMultimediaRef']['Items'][0]);extra['Multimedia'][0]['full']='multimedia/2/multimedia-2.large.jpg';c['item']['ObjMultimediaRef']['Items'].append(extra);c['item']['ObjMultimediaRef']['Items'][0]['MulRightsTxt']='Unknown'
  with self.assertRaises(ValueError):m.exact_image(c)
 def test_explicit_photographic_copyright_held(self):
  _,c=self.fixture();c['item']['ObjMultimediaRef']['Items'][0]['MulPhotographicalCopyrightTxt']='All rights reserved'
  with self.assertRaises(ValueError):m.exact_image(c)
 def test_external_default_image_held(self):
  _,c=self.fixture();c['item']['DefaultImage']='https://example.org/picture.jpg'
  with self.assertRaises(ValueError):m.exact_image(c)
 def test_unlinked_default_held(self):
  _,c=self.fixture();c['rendered_image_paths']=[]
  with self.assertRaises(ValueError):m.exact_image(c)
 def test_same_name_wrong_lifespan_held(self):
  lead,c=self.fixture();lead['artist']['birth_year']=1801
  with self.assertRaises(ValueError):m.fact_check(lead,c)
 def test_workshop_attribution_held(self):
  lead,c=self.fixture();c['item']['ObjPersonRef']['Items'][0]['RoleVoc']['LabelTxt']='Workshop of'
  with self.assertRaises(ValueError):m.fact_check(lead,c)
 def test_lifetime_is_not_work_date(self):
  lead,c=self.fixture();c['item'].update(ObjFromYearTxt='1800',ObjToYearTxt='1880',ObjDateMainTxt='1800-1880')
  with self.assertRaises(ValueError):m.fact_check(lead,c)
 def test_crossing_cutoff_held(self):
  lead,c=self.fixture();c['item'].update(ObjFromYearTxt='1960',ObjToYearTxt='1980',ObjDateMainTxt='1960-1980')
  with self.assertRaises(ValueError):m.fact_check(lead,c)
 def test_conflicting_date_text_held(self):
  lead,c=self.fixture();c['item']['ObjDateMainTxt']='Signed 1840 or 1850'
  with self.assertRaises(ValueError):m.fact_check(lead,c)
 def test_explicit_decade_retained(self):
  lead,c=self.fixture();c['item'].update(ObjFromYearTxt='1850',ObjToYearTxt='1859',ObjDateMainTxt='1850s');self.assertEqual(m.fact_check(lead,c)['date_precision'],'decade')
 def test_loan_not_asserted_as_owned(self):
  lead,c=self.fixture();c['item']['ObjDonationTxt']='Loan from private collection'
  with self.assertRaises(ValueError):m.fact_check(lead,c)
 def test_print_not_imported_as_painting(self):
  lead,c=self.fixture();c['item']['ObjCategoryTxt']='#print#'
  with self.assertRaises(ValueError):m.fact_check(lead,c)
 def test_explicit_sharealike_image_accepted(self):
  _,c=self.fixture();c['item']['ObjMultimediaRef']['Items'][0]['MulRightsTxt']='CC BY SA, '+m.BYSA;self.assertEqual(m.exact_image(c)[3][0],m.BYSA)
 def test_sharealike_requires_photographer_credit(self):
  _,c=self.fixture();c['item']['ObjMultimediaRef']['Items'][0].update(MulRightsTxt='CC BY SA, '+m.BYSA,MulPhotocreditTxt='')
  with self.assertRaises(ValueError):m.exact_image(c)
 def test_public_domain_preserves_provenance_without_inventing_photographer(self):
  _,c=self.fixture();c['item']['ObjMultimediaRef']['Items'][0]['MulPhotocreditTxt']='';self.assertIn('photographer not credited',m.exact_image(c)[1])
 def test_noncommercial_license_held(self):
  _,c=self.fixture();c['item']['ObjMultimediaRef']['Items'][0]['MulRightsTxt']='CC BY NC, https://creativecommons.org/licenses/by-nc/4.0/'
  with self.assertRaises(ValueError):m.exact_image(c)

if __name__=='__main__':unittest.main()
