#!/usr/bin/env python3
"""Seven exact Tate authority crosswalks, preserving approximate life dates."""
import argparse,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('apply-closed-identity-countries.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
ORIGINAL=c.RUN;ROOT=c.m.x.BASE/'country-gap-followup/tate-qualified-life-primary';CORE=c.CORE
c.RUN=ROOT/'review';c.SOURCE='overnight-tate-qualified-life-countries-20260913';c.m.BACKUPS=c.m.BACKUPS/'tate-qualified-country'
QIDS={'Q6076334','Q4302276','Q21461028','Q5081991','Q2543048','Q4755278','Q5075815'}
PROPOSALS=[p for p in json.loads((ORIGINAL/'primary-citation-followup-candidates.json').read_text()) if p['candidate']['qid'] in QIDS]
PRIMARY={r['id']:r for r in json.loads((ROOT/'selected-primary-creators.json').read_text())};RECEIPT=json.loads((ROOT/'artist_data.receipt.json').read_text());assert CORE.sha((ROOT/'artist_data.csv').read_bytes())==RECEIPT['sha256']
def proof(a,citations):
 p=next(p for p in PROPOSALS if p['artist']['slug']==a['slug']);q=p['candidate']['qid'];capture=json.loads((c.m.x.r.RUN/'entities'/(q+'.json')).read_text());entity=capture['entity'];tate=c.m.m.r.values(entity,'P2741');out=[]
 for identity in tate:
  pid=identity.rsplit('-',1)[-1];person=PRIMARY.get(pid)
  if not person:continue
  assert person['url'].endswith('/'+identity);assert (int(person['yearOfBirth']),int(person['yearOfDeath']))==(a['birth_year'],a['death_year'])
  surname,forename=person['name'].split(', ',1);assert c.m.f.names.namekey(forename+' '+surname)==c.m.f.names.namekey(a['display_name'])
  matches=[ct for ct in citations if (ct['source_url'] or '').rstrip('/').endswith('/'+identity)]
  if matches:out.append(dict(source_url=person['url'].replace('http:','https:'),field_name='museum_creator_record',source_record_id=pid,primary_creator_record=person,primary_receipt=RECEIPT,original_citations=matches,wikidata_crosswalk=dict(qid=q,property='P2741',value=identity,receipt=p['candidate']['entity_receipt']),identity_policy='Exact Tate person identifier crosswalk plus primary full name and compatible qualified life years. Approximate or alternative biography dates remain qualified in evidence and existing DB dates unchanged. Place fields are not used as affiliation evidence.',source_warning='Tate historicalCSV Fuller row has apparent incorrect German place fields; those fields are not imported or used. Country is separately corroborated English role wording in the identified Wikipedia biography.' if q=='Q6076334' else None))
 return out
c.primary_proof=proof

def plan():
 for target in ('local','production'):
  with c.m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY')
   for p in PROPOSALS:
    entity=json.loads((c.m.x.r.RUN/'entities'/(p['candidate']['qid']+'.json')).read_text())['entity'];ids=[v.rsplit('-',1)[-1] for v in c.m.m.r.values(entity,'P2741')]
    assert db.execute("SELECT 1 FROM external_identifiers e JOIN artists a ON a.id=e.entity_id WHERE e.entity_type='artist' AND a.slug=%s AND e.scheme='tate-person' AND e.external_id=ANY(%s)",(p['artist']['slug'],ids)).fetchone()
 path=c.RUN/'round-01/research.json'
 if not path.exists():CORE.save_new(path,dict(at=CORE.now(),country_proposals=PROPOSALS,policy='Exact primary Tate identifier crosswalk, not a closed-exact-lifespan assumption.'))
 c.plan(1)
def apply():c.apply(1)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);a=p.parse_args();globals()[a.command]()
