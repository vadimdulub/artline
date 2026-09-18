#!/usr/bin/env python3
"""Attach explicit Armenian/Georgian affiliations and women evidence by authority."""
import importlib.util,json,collections
from pathlib import Path
from psycopg.types.json import Jsonb
spec=importlib.util.spec_from_file_location('b',Path(__file__).with_name('research-armenian-georgian-artworks.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
s=b.s;r=b.r

def main():
 ids=set()
 for f in (s.RUN/'final-ready').glob('*.json'):ids.add(json.loads(f.read_bytes())['record']['creator_qid'])
 baseline=json.loads((s.RUN/'local-expanded-cohort-before.json').read_bytes());ids.update(e['id'] for a in baseline['artists'] for e in a['identifiers'] or [] if e['scheme']=='wikidata')
 entities,receipts=r.entities(sorted(ids));evidence=[]
 for q,e in entities.items():
  affiliations=[]
  for prop,rel,mapping in [('P172','cultural_affiliation',{'Q79797':'AM','Q48441':'GE'}),('P27','citizenship',{'Q399':'AM','Q230':'GE'})]:
   for claim in r.claims(e,prop):
    code=mapping.get(r.value(claim).get('id'))
    if code:affiliations.append({'country':code,'relationship':rel,'claim':claim,'property':prop})
  genders=r.claims(e,'P21');values={r.value(c).get('id') for c in genders};woman=bool(values and values<={'Q6581072','Q1052281'})
  evidence.append({'qid':q,'affiliations':affiliations,'is_woman':woman,'gender_claims':genders,'receipt':receipts[q]})
 path=s.RUN/'artist-affiliation-evidence.json'
 if path.exists():
  pinned=json.loads(path.read_bytes());assert {x['qid']:x for x in pinned}=={x['qid']:x for x in evidence},'Changed authority evidence requires review';evidence=pinned
 else:s.save(path,evidence)
 for target in ['local','production']:
  output=[]
  with s.connect(target) as db:
   db.execute("INSERT INTO countries(code,name,region_code,historical_note) VALUES('AM','Armenia','western-asia','Region follows UN M49, https://unstats.un.org/unsd/methodology/m49/overview ; country reference added for explicit Armenian cultural/citizenship evidence, not inferred birthplace.') ON CONFLICT DO NOTHING")
   db.execute("INSERT INTO sources(slug,name,source_type,base_url) VALUES('armenian-georgian-artist-evidence','Armenian and Georgian artist authority evidence','authority_data','https://www.wikidata.org/') ON CONFLICT DO NOTHING")
   sid=db.execute("SELECT id FROM sources WHERE slug='armenian-georgian-artist-evidence'").fetchone()['id'];db.commit()
   for e in evidence:
    q=e['qid'];artist=db.execute("SELECT a.id::text,a.slug,a.status FROM artists a JOIN external_identifiers e ON e.entity_id=a.id AND e.entity_type='artist' WHERE e.scheme='wikidata' AND e.external_id=%s AND a.status<>'archived'",(q,)).fetchone()
    if not artist:db.commit();continue
    for a in e['affiliations']:
     note='Explicit Wikidata '+a['property']+' statement, '+a['claim']['id']+'. Cultural affiliation and citizenship remain separate; no inference from birthplace. '+e['receipt']['sha256']
     db.execute('INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,%s,%s,false,%s) ON CONFLICT DO NOTHING',(artist['id'],a['country'],a['relationship'],note))
    if e['affiliations']:
     db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) SELECT 'artist',%s,'armenian_georgian_affiliation',%s,%s,%s,%s,%s,'local-european-research' WHERE NOT EXISTS(SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s AND field_name='armenian_georgian_affiliation')",(artist['id'],sid,q,'https://www.wikidata.org/wiki/'+q,json.dumps(e,ensure_ascii=False),e['receipt']['retrieved_at'],artist['id'],sid))
    if e['is_woman']:
     db.execute('INSERT INTO artist_gender_evidence(artist_id,is_woman,basis,source_url,source_record_id,source_checksum,evidence_json,checked_at) VALUES(%s,true,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',(artist['id'],'Explicit non-deprecated P21 statements; no inferred identity','https://www.wikidata.org/wiki/'+q,q,s.core.sha(s.core.encode(e)),Jsonb(e),e['receipt']['retrieved_at']))
    db.commit();output.append({'qid':q,**artist,'affiliations':e['affiliations'],'woman':e['is_woman']})
  s.save(s.RUN/('artist-evidence-'+target+'.json'),{'at':s.core.now(),'artists':output});print(target,'artist evidence',len(output),flush=True)
if __name__=='__main__':main()
