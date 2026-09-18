import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('nmc',Path(__file__).with_name('followup-nationalmuseum-commons.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class MuseumLinkedFile(unittest.TestCase):
 def fixture(self):
  c={'external_id':'1','accession_number':'NM 1','qid':'Q2','title':'Synthetic painting','artist':'Synthetic Artist','raw':{'lead':{'people':[{'name':'Synthetic Artist'}]},'official_capture':{'item':{'ObjWikimediaLinkTxt':'https://commons.wikimedia.org/wiki/File:Synthetic_painting.tif'}}}}
  wt='''{{Artwork
 |artist = Synthetic Artist
 |title = Synthetic painting
 |wikidata = Q2
 |accession number = NM 1
 |source = {{Nationalmuseum Stockholm link|1|Nationalmuseum}}
 |permission = {{Nationalmuseum Stockholm cooperation project}}
{{Licensed-PD-Art|1=PD-old-auto|2=PD-Nationalmuseum_Stockholm|deathyear=1800}}
 |description = This synthetic description must not enter production.
}}'''
  fields={'Artist':'Synthetic Artist','ObjectName':'Synthetic painting','LicenseShortName':'Public domain','Copyrighted':'False','LicenseUrl':m.nm.PDM,'Credit':'Nationalmuseum'}
  page={'pageid':10,'title':'File:Synthetic painting.tif','revisions':[{'revid':20,'slots':{'main':{'*':wt}}}],'imageinfo':[{'extmetadata':{k:{'value':v} for k,v in fields.items()},'thumburl':'https://upload.wikimedia.org/synthetic.jpg','descriptionurl':'https://commons.wikimedia.org/wiki/File:Synthetic_painting.tif'}]}
  return c,page,None,{}
 def test_independently_licensed_exact_donation(self):self.assertEqual(m.verify_file(*self.fixture())[0],'https://upload.wikimedia.org/synthetic.jpg')
 def test_wrong_linked_filename_held(self):
  c,p,r,s=self.fixture();p['title']='File:Other.tif'
  with self.assertRaises(ValueError):m.verify_file(c,p,r,s)
 def test_wrong_accession_held(self):
  c,p,r,s=self.fixture();c['accession_number']='NM 2'
  with self.assertRaises(ValueError):m.verify_file(c,p,r,s)
 def test_other_physical_object_held(self):
  c,p,r,s=self.fixture();s={'claims':{'P6243':[{'rank':'normal','mainsnak':{'snaktype':'value','datavalue':{'value':{'id':'Q3'}}}}]}}
  with self.assertRaises(ValueError):m.verify_file(c,p,r,s)
 def test_pd_art_without_museum_photograph_release_held(self):
  c,p,r,s=self.fixture();p['revisions'][0]['slots']['main']['*']=p['revisions'][0]['slots']['main']['*'].replace('2=PD-Nationalmuseum_Stockholm','2=PD-old')
  with self.assertRaises(ValueError):m.verify_file(c,p,r,s)
 def test_licence_from_different_revision_held(self):
  c,p,r,s=self.fixture();p['imageinfo'][0]['extmetadata'].pop('LicenseUrl');r={'pageid':10,'revid':21,'uri':m.nm.PDM}
  with self.assertRaises(ValueError):m.verify_file(c,p,r,s)
 def test_licence_from_exact_rendered_revision(self):
  c,p,r,s=self.fixture();p['imageinfo'][0]['extmetadata'].pop('LicenseUrl');r={'pageid':10,'revid':20,'uri':m.nm.PDM};m.verify_file(c,p,r,s)
 def test_descriptions_excluded_from_production_projection(self):
  c,p,r,s=self.fixture();p['imageinfo'][0]['extmetadata']['ImageDescription']={'value':'Synthetic description'};projected=m.project_file(p);m.verify_file(c,projected,r,s);self.assertNotIn('ImageDescription',projected['imageinfo'][0]['extmetadata']);self.assertNotIn('synthetic description',projected['revisions'][0]['slots']['main']['*'])
 def test_source_swedish_title_is_a_valid_translation_match(self):
  c,p,r,s=self.fixture();c['raw']['official_capture']['item']['ObjTitleMainTxt_sv']='Syntetisk målning';p['imageinfo'][0]['extmetadata']['ObjectName']['value']='Syntetisk målning';m.verify_file(c,p,r,s)
 def test_rendered_accession_requires_same_file_revision(self):
  c,p,r,s=self.fixture();p['revisions'][0]['slots']['main']['*']=p['revisions'][0]['slots']['main']['*'].replace(' |accession number = NM 1','');c['rendered_identity_evidence']={'pageid':10,'revid':21,'accessions':['NM 1']}
  with self.assertRaises(ValueError):m.verify_file(c,p,r,s)
  c['rendered_identity_evidence']['revid']=20;m.verify_file(c,p,r,s)
 def test_rendered_accession_cannot_override_conflicting_number(self):
  c,p,r,s=self.fixture();p['revisions'][0]['slots']['main']['*']=p['revisions'][0]['slots']['main']['*'].replace('NM 1','NM 2');c['rendered_identity_evidence']={'pageid':10,'revid':20,'accessions':['NM 1']}
  with self.assertRaises(ValueError):m.verify_file(c,p,r,s)
 def test_reserved_character_in_official_filename(self):self.assertEqual(m.file_title('https://commons.wikimedia.org/wiki/File:Question?_painting.tif'),'File:Question? painting.tif')
 def test_arbitrary_query_not_a_filename(self):
  with self.assertRaises(ValueError):m.file_title('https://commons.wikimedia.org/wiki/File:Painting.tif?secret=not-a-title')
 def test_legacy_http_metadata_link_is_normalized_without_fetching_it(self):
  self.assertEqual(m.file_title('http://commons.wikimedia.org/wiki/File:Synthetic_painting.tif'),'File:Synthetic painting.tif')
 def test_empty_accession_does_not_consume_next_template_field(self):
  c,p,r,s=self.fixture();p['revisions'][0]['slots']['main']['*']=p['revisions'][0]['slots']['main']['*'].replace(' |accession number = NM 1',' |accession number =\n |place of creation = Somewhere')
  c['rendered_identity_evidence']={'pageid':10,'revid':20,'accessions':['NM 1']};m.verify_file(c,p,r,s)
 def test_exact_native_accession_link_is_accepted(self):
  c,p,r,s=self.fixture();p['revisions'][0]['slots']['main']['*']=p['revisions'][0]['slots']['main']['*'].replace(' |accession number = NM 1',' |accession number = {{Nationalmuseum Stockholm link|1|NM 1}}');m.verify_file(c,p,r,s)
 def test_accession_link_cannot_name_another_museum_object(self):
  c,p,r,s=self.fixture();p['revisions'][0]['slots']['main']['*']=p['revisions'][0]['slots']['main']['*'].replace(' |accession number = NM 1',' |accession number = {{Nationalmuseum Stockholm link|2|NM 1}}')
  with self.assertRaises(ValueError):m.verify_file(c,p,r,s)
 def discovery_fixture(self):
  c,p,r,s=self.fixture();c['raw']['official_capture']['item']['ObjWikimediaLinkTxt']=''
  c['raw']['commons_discovery']={'source_object_id':'1','query':'"Nationalmuseum" "1"','retrieved_at':'2026-01-01T00:00:00Z','response':{'query':{'search':[{'pageid':10,'title':p['title']}]}}}
  return c,p,r,s
 def test_discovered_file_still_requires_full_object_and_image_evidence(self):m.verify_file(*self.discovery_fixture())
 def test_discovery_does_not_override_an_existing_official_link(self):
  c,p,r,s=self.discovery_fixture();c['raw']['official_capture']['item']['ObjWikimediaLinkTxt']='https://commons.wikimedia.org/wiki/File:Other.tif'
  with self.assertRaises(ValueError):m.verify_file(c,p,r,s)
 def test_discovery_cannot_override_missing_photo_release(self):
  c,p,r,s=self.discovery_fixture();p['revisions'][0]['slots']['main']['*']=p['revisions'][0]['slots']['main']['*'].replace('2=PD-Nationalmuseum_Stockholm','2=PD-old')
  with self.assertRaises(ValueError):m.verify_file(c,p,r,s)
 def test_discovery_must_identify_the_exact_file_page(self):
  c,p,r,s=self.discovery_fixture();c['raw']['commons_discovery']['response']['query']['search'][0]['pageid']=11
  with self.assertRaises(ValueError):m.verify_file(c,p,r,s)
 def test_discovered_detail_is_held(self):
  c,p,r,s=self.discovery_fixture();p['title']='File:Synthetic painting detail.tif';c['raw']['commons_discovery']['response']['query']['search'][0]['title']=p['title']
  with self.assertRaises(ValueError):m.verify_file(c,p,r,s)
if __name__=='__main__':unittest.main()
