"""Bounded selected ArCo object pages and exact RDF subjects; no DB writes."""
import collections,gzip,hashlib,importlib.util,json,re,threading,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-italy-fourth-discovery-20261008.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m;a=d.arco;RUN=d.RUN
ROOT=RUN/'current-001';ENDPOINT='https://dati.cultura.gov.it/sparql';STOP=threading.Event();FAILURES=collections.Counter();LOCK=threading.Lock()
class SourceFailure(Exception):pass
def fetch(url,params=None):
 key=hashlib.sha256(json.dumps(dict(url=url,params=params),sort_keys=True).encode()).hexdigest();dest=ROOT/'captures'/(key+'.json');body=ROOT/'captures'/(key+'.body.gz')
 if dest.exists():
  saved=m.load(dest)
  if saved.get('status')!=200:raise SourceFailure('Retained failed request '+key)
  raw=gzip.decompress(body.read_bytes());assert hashlib.sha256(raw).hexdigest()==saved['sha256'];return raw,saved,d.ref(dest),d.ref(body)
 if STOP.is_set():raise SourceFailure('Source requests stopped after access denial or repeated transient failures')
 time.sleep(.12);host=urlparse(url).netloc
 receipt=dict(url=url,params=params,retrieved_at=m.now(),method='GET')
 try:
  with requests.get(url,params=params,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected metadata; no images)'},timeout=(12,45),stream=True) as response:
   raw=b''
   for chunk in response.iter_content(65536):
    raw+=chunk
    if len(raw)>5_000_000:raise ValueError('Selected metadata bound exceeded')
   receipt.update(status=response.status_code,final_url=response.url,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),content_type=response.headers.get('Content-Type'))
   body.parent.mkdir(parents=True,exist_ok=True);assert not body.exists();body.write_bytes(gzip.compress(raw,mtime=0))
   if response.status_code!=200:raise SourceFailure('HTTP '+str(response.status_code))
  with LOCK:FAILURES[host]=0
 except Exception as error:
  receipt['error']=repr(error)
  with LOCK:
   FAILURES[host]+=1
   if receipt.get('status') in [401,403,429] or FAILURES[host]>=3:STOP.set()
  receipt['no_retry']=True;m.save(dest,receipt);raise SourceFailure(str(error))
 m.save(dest,receipt);return raw,receipt,d.ref(dest),d.ref(body)
def subjects(uris):
 assert 1<=len(uris)<=20 and len(set(uris))==len(uris)
 assert all(re.fullmatch(r'https://w3id.org/arco/resource/[A-Za-z0-9_./%-]+',v) for v in uris)
 query='SELECT DISTINCT ?s ?p ?o WHERE { VALUES ?s { '+' '.join('<'+v+'>' for v in uris)+' } ?s ?p ?o } ORDER BY ?s ?p ?o LIMIT 10000'
 raw,receipt,rp,bp=fetch(ENDPOINT,dict(query=query,format='application/sparql-results+json'))
 data=json.loads(raw);rows=[{k:v['value'] for k,v in row.items()} for row in data['results']['bindings']]
 assert len(rows)<10000 and all(row['s'] in uris for row in rows)
 return rows,dict(subjects=uris,receipt_reference=rp,body_reference=bp,rows=len(rows))
LINKS=(a.GRAPH_LINKS-{a.LOC+'hasCulturalPropertyAddress'})|{a.DD+'hasMeasurementCollection',a.DD+'hasCulturalPropertyType',a.CORE+'hasCulturalPropertyCataloguingCategory'}
def graph_batch(rows):
 uris=['https://w3id.org/arco/resource/'+v['index_record']['source_record_id'] for v in rows];roots,component=subjects(uris);triples=list(roots);components=[component]
 children=sorted({v['o'] for v in roots if v['p'] in LINKS and v['o'].startswith('https://w3id.org/arco/resource/')}-set(uris))
 for start in range(0,len(children),20):
  extra,comp=subjects(children[start:start+20]);triples+=extra;components.append(comp)
 measurements=sorted({v['o'] for v in triples if v['p']==a.DD+'hasMeasurement' and v['o'].startswith('https://w3id.org/arco/resource/')}-set(children)-set(uris))
 for start in range(0,len(measurements),20):
  extra,comp=subjects(measurements[start:start+20]);triples+=extra;components.append(comp)
 return triples,components
def page(row):
 try:
  raw,receipt,rp,bp=fetch(row['index_record']['source_url']);fields=a.fields(raw);soup=BeautifulSoup(raw,'html.parser')
  for tag in soup(['script','style','noscript']):tag.decompose()
  path=ROOT/'pages'/('%04d.txt'%row['number']);path.parent.mkdir(exist_ok=True);text=soup.get_text('\n',strip=True)
  if path.exists():assert path.read_text()==text
  else:path.write_text(text)
  return dict(number=row['number'],fields=fields,receipt_reference=rp,body_reference=bp,text_reference=d.ref(path),retrieved_at=receipt['retrieved_at'])
 except Exception as error:return dict(number=row['number'],error=repr(error),state='object_source_failure')
def main():
 ROOT.mkdir(exist_ok=True);(ROOT/'batches').mkdir(exist_ok=True)
 discovery=m.load(RUN/'five-museum-discovery-001.json.gz');allowed=set(m.load(RUN/'source-aliases-001.json.gz')['capture_numbers']);rows=[v for v in discovery['rows'] if v['number'] in allowed];done=[]
 # Keep museum scope boundaries explicit, including multiple old institute URIs.
 for iid in dict.fromkeys(v['institution_id'] for v in rows):
  selected=[v for v in rows if v['institution_id']==iid]
  for offset in range(0,len(selected),15):
   group=selected[offset:offset+15];dest=ROOT/'batches'/('%04d-%04d.json.gz'%(group[0]['number'],group[-1]['number']))
   if dest.exists():done.append(d.ref(dest));continue
   if STOP.is_set():break
   try:
    triples,components=graph_batch(group)
    with ThreadPoolExecutor(max_workers=2) as pool:pages=list(pool.map(page,group))
    result=dict(at=m.now(),numbers=[v['number'] for v in group],institution_id=iid,triples=triples,graph_components=components,pages=pages,source_state='captured',database_writes=0,images=0)
   except Exception as error:result=dict(at=m.now(),numbers=[v['number'] for v in group],institution_id=iid,source_state='graph_source_failure',error=repr(error),database_writes=0,images=0)
   m.save(dest,result);done.append(d.ref(dest));print(json.dumps(dict(numbers=result['numbers'],state=result['source_state'],pages=len(result.get('pages',[])),failed_pages=sum('error' in v for v in result.get('pages',[])),stopped=STOP.is_set())),flush=True)
  if STOP.is_set():break
 target=RUN/'source-capture-001.json';assert not target.exists();m.save(target,dict(at=m.now(),selected=len(rows),batches=done,requests_stopped=STOP.is_set(),failure_counters=dict(FAILURES),capture_reference=d.ref(Path(__file__).resolve()),discovery_reference=d.ref(RUN/'five-museum-discovery-001.json.gz'),source_aliases_reference=d.ref(RUN/'source-aliases-001.json.gz'),policy='Bounded selected primary metadata only. Each actual HTTP response and exact RDF subject request preserved. No retry after denied/failed request. Captures are not artwork approvals; source custody, dates, physical identity and components require review.',database_writes=0,images=0))
 print(json.dumps(dict(complete=True,batches=len(done),stopped=STOP.is_set())),flush=True)
if __name__=='__main__':main()
