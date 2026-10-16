#!/usr/bin/env python3
"""Withdraw one contradictory CSV creator mapping; preserve all real objects."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('w',Path(__file__).with_name('million-wikiart-images-20261011.py'));w=importlib.util.module_from_spec(s);s.loader.exec_module(w);m=w.m
RUN=m.RUN/'lifetime-followup-20261011/met-larciani-review';ARTIST='b5f85b29-93bb-52a9-a736-11f571742608';CONFIRMED={'339756','339758'}
def plan():
 path=RUN/'plan.json.gz'
 if path.exists():return m.load(path)
 historical=m.load(m.RUN/'lifetime-followup-20261011/original-art-chronology-followup-candidates.json.gz')['rows'];ids={r['id'] for r in historical if r['artist_id']==ARTIST};assert len(ids)==87
 rows=[r for r in m.load(m.RUN/'met/002/plan.json.gz')['new_artworks'] if r['artwork_id'] in ids];assert len(rows)==87
 assert all(r['first']>=1670 and r['last']<=1800 and r['work_type']=='drawing' and len(r['links'])==1 and r['links'][0]['artist_id']==ARTIST for r in rows)
 with w.r.connect() as db:before=w.d.snapshots(db,list(ids));artist=db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(ARTIST,)).fetchone()['v']
 assert (artist['birth_year'],artist['death_year'])==(1484,1527)
 held=[dict(artwork_id=r['artwork_id'],snapshot=before[r['artwork_id']],reason='Existing qualified attribution is preserved pending individual object evidence') for r in rows if before[r['artwork_id']]['creators'][0]['attribution_role']!='primary']
 assert all(len(r['snapshot']['creators'])==1 and r['snapshot']['creators'][0]['artist_id']==ARTIST and r['snapshot']['creators'][0]['attribution_role']=='attributed_to' for r in held)
 heldids={r['artwork_id'] for r in held};rows=[r for r in rows if r['artwork_id'] not in heldids];before={aid:value for aid,value in before.items() if aid not in heldids}
 for row in rows:
  aid=row['artwork_id'];a=before[aid]['artwork'];assert a['status']=='review' and (a['creation_year_start'],a['creation_year_end'])==(row['first'],row['last']) and a['title']==row['title']
  assert len(before[aid]['creators'])==1 and before[aid]['creators'][0]['artist_id']==ARTIST and before[aid]['creators'][0]['attribution_role']=='primary'
  row['reviewed_label']='Anonymous, Italian, 18th century' if row['native_id'] in CONFIRMED else 'Unresolved CSV attribution: '+row['creator_label']
 out=dict(at=m.now(),rows=rows,before=before,artist=artist,held=held,decision='Remove only the unsupported primary painter links. Two exact object pages establish anonymous Italian eighteenth-century attribution. The other selected records retain the original CSV creator wording as explicitly unresolved object labels; neither their anonymity nor another creator is invented. Preserve the preexisting qualified attribution for separate object review. Keep all artwork dates, images, inventories, holdings and review status.',
  official_page_observations=[dict(native_id='339756',url='https://www.metmuseum.org/art/collection/search/339756',title='Two Angels',inventory='80.3.366',creator='Anonymous, Italian, 18th century',date='18th century'),dict(native_id='339758',url='https://www.metmuseum.org/art/collection/search/339758',title='Saint Sebastian Exhorts the Christian Prisoners',inventory='80.3.367',creator='Anonymous, Italian, 18th century',date='18th century')],
  evidence_method='Official collection pages read with the web research tool on 11 October 2026. Subsequent direct HTTP returned 429; that website is held and was not retried. The separate collection API remains held from its earlier 403. The captured CSV and original creator links remain in immutable history.',source_access_hold=m.load(m.RUN/'lifetime-followup-20261011/met-anonymous-probe.json'))
 for evidence in out['official_page_observations']:
  row=next(r for r in rows if r['native_id']==evidence['native_id']);assert row['title']==evidence['title'] and row['accession_number']==evidence['inventory']
 m.save(path,out);m.save(RUN/'pin.json',dict(sha256=m.sha(path.read_bytes())));m.save(m.BACKUP/'lifetime-followup-20261011/met-larciani-review/plan.json.gz',out);return out
def apply():
 if (RUN/'applied.json').exists():return
 p=plan();ids=list(p['before']);pin=m.load(RUN/'pin.json')['sha256'];assert pin==m.sha((RUN/'plan.json.gz').read_bytes())
 with w.r.connect(write=True) as db:
  db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
  before=w.d.snapshots(db,ids);existing=db.execute("SELECT count(*) n FROM citations WHERE entity_id=ANY(%s::uuid[]) AND field_name='million_lifetime_creator_conflict_review'",(ids,)).fetchone()['n']
  if existing:assert existing==len(ids)
  else:
   assert before==p['before'],'Records changed after individual source review'
   for row in p['rows']:
    aid=row['artwork_id'];evidence=dict(plan_sha256=pin,original_row=row,previous_creator_links=before[aid]['creators'],previous_object=before[aid]['artwork'],decision=p['decision'],official_page=next((r for r in p['official_page_observations'] if r['native_id']==row['native_id']),None),evidence_method=p['evidence_method'])
    w.n.copy_rows(db,'citations',[dict(id=m.uid('met-creator-conflict/'+aid),entity_type='artwork',entity_id=aid,field_name='million_lifetime_creator_conflict_review',source_id=m.uid('source/met'),source_record_id=row['native_id'],source_url=row['source_url'],evidence_note=json.dumps(evidence,ensure_ascii=False),retrieved_at=m.now(),created_by=m.ACTOR)])
    db.execute("DELETE FROM artwork_artists WHERE artwork_id=%s AND artist_id=%s AND attribution_role='primary'",(aid,ARTIST))
    db.execute('UPDATE artworks SET unlinked_creator_label=%s,updated_by=%s,updated_at=now(),revision=revision+1 WHERE id=%s',(row['reviewed_label'],m.ACTOR,aid))
   after=w.d.snapshots(db,ids)
   for row in p['rows']:
    aid=row['artwork_id'];assert not after[aid]['creators'];assert after[aid]['attachments']==before[aid]['attachments'];assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in {'unlinked_creator_label','updated_by','updated_at','revision'})
   db.commit()
 confirmed=sum(r['native_id'] in CONFIRMED for r in p['rows']);m.save(RUN/'applied.json',dict(at=m.now(),artworks=ids,withdrawn_primary_links=len(ids),confirmed_anonymous_labels=confirmed,unresolved_source_labels=len(ids)-confirmed,qualified_attributions_preserved=len(p['held']),plan_sha256=pin));print('Withdrew',len(ids),'unsupported primary painter links;',confirmed,'anonymous attributions verified;',len(p['held']),'existing qualified attribution preserved',flush=True)
def verify():
 p=plan();ids=list(p['before'])
 with w.r.connect() as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=w.d.snapshots(db,ids)
  for row in p['rows']:
   aid=row['artwork_id'];assert not after[aid]['creators'];assert after[aid]['artwork']['unlinked_creator_label']==row['reviewed_label'];assert after[aid]['attachments']==p['before'][aid]['attachments'];assert all(after[aid]['artwork'][k]==v for k,v in p['before'][aid]['artwork'].items() if k not in {'unlinked_creator_label','updated_by','updated_at','revision'})
  assert db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(ARTIST,)).fetchone()['v']==p['artist']
  assert db.execute("SELECT count(*) n FROM citations WHERE entity_id=ANY(%s::uuid[]) AND field_name='million_lifetime_creator_conflict_review'",(ids,)).fetchone()['n']==len(ids)
  assert db.execute('SELECT count(*) n FROM artwork_search_documents s JOIN artworks a USING(id) WHERE a.id=ANY(%s::uuid[]) AND s.status=a.status AND s.title=a.title AND s.primary_media_id IS NOT DISTINCT FROM a.primary_media_id',(ids,)).fetchone()['n']==len(ids)
  for held in p['held']:assert w.d.snapshots(db,[held['artwork_id']])[held['artwork_id']]==held['snapshot']
 with w.r.connect(local=True) as db:local={t:db.execute('SELECT count(*) n FROM '+t).fetchone()['n'] for t in m.load(m.RUN/'baseline.json.gz')['local_readonly_counts']}
 assert local==m.load(m.RUN/'baseline.json.gz')['local_readonly_counts'];m.save(RUN/'verification.json',dict(at=m.now(),artworks_preserved=len(ids),wrong_primary_links_removed=len(ids),confirmed_anonymous=2,unresolved_creator_labels=len(ids)-2,qualified_attributions_preserved=len(p['held']),source_citations=len(ids),search_documents=len(ids),local_baseline_equal=True));print('Verified',len(ids),'creator corrections; object dates, images, holdings and states preserved',flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['plan','apply','verify']);a=ap.parse_args();globals()[a.action]()
