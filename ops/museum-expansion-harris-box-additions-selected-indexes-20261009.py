"""Museum-scoped art discovery before selecting dated physical objects."""
import gzip,importlib.util,json
from pathlib import Path
from urllib.parse import urlencode
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-harris-box-additions-common-20261009.py');n=module('n','museum-expansion-britain-nine-native-20261009.py');m=s.m;RUN=s.RUN;n.RUN=RUN
def main():
 dest=RUN/'selected-indexes-001.json.gz';assert not dest.exists();disc=m.load(RUN/'native-discovery-001.json.gz');tax=m.load(RUN/'harris-taxonomy-001.json.gz')['rows'][0]['data'];assert {238,240,237}<={x['id'] for x in tax};rows=[]
 tasks=[('harris','/wp/v2/collection-item',{'collections':'238,240,237','per_page':80,'orderby':'id','order':'asc','_fields':'id,link,slug,title,content,collections'}),('box','/wp/v2/posts',{'search':'painting','per_page':20,'page':1,'_fields':'id,link,slug,title,excerpt,content'})]
 for provider,route,params in tasks:
  dis=next(x for x in disc['rows'] if x['provider']==provider);raw=json.loads(gzip.decompress((m.ROOT/dis['capture']['body_path']).read_bytes()));assert route in raw['routes'];base=raw['routes'][route]['_links']['self'][0]['href'];url=base+'?'+urlencode(params)
  try:
   b,cap=n.capture(provider,url);data=json.loads(b);assert isinstance(data,list) and len(data)<=params['per_page'];rows.append(dict(provider=provider,url=url,capture=cap,data=data));print(json.dumps(dict(provider=provider,records=len(data),objects=[dict(id=x['id'],title=x['title']['rendered'],link=x['link']) for x in data]),ensure_ascii=False),flush=True)
  except Exception as e:rows.append(dict(provider=provider,url=url,error=type(e).__name__+': '+str(e)));print(json.dumps(rows[-1]),flush=True)
 m.save(dest,dict(at=m.now(),rows=rows,discovery_reference=s.ref(RUN/'native-discovery-001.json.gz'),taxonomy_reference=s.ref(RUN/'harris-taxonomy-001.json.gz'),script_reference=s.ref(Path(__file__).resolve()),policy='Bounded public Harris curated painting/paper/sculpture subset,not entire museum collection.20Box painting-related articles maximum. Selection requires literal artwork date,creator,physical identity and holding evidence; article/publication dates,exhibition loans and depicted years are not creation/ownership. No media download.'))
if __name__=='__main__':main()
