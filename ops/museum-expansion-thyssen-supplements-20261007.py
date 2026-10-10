#!/usr/bin/env python3
"""Bounded primary version evidence and historical-attribution identity leads."""
import argparse,collections,gzip,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-thyssen-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);m=i.m;f=i.f;RUN=i.RUN;n=f.d.n
PAGES=[('met','https://www.metmuseum.org/art/collection/search/334344'),('toledo','https://emuseum.toledomuseum.org/objects/54772/houses-at-auvers'),('moma','https://www.moma.org/collection/works/79463'),('met','https://www.metmuseum.org/art/collection/search/437990'),('met','https://www.metmuseum.org/art/collection/search/436126'),('artic','https://archive.artic.edu/homer/artwork/16785')]
def pages():
 refs=[]
 for number,(name,url) in enumerate(PAGES,1):
  key='thyssen-comparison-'+name;n.SITES[key]='/'.join(url.split('/')[:3]);path=RUN/'version-public-pages-001'/('%03d.json.gz'%number)
  if not path.exists():
   try:
    raw,cap=n.capture(key,url);m.save(path,dict(source_url=url,capture=cap,text=f.d.d.BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)))
   except Exception as ex:m.save(path,dict(source_url=url,error=type(ex).__name__+': '+str(ex)))
  refs.append(f.ref(path));print('Version page',number,flush=True)
 m.save(RUN/'version-public-capture-001.json.gz',dict(at=m.now(),pages=refs,reviewer_reference=f.ref(Path(__file__).resolve()),policy='Selected existing-object comparison pages; no images or catalogue metadata changes.'))
def old_bodies():
 snapshot=RUN/'version-scope-001.json.gz';v=m.load(snapshot);out=[]
 for aid in ['6ede5cac-415f-4cd2-b980-076af58282ec','eeccc421-8840-4bc2-87d7-199e7aa94e50','bb2781a9-92e8-580b-a5de-afc2bb4cf011']:
  for c in v['citations']:
   if c['entity_id']!=aid:continue
   try:j=json.loads(c['evidence_note'])
   except ValueError:continue
   receipt=j.get('source_receipt',{});path=j.get('evidence_path') or receipt.get('body_path');sha=j.get('source_response_sha256') or receipt.get('sha256')
   if not path or not sha:continue
   p=m.ROOT/path;raw=gzip.decompress(p.read_bytes());assert hashlib.sha256(raw).hexdigest()==sha
   out.append(dict(artwork_id=aid,citation=c,body_reference=f.ref(p),raw_sha256=sha))
 assert len(out)==3
 m.save(RUN/'version-prior-bodies-001.json.gz',dict(at=m.now(),records=out,scope_reference=f.ref(snapshot),policy='Prior captured primary V&A/Whitney and secondary WikiArt evidence rechecked against saved receipt hashes. Their old catalogue fields are not rewritten.'))
def aliases():
 terms=['vigoroso','santa chiara','master wb','meister wb','maestro allegro','foschi'];p={k:[] for k in ['patterns','raw_patterns','title_keys','inventories','source_urls','qids','native_object_ids','native_identifiers']};p['patterns']=p['raw_patterns']=['%'+x+'%' for x in terms]
 with m.connect() as db:state=i.queries(db,p)
 m.save(RUN/'historical-creator-identity-001.json.gz',dict(at=m.now(),params=p,state=state,reviewer_reference=f.ref(Path(__file__).resolve()),candidate_reference=f.ref(RUN/'native-candidates-002.json.gz'),mapping={'1934.30.1-3':['vigoroso','santa chiara'],'1934.15.a':['master wb','meister wb'],'1933.5':['maestro allegro','foschi']},policy='Literal historical attributions explicitly discussed by the selected official object essays. Discovery only; preserve current anonymous/qualified creator labels.'))
 print('Alias counts',{k:len(v) for k,v in state.items()},flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['pages','old_bodies','aliases']);a=p.parse_args();globals()[a.command]()
