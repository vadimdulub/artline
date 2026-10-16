#!/usr/bin/env python3
"""Independent read-only final count, phase receipts and artist timeline audit."""
import argparse,collections,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('controller',Path(__file__).with_name('million-rijks-continue-20261010.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c);m=c.m
ARTIST_FIELDS=['display_name','entity_type','birth_year','death_year','birth_display','death_display','birth_precision','death_precision','active_start_year','active_end_year','activity_display','timeline_start_year','timeline_end_year','timeline_display','timeline_basis']
ANTONIAZZO=('d9960c05-d85c-51c9-abe3-9b802cea2d4f','4c060840-f8ec-538b-ad36-11e056630016')
def main(label,require_target):
 dest=m.RUN/('goal-audit-'+label+'.json');assert not dest.exists(),'Choose a new immutable audit label'
 paths=[m.RUN/'nga/plan-v2.json.gz',m.RUN/'met/002/plan.json.gz',*sorted((m.RUN/'rijks').glob('*/plan.json.gz')),m.RUN/'moma/002/plan.json.gz',m.RUN/'aic/002/plan.json.gz']
 phases=[];pending=[];expected={};source_ids=[]
 for path in paths:
  if not path.exists():continue
  folder=path.parent;provider=folder.name if folder.name=='nga' else folder.parent.name
  if not (folder/'full-verification.json').exists():
   if list((folder/'batches').glob('*.json')):pending.append(str(folder.relative_to(m.RUN)))
   continue
  assert c.complete(folder);v=m.load(folder/'full-verification.json');p=m.load(path)
  phases.append(dict(provider=provider,phase=folder.name,artworks=v['expected_artworks'],verification=str((folder/'full-verification.json').relative_to(m.RUN)),verification_sha256=m.sha((folder/'full-verification.json').read_bytes()),checks=v['checks']))
  expected.update({a['id']:a for a in p['new_artists']});source_ids.append(m.uid('source/'+provider))
 overrides=m.RUN/'lifetime-followup-20261011/activity-review/verification.json'
 if overrides.exists():
  for row in m.load(overrides.parent/'plan.json')['rows']:
   if row['artist_id'] in expected:expected[row['artist_id']].update(row['update'])
 sharpe=m.RUN/'lifetime-followup-20261011/sharpe-review/verification.json'
 if sharpe.exists():
  artist=m.load(sharpe.parent/'plan.json')['artist'];expected[artist['id']]=artist
 with m.m.connect() as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  raw=db.execute("""SELECT count(*) FILTER(WHERE status<>'archived') active,
   count(*) FILTER(WHERE status<>'archived' AND primary_media_id IS NOT NULL) illustrated,
   count(*) FILTER(WHERE status<>'archived' AND creation_year_end<=1970) known_through_1970,
   count(*) FILTER(WHERE status<>'archived' AND (creation_year_start IS NULL OR creation_year_end IS NULL)) date_incomplete,
   count(*) FILTER(WHERE status<>'archived' AND (creation_year_end>1970 OR creation_year_start>1970)) date_outside_or_crossing_cutoff
   FROM artworks""").fetchone()
  excluded=db.execute("""SELECT id::text,title,current_institution_id::text,accession_number,creation_year_start,creation_year_end,
   (creation_year_end>1970 OR creation_year_start>1970) date_exclusion,
   (current_institution_id=%s AND accession_number ~* '\\((V|VERSO)\\)[[:space:]]*$') physical_view
   FROM artworks WHERE status<>'archived' AND ((creation_year_end>1970 OR creation_year_start>1970) OR (current_institution_id=%s AND accession_number ~* '\\((V|VERSO)\\)[[:space:]]*$'))""",(c.r.MID,c.r.MID)).fetchall()
  pairs=[(r['new_id'],r['existing_id']) for r in m.load(m.RUN/'nga/duplicate-followup-visual-review.json')['decisions'] if r['decision']=='same_painting']+[ANTONIAZZO]
  duplicates=db.execute("SELECT a.id::text,a.title,p.existing_id::text FROM unnest(%s::uuid[],%s::uuid[]) p(new_id,existing_id) JOIN artworks a ON a.id=p.new_id JOIN artworks old ON old.id=p.existing_id WHERE a.status<>'archived' AND old.status<>'archived'",([p[0] for p in pairs],[p[1] for p in pairs])).fetchall()
  excluded_ids={r['id'] for r in excluded}|{r['id'] for r in duplicates};qualifying=raw['active']-len(excluded_ids)
  artists=db.execute("""SELECT count(*) FILTER(WHERE status<>'archived') active,
   count(*) FILTER(WHERE status<>'archived' AND birth_year IS NOT NULL AND death_year IS NOT NULL) both_life_endpoints,
   count(*) FILTER(WHERE status<>'archived' AND timeline_basis='activity') activity_timeline,
   count(*) FILTER(WHERE status<>'archived' AND timeline_basis='estimated') estimated_timeline FROM artists""").fetchone()
  artist_rows=[]
  for ids in m.chunks(list(expected),2000):artist_rows.extend(db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(ids,)).fetchall())
  actual={r['v']['id']:r['v'] for r in artist_rows};mismatches=[]
  for aid,e in expected.items():
   if aid not in actual:continue # A source exclusion can make an unused plan artist unnecessary.
   fields={k:dict(expected=e[k],actual=actual[aid][k]) for k in ARTIST_FIELDS if actual[aid][k]!=e[k]}
   if fields:mismatches.append(dict(artist_id=aid,name=e['display_name'],fields=fields))
  short=db.execute("SELECT id::text,display_name,birth_year,death_year,timeline_basis FROM artists WHERE status<>'archived' AND entity_type='person' AND birth_year IS NOT NULL AND death_year IS NOT NULL AND (death_year-birth_year<15 OR death_year-birth_year>125)").fetchall()
  campaign=db.execute("""SELECT c.field_name,count(DISTINCT a.id) total,count(DISTINCT a.id) FILTER(WHERE a.status<>'archived') active,
   count(DISTINCT a.id) FILTER(WHERE a.primary_media_id IS NOT NULL AND a.status<>'archived') illustrated
   FROM citations c JOIN artworks a ON a.id=c.entity_id WHERE c.entity_type='artwork' AND c.source_id=ANY(%s::uuid[]) AND c.field_name=ANY(%s) GROUP BY c.field_name ORDER BY c.field_name""",(list(set(source_ids)),['million_catalogue_'+p for p in ['nga','met','rijks','moma','aic']])).fetchall()
 with m.m.connect(local=True) as db:local={t:db.execute('SELECT count(*) n FROM '+t).fetchone()['n'] for t in m.load(m.RUN/'baseline.json.gz')['local_readonly_counts']}
 assert local==m.load(m.RUN/'baseline.json.gz')['local_readonly_counts']
 out=dict(at=m.now(),target=m.TARGET,target_met=qualifying>=m.TARGET,production_artworks=raw,production_artists=artists,conservative_goal_count=qualifying,excluded_unique_records=len(excluded_ids),excluded_date_or_view_records=excluded,active_confirmed_duplicate_pairs=duplicates,method='Consistent production read-only snapshot of all active records, including incomplete review records, minus the union of known date exclusions, explicit Rijks verso views and individually confirmed duplicate pairs. Unknown dates remain explicit; this count does not claim that every record is fully dated or illustrated.',verified_phases=phases,pending_committed_phases=pending,campaign_artworks=campaign,planned_artists_checked=len(actual),planned_artist_field_mismatches=mismatches,remaining_short_or_long_lifespans=short,local_readonly_counts=local,local_baseline_equal=True)
 m.save(dest,out);print(json.dumps({k:v for k,v in out.items() if k in ['at','target_met','production_artworks','production_artists','conservative_goal_count','excluded_unique_records','pending_committed_phases','planned_artists_checked','planned_artist_field_mismatches','remaining_short_or_long_lifespans']},ensure_ascii=False),flush=True)
 if require_target:
  assert qualifying>=m.TARGET and not pending,'Target or completed-source verification is still outstanding'
  assert not mismatches,'Imported artist values differ from the reviewed plans'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('--require-target',action='store_true');a=p.parse_args();assert a.label.replace('-','').isalnum();main(a.label,a.require_target)
