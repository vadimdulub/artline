#!/usr/bin/env python3
"""Add ten individually corroborated cultural affiliations while preserving existing ones."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('apply-reviewed-primary-country-context.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
m=a.m;C=a.CORE;B=m.x.SESSION_BASE;RUN=B/'country-affiliation-second-pass/approved-additions';a.RUN=RUN;a.SOURCE=m.x.SESSION_NAME+'-corroborated-additional-affiliations';a.SOURCE_NAME='Getty and independently reviewed biographical cultural affiliations';a.SOURCE_ROOT='https://vocab.getty.edu/ulan/';m.BACKUPS=m.BACKUPS/'country-affiliation-second-pass'
APPROVED={'Q14540323':'CH','Q160448':'HU','Q2331466':'FR','Q19422204':'DE','Q1500210':'US','Q116240':'DE','Q320671':'DE','Q21168722':'AT','Q281812':'PL','Q122382':'GB'}
def prepare():
 dest=RUN/'reviewed-evidence.json'
 if dest.exists():return
 f=B/'country-affiliation-second-pass/biography-crosscheck.json';data=json.loads(f.read_text());by={r['artist']['qid']:r for r in data['candidates']};entries=[]
 for q,code in APPROVED.items():
  r=by[q];artist=r['artist'];assert code in r['additional_codes'];support=[]
  for src in r['sources']:
   if not any(data['mapping'].get(term)==code for term in src['terms']):continue
   p=Path(src['file']);d=json.loads(p.read_text());assert d['identity_reciprocal'] and d['qid']==q
   for key,field in [('birth','birth_year'),('death','death_year')]:
    span=d.get(key) or {};first=span.get('begin_of_the_begin');last=span.get('end_of_the_end');year=artist[field]
    if year is not None and first and last:assert int(first[:4])<=year<=int(last[:4]),(q,key)
   support.append(dict(kind='Getty ULAN explicit cultural/nationality class with reciprocal Wikidata identity',capture_path=str(p),capture_sha256=C.sha(p.read_bytes()),url=d['source']['url'],retrieved_at=d['source']['retrieved_at'],terms=d['nationalities']))
  assert support
  if q=='Q122382':
   p=B/'country-affiliation-second-pass/primary/Q122382.browser-review.json';d=json.loads(p.read_text());assert d['qid']==q and set(d['cultural_affiliations'])=={'British','Swiss'} and d['life']==[1741,1825];support.append(dict(kind='Actual official British Museum biography read through browser; directHTTP403retained',capture_path=str(p),capture_sha256=C.sha(p.read_bytes()),url=d['url'],retrieved_at=d['retrieved_at']))
  else:
   assert r['corroborated_additional_codes']==[code];p=RUN/'biography-evidence'/(q+'.json');C.save_new(p,dict(qid=q,approved_additional_code=code,biographies=r['wikipedia_biographies'],source_audit_path=str(f),source_audit_sha256=C.sha(f.read_bytes())));bio=r['wikipedia_biographies'][0];support.append(dict(kind='Explicit independent Wikipedia biographical-role affiliation, not birthplace',capture_path=str(p),capture_sha256=C.sha(p.read_bytes()),url=bio['url'],retrieved_at=bio['receipt']['retrieved_at']))
  conclusion='Additional '+code+' cultural affiliation explicitly supported by Getty ULAN and an independently reviewed biographical source. Retain all previous countries, primary-country flags and lifespan assertions. This is not an exclusive nationality, citizenship, birthplace or museum-location inference; editorial publication remains in review.'
  entries.append(dict(reviewed=True,slug=artist['slug'],qid=q,identity_lifespan=[artist['birth_year'],artist['death_year']],country_relationship='cultural_affiliation',add_code=code,conclusion=conclusion,evidence=support))
 C.save_new(dest,dict(at=C.now(),entries=entries,review='Nine explicit independent introductory affiliations plus officialBritishMuseumFuseli British/Swiss; exact reciprocalGettyidentity and compatibleknownlifedates. Other126candidatepainters retained for research rather than automatically classifying country from an isolated term.'))

def plan():prepare();a.plan()
def apply():a.apply()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','plan','apply']);x=p.parse_args();globals()[x.command]()
