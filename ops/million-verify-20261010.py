#!/usr/bin/env python3
"""Read-only scoped verification of completed production expansion phases."""
import argparse,collections,importlib.util,json,time
from psycopg import OperationalError
from pathlib import Path
s=importlib.util.spec_from_file_location('bulk',Path(__file__).with_name('million-bulk-import-20261010.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);m=b.m
def verify(provider,phase):
 for attempt in range(20):
  try:return verify_once(provider,phase)
  except OperationalError as error:
   state=getattr(error,'sqlstate',None)
   if state and not (state.startswith('08') or state in ('57P01','57P02','57P03')):raise
   if attempt==19:raise
   print('Read-only verification connection interrupted; restarting the consistent snapshot.',flush=True);time.sleep(5)
def verify_once(provider,phase):
 if provider=='nga':
  folder=m.RUN/provider;p=m.load(folder/b.n.PLAN);scheme=b.n.SCHEME;mid=b.n.MID
  canonical=m.load(folder/'duplicate-reconciliation.json')['canonical_map'];excluded=set()
  followup=folder/'identity-followup-002/applied.json'
  if followup.exists():canonical.update(m.load(followup)['canonical_map'])
 else:
  cfg=b.setup(provider,phase);folder=cfg['run'];p=m.load(folder/'plan.json.gz');scheme=cfg['schemes'][0];mid=cfg['mid'];canonical={}
  ex=b.execution_exclusions(folder);excluded={r['artwork_id'] for r in m.load(ex)['rows']} if ex.exists() else set()
 rows=[r for r in p['new_artworks'] if r['artwork_id'] not in excluded];counts=collections.Counter();fail=[];chronology=[]
 with m.m.connect() as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  for group in m.chunks(rows,1500):
   ids=[r['artwork_id'] for r in group]
   actual={r['id']:r for r in db.execute('SELECT id::text,title,creation_year_start,creation_year_end,date_precision,status,current_institution_id::text,published_at,primary_media_id FROM artworks WHERE id=ANY(%s::uuid[])',(ids,))}
   for r in group:
    a=actual.get(r['artwork_id']);expected='archived' if r['artwork_id'] in canonical else 'review'
    if not a or (a['title'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['status'],a['current_institution_id'],a['published_at'])!=(r['title'],r['first'],r['last'],r['precision'],expected,mid,None):fail.append(dict(id=r['artwork_id'],reason='metadata_or_state_mismatch'))
   counts['artworks']+=len(actual);counts['illustrated']+=sum(a['primary_media_id'] is not None for a in actual.values())
   for table,column,condition in [('citations','entity_id',' AND field_name=\'million_catalogue_'+provider+'\''),('artwork_location_assertions','artwork_id'," AND claim_type='holding'"),('artwork_artists','artwork_id','')]:
    counts[table]+=db.execute('SELECT count(*) n FROM '+table+' WHERE '+column+'=ANY(%s::uuid[])'+condition,(ids,)).fetchone()['n']
   counts['matching_search_documents']+=db.execute('SELECT count(*) n FROM artworks a JOIN artwork_search_documents s ON s.id=a.id WHERE a.id=ANY(%s::uuid[]) AND s.title=a.title AND s.status=a.status AND s.primary_media_id IS NOT DISTINCT FROM a.primary_media_id',(ids,)).fetchone()['n']
   ex={r['external_id']:r['entity_id'] for r in db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=ANY(%s)",(scheme,[r['native_id'] for r in group]))}
   for r in group:
    if ex.get(r['native_id'])!=canonical.get(r['artwork_id'],r['artwork_id']):fail.append(dict(id=r['artwork_id'],reason='native_identity_mismatch'))
   counts['native_identity_checks']+=len(group)
   chronology+=db.execute("SELECT a.id::text,a.title,a.work_type,a.date_display,a.creation_year_start,a.creation_year_end,ar.id::text artist_id,ar.display_name,ar.birth_year,ar.death_year,aa.attribution_role FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id JOIN artists ar ON ar.id=aa.artist_id WHERE a.id=ANY(%s::uuid[]) AND a.status<>'archived' AND (a.creation_year_end<ar.birth_year OR a.creation_year_start>ar.death_year)",(ids,)).fetchall()
  artistids=[a['id'] for a in p['new_artists']]
  counts['artist_citations']=db.execute("SELECT count(*) n FROM citations WHERE entity_id=ANY(%s::uuid[]) AND field_name=%s",(artistids,'million_catalogue_'+provider+'_artist')).fetchone()['n']
  globalcounts={table:db.execute("SELECT count(*) total,count(*) FILTER(WHERE status<>'archived') active FROM "+table).fetchone() for table in ['artworks','artists']}
 with m.m.connect(local=True) as db:
  db.execute('SET TRANSACTION READ ONLY');local={t:db.execute('SELECT count(*) n FROM '+t).fetchone()['n'] for t in ['artists','artworks','artwork_artists','media_assets']}
 out=dict(at=m.now(),checks=dict(counts),expected_artworks=len(rows),failures=fail,chronology_review_cases=len(chronology),production_snapshot=globalcounts,local_readonly_counts=local,local_baseline_equal=local==m.load(m.RUN/'baseline.json.gz')['local_readonly_counts'])
 m.save(folder/'full-verification.json',out);m.save(folder/'chronology-review.json.gz',dict(at=m.now(),rows=chronology,note='Source-backed out-of-life dates require version, impression, attribution and biography review; posthumous prints/casts must not be rewritten as lifetime works. No automatic date correction.'))
 print(json.dumps(out,default=str),flush=True)
 assert not fail
 assert all(counts[k]==len(rows) for k in ['citations','artwork_location_assertions','matching_search_documents','native_identity_checks','artworks'])
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('provider',choices=['nga','met','rijks','moma','aic']);ap.add_argument('--phase',default='002');a=ap.parse_args();verify(a.provider,a.phase)
 if a.provider=='rijks' and (m.RUN/'rijks/checkpoint-before-next-window.json').exists():
  print('Verification passed. Requested controller restart checkpoint reached; no next window started.',flush=True)
  raise SystemExit(75)
