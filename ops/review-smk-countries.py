#!/usr/bin/env python3
"""Country review using SMK SARA creator nationality and exact person IDs."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('review-painter-countries.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
RUN=c.BASE/'country-review-smk';FIELD='smk_country_review_20260913'
MAP={'Dansk':'DK','Danish':'DK','Hollandsk':'NL','Dutch':'NL','Italiensk':'IT','Italian':'IT','Fransk':'FR','French':'FR','Tysk':'DE','German':'DE','Svensk':'SE','Norsk':'NO','Norwegian':'NO','Spansk':'ES','Finsk':'FI','Engelsk':'GB','Østrigsk':'AT','Islandsk':'IS','Tjekkisk':'CZ','Belgisk':'BE','Polsk':'PL','Amerikansk':'US','Schweizisk':'CH','Græsk':'GR','Russisk':'RU','Mexicansk':'MX','Skotsk':'GB','Britisk':'GB'}
def save(path,value):c.m.r.core.save_new(path,value)
def year(value):
 match=re.match(r'^(\d{4})-',value or '');return int(match[1]) if match and int(match[1]) else None

def plan():
 if (RUN/'manifest.json').exists():return
 candidates=json.loads((c.BASE/'smk-country-candidates.json').read_text());facts=collections.defaultdict(list);receipts={};held=[]
 for e in candidates:
  p=e['creator'];pid=p['creator_lref']
  if not re.fullmatch(r'\d+_person',pid):continue
  path=c.ROOT/e['capture_path'];receipt_path=c.ROOT/e['receipt_path']
  if str(path) not in receipts:
   receipt=json.loads(receipt_path.read_text());assert c.m.r.core.sha(path.read_bytes())==receipt['sha256'];assert 'api.smk.dk/' in receipt['url'];receipts[str(path)]=receipt
  facts[pid].append({**e,'receipt':receipts[str(path)]})
 with c.m.r.base.connect(False) as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY')
  selected=db.execute("SELECT DISTINCT a.slug FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='smk-person' WHERE a.status='review' AND a.entity_type='person' AND EXISTS(SELECT 1 FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id WHERE aa.artist_id=a.id AND w.status<>'archived') AND NOT EXISTS(SELECT 1 FROM citations ct WHERE ct.entity_type='artist' AND ct.entity_id=a.id AND ct.field_name='museum_country_review_20260913')").fetchall()
  rows=c.selected(db,[{'artist':{'slug':a['slug']}} for a in selected]);configured={r['code'] for r in db.execute('SELECT code FROM countries').fetchall()}
 entries=[]
 for slug,row in rows.items():
  a=row['row']
  if slug=='alexis-gritchenko-research-83eca0e9af0b':
   held.append({'slug':slug,'reason':'historical_russian_label_conflicts_with_primary_ukrainian_affiliation','primary_source':'https://collection.barnesfoundation.org/objects/6864/Mistra/'});continue
  pids=[e['id'] for e in row['authorities'] if e['scheme']=='smk-person'];found=[e for pid in pids for e in facts[pid]]
  if not found:continue
  reason=None;codes=set()
  for e in found:
   p=e['creator'];country=MAP.get(p['creator_nationality'])
   if not country or country not in configured:reason='historical_multiple_or_unmapped_nationality_requires_context';break
   codes.add(country)
   for field,key in [('birth_year','creator_date_of_birth'),('death_year','creator_date_of_death')]:
    y=year(p.get(key))
    if y is not None and a[field] is not None and y!=a[field]:reason='source_person_biography_conflict'
   if reason:break
  if len(codes)>1:reason='source_country_disagreement'
  existing={r['country_code'] for r in row['countries'] if r['relationship_type']=='cultural_affiliation'}
  if not reason and existing and not codes<=existing:reason='existing_country_affiliation_requires_context'
  if reason:held.append({'slug':slug,'reason':reason,'literal_nationalities':[e['creator']['creator_nationality'] for e in found]});continue
  code=next(iter(codes));entries.append({'slug':slug,'artist_id':a['id'],'country_code':code,'add':code not in existing,'evidence':found})
 save(RUN/'plan.json',entries);save(RUN/'holds.json',held)
 manifest={'at':c.m.r.core.now(),'sha256':c.m.r.core.sha((RUN/'plan.json').read_bytes()),'painters':len(entries),'new_country_relationships':sum(e['add'] for e in entries),'countries':dict(collections.Counter(e['country_code'] for e in entries)),'held':dict(collections.Counter(e['reason'] for e in held)),'source_data_definition':'https://www.smk.dk/en/article/where-does-extra-data-on-smk-open-come-from/','translation_evidence':'https://ordnet.dk/ods/ordbog/hollandsk','policy':'Exact SMK person IDs, explicit SARA creator nationality, compatible source lifespan. Netherlandish/Flemish and multi-value labels held; no birthplace inference. Review retained.'}
 save(RUN/'manifest.json',manifest);print(json.dumps(manifest,indent=2),flush=True)

def preflight():
 entries=json.loads((RUN/'plan.json').read_text());manifest=json.loads((RUN/'manifest.json').read_text());assert c.m.r.core.sha((RUN/'plan.json').read_bytes())==manifest['sha256']
 allrows={}
 for target in ['local','production']:
  with c.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY');rows=c.selected(db,[{'artist':{'slug':e['slug']}} for e in entries])
   for e in entries:
    row=rows[e['slug']];assert row['row']['status']=='review'
    assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND field_name=%s",(row['row']['id'],FIELD)).fetchone()
  allrows[target]=rows;save(c.BACKUPS/('smk-country-'+target+'-preimages.json'),rows)
  save(RUN/(target+'-preflight.json'),{'at':c.m.r.core.now(),'plan_sha256':manifest['sha256'],'rows':len(rows)})
 for e in entries:
  left=allrows['local'][e['slug']];right=allrows['production'][e['slug']]
  assert [{k:v for k,v in r.items() if k!='artist_id'} for r in left['countries']]==[{k:v for k,v in r.items() if k!='artist_id'} for r in right['countries']] and left['authorities']==right['authorities']
  for k in ['display_name','birth_year','death_year','status','geography_review_state']:assert left['row'][k]==right['row'][k]
 print('SMK country both-target preflight passed',len(entries),flush=True)

def apply(target):
 entries=json.loads((RUN/'plan.json').read_text());manifest=json.loads((RUN/'manifest.json').read_text());assert c.m.r.core.sha((RUN/'plan.json').read_bytes())==manifest['sha256']
 for t in ['local','production']:assert json.loads((RUN/(t+'-preflight.json')).read_text())['plan_sha256']==manifest['sha256']
 before=json.loads((c.BACKUPS/('smk-country-'+target+'-preimages.json')).read_text())
 assert json.loads((c.BACKUPS/'production-managed-backup.json').read_text())['status']=='SUCCESSFUL' and (c.BACKUPS/'local-before.dump').stat().st_size>0
 with c.m.r.base.connect(target=='production') as db:
  for start in range(0,len(entries),75):
   path=RUN/'applied'/target/f'{start//75+1:03d}.json'
   if path.exists():continue
   batch=entries[start:start+75]
   with db.transaction():
    db.execute('SELECT pg_advisory_xact_lock(559220260914)');db.execute("SET LOCAL statement_timeout='90s'")
    rows=c.selected(db,[{'artist':{'slug':e['slug']}} for e in batch],True)
    db.execute("INSERT INTO sources(slug,name,source_type,base_url) VALUES('overnight-smk-country-20260913','SMK SARA creator nationality review','museum_api','https://api.smk.dk/') ON CONFLICT(slug) DO NOTHING")
    sid=db.execute("SELECT id FROM sources WHERE slug='overnight-smk-country-20260913'").fetchone()['id']
    with db.pipeline():
     for e in batch:
      assert rows[e['slug']]==before[e['slug']],('Artist changed after preflight',e['slug']);aid=rows[e['slug']]['row']['id'];first=e['evidence'][0];evidence={'plan_sha256':manifest['sha256'],'country_code':e['country_code'],'source_creator_records':e['evidence'],'policy':manifest['policy']}
      if e['add']:db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,%s,'cultural_affiliation',false,%s)",(aid,e['country_code'],"SMK creator nationality: "+first['creator']['creator_nationality']+'. Exact person ID '+first['creator']['creator_lref']+'. Country source citation retained.'))
      db.execute("UPDATE artists SET geography_review_state=CASE WHEN geography_review_state='not_reviewed' THEN 'classified' ELSE geography_review_state END,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(c.ACTOR,aid))
      for field in [FIELD,'geography']:c.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=aid,source_id=sid,field_name=field,source_record_id=first['creator']['creator_lref'],source_url=first['receipt']['url'],retrieved_at=first['receipt']['retrieved_at'],created_by=c.ACTOR,evidence_note=json.dumps(evidence,ensure_ascii=False)))
   save(path,{'at':c.m.r.core.now(),'plan_sha256':manifest['sha256'],'slugs':[e['slug'] for e in batch]});print(target,'SMK country batch',start//75+1,len(batch),flush=True)
 checked=[]
 with c.m.r.base.connect(target=='production') as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY')
  rows=c.selected(db,[{'artist':{'slug':e['slug']}} for e in entries])
  for e in entries:
   now=rows[e['slug']];old=before[e['slug']];ignored={'revision','updated_at','updated_by','geography_review_state'}
   assert {k:v for k,v in now['row'].items() if k not in ignored}=={k:v for k,v in old['row'].items() if k not in ignored}
   assert now['authorities']==old['authorities'] and now['row']['status']=='review'
   assert now['row']['geography_review_state']==('classified' if old['row']['geography_review_state']=='not_reviewed' else old['row']['geography_review_state'])
   assert now['row']['revision']==old['row']['revision']+1 and all(r in now['countries'] for r in old['countries'])
   assert any(r['country_code']==e['country_code'] and r['relationship_type']=='cultural_affiliation' for r in now['countries'])
   proof=db.execute('SELECT evidence_note FROM citations WHERE entity_type=\'artist\' AND entity_id=%s AND field_name=%s',(now['row']['id'],FIELD)).fetchall();assert len(proof)==1 and json.loads(proof[0]['evidence_note'])['plan_sha256']==manifest['sha256'];checked.append(e['slug'])
 save(RUN/(target+'-verification.json'),{'at':c.m.r.core.now(),'plan_sha256':manifest['sha256'],'verified':len(checked),'other_metadata_and_review_status_preserved':True,'slugs':checked});print(target,'SMK country verified',len(checked),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','preflight','apply']);p.add_argument('--target',choices=['local','production']);a=p.parse_args();{'plan':plan,'preflight':preflight,'apply':lambda:apply(a.target)}[a.command]()
