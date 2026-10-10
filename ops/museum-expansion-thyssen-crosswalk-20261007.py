#!/usr/bin/env python3
"""Bounded independent Wikidata title/ID leads for already selected official pages."""
import argparse,importlib.util,json
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-thyssen-facts-20261007.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f);m=f.m;RUN=f.RUN;n=f.d.n
n.SITES['thyssen-sparql']='https://query.wikidata.org';n.SITES['thyssen-wikidata']='https://www.wikidata.org'
def index():
 source=RUN/'native-candidates-002.json.gz';rows=m.load(source)['rows'];urls=sorted({url for r in rows if 'facts' in r for url in r['facts']['native_page_urls']});assert len(urls)<=550;refs=[]
 for start in range(0,len(urls),24):
  selected=urls[start:start+24];path=RUN/'wikidata-url-index-001'/('%03d.json.gz'%(start//24+1))
  if not path.exists():
   query='SELECT DISTINCT ?item ?url WHERE { VALUES ?url { '+' '.join('<'+url+'>' for url in selected)+' } ?item wdt:P195 wd:Q176251; wdt:P973 ?url . }'
   request=requests.Request('GET','https://query.wikidata.org/sparql',params={'query':query,'format':'json'}).prepare().url
   try:
    raw,cap=n.capture('thyssen-sparql',request);data=json.loads(raw)['results']['bindings'];result=[{k:v['value'] for k,v in r.items()} for r in data];assert len(result)<=100 and all(r['url'] in selected for r in result)
    m.save(path,dict(query=query,selected_urls=selected,rows=result,capture=cap,candidate_reference=f.ref(source)))
   except Exception as ex:
    m.save(path,dict(query=query,selected_urls=selected,error=type(ex).__name__+': '+str(ex),candidate_reference=f.ref(source)));print('ERROR',start,str(ex),flush=True);refs.append(f.ref(path));break
  refs.append(f.ref(path));print('URL batch',start+len(selected),'of',len(urls),flush=True)
 m.save(RUN/'wikidata-url-crosswalk-001.json.gz',dict(at=m.now(),batches=refs,policy='Only exact URLs of267already captured primary objects. Museum-scoped secondary identity leads,not approvals; no unrelated object or image download. Native metadata remains authoritative for these selected records.'))
def entities():
 refs=[];ids=set()
 for ref in m.load(RUN/'wikidata-url-crosswalk-001.json.gz')['batches']:
  p=m.ROOT/ref['path'];assert f.ref(p)==ref;v=m.load(p)
  for row in v.get('rows',[]):ids.add(row['item'].rsplit('/',1)[-1])
 ids=sorted(ids);assert len(ids)<=300
 for start in range(0,len(ids),25):
  selected=ids[start:start+25];p=RUN/'wikidata-objects-001'/('%03d.json.gz'%(start//25+1))
  if not p.exists():
   url=requests.Request('GET','https://www.wikidata.org/w/api.php',params={'action':'wbgetentities','ids':'|'.join(selected),'props':'labels|aliases|claims','format':'json'}).prepare().url
   raw,cap=n.capture('thyssen-wikidata',url);data=json.loads(raw)['entities'];assert set(data)==set(selected);m.save(p,dict(ids=selected,entities=data,capture=cap))
  refs.append(f.ref(p));print('Secondary objects',start+len(selected),'of',len(ids),flush=True)
 m.save(RUN/'wikidata-capture-001.json.gz',dict(at=m.now(),objects=len(ids),batches=refs,policy='Secondary exact-native-URL identity and multilingual-title leads. Raw qualifiers,references and claims retained. No native or secondary images.'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['index','entities']);a=p.parse_args();globals()[a.command]()
