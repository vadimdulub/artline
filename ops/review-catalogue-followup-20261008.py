#!/usr/bin/env python3
"""Repeat one-way catalogue reconciliation with immutable evidence and preflight."""
import importlib.util,json,uuid,sys
from pathlib import Path
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('alignment',Path(__file__).with_name('align-catalogues-20261008.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
RUN=m.ROOT/'docs/research/catalogue-review-expansion-20261008'
BACKUP=Path.home()/'Library/Application Support/Artline/backups/catalogue-review-expansion-20261008'
def uid(key): return str(uuid.uuid5(uuid.NAMESPACE_URL,'artline:catalogue-review-20261008:'+key))
def prepare():
 local=m.load(BACKUP/'local-relations-v3.json.gz');prod=m.load(BACKUP/'production-relations-v3.json.gz')
 slugs={r['slug'] for r in prod['artworks']};aliases={x['local_id'] for x in m.load(m.BACKUP/'delivery-plan.json.gz')['existing']}|set(m.load(m.BACKUP/'supplemental/delivery-plan.json.gz')['reused_artworks'])
 ids=[r['id'] for r in local['artworks'] if r['slug'] not in slugs and r['id'] not in aliases]
 with m.connect('local') as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  rows={'artworks':m.select_rows(db,'artworks','id',ids)}
  for t,col,extra in [('artwork_artists','artwork_id',''),('artwork_location_assertions','artwork_id',''),('artwork_media','artwork_id',''),('artwork_places','artwork_id',''),('citations','entity_id',"AND entity_type='artwork'"),('external_identifiers','entity_id',"AND entity_type='artwork'")]:rows[t]=m.select_rows(db,t,col,ids,extra)
  sources=m.select_rows(db,'sources','id',sorted({r['source_id'] for v in rows.values() for r in v if r.get('source_id')}))
  museums=m.select_rows(db,'institutions','id',sorted({r['current_institution_id'] for r in rows['artworks'] if r['current_institution_id']}))
 assert len(ids)==121
 assert all(r['status']=='review' and r['primary_media_id'] is None and r['creation_year_end'] is not None and r['creation_year_end']<=1970 for r in rows['artworks'])
 assert not rows['artwork_media'] and not rows['artwork_places']
 source_rows=json.loads(json.dumps(rows));maps={};new_sources=[]
 with m.connect('production') as db:
  assert not m.select_rows(db,'artworks','id',ids)
  for r in sources:
   old=db.execute('SELECT id FROM sources WHERE slug=%s',(r['slug'],)).fetchone()
   if old:maps[r['id']]=str(old['id'])
   else:maps[r['id']]=r['id'];new_sources.append(r)
  instmap={}
  for r in museums:
   old=db.execute('SELECT id FROM institutions WHERE slug=%s',(r['slug'],)).fetchone();assert old,r['slug'];instmap[r['id']]=str(old['id'])
  for r in rows['external_identifiers']:
   assert not db.execute("SELECT 1 FROM external_identifiers WHERE scheme=%s AND external_id=%s",(r['scheme'],r['external_id'])).fetchone(),('existing native identity',r)
  scope=m.select_rows(db,'artworks','current_institution_id',list(instmap.values()));suspects=[]
  for r in rows['artworks']:
   conflicts=[p for p in scope if p['current_institution_id']==instmap[r['current_institution_id']] and ((r['accession_number'] and m.normal(r['accession_number'])!='sn' and m.normal(r['accession_number'])==m.normal(p['accession_number'])) or (m.normal(r['title'])==m.normal(p['title']) and not(r['accession_number'] and p['accession_number'])))]
   if conflicts:suspects.append(dict(local=r,candidates=conflicts,citations=m.select_rows(db,'citations','entity_id',[p['id'] for p in conflicts],"AND entity_type='artwork'")))
 aliases={}
 facts={r['Reference']:r for r in m.load(RUN/'sources/joconde-version-check.json')['data']}
 decisions=[]
 for x in suspects:
  assert len(x['candidates'])==1
  identifier=next(r['external_id'] for r in rows['external_identifiers'] if r['entity_id']==x['local']['id'])
  prior=next(r['source_record_id'] for r in x['citations'] if '/notice/joconde/' in r['source_url'])
  assert identifier!=prior and facts[identifier]['Numero_inventaire']!=facts[prior]['Numero_inventaire']
  assert m.normal(facts[identifier]['Numero_inventaire'])==m.normal(x['local']['accession_number'])
  assert facts[identifier]['Mesures']!=facts[prior]['Mesures']
  decisions.append(dict(local_id=x['local']['id'],action='add_distinct_object',local_reference=identifier,prior_reference=prior,basis='Distinct primary catalogue reference, inventory and dimensions; Carriere lithograph versus oil painting; Wyld workshop gouache versus Bouchon painting. Same titles do not establish identity.'))
 m.save(RUN/'late-local-next-identity-decisions.json',dict(aliases=aliases,decisions=decisions))
 rows['artworks']=[r for r in rows['artworks'] if r['id'] not in aliases]
 rows['artwork_location_assertions']=[r for r in rows['artwork_location_assertions'] if r['artwork_id'] not in aliases]
 for values in rows.values():
  for r in values:
   for col in ['artwork_id','entity_id']:
    if r.get(col) in aliases:r[col]=aliases[r[col]]
 for values in rows.values():
  for r in values:
   if r.get('source_id'):r['source_id']=maps[r['source_id']]
   for col in ['institution_id','current_institution_id']:
    if r.get(col):r[col]=instmap[r[col]]
 rows={'sources':new_sources,**rows}
 plan=dict(at=m.now(),source_rows=source_rows,inserts=rows,direction='local_to_production_only',duplicate_check='Database IDs, native identifiers, museum inventories and unresolved same-title candidates checked',publication_changes=0,existing_record_updates=0)
 m.save(BACKUP/'late-local-next-plan.json.gz',plan);m.save(RUN/'late-local-next-plan-pin.json',dict(sha256=m.digest(BACKUP/'late-local-next-plan.json.gz'),counts={t:len(v) for t,v in rows.items()}));print({t:len(v) for t,v in rows.items()})
def apply():
 path=BACKUP/'late-local-next-plan.json.gz';plan=m.load(path);assert m.digest(path)==m.load(RUN/'late-local-next-plan-pin.json')['sha256'];assert m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL';assert not (RUN/'late-local-next-applied.json').exists()
 with m.connect('local') as db:
  for t,rs in plan['source_rows'].items():
   if not rs:continue
   key='id' if 'id' in rs[0] else 'artwork_id';actual=m.select_rows(db,t,key,[r[key] for r in rs]);assert {json.dumps(r,sort_keys=True) for r in actual}=={json.dumps(r,sort_keys=True) for r in rs},(t,'local source changed')
 with m.connect('production',False) as db:
  db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  assert not m.select_rows(db,'artworks','id',[r['id'] for r in plan['inserts']['artworks']])
  for r in plan['inserts']['external_identifiers']:assert not db.execute('SELECT 1 FROM external_identifiers WHERE scheme=%s AND external_id=%s',(r['scheme'],r['external_id'])).fetchone()
  meta=m.load(RUN/'inventory/production-schema.json')['tables']
  for t in ['sources','artworks','artwork_artists','artwork_media','artwork_places','citations','external_identifiers','artwork_location_assertions']:m.insert(db,t,plan['inserts'][t],meta[t])
  db.execute("INSERT INTO audit_log(actor_user_id,action,entity_type,entity_id,request_id,after_json) SELECT %s,'catalogue_alignment_added','artwork',(r->>'id')::uuid,%s,r FROM jsonb_array_elements(%s) r",(m.ACTOR,'catalogue-review-next-20261008',Jsonb(plan['inserts']['artworks'])))
  for t,rs in plan['inserts'].items():
   if not rs or 'id' not in rs[0]:continue
   assert {r['id']:r for r in m.select_rows(db,t,'id',[r['id'] for r in rs])}=={r['id']:r for r in rs},t
 m.save(RUN/'late-local-next-applied.json',dict(at=m.now(),counts={t:len(v) for t,v in plan['inserts'].items()},backup_id='1791461266671',publication_changes=0,local_writes=0));print('Committed',len(plan['inserts']['artworks']),'artworks and preserved source evidence')
if __name__=='__main__': {'prepare':prepare,'apply':apply}[sys.argv[1]]()
