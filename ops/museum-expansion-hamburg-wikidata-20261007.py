#!/usr/bin/env python3
"""Bounded independent public Wikidata metadata discovery for Hamburg; no images or DB writes."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-hamburg-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m;n=d.n
n.SITES['hamburg-sparql']='https://query.wikidata.org';n.SITES['hamburg-wikidata']='https://www.wikidata.org'
QUERY='''SELECT DISTINCT ?item ?date ?inventory ?creator ?label ?german ?url ?wikiart WHERE {
 ?item wdt:P195 wd:Q169542; wdt:P31 wd:Q3305213; wdt:P571 ?date; wdt:P170 ?creator.
 FILTER(?date < "1971-01-01T00:00:00Z"^^xsd:dateTime)
 OPTIONAL { ?item wdt:P217 ?inventory }
 OPTIONAL { ?item rdfs:label ?label FILTER(LANG(?label)="en") }
 OPTIONAL { ?item rdfs:label ?german FILTER(LANG(?german)="de") }
 OPTIONAL { ?item wdt:P973 ?url }
 OPTIONAL { ?item wdt:P6002 ?wikiart }
} ORDER BY ?item ?inventory ?url LIMIT 261'''

def index():
 out=d.RUN/'wikidata-index-001.json.gz';assert not out.exists()
 url=requests.Request('GET','https://query.wikidata.org/sparql',params={'query':QUERY,'format':'json'}).prepare().url
 try:
  raw,cap=n.capture('hamburg-sparql',url);data=json.loads(raw)
  rows=[{k:v['value'] for k,v in row.items()} for row in data['results']['bindings']]
  assert len(rows)<=261
  m.save(out,dict(at=m.now(),query=QUERY,capture=cap,rows=rows,policy='Bounded secondary-source discovery only. Preferred/truthy claims do not validate qualifiers, ownership, versions or identities. No artwork additions or images.'))
  print(json.dumps(dict(rows=len(rows),distinct_objects=len({r['item'] for r in rows}))),flush=True)
 except Exception as ex:
  m.save(d.RUN/'wikidata-index-error-001.json',dict(at=m.now(),query=QUERY,url=url,error=type(ex).__name__+': '+str(ex)))
  raise

def entities():
 source=d.RUN/'wikidata-index-001.json.gz';rows=m.load(source)['rows']
 ids=sorted({r['item'].rsplit('/',1)[-1] for r in rows});assert len(ids)==140
 refs=[]
 for start in range(0,len(ids),20):
  selected=ids[start:start+20];dest=d.RUN/'wikidata-objects-001'/('%03d.json.gz'%(start//20+1))
  if not dest.exists():
   url=requests.Request('GET','https://www.wikidata.org/w/api.php',params={'action':'wbgetentities','ids':'|'.join(selected),'props':'labels|aliases|claims','format':'json'}).prepare().url
   raw,cap=n.capture('hamburg-wikidata',url);data=json.loads(raw)['entities'];assert set(data)==set(selected)
   m.save(dest,dict(ids=selected,entities=data,capture=cap,index_reference=dict(path=str(source.relative_to(m.ROOT)),sha256=hashlib.sha256(source.read_bytes()).hexdigest())))
  refs.append(dict(path=str(dest.relative_to(m.ROOT)),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()));print('objects',start+len(selected),'of',len(ids),flush=True)
 m.save(d.RUN/'wikidata-selected-capture-001.json.gz',dict(at=m.now(),objects=len(ids),batches=refs,policy='Selected140indexed painting objects only; raw claims, ranks, qualifiers and references preserved. No native catalogue bypass, images or DB writes.'))

def creators():
 capture=m.load(d.RUN/'wikidata-selected-capture-001.json.gz');ids=set()
 for ref in capture['batches']:
  v=m.load(m.ROOT/ref['path'])
  for entity in v['entities'].values():
   for claim in entity.get('claims',{}).get('P170',[]):
    value=claim.get('mainsnak',{}).get('datavalue',{}).get('value',{})
    if isinstance(value,dict) and value.get('id'):ids.add(value['id'])
 ids=sorted(ids);assert len(ids)<=160;refs=[]
 for start in range(0,len(ids),40):
  selected=ids[start:start+40];dest=d.RUN/'wikidata-creators-001'/('%03d.json.gz'%(start//40+1))
  if not dest.exists():
   url=requests.Request('GET','https://www.wikidata.org/w/api.php',params={'action':'wbgetentities','ids':'|'.join(selected),'props':'labels|aliases','format':'json'}).prepare().url
   raw,cap=n.capture('hamburg-wikidata',url);data=json.loads(raw)['entities'];assert set(data)==set(selected)
   m.save(dest,dict(ids=selected,entities=data,capture=cap))
  refs.append(dict(path=str(dest.relative_to(m.ROOT)),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()));print('creator labels',start+len(selected),'of',len(ids),flush=True)
 m.save(d.RUN/'wikidata-creator-capture-001.json.gz',dict(at=m.now(),creators=len(ids),batches=refs,policy='Object-creator label authorities only. No artist biographies, database artist additions or creator links.'))

def next_index():
 old=m.load(d.RUN/'wikidata-index-001.json.gz');cursor=max(r['item'] for r in old['rows'])
 query='''SELECT DISTINCT ?item WHERE {
 ?item wdt:P195 wd:Q169542; wdt:P31 wd:Q3305213; wdt:P571 ?date.
 FILTER(?date < "1971-01-01T00:00:00Z"^^xsd:dateTime)
 FILTER(STR(?item)>'''+json.dumps(cursor)+''')
 } ORDER BY ?item LIMIT 120'''
 url=requests.Request('GET','https://query.wikidata.org/sparql',params={'query':query,'format':'json'}).prepare().url
 raw,cap=n.capture('hamburg-sparql',url);rows=[{k:v['value'] for k,v in r.items()} for r in json.loads(raw)['results']['bindings']]
 assert len(rows)==len({r['item'] for r in rows})<=120 and not {r['item'] for r in rows}&{r['item'] for r in old['rows']}
 m.save(d.RUN/'wikidata-index-002.json.gz',dict(at=m.now(),query=query,cursor=cursor,capture=cap,rows=rows,policy='Next120distinctmuseum-linked pre1971painting leads; no creator requirement, images or DB writes. Qualifiers and actual holding identities remain unvalidated.'))
 print('Next index',len(rows),flush=True)

def next_entities():
 source=d.RUN/'wikidata-index-002.json.gz';ids=[r['item'].rsplit('/',1)[-1] for r in m.load(source)['rows']];assert len(ids)<=120;refs=[]
 for start in range(0,len(ids),20):
  selected=ids[start:start+20];dest=d.RUN/'wikidata-objects-002'/('%03d.json.gz'%(start//20+1))
  if not dest.exists():
   url=requests.Request('GET','https://www.wikidata.org/w/api.php',params={'action':'wbgetentities','ids':'|'.join(selected),'props':'labels|aliases|claims','format':'json'}).prepare().url
   raw,cap=n.capture('hamburg-wikidata',url);data=json.loads(raw)['entities'];assert set(data)==set(selected)
   m.save(dest,dict(ids=selected,entities=data,capture=cap,index_reference=dict(path=str(source.relative_to(m.ROOT)),sha256=hashlib.sha256(source.read_bytes()).hexdigest())))
  refs.append(dict(path=str(dest.relative_to(m.ROOT)),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()));print('next objects',start+len(selected),'of',len(ids),flush=True)
 m.save(d.RUN/'wikidata-selected-capture-002.json.gz',dict(at=m.now(),objects=len(ids),batches=refs,policy='Second bounded metadata selection only; no images or DB writes.'))

def extra_labels():
 old=set()
 for rr in m.load(d.RUN/'wikidata-creator-capture-001.json.gz')['batches']:old.update(m.load(m.ROOT/rr['path'])['ids'])
 ids=set()
 for suffix in ['001','002']:
  for rr in m.load(d.RUN/('wikidata-selected-capture-'+suffix+'.json.gz'))['batches']:
   for e in m.load(m.ROOT/rr['path'])['entities'].values():
    for prop in ['P170','P186','P2048','P2049','P2610']:
     for c in e.get('claims',{}).get(prop,[]):
      val=c.get('mainsnak',{}).get('datavalue',{}).get('value',{})
      if isinstance(val,dict):
       if val.get('id'):ids.add(val['id'])
       if '/entity/Q' in str(val.get('unit')):ids.add(val['unit'].rsplit('/',1)[-1])
      for qs in c.get('qualifiers',{}).values():
       for q in qs:
        v=q.get('datavalue',{}).get('value',{})
        if isinstance(v,dict) and v.get('id'):ids.add(v['id'])
 ids=sorted(ids-old);assert len(ids)<=250;refs=[]
 for start in range(0,len(ids),40):
  selected=ids[start:start+40];dest=d.RUN/'wikidata-labels-002'/('%03d.json.gz'%(start//40+1))
  if not dest.exists():
   url=requests.Request('GET','https://www.wikidata.org/w/api.php',params={'action':'wbgetentities','ids':'|'.join(selected),'props':'labels|aliases','format':'json'}).prepare().url
   raw,cap=n.capture('hamburg-wikidata',url);data=json.loads(raw)['entities'];assert set(data)==set(selected)
   m.save(dest,dict(ids=selected,entities=data,capture=cap))
  refs.append(dict(path=str(dest.relative_to(m.ROOT)),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()));print('additional labels',start+len(selected),'of',len(ids),flush=True)
 m.save(d.RUN/'wikidata-extra-label-capture-002.json.gz',dict(at=m.now(),labels=len(ids),batches=refs,policy='Labels for selected object creators, material roles and dimension units; no added authority records or biographies.'))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['index','entities','creators','next_index','next_entities','extra_labels']);globals()[p.parse_args().command]()
