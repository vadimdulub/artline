#!/usr/bin/env python3
"""Bounded French reconciliation then NGA native primary-image enrichment."""
import importlib.util,json,sys,subprocess,gzip,fcntl,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base','continuous-image-batch-000002.py');i=base.i;h=base.h
OLD=base.OLD;E=ROOT/'docs/research/continuous-production-20261011/batches/000010';RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000010';B='nga-000'
i.OP='continuous-primary-images-20261011-b000010';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
save=i.saved;load=i.m.load;connect=base.connect;target=base.target
for p in [E,RUNTIME,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def french():
 dest=E/'french-reserve-production-reconciliation.json'
 if dest.exists():return
 f=mod('french','continuous-french-reserve-batch-000001.py');initial=load(f.MAIN/'delivery-plan.json.gz');top=load(f.MAIN/'scope-topup/delivery-plan.json.gz');ids=set(initial['eligible_reserve'])-{r['artwork_id'] for r in top['rows']};assert len(ids)==188
 rows=[r for r in f.d.identity_rows() if r['artwork_id'] in ids];approved={}
 for path in (f.MAIN/'visual-decisions').glob('*.json'):
  dec=load(path);sheet=load(f.MAIN/'visual-sheets'/path.name);assert dec['sheet_sha256']==h.sha(Path(sheet['sheet']).read_bytes())
  for im in sheet['images']:
   if im['artwork_id'] in ids and im['artwork_id'] in dec['approved']:approved[im['artwork_id']]=dict(decision_path=str(path.relative_to(ROOT)),decision_sha256=h.sha(path.read_bytes()),sheet_sha256=dec['sheet_sha256'],derivative_sha256=im['sha256'])
 assert set(approved)==ids
 records=[]
 with connect() as db:
  current=h.snapshot(db,list(ids));assert set(current)==ids
  for r in rows:
   aid=r['artwork_id'];im=load(f.MAIN/'prepared-images'/(aid+'.json'));assert im['sha256']==approved[aid]['derivative_sha256']==h.sha(Path(im['local_path']).read_bytes())
   assert h.sha((ROOT/r['source_record_reference']).read_bytes())==r['source_record_sha256']
   a=current[aid]['artwork'];assert a['accession_number']==r['accession_number'] and a['primary_media_id']
   native=db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=%s AND scheme=ANY(%s)",(aid,['yale-object','museum-expansion-yale-object','yale-lux-object'])).fetchall();assert any(x['external_id']==r['native_id'] for x in native)
   citations=db.execute("SELECT evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name='french_printmaking_source_identity'",(aid,)).fetchall();assert citations
   ma=db.execute('SELECT checksum_sha256::text FROM media_assets WHERE id=%s',(a['primary_media_id'],)).fetchone();assert ma['checksum_sha256']==im['sha256']
   records.append(dict(artwork_id=aid,native_id=r['native_id'],reason='already_delivered_by_other_campaign',persisted_plan_checksums=citations,prior_actual_visual_evidence=approved[aid],source_record_sha256=r['source_record_sha256']))
 save(dest,dict(at=h.now(),inspected=188,unimported=0,verified_programme_increments=0,records=records,historical_plans_unchanged=True))
def prepare():
 french()
 if (i.folder(B)/'selection.json.gz').exists():
  assert h.sha((i.folder(B)/'selection.json.gz').read_bytes())==load(i.folder(B)/'pin.json')['sha256']
  return finish_preparation(i.selected(B)['rows'])
 save(E/'production-target-reconciliation.json',target())
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');rs=list(__import__('csv').DictReader(registry.open()));assert len(rs)==111
 holds={str(p.relative_to(ROOT)):load(p) for p in (OLD/'access-holds').glob('*.json')}
 save(E/'source-register.json',dict(at=h.now(),registry_path=str(registry),registry_sha256=h.sha(registry.read_bytes()),registry_records=111,sources=[r for r in rs if r['source_id'] in ['nga_washington','yale_lux']],policy_reference='docs/ARTLINE_IMAGE_USE.md',retained_access_holds=holds))
 assert not (OLD/'access-holds/api.nga.gov.json').exists()
 planpath=i.m.RUN/'nga/plan-v2.json.gz';plan=load(planpath);pin=h.sha(planpath.read_bytes());excluded=set()
 for p in (OLD/'batches').glob('nga-*/quality-audit.json'):excluded.update(load(p)['identity_holds'])
 for p in (OLD/'batches').glob('nga-*/visual-review.json'):excluded.update(x['artwork_id'] for x in load(p)['decisions'] if x['decision']!='accept')
 candidates=[r for r in plan['new_artworks'] if i.native_image('nga',r)];reconciled=[];chosen=[];creators=collections.Counter()
 with connect() as db:
  present={}
  for part in i.m.chunks([r['artwork_id'] for r in candidates],2000):present.update({x['id']:x for x in db.execute('SELECT id::text,title,accession_number,creation_year_start,creation_year_end,date_precision,current_institution_id::text,status,primary_media_id FROM artworks WHERE id=ANY(%s::uuid[])',(part,))})
  for position,r in enumerate(candidates):
   a=present.get(r['artwork_id']);reason='eligible'
   if not a or a['status']=='archived':reason='missing_or_archived'
   elif a['primary_media_id']:reason='already_illustrated'
   elif r['artwork_id'] in excluded:reason='immutable_prior_identity_or_visual_hold'
   elif (a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['current_institution_id'])!=(r['title'],r['accession_number'],r['first'],r['last'],r['precision'],i.CFG['nga']['mid']):reason='source_identity_changed'
   elif creators[r['creator_label']]>=2:reason='creator_variety_deferred'
   if reason=='eligible':
    keep={k:r[k] for k in ['artwork_id','native_id','title','creator_label','source_url','accession_number','first','last','precision','work_type']}
    chosen.append(dict(keep,provider='nga',image=i.native_image('nga',r),plan_path=str(planpath),plan_sha256=pin));creators[r['creator_label']]+=1
   reconciled.append(dict(artwork_id=r['artwork_id'],position=position,reason=reason))
   if len(chosen)==25:break
 assert chosen
 save(E/'nga-gap-reconciliation.json',dict(at=h.now(),candidate_count=len(candidates),selected=len(chosen),prior_holds_excluded=sorted(excluded),rows=reconciled,resume_position=position+1,policy='Earlier delivered objects excluded, max two per creator for varied bounded selection; deferred earlier positions retained.'))
 save(i.folder(B)/'selection.json.gz',dict(at=h.now(),provider='nga',batch=B,rows=chosen,selection_basis='Fresh production gaps beyond prior illustrated selection; exact native primary image, openaccess=1, through 1955; prior rejected identities excluded.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 finish_preparation(chosen)
def finish_preparation(chosen):
 for r in chosen:
  info=r['image']['native_url']+'/info.json'
  receiptpath=E/'source-captures'/(r['native_id']+'.info.receipt.json')
  if receiptpath.exists():
   receipt=load(receiptpath);body=gzip.decompress((ROOT/receipt['body_path']).read_bytes());assert h.sha(body)==receipt['sha256'] and receipt['status']==200;data=json.loads(body)
   assert data.get('@id',data.get('id'))==r['image']['native_url'];i.prepare_one(r,B);continue
  res=i.session().get(info,timeout=(15,60));body=res.content
  path=E/'source-captures'/(r['native_id']+'.info.body.gz');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(gzip.compress(body,mtime=0));receipt=dict(at=h.now(),url=info,status=res.status_code,sha256=h.sha(body),body_path=str(path.relative_to(ROOT)))
  save(path.with_name(r['native_id']+'.info.receipt.json'),receipt)
  if res.status_code in [401,403,429]:save(E/'access-holds/api.nga.gov.json',dict(receipt,retry_after=res.headers.get('Retry-After')));raise RuntimeError('NGA access hold')
  res.raise_for_status();data=res.json();assert data.get('@id',data.get('id'))==r['image']['native_url'];assert data['width']==int(r['image']['source']['width']) and data['height']==int(r['image']['source']['height'])
  i.prepare_one(r,B)
 save(E/'cloud-backup.json',load(OLD/'cloud-backup.json'));i.audit(B)
 print('SHEET',load(i.folder(B)/'sheets/000.json')['path'])
def deliver():
 checked=target(True)
 if not (E/'production-target-before-write.json').exists():save(E/'production-target-before-write.json',checked)
 assert not (E/'access-holds/api.nga.gov.json').exists();i.upload(B);target(True);i.apply(B)
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
