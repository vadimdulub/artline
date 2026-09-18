#!/usr/bin/env python3
"""Link exact source-supported artwork authorities; never merge physical works."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('discovery',Path(__file__).with_name('discover-overnight-popular-native-commons.py'));discovery=importlib.util.module_from_spec(s);s.loader.exec_module(discovery);common=discovery.common;core=common.core
SOURCE='overnight-popular-native-wikidata-20260915'
def verify_lead(c):
 e=c['artwork_entity'];common.entity_match(c,e)
 assert common.ids(e,'P195')=={c['institution_qid']} and common.ids(e,'P170')=={c['creators'][0]['qid']}
 assert common.norm(c['accession_number']) in {common.norm(v) for v in common.values(e,'P217') if isinstance(v,str)}
 years=[int(re.match(r'^\+(\d+)-',d['time'])[1]) for d in common.values(e,'P571') if isinstance(d,dict) and d.get('precision',0)>=9 and re.match(r'^\+(\d+)-',d.get('time',''))]
 assert years and all(c['creation_year_start']<=year<=c['creation_year_end'] for year in years),'Source year must agree exactly within the catalogue interval'
 i=c['institution_entity'];assert i['id']==c['institution_qid'] and discovery.host(c['website_url']) in {discovery.host(u) for u in common.values(i,'P856') if isinstance(u,str)}
def snapshot(db,records):
 native=[{'local_id':c['artwork_id'],'scheme':e['scheme'],'external_id':e['external_id']} for c in records for e in c['native_identifiers'] if discovery.host(e['url'])==discovery.host(c['website_url']) or discovery.host(e['url']).endswith('.'+discovery.host(c['website_url']))]
 rows=db.execute("""WITH requested AS (SELECT * FROM jsonb_to_recordset(%s) AS x(local_id text,scheme text,external_id text))
  SELECT DISTINCT r.local_id,a.id::text,a.slug,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,a.status,a.published_at,
   artline_has_selection_evidence(a.id) selected,i.slug institution_slug,i.website_url,
   ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.attribution_role) roles,
   ARRAY(SELECT e.external_id FROM artwork_artists aa JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=aa.artist_id AND e.scheme='wikidata' WHERE aa.artwork_id=a.id ORDER BY e.external_id) creator_qids
  FROM requested r JOIN external_identifiers e ON e.entity_type='artwork' AND e.scheme=r.scheme AND e.external_id=r.external_id
  JOIN artworks a ON a.id=e.entity_id JOIN institutions i ON i.id=a.current_institution_id""",(Jsonb(native),)).fetchall()
 ids=[x['id'] for x in rows];links=db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND (entity_id=ANY(%s::uuid[]) OR external_id=ANY(%s))",(ids,[c['qid'] for c in records])).fetchall()
 return {'rows':rows,'links':links}
def check(c,state):
 verify_lead(c);hits=[x for x in state['rows'] if x['local_id']==c['artwork_id']]
 if len(hits)!=1:raise ValueError('Native museum identifier absent or ambiguous in target')
 row=hits[0]
 for key in ('slug','title','accession_number','creation_year_start','creation_year_end','date_precision','date_display','work_type','institution_slug'):
  if row[key]!=c[key]:raise ValueError('Target '+key+' differs')
 if row['status']!='review' or row['published_at'] is not None or not row['selected'] or row['roles']!=['primary']:raise ValueError('Target editorial, selection or attribution state differs')
 if row['creator_qids']!=sorted(x['qid'] for x in c['creators']) or discovery.host(row['website_url'])!=discovery.host(c['website_url']):raise ValueError('Target creator or institution identity differs')
 for link in state['links']:
  if (link['external_id']==c['qid'] and link['entity_id']!=row['id']) or (link['entity_id']==row['id'] and link['external_id']!=c['qid']):raise ValueError('Existing artwork authority requires duplicate reconciliation')
 return row['id']
def plan(run):
 if (run/'plan.json').exists():return
 records=json.loads((run/'native-match-leads.json').read_text());counts=collections.Counter(c['qid'] for c in records);held=[{'artwork_id':c['artwork_id'],'qid':c['qid'],'reason':'Multiple catalogue works match one authoritative physical object'} for c in records if counts[c['qid']]!=1];records=[c for c in records if counts[c['qid']]==1];states={};backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915'/run.name
 for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
  with psycopg.connect(dsn,autocommit=True,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:states[target]=snapshot(db,records)
  core.save_new(backup/(target+'-authority-preflight.json'),states[target])
 selected=[]
 for c in records:
  try:
   c['target_ids']={target:check(c,state) for target,state in states.items()};selected.append(c)
  except ValueError as exc:held.append({'artwork_id':c['artwork_id'],'qid':c['qid'],'reason':str(exc)})
 core.save_new(run/'plan.json',{'at':core.now(),'records':selected,'held':held,'policy':'Exact independent museum inventory, creator, holding and source date agreement; both targets preflighted. No artwork merged, artist changed or institution authority guessed. Image rights remain a separate mandatory stage.'});core.save_new(run/'plan-manifest.json',{'sha256':core.sha((run/'plan.json').read_bytes()),'count':len(selected)});print('Exact popular artwork authority links',len(selected),'held',len(held),flush=True)
def apply(run,target):
 data=json.loads((run/'plan.json').read_text());manifest=json.loads((run/'plan-manifest.json').read_text());assert core.sha((run/'plan.json').read_bytes())==manifest['sha256'];records=data['records'];dsn='postgres://localhost/artline' if target=='local' else core.cloud_dsn();out=[]
 with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
  state=snapshot(db,records)
  for c in records:assert check(c,state)==c['target_ids'][target]
  with db.transaction():
   db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES(%s,'Wikidata: museum-inventory corroborated artwork authorities','authority_data','https://www.wikidata.org/',%s) ON CONFLICT(slug) DO NOTHING",(SOURCE,common.CC0));sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
  for start in range(0,len(records),25):
   with db.transaction():
    db.execute('SELECT pg_advisory_xact_lock(559220260915)');group=records[start:start+25]
    db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) FOR UPDATE',([c['target_ids'][target] for c in group],)).fetchall();fresh=snapshot(db,group)
    for c in group:
     aid=check(c,fresh);prior=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=%s",(c['qid'],)).fetchall()
     if prior:assert prior==[{'entity_id':aid}];out.append({'artwork_id':aid,'qid':c['qid'],'outcome':'already_present'});continue
     page='https://www.wikidata.org/wiki/'+c['qid'];db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,'wikidata',%s,%s,%s,%s)",(aid,c['qid'],page,sid,c['checked_at']))
     evidence={'museum_inventory':c['accession_number'],'native_museum_identifiers':c['native_identifiers'],'museum_website':c['website_url'],'institution_qid':c['institution_qid'],'artist_qids':[x['qid'] for x in c['creators']],'source_artwork_entity':c['artwork_entity'],'source_institution_entity':c['institution_entity'],'review':'Exact inventory and single current holding/primary creator; source year agrees within the catalogue interval. Both databases checked for existing or conflicting physical-object identifiers. No institution, artist, date, publication state or artwork row changed.'}
     db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'corroborated_museum_inventory_authority',%s,%s,%s,%s,%s)",(aid,sid,c['qid'],page,json.dumps(evidence,ensure_ascii=False),c['checked_at'],core.ACTOR));out.append({'artwork_id':aid,'qid':c['qid'],'outcome':'inserted'})
   print(core.now(),target,'Popular artwork authority links',len(out),'of',len(records),flush=True)
  verified=snapshot(db,records)
  for c in records:assert check(c,verified)==c['target_ids'][target] and {'entity_id':c['target_ids'][target],'external_id':c['qid']} in verified['links']
 core.save_new(run/(target+'-links-verified.json'),{'at':core.now(),'count':len(out),'records':out})
 if target=='local':
  candidates=[]
  for c in records:
   im={k:v for k,v in c.items() if k not in ('artwork_entity','institution_entity','native_identifiers','checked_at')};im.update(external_id=c['qid'],scheme='wikidata',provider='night-commons',artist='; '.join(x['name'] for x in c['creators']));candidates.append(im)
  core.save_new(run/'candidates.json',{'selected_at':data['at'],'candidates':candidates})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','apply']);p.add_argument('--run',type=Path,required=True);p.add_argument('--target',choices=['local','cloud'],default='local');a=p.parse_args();plan(a.run) if a.phase=='plan' else apply(a.run,a.target)
