"""Selected further public museum articles and acquisition-funder navigation."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urlencode
z=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-box-continuation-discovery-20261009.py'));d=importlib.util.module_from_spec(z);z.loader.exec_module(d)
def main():
 dest=d.RUN/'supplements-001.json.gz';assert not dest.exists();rows=[];stopped=set();fails={}
 tasks=[('box','https://theboxplymouth.com/wp-json/wp/v2/posts?'+urlencode(dict(search='painting',per_page=20,page=p,orderby='id',order='asc',_fields='id,link,slug,title,excerpt,content'))) for p in [4,5,6]]
 tasks += [('box','https://theboxplymouth.com/wp-json/wp/v2/media?'+urlencode(dict(search='reynolds',mime_type='application/pdf',per_page=20,_fields='id,link,slug,title,caption,description,mime_type,source_url'))),('artfund','https://www.artfund.org/explore/museums-and-galleries/the-box-plymouth')]
 for provider,url in tasks:
  if provider in stopped:rows.append(dict(provider=provider,url=url,state='unrequested_after_access_hold'));continue
  try:
   body,cap=d.n.capture(provider,url);v=dict(provider=provider,url=url,capture=cap)
   if '/wp-json/' in url:v['data']=json.loads(body);assert isinstance(v['data'],list) and len(v['data'])<=20
   else:v['parsed']=d.n.parsed(body)
   rows.append(v);fails[provider]=0;print(json.dumps(dict(provider=provider,records=len(v.get('data',[])),bytes=len(body))),flush=True)
  except Exception as e:
   rows.append(dict(provider=provider,url=url,error=type(e).__name__+': '+str(e)));fails[provider]=fails.get(provider,0)+1
   if fails[provider]>=3 or any(t in str(e) for t in ['403','429','robots']):stopped.add(provider)
 d.m.save(dest,dict(at=d.m.now(),rows=rows,stopped_providers=sorted(stopped),script_reference=d.s.ref(Path(__file__).resolve()),policy='Public GET view-only bounded article review. No media bytes,artist-lifespan date inference or database writes.'))
if __name__=='__main__':main()
