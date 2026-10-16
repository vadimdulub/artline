#!/usr/bin/env python3
"""Fresh production reconciliation and delivery of the reviewed French reserve."""
import importlib.util,json,subprocess,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('french-printmaking-delivery-20261011.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
m=d.m;ORIGINAL=d.RUN;PARENT=m.ROOT/'docs/research/printmaking-continuation-20261011';RUN=PARENT/'french-reserve';BACKUP=Path.home()/'Library/Application Support/Artline/backups/printmaking-continuation-20261011/french-reserve'
d.RUN=RUN;d.BACKUP=BACKUP
DESCRIPTION='Before printmaking continuation 20261011 1554 UTC'

def stage():
 initial=m.load(ORIGINAL/'delivery-plan.json.gz');extra=m.load(ORIGINAL/'scope-topup/delivery-plan.json.gz');prior=m.load(ORIGINAL/'completion-verification.json')
 assert prior['new_artworks']==3002 and not prior['errors']
 reserve=set(initial['eligible_reserve'])-{r['artwork_id'] for r in extra['rows']};assert len(reserve)==188
 base=d.baseline();artists={r['id']:r for r in base['artists']}
 approved={}
 for path in (ORIGINAL/'visual-decisions').glob('*.json'):
  decision=m.load(path);sheet=m.load(ORIGINAL/'visual-sheets'/path.name)
  assert decision['sheet_sha256']==m.sha(Path(sheet['sheet']).read_bytes())
  for im in sheet['images']:
   if im['artwork_id'] in reserve and im['artwork_id'] in decision['approved']:approved[im['artwork_id']]=dict(decision_reference=str(path.relative_to(m.ROOT)),decision_sha256=m.sha(path.read_bytes()),image_sha256=im['sha256'])
 assert set(approved)==reserve
 rows=[]
 for p in (ORIGINAL/'identity-rows').glob('*.json'):
  row=m.load(p);aid=row.get('artwork_id')
  if aid not in reserve:continue
  assert row['action']=='create' and aid not in initial['held']
  ap=row['artist_identity'];current=artists[row['artist_id']];assert ap['action']=='existing' and current['status']!='archived'
  assert all(current[k]==ap['existing'][k] for k in ('display_name','birth_year','death_year'))
  ap['existing']=current;row['continuation_visual_evidence']=approved[aid]
  im=m.load(ORIGINAL/'prepared-images'/(aid+'.json'));assert im['sha256']==approved[aid]['image_sha256'] and m.sha(Path(im['local_path']).read_bytes())==im['sha256']
  assert m.sha((m.ROOT/row['source_record_reference']).read_bytes())==row['source_record_sha256']
  m.save(RUN/'identity-rows'/p.name,row);m.save(RUN/'prepared-images'/(aid+'.json'),im);rows.append(row)
 assert len(rows)==188
 m.save(RUN/'authorization.json',(PARENT/'authorization.json').read_bytes())
 m.save(RUN/'source-review-completion.json',dict(at=m.now(),candidates=len(rows),parent_plan_sha256=prior['plan_sha256'],parent_completion_sha256=m.sha((ORIGINAL/'completion-verification.json').read_bytes()),policy='Reuse the 188 previously source-checked, individually visually reviewed reserve prints. Recheck current production native identities, creator state and image duplicates before committing.'))
 print('STAGED',len(rows),flush=True)

def audit():d.audit(required_reports=('source-review-completion.json',))

def freeze():
 rows=d.identity_rows();audit=m.load(RUN/'image-audit.json');held=audit['held_artwork_ids'];chosen=[r for r in rows if r['artwork_id'] not in held];assert chosen
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  existing=[r['artwork_id'] for r in db.execute('SELECT artwork_id::text FROM curated_collection_items WHERE collection_id=%s',(d.COLLECTION,))]
  assert len(existing)==3002 and not set(existing)&{r['artwork_id'] for r in chosen}
  dates={(r['date']['creation_year_start'],r['date']['creation_year_end'],r['date']['date_precision']) for r in chosen}
  for args in dates:assert db.execute('SELECT artline_creation_scope(%s,%s,%s) scope',args).fetchone()['scope']=='eligible'
  before=m.dbutil.snapshot(db,[r['artwork_id'] for r in chosen]);assert not before
 data=dict(at=m.now(),rows=chosen,images={r['artwork_id']:m.load(RUN/'prepared-images'/(r['artwork_id']+'.json')) for r in chosen},held=held,image_gaps={},authorization_sha256=m.sha((RUN/'authorization.json').read_bytes()),baseline_sha256=m.sha((RUN/'production-baseline.json.gz').read_bytes()),selection='Additional individually accessioned Gavarni prints from the previously reviewed French printmaking reserve, rechecked against current production. Documented Yale holdings; no current-display or museum-masterpiece assertion.',position_offset=len(existing),collection_expected_ids=sorted(existing+[r['artwork_id'] for r in chosen]))
 m.save(RUN/'delivery-plan.json.gz',data);pin=m.sha((RUN/'delivery-plan.json.gz').read_bytes());m.save(RUN/'delivery-plan-pin.json',dict(sha256=pin));m.save(BACKUP/'delivery-preimages.json.gz',dict(at=m.now(),plan_sha256=pin,artworks=before))
 print('FROZEN',len(chosen),'new works and images;',len(held),'fresh holds',flush=True)

def backup():
 records=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--limit=20','--format=json'],text=True))
 record=next(r for r in records if r.get('description')==DESCRIPTION);assert record['status']=='SUCCESSFUL'
 m.save(RUN/'cloud-backup.json',record);m.save(BACKUP/'cloud-backup.json',record);print('BACKUP VERIFIED',record['id'],flush=True)

def flag_source_dates():
 dest=RUN/'source-date-followup.json'
 if dest.exists():return
 plan,pin=d.final_plan();rows=[r for r in plan['rows'] if r['artist_identity'].get('death_year') and r['date']['creation_year_start']>r['artist_identity']['death_year']];assert {r['native_id'] for r in rows}=={'80082','80437','81054'}
 ids=[r['artwork_id'] for r in rows];decisions=[]
 with m.connect(True) as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(d.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  before=m.dbutil.snapshot(db,ids);pre=BACKUP/'source-date-followup-preimages.json.gz'
  if not pre.exists():m.save(pre,dict(at=m.now(),artworks=before,plan_sha256=pin))
  for r in rows:
   a=before[r['artwork_id']]['artwork'];assert a['status']=='review' and all(a[k]==r['date'][k] for k in r['date'])
   note=dict(artwork_id=r['artwork_id'],native_id=r['native_id'],source_url=r['source_url'],date=r['date'],creator_label=r['source_creator_label'],review='The official source gives ca. 1935 for a print credited to Paul Gavarni (1804–1866). Whether this describes a later physical impression or a source-date error remains unresolved. Retain the supplied date in review; do not substitute 1835 or infer a printing year from the artist lifespan.',source_record_sha256=r['source_record_sha256'],plan_sha256=pin)
   cid=m.uid('continuation-source-date-review/'+r['native_id'])
   db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,%s,'french_printmaking_physical_date_review',%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING",(cid,r['artwork_id'],d.SID,r['native_id'],r['source_url'],json.dumps(note,ensure_ascii=False),r['receipt']['retrieved_at'],d.ACTOR));decisions.append(dict(note,citation_id=cid))
  after=m.dbutil.snapshot(db,ids)
  for aid in ids:
   for field in ('title','date_display','date_precision','creation_year_start','creation_year_end','primary_media_id','status','published_at','current_institution_id'):assert before[aid]['artwork'][field]==after[aid]['artwork'][field]
  assert db.execute('SELECT count(*) n FROM citations WHERE id=ANY(%s::uuid[])',([r['citation_id'] for r in decisions],)).fetchone()['n']==3
 m.save(dest,dict(at=m.now(),records=decisions,metadata_changes=0,new_artworks=0,scope='Additional editorial uncertainty; all three remain review records and still have source date bounds before 1970. This does not assert that a posthumous impression is verified.'))
 print('SOURCE DATE REVIEW CITATIONS',len(decisions),flush=True)

if __name__=='__main__':
 command=sys.argv[1]
 if command in ('stage','audit','freeze','backup','flag_source_dates'):globals()[command]()
 else:
  assert command in ('upload','apply','verify','public_verify','manifest');getattr(d,command)()
