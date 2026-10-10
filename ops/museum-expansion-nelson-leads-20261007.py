#!/usr/bin/env python3
"""Bounded secondary index to selected official Nelson-Atkins object URLs."""
import argparse, importlib.util, json
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-nelson-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m;n=d.n;RUN=d.RUN
n.SITES['nelson-sparql']='https://query.wikidata.org';n.SITES['nelson-wikidata']='https://www.wikidata.org'
QUERY='''SELECT DISTINCT ?item ?date ?inventory ?label ?url WHERE {
 ?item wdt:P195 wd:Q1976985; wdt:P31 wd:Q3305213; wdt:P571 ?date; wdt:P973 ?url.
 FILTER(?date < "1971-01-01T00:00:00Z"^^xsd:dateTime)
 FILTER(STRSTARTS(STR(?url), "https://art.nelson-atkins.org/objects/"))
 OPTIONAL { ?item wdt:P217 ?inventory }
 OPTIONAL { ?item rdfs:label ?label FILTER(LANG(?label)="en") }
} ORDER BY ?item ?inventory ?url LIMIT 261'''
def index():
 url=requests.Request('GET','https://query.wikidata.org/sparql',params={'query':QUERY,'format':'json'}).prepare().url
 try:
  raw,cap=n.capture('nelson-sparql',url);data=json.loads(raw)['results']['bindings'];rows=[{k:v['value'] for k,v in row.items()} for row in data];assert len(rows)<=261
  m.save(RUN/'wikidata-index-001.json.gz',dict(at=m.now(),query=QUERY,capture=cap,rows=rows,policy='At most 261 secondary index rows for pre-1971 painting leads explicitly linked to Nelson-Atkins and an official object URL. No named-creator requirement. Truthy claims alone do not approve additions, dates, holdings or physical identities. No images or database writes.'))
  print(json.dumps(dict(rows=len(rows),objects=len({r['item'] for r in rows}))),flush=True)
 except Exception as ex:
  m.save(RUN/'wikidata-index-error-001.json',dict(at=m.now(),url=url,query=QUERY,error=type(ex).__name__+': '+str(ex)));raise
def expanded_index():
 query='''SELECT DISTINCT ?item WHERE {
 ?item wdt:P195 wd:Q1976985; wdt:P31 wd:Q3305213; wdt:P571 ?date.
 FILTER(?date < "1971-01-01T00:00:00Z"^^xsd:dateTime)
 } ORDER BY ?item LIMIT 261'''
 url=requests.Request('GET','https://query.wikidata.org/sparql',params={'query':query,'format':'json'}).prepare().url
 raw,cap=n.capture('nelson-sparql',url);data=json.loads(raw)['results']['bindings'];rows=[{k:v['value'] for k,v in row.items()} for row in data];assert len(rows)<=261
 m.save(RUN/'wikidata-index-002.json.gz',dict(at=m.now(),query=query,capture=cap,rows=rows,policy='At most 261 pre-1971 museum-linked painting identities. Native object URLs may occur in statement references instead of the described-at-URL property. No creator requirement, image or database write.'))
 print(json.dumps(dict(rows=len(rows),objects=len({r['item'] for r in rows}))),flush=True)
def entities():
 source=RUN/'wikidata-index-002.json.gz';ids=sorted({r['item'].rsplit('/',1)[-1] for r in m.load(source)['rows']});assert len(ids)<=261;refs=[]
 for start in range(0,len(ids),20):
  selected=ids[start:start+20];dest=RUN/'wikidata-objects-001'/('%03d.json.gz'%(start//20+1))
  if not dest.exists():
   url=requests.Request('GET','https://www.wikidata.org/w/api.php',params={'action':'wbgetentities','ids':'|'.join(selected),'props':'labels|aliases|claims','format':'json'}).prepare().url
   raw,cap=n.capture('nelson-wikidata',url);data=json.loads(raw)['entities'];assert set(data)==set(selected)
   m.save(dest,dict(ids=selected,entities=data,capture=cap,index_reference=d.ref(source)))
  refs.append(d.ref(dest));print('Selected entities',start+len(selected),'of',len(ids),flush=True)
 m.save(RUN/'wikidata-capture-001.json.gz',dict(at=m.now(),objects=len(ids),batches=refs,policy='Selected object identities and source-reference URLs only. Native object metadata and physical-version checks remain required. No catalogue write, painter authority or image fetch.'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['index','expanded_index','entities']);a=p.parse_args();globals()[a.command]()
