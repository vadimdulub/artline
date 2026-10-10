"""Bounded public collection supplements; source PDFs are research evidence only."""
import gzip,importlib.util,json
from pathlib import Path
from urllib.parse import urlencode
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-harris-box-additions-common-20261009.py');n=module('n','museum-expansion-britain-nine-native-20261009.py');m=s.m;RUN=s.RUN;n.RUN=RUN
n.HOSTS['artfund']={'www.artfund.org','artfund.org'}
TASKS=[
 ('box','https://theboxplymouth.com/wp-json/wp/v2/posts?'+urlencode({'search':'Cottonian','per_page':20,'_fields':'id,link,slug,title,excerpt,content'})),
 ('box','https://theboxplymouth.com/wp-json/wp/v2/posts?'+urlencode({'search':'Collections Insight','per_page':20,'page':1,'_fields':'id,link,slug,title,excerpt,content'})),
 ('harris','https://theharris.org.uk/wp-json/wp/v2/collection-item?'+urlencode({'collections':278,'per_page':25,'_fields':'id,link,slug,title,content,collections'})),
 ('artfund','https://www.artfund.org/our-purpose/art-funded-by-you/puck'),
 ('box','https://www.theboxplymouth.com/storage/sir-joshua-reynolds-ks2-3-1580918044.pdf')]
def main():
 dest=RUN/'supplements-001.json.gz';assert not dest.exists();rows=[];stopped=set();fails={}
 for provider,url in TASKS:
  if provider in stopped:rows.append(dict(provider=provider,url=url,state='unrequested_after_access_hold'));continue
  try:
   b,c=n.capture(provider,url);v=dict(provider=provider,url=url,capture=c)
   if b.startswith(b'%PDF'):v['format']='pdf'
   elif '/wp-json/' in url:v['data']=json.loads(b)
   else:v['parsed']=n.parsed(b)
   rows.append(v);fails[provider]=0;print(json.dumps(dict(provider=provider,url=url,bytes=len(b),format=v.get('format'),records=len(v.get('data',[])))),flush=True)
  except Exception as e:
   fails[provider]=fails.get(provider,0)+1;rows.append(dict(provider=provider,url=url,error=type(e).__name__+': '+str(e)));print(json.dumps(rows[-1]),flush=True)
   if fails[provider]>=3 or any(t in str(e) for t in ['403','429','robots']):stopped.add(provider)
 m.save(dest,dict(at=m.now(),rows=rows,stopped_providers=sorted(stopped),script_reference=s.ref(Path(__file__).resolve()),policy='Selected museum-curated art articles and official Reynolds education guide plus acquisition-funder object record. No held-provider requests,media attachments or creation date inference from post publication. PDF illustrations remain research evidence.'))
if __name__=='__main__':main()
