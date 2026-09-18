"""Synthetic rights/identity boundary tests. No catalogue writes or live requests."""
import copy
import importlib.util
import unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('donations',Path(__file__).with_name('popular-reims-donations.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def claim(qid):return {'mainsnak':{'snaktype':'value','datavalue':{'value':{'id':qid}}}}

def fixture():
 c={'artist_names':['Example Painter'],'creators':[{'death':1850}],'qid':'Q123'}
 obj={'title':'Synthetic Painting','titles':['Synthetic Painting'],'accession_number':'123.4.5','photographer':'Example Photographer','page':'https://musees-reims.fr/oeuvre/synthetic-painting'}
 text='''{{Artwork
 |artist = {{creator:Example Painter}}
 |photographer = Example Photographer
 |title = Synthetic Painting
 |object type = painting
 |institution = {{Institution:Musée des Beaux-Arts, Reims}}
 |source = {{Institution:Musée des Beaux-Arts, Reims}}
 |accession number = 123.4.5
 |references = https://musees-reims.fr/oeuvre/synthetic-painting
}}
{{Licensed-PD-Art-two|PD-old-auto|PD-US-expired|deathyear=1850|Cc-by-sa-2.0-fr}}'''
 page={'pageid':123,'title':'File:Synthetic Painting.jpg','revisions':[{'revid':456,'slots':{'main':{'*':text}}}],'imageinfo':[{'user':m.DONOR,'timestamp':'2022-12-21T11:00:00Z','mime':'image/jpeg','width':960,'height':800,'url':'https://upload.wikimedia.org/wikipedia/commons/0/00/Synthetic.jpg','extmetadata':{'LicenseShortName':{'value':'Public domain'}}}]}
 sdc={'id':'M123','statements':{'P275':[claim('Q77355872')],'P6243':[claim('Q123')]}}
 html=f'<div class="licensetpl"><span class="licensetpl_link">{m.LICENSE}deed.en</span></div>'
 render={'pageid':123,'revision':456,'licence_html':html,'selected_fields_sha256':m.core.sha(html.encode())}
 return c,obj,page,sdc,render

class DonationBoundary(unittest.TestCase):
 def test_explicit_donation_license_is_supported(self):self.assertIn('upload.wikimedia.org',m.verify_file(*fixture()))
 def reject(self,mutator,message=None):
  f=fixture();mutator(*f)
  with self.assertRaisesRegex(ValueError,message or '.'):m.verify_file(*f)
 def test_third_party_uploader_not_institutional_provenance(self):self.reject(lambda c,o,p,s,r:p['imageinfo'][0].update(user='Someone Else'),'donation')
 def test_api_public_domain_summary_does_not_clear_image(self):
  self.reject(lambda c,o,p,s,r:p['revisions'][0]['slots']['main'].update({'*':p['revisions'][0]['slots']['main']['*'].replace('Cc-by-sa-2.0-fr','PD-Art')}),'photograph')
 def test_wrong_inventory(self):self.reject(lambda c,o,p,s,r:o.update(accession_number='987.6.5'),'inventory')
 def test_wrong_artist(self):self.reject(lambda c,o,p,s,r:c.update(artist_names=['Other Painter']),'creator')
 def test_new_museum_photo_does_not_change_donated_credit(self):
  f=fixture();f[1]['reference_photographer']='New Photographer';m.verify_file(*f);self.assertEqual(m.photographer(f[2]),'Example Photographer')
 def test_missing_photographer_held(self):
  self.reject(lambda c,o,p,s,r:p['revisions'][0]['slots']['main'].update({'*':p['revisions'][0]['slots']['main']['*'].replace('|photographer = Example Photographer','|unused = Example Photographer')}),'credit')
 def test_wrong_file_revision(self):self.reject(lambda c,o,p,s,r:r.update(revision=999),'revision')
 def test_restricted_statement(self):self.reject(lambda c,o,p,s,r:p['imageinfo'][0]['extmetadata'].update(Restrictions={'value':'non-commercial'}),'restriction')
 def test_nc_template_is_conflict(self):
  self.reject(lambda c,o,p,s,r:p['revisions'][0]['slots']['main'].update({'*':p['revisions'][0]['slots']['main']['*']+'\n{{cc-by-nc-4.0}}'}),'Restricted')
 def test_structured_licence_conflict(self):self.reject(lambda c,o,p,s,r:s['statements']['P275'].append(claim('Q999')),'licence')
 def test_wrong_physical_object(self):self.reject(lambda c,o,p,s,r:s['statements'].update(P6243=[claim('Q987')]),'identity')
 def test_unknown_artwork_copyright(self):self.reject(lambda c,o,p,s,r:c['creators'][0].update(death=None),'copyright')
 def test_search_engine_url_rejected(self):self.reject(lambda c,o,p,s,r:p['imageinfo'][0].update(thumburl='https://images.google.com/foo.jpg'),'resource')
 def test_donor_requires_official_site_link(self):
  proof={'url':m.DONATION_PAGE,'retrieved_at':'now','response_sha256':'abc','links':[{'href':'https://commons.wikimedia.org/w/index.php?title=Special:ListFiles/Mus%C3%A9e_des_Beaux-Arts_de_Reims'}]}
  m.verify_donor(proof)
  proof['links'][0]['href']='https://commons.wikimedia.org/w/index.php?title=Special:ListFiles/Someone_Else'
  with self.assertRaises(ValueError):m.verify_donor(proof)
 def test_licence_version_and_jurisdiction_preserved(self):
  self.assertEqual(m.canonical(m.LICENSE+'deed.en'),m.LICENSE)
  self.assertNotEqual(m.canonical(m.LICENSE.replace('/fr/','/de/')),m.LICENSE)
 def test_general_pd_does_not_override_exact_photo_sa(self):
  f=fixture();html=f'<span class="licensetpl_link">{m.common.PDM}</span>'
  f[-1].update(licence_html=html,selected_fields_sha256=m.core.sha(html.encode()))
  with self.assertRaisesRegex(ValueError,'licence'):m.verify_file(*f)

if __name__=='__main__':unittest.main()
