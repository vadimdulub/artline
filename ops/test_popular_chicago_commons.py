"""Synthetic Commons/native identity and layered image-rights checks."""
import copy,importlib.util,unittest
from pathlib import Path
def module(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('m','popular-chicago-commons.py');fixtures=module('fixtures','test_popular_chicago_verification.py')
class Commons(unittest.TestCase):
    def setUp(self):
        f=fixtures.Verification();f.setUp();facts=m.native.metadata(f.obj,f.artist,f.person)
        def claim(q):return {'rank':'normal','mainsnak':{'snaktype':'value','datavalue':{'value':{'id':q}}}}
        url='https://www.artic.edu/artworks/2';file='https://commons.wikimedia.org/wiki/File:Synthetic_1900.1.jpg';photo='https://upload.wikimedia.org/synthetic.jpg'
        page={'ns':6,'pageid':10,'title':'File:Synthetic 1900.1.jpg','imageinfo':[{'mime':'image/jpeg','descriptionurl':file,'thumburl':photo,'extmetadata':{'Credit':{'value':'<a href="'+url+'">museum</a>'},'Artist':{'value':'Example Painter'}}}],
              'revisions':[{'revid':12,'slots':{'main':{'*':'{{Artwork|source='+url+'|wikidata=Q123}} {{Licensed-PD-Art|PD-old-auto-1923|Cc-zero|deathyear=1880}}'}}}]}
        sdc={'statements':{'P275':[claim('Q6938433')],'P6243':[claim('Q123')],'P180':[claim('Q123')]}}
        rendered={'parse':{'pageid':10,'revid':12,'text':{'*':'<span class="licensetpl_link">'+m.native.CC0+'</span><span class="licensetpl_link">'+m.common.PDM+'</span>'}}}
        self.im={**facts,'external_id':'2','artist':'Example Painter','artist_evidence':f.artist,'source_artist':f.person,'policy_url':m.native.CC0,'rights_status':'cc0','page':file,'source_record_url':url,'source_image_url':photo,'creator_credit':'Example Painter; Art Institute of Chicago','attribution_text':'Synthetic credit; CC0','raw':{'museum_record':f.obj,'commons':page,'structured_data':sdc,'rendered_licences':rendered}}
    def test_exact_native_file_and_cc0_photo(self):m.verify(self.im)
    def test_licensing_revision_change_is_rejected(self):
        self.im['raw']['rendered_licences']['parse']['revid']=13
        with self.assertRaises(AssertionError):m.verify(self.im)
    def test_native_source_url_change_is_rejected(self):
        self.im['raw']['commons']['imageinfo'][0]['extmetadata']['Credit']['value']='<a href="https://www.artic.edu/artworks/3">other</a>'
        with self.assertRaises(AssertionError):m.verify(self.im)
    def test_object_copyright_cannot_be_overridden_by_photo_label(self):
        self.im['raw']['museum_record']['copyright_notice']='Rights reserved'
        with self.assertRaises(AssertionError):m.verify(self.im)
    def test_a_metadata_cc0_label_is_insufficient(self):
        self.im['raw']['commons']['revisions'][0]['slots']['main']['*']='{{Artwork|source=https://www.artic.edu/artworks/2|wikidata=Q123}} Metadata CC0'
        with self.assertRaises(AssertionError):m.verify(self.im)
if __name__=='__main__':unittest.main()
