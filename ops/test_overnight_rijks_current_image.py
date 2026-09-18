"""Synthetic source-page rights/resource regression checks."""
import copy,importlib.util,json,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('rijks',Path(__file__).with_name('overnight-rijks-images.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def html(obj):
 nodes=[]
 def pack(v):
  i=len(nodes);nodes.append(None)
  if isinstance(v,dict):nodes[i]={k:pack(x) for k,x in v.items()}
  elif isinstance(v,list):nodes[i]=[pack(x) for x in v]
  else:nodes[i]=v
  return i
 pack(obj);return '<script id="__NUXT_DATA__" type="application/json">'+json.dumps(nodes)+'</script>'
class TestCurrentRijksImage(unittest.TestCase):
 def setUp(self):
  self.c={'external_id':'42','title':'Synthetic flowers','accession_number':'SK-SYNTHETIC-42'}
  self.obj={'objectNodeUri':'https://id.rijksmuseum.nl/42','objectNumber':'SK-SYNTHETIC-42','title':'Synthetic flowers','dataTab':[{'name':'Copyright','values':['<a href="'+m.PDM+'deed.en">Public domain</a>']}],'micrioImage':{'type':'MicrioImageApiModel','micrioId':'Example42','isDownloadable':True,'crop':None,'altText':'Synthetic flowers','width':1200,'height':2400}}
  self.service={'id':'https://iiif.micr.io/Example42','type':'ImageService3','organisation':{'slug':'rijks-collectie'},'width':1200,'height':2400}
 def test_exact_current_resource(self):self.assertEqual(m.current_page_image(self.c,html(self.obj),self.service),'https://iiif.micr.io/Example42/full/1000,/0/default.jpg')
 def test_wrong_accession(self):
  self.obj['objectNumber']='SK-OTHER'
  with self.assertRaises(ValueError):m.current_page_image(self.c,html(self.obj),self.service)
 def test_no_download_permission(self):
  self.obj['micrioImage']['isDownloadable']=False
  with self.assertRaises(ValueError):m.current_page_image(self.c,html(self.obj),self.service)
 def test_restricted_licence(self):
  self.obj['dataTab'][0]['values']=['<a href="https://creativecommons.org/licenses/by-nc/4.0/">Public domain</a>']
  with self.assertRaises(ValueError):m.current_page_image(self.c,html(self.obj),self.service)
 def test_different_service(self):
  self.service['id']='https://iiif.micr.io/Other'
  with self.assertRaises(ValueError):m.current_page_image(self.c,html(self.obj),self.service)
 def test_conflicting_rights(self):
  self.obj['dataTab'].append({'name':'Copyright','values':['Reserved']})
  with self.assertRaises(ValueError):m.current_page_image(self.c,html(self.obj),self.service)
 def test_cropped_image(self):
  self.obj['micrioImage']['crop']='100,100,500,500'
  with self.assertRaises(ValueError):m.current_page_image(self.c,html(self.obj),self.service)
if __name__=='__main__':unittest.main()
