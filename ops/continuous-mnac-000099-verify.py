"""Verify own persisted source/plan attribution, audit inserts, holdings and public API."""
import importlib.util,json,fcntl
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('b','ops/continuous-mnac-batch-000099.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']];assert len(ids)==11
bp=h.BACKUP/b.PHASE/'locked-before.json.gz';pre=h.load(bp);assert pre['artworks']=={} and pre['plan_sha256']==pin
assert h.load(b.E/'independent-source-verification.json')['plan_sha256']==pin
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids);assert len(after)==len(ids)
 citations=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,b.FIELD))];assert len(citations)==len(ids)
 events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='insert'",(ids,))];assert len(events)==len(ids)
 for r in p['records']:
  aid=r['artwork_id'];state=after[aid];a=state['artwork'];note=next(x for x in citations if x['entity_id']==aid)
  assert note['source_record_id']==r['source_id'] and note['note']['plan_sha256']==pin and note['note']['evidence']['sha256']==r['evidence']['sha256']
  assert a['status']=='review' and a['published_at'] is None and a['research_candidate'] and a['current_institution_id']==b.MID and a['primary_media_id'] is None and not state['attachments']
  fields=['title','accession_number','date_display','creation_year_start','creation_year_end','date_precision','dimensions_text','medium_text','unlinked_creator_label','work_type']
  want=[r['title'],r['accession_number'],r['date_display'],r['first'],r['last'],r['precision'],r['dimensions'],r['medium'],None if r['artist_id'] else r['creator_label'],'painting']
  assert [a[k] for k in fields]==want
  if r['artist_id']:assert len(state['creators'])==1 and state['creators'][0]['artist_id']==r['artist_id'] and state['creators'][0]['attribution_role']=='primary'
  else:assert not state['creators']
  holdings=state['holdings'];assert len(holdings)==1 and holdings[0]['claim_type']=='holding' and holdings[0]['review_state']=='accepted' and holdings[0]['institution_id']==b.MID
  ev=json.loads(holdings[0]['evidence_note']);assert ev['source_sha256']==r['evidence']['sha256'] and ev['confidence']>=.8 and ev['inventory']==r['accession_number']
  ext=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(r['scheme'],r['source_id'])).fetchall();assert ext==[dict(entity_id=aid)]
  assert db.execute('SELECT count(*) n FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(b.MID,r['accession_number'])).fetchone()['n']==1
  event=next(x for x in events if x['entity_id']==aid);assert event['before_json'] in [None,{}] and event['after_json']['title']==r['title'] and event['after_json']['primary_media_id'] is None
 scope=[dict(x) for x in db.execute('SELECT id::text,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope FROM artworks WHERE id=ANY(%s::uuid[])',(ids,))];assert all(x['scope']=='eligible' for x in scope)
 search=db.execute('SELECT count(*) n FROM artworks a JOIN artwork_search_documents s ON s.id=a.id WHERE a.id=ANY(%s::uuid[]) AND s.title=a.title AND s.status=a.status',(ids,)).fetchone()['n'];assert search==len(ids)
 original=h.load(b.E/'institution-scope-before.json.gz');live={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id=ANY(%s::uuid[])',([a['id'] for a in original],))};assert live=={a['id']:a for a in original}
 artistrows={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(list(p['artists']),))};assert artistrows==p['artists']
 total_audit=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']
b.save('independent-production-verification.json',dict(at=h.now(),rows=after,citations=citations,plan_sha256=pin,creation_scope=scope,search_documents=search,new_review_artworks=len(ids),accepted_holdings=len(ids),transaction_preimages=str(bp),preimages_sha256=h.sha(bp.read_bytes()),empty_new_object_preimages_verified=True,existing_artworks_unchanged=len(original),existing_creator_unchanged=True,local_database_connections=0))
b.save('independent-audit-history-verification.json',dict(at=h.now(),inserts=events,empty_locked_preimages_verified=True))
public=[]
for aid in ids:
 url='https://artlines.org/api/backend/v1/atlas/artworks/'+aid;res=requests.get(url,timeout=(15,45));assert res.status_code==200
 a=res.json();assert a['id']==aid and a['title']==after[aid]['artwork']['title'];b.save('public-api/'+aid+'.json',a)
 public.append(dict(artwork_id=aid,url=url,status=res.status_code,response_sha256=h.sha(res.content)))
b.save('independent-public-verification.json',dict(at=h.now(),rows=public,all_review_artworks_public=True,image_files=0,images_verified=0))
counts=dict(new_painters=0,new_artworks=len(ids),newly_illustrated=0,alternate_images=0,museum_links=len(ids))
b.save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,plan_sha256=pin,production_target=b.target(),attribution='Absent locked metadata preimages, own persisted citation plan/source checksums and exactly one insertion audit event per object. Existing records and prior campaigns excluded.',images_downloaded=0,new_artist_connections=1,limitations=['Native museum images remain permission-held; no image file prepared or visually reviewed.','Source anonymous and conventional Master labels retained without fabricated painters; Antonio Veneziano authority unresolved.','Source late-century wording retains conservative full-century bounds; no precise year invented.','Scoped schema and affected-row recovery export is not a full database backup.']))
# Reconcile exact attribution before invoking idempotent resume; no fresh write on replay.
b.apply()
with h.connect() as db:
 assert h.snapshot(db,ids)==after
 assert db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==total_audit
b.save('independent-resume-verification.json',dict(at=h.now(),unchanged_snapshot=True,unchanged_audit_events=total_audit,attribution_reconciled_before_replay=True,replay_increments={k:0 for k in counts}))
print(json.dumps(dict(verified_counts=counts,replay_changes=0)))
