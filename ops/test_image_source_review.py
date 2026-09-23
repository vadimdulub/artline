"""Offline evidence counterexamples; no database fixtures."""
import importlib.util,json,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('prepare-wikimedia-catalogue-images.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def record(death):return {'creator_entity':{'claims':{'P570':[{'rank':'normal','mainsnak':{'snaktype':'value','datavalue':{'value':{'precision':9,'time':f'+{death:04d}-01-01T00:00:00Z'}}}}]}}}
class Review(unittest.TestCase):
 def test_legacy_cc0_link_retains_licence_and_language(self):
  self.assertEqual(m.licence_policy_url('CC0','http://creativecommons.org/publicdomain/zero/1.0/deed.en'),'https://creativecommons.org/publicdomain/zero/1.0/deed.en')
 def test_different_licence_is_not_silently_relabelled(self):
  with self.assertRaises(ValueError):m.licence_policy_url('CC BY 4.0','https://creativecommons.org/licenses/by-nc/4.0/')
 def test_lookalike_licence_host_is_rejected(self):
  with self.assertRaises(ValueError):m.licence_policy_url('CC0','https://creativecommons.org.example.com/publicdomain/zero/1.0/')
 def test_saved_original_survives_smaller_resume_download_budget(self):
  with tempfile.TemporaryDirectory(prefix='artline-image-resume-') as folder:
   root=Path(folder);run=root/'run';backups=root/'backups';raw=b'preserved-original'
   rec={'qid':'Q123','images':['Example.jpg'],'entity':{},'creator_entity':{'claims':{}},'creator_label':'Named painter','title':'Example','titles':['Example'],'accession':None}
   info={'size':len(raw),'width':2000,'height':2000,'url':'https://upload.wikimedia.org/example.jpg','thumburl':'https://thumb.wikimedia.org/example.jpg','descriptionurl':'https://commons.wikimedia.org/wiki/File:Example.jpg','sha1':'unused-preserved-source-hash','extmetadata':{k:{'value':v} for k,v in {'LicenseShortName':'Public domain','Copyrighted':'False','Artist':'Named painter','ObjectName':'Example'}.items()}}
   page={'imageinfo':[info],'revisions':[{'slots':{'main':{'*':'Q123'}}}]}
   download={'kind':'commons_original','url':info['url'],'sha256':m.r.core.sha(raw),'bytes':len(raw)}
   m.r.core.save_new(run/'selected/records.json',{'selected':[rec]});m.r.core.save_new(run/'image-receipts/Q123.json',download);m.r.core.save_new(backups/'selected-originals/Q123.original',raw)
   fetcher=types.SimpleNamespace(session=types.SimpleNamespace(headers={}))
   with patch.multiple(m.r,RUN=run,BACKUPS=backups,ROOT=root),patch.object(m.r,'fetch',return_value=({'query':{'pages':{'1':page}}},{})),patch.object(m.r,'date',return_value={'eligible':True}),patch.object(m.r.core,'Fetcher',return_value=fetcher),patch.object(m.r.core,'compress',side_effect=OSError('Source JPEG is truncated')):
    m.main(original_byte_limit=1,original_pixel_limit=1)
   failed=json.loads((run/'ready/Q123.json').read_text());self.assertIsNone(failed['image']);self.assertEqual(failed['image_reason'],'Source JPEG is truncated')
   (run/'ready/Q123.json').rename(run/'deferred-Q123.json')
   with patch.multiple(m.r,RUN=run,BACKUPS=backups,ROOT=root),patch.object(m.r,'fetch',return_value=({'query':{'pages':{'1':page}}},{})),patch.object(m.r,'date',return_value={'eligible':True}),patch.object(m.r.core,'Fetcher',return_value=fetcher),patch.object(m.r.core,'compress',return_value=(b'compressed',1,1,80)):
    m.main(original_byte_limit=1,original_pixel_limit=1)
   result=json.loads((run/'ready/Q123.json').read_text())
   self.assertEqual(result['image_outcome'],'prepared');self.assertEqual(result['image']['download'],download);self.assertEqual(result['image']['source_image_url'],info['url']);self.assertEqual((backups/'selected-originals/Q123.original').read_bytes(),raw)
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
