"""Bounded selected public Box articles,document metadata and acquisition records."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urlencode
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-box-continuation-common-20261009.py');n=module('n','museum-expansion-britain-nine-native-20261009.py');m=s.m;RUN=s.RUN;n.RUN=RUN;n.HOSTS['artfund']={'www.artfund.org','artfund.org'}
PRIOR=m.RUN/'native/harris-box-additions-20261009'
ARTFUND=['the-royal-william-victualling-yard-at-plymouth','plymouth-pier-from-the-hoe','plymouth-harbour','plymouth-from-mount-edgcumbe','the-drake-cup','kilchurn-castle-and-loch-awe','large-anthropomorphic-crab','panel-2','model-of-the-napoleonic-ship-lalexandre']
def tasks():
 for page in [2,3]:yield 'box','https://theboxplymouth.com/wp-json/wp/v2/posts?'+urlencode(dict(search='painting',per_page=20,page=page,orderby='id',order='asc',_fields='id,link,slug,title,excerpt,content'))
 yield 'box','https://theboxplymouth.com/wp-json/wp/v2/media?'+urlencode(dict(search='art',mime_type='application/pdf',per_page=20,_fields='id,link,slug,title,caption,description,mime_type,source_url'))
 for slug in ARTFUND:yield 'artfund','https://www.artfund.org/our-purpose/art-funded-by-you/'+slug
def main():
 dest=RUN/'native-discovery-001.json.gz';assert not dest.exists();rows=[];stopped=set();fails={}
 for provider,url in tasks():
  if provider in stopped:rows.append(dict(provider=provider,url=url,state='unrequested_after_access_hold'));continue
  try:
   b,c=n.capture(provider,url);v=dict(provider=provider,url=url,capture=c)
   if '/wp-json/' in url:v['data']=json.loads(b);assert isinstance(v['data'],list) and len(v['data'])<=20
   else:v['parsed']=n.parsed(b)
   rows.append(v);fails[provider]=0;print(json.dumps(dict(provider=provider,url=url,bytes=len(b),records=len(v.get('data',[])))),flush=True)
  except Exception as e:
   rows.append(dict(provider=provider,url=url,error=type(e).__name__+': '+str(e)));print(json.dumps(rows[-1]),flush=True);fails[provider]=fails.get(provider,0)+1
   if fails[provider]>=3 or any(t in str(e) for t in ['403','429','robots']):stopped.add(provider)
 m.save(dest,dict(at=m.now(),rows=rows,stopped_providers=sorted(stopped),api_registry_reference=s.ref(PRIOR/'native-discovery-001.json.gz'),script_reference=s.ref(Path(__file__).resolve()),policy='Forty selected historical painting articles maximum,twenty public document-metadata matches andnine selected acquisition-funder object records. No image/PDF bytes,private fields,publication-date inference,held-provider requests or database writes. Artist lifespan accidentally used in funder date field is not accepted as object date. Unlocated architectural panel held,not blindly assigned.'))
if __name__=='__main__':main()
