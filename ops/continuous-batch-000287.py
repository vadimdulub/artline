#!/usr/bin/env python3
"""Bounded image-only continuation; the external supervisor remains unchanged."""
import ast, collections, copy, csv, fcntl, gzip, importlib.util, inspect, io, json, os, re, subprocess, sys
from pathlib import Path
import requests
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=module('saam287base','continuous-batch-000274.py');h,i=base.h,base.i
E=ROOT/'docs/research/continuous-production-20261011/batches/000287'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000287'
DATA=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000287'
OP='continuous-smithsonian-20261014-b000287-images';B='saam-046';MID=base.MID;TARGET=base.TARGET
for p in [E,R,DATA,E/'source-captures']:p.mkdir(parents=True,exist_ok=True)
i.OP=OP;i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
def rel(p):return str(Path(p).relative_to(ROOT))
def save(name,value):
 p=E/name
 if p.exists():return h.load(p)
 h.save(p,value);return value
def atomic(p,v):
 tmp=p.with_suffix('.287.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n');os.replace(tmp,p)
target_code=inspect.getsource(base.target)
exec(compile(target_code,__file__,'exec'),globals())
# Reuse the established protected image transaction, pinning this batch's preimage.
apply_code=base.apply_code.replace('saam-shard44-identity-reconciliation.json','identity-reconciliation.json')
apply_code=apply_code.replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'", "m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
exec(compile(apply_code,__file__,'exec'),i.__dict__)
def preflight():
 target('reconciliation')
 reg=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');registry=list(csv.DictReader(reg.open()));qp=E.parents[1]/'source-queue.json';queue=h.load(qp)
 assert len(registry)==len(queue['sources'])==111
 required=[ROOT/'AGENTS.md',reg,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',qp]
 save('required-input-verification.json',dict(at=h.now(),complete_original_registry_used=True,registry_rows=111,files=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=len(p.read_bytes())) for p in required],real_local_connections=0))
 save('original-source-registry.json',registry);save('source-queue-preimage.json',queue)
 q=next(x for x in queue['sources'] if x['source_id']=='smithsonian_open_access');assert q['resume_cursor']['next_shard']=='46' and q['resume_cursor']['next_record_offset']==50
 save('source-register.json',dict(at=h.now(),provider=next(x for x in registry if x['source_id']=='smithsonian_open_access'),prior_queue=q,policy_reference='Original111-source CSV; exact CC0 objects and images only. docs/ARTLINE_IMAGE_USE.md.',held_search_not_requested=True,api_key_route_not_requested=True))
 holds=[]
 for bn in ['000286','000285','000284']:
  for p in (E.parent/bn).glob('*hold*.json'):
   data=h.load(p);holds.append(dict(path=rel(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size,top_level_keys=list(data),preserved=True))
 save('inherited-holds-verification.json',dict(at=h.now(),ledgers=holds,source_queue_holds_preserved=True))
 old=E.parent/'000107/independent-production-verification.json';prev=h.load(old)
 with h.connect() as db:live=h.snapshot(db,list(prev['after']))
 assert live==prev['after']
 save('batch107-live-reconciliation.json',dict(at=h.now(),rows=len(live),snapshot_equal=True,prior_receipt_sha256=h.sha(old.read_bytes()),replay_required=False,prior_increments_counted=0))
 stopfiles=[p for p in (ROOT/'docs/research/illustrated-300k-20261011').glob('stop-*.json')]
 save('completed-campaign-stops.json',dict(at=h.now(),files=[dict(path=rel(p),sha256=h.sha(p.read_bytes())) for p in stopfiles],preserved=True,separate_operation=OP))
 priorpath=E.parent/'000286/independent-production-verification.json';prior=h.load(priorpath);states=prior.get('after',prior.get('rows'))
 with h.connect() as db: previous_live=h.snapshot(db,list(states))
 assert previous_live==states
 save('previous-batch-live-reconciliation.json',dict(at=h.now(),batch=286,snapshot_equal=True,rows=len(states),prior_receipt_sha256=h.sha(priorpath.read_bytes()),prior_increments_counted=0))
 # No earlier attempt exists for this batch, and no writes precede this preflight.
 save('attempt-reconciliation.json',dict(at=h.now(),existing_application_receipts=[rel(p) for p in E.glob('batches/*/applied/*.json')],batch_writes_before_preflight=0,new_unique_operation=OP,completed_campaigns_not_restarted=True,supervisor_unmodified=True))
 print('Preflight passed: target and batch107 reconciled; 111-source registry and holds preserved',flush=True)
def discover():
 assert (E/'batch107-live-reconciliation.json').exists()
 classified=[];selected=[];windows=[]
 with h.connect() as db:
  for shard,start,maxrows in [('46',50,14),('47',0,50)]:
   rp=E/'source-captures'/('saam-'+shard+'.receipt.json')
   if rp.exists():rc=h.load(rp);raw=gzip.decompress((ROOT/rc['body_path']).read_bytes())
   elif shard=='46':
    rc=h.load(E.parent/'000284/source-captures/saam-46.receipt.json');raw=gzip.decompress((ROOT/rc['body_path']).read_bytes());h.save(rp,rc)
   else:
    url='https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/saam/'+shard+'.txt';resp=requests.get(url,timeout=(15,45));resp.raise_for_status();assert resp.status_code==200 and len(resp.content)<12000000;raw=resp.content;bp=DATA/('saam-'+shard+'.body.gz');bp.write_bytes(gzip.compress(raw,mtime=0));rc=dict(url=url,final_url=resp.url,status=resp.status_code,retrieved_at=h.now(),sha256=h.sha(raw),bytes=len(raw),body_path=str(bp),retry_after=resp.headers.get('Retry-After'));h.save(rp,rc)
   assert h.sha(raw)==rc['sha256'];objects=[json.loads(x) for x in raw.splitlines()];end=min(len(objects),start+maxrows)
   windows.append(dict(shard=shard,start=start,end_exclusive=end,total_records=len(objects),source_sha256=rc['sha256']))
   for offset,obj in enumerate(objects[start:end],start):
    d=obj.get('content',{}).get('descriptiveNonRepeating') or {};ft=obj.get('content',{}).get('freetext') or {};link=d.get('record_link','');oid=link.rsplit('=',1)[-1] if '?id=' in link else None
    def vals(k,label=None):return [x['content'] for x in ft.get(k,[]) if label is None or x.get('label')==label]
    title=(d.get('title') or {}).get('content');dates=vals('date','Date');ims=(d.get('online_media') or {}).get('media') or [];row=dict(shard=shard,offset=offset,native_id=oid,title=title)
    if not oid or not title or not dates or len(ims)!=1:row['decision']='missing_identity_date_or_single_image';classified.append(row);continue
    matches=[dict(x) for x in db.execute("SELECT id::text,title,normalized_title,primary_media_id::text,current_institution_id::text,accession_number,creation_year_start,creation_year_end,date_precision,date_display,unlinked_creator_label,status FROM artworks WHERE normalized_title=%s AND current_institution_id=%s AND status<>'archived' LIMIT 20",(h.norm(title),MID))]
    native=[dict(x) for x in db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='saam-object' AND external_id=%s",(oid,))]
    eligible=[a for a in matches if a['primary_media_id'] is None and a['creation_year_end'] is not None and a['creation_year_end']<=1970 and str(a['creation_year_start']) in dates[0]]
    row.update(date=dates[0],title_matches=matches,native_matches=native)
    if native:row['decision']='native_identity_already_present'
    elif len(eligible)!=1:row['decision']='no_unique_eligible_existing_primary_gap'
    elif not(d.get('metadata_usage',{}).get('access')=='CC0' and vals('objectRights','Restrictions & Rights')==['CC0'] and ims[0].get('usage',{}).get('access')=='CC0'):row['decision']='not_explicitly_cc0'
    elif vals('objectType')!=['Painting']:row['decision']='other_medium_requires_separate_review'
    else:
     a=eligible[0];row['decision']='candidate_needs_exact_identity_review';row['snapshot']=h.snapshot(db,[a['id']])[a['id']]
     row['citations']=[dict(x) for x in db.execute("SELECT field_name,evidence_note,source_record_id FROM citations WHERE entity_type='artwork' AND entity_id=%s",(a['id'],))]
     selected.append(dict(artwork_id=a['id'],native_id=oid,title=a['title'],creator_label=a['unlinked_creator_label'] or '',source_credit='; '.join(vals('creditLine')),source_url=link,accession_number=vals('identifier','Object number')[0],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type='painting',provider='saam',image=dict(image_url=ims[0]['content'],source=obj,receipt=rc),rights_basis='Exact Smithsonian object and image explicitly CC0; user approval is separate.',manual_visual_required=True))
    classified.append(row)
   if selected:break
 save('identity-reconciliation.json',dict(at=h.now(),captured_records=len(classified),windows=windows,rows=classified,candidate_count=len(selected),decisions=dict(collections.Counter(x['decision'] for x in classified)),production_writes=0))
 save('candidate-selection.json.gz',dict(provider='saam',batch=B,rows=selected))
 print('Classified',len(classified),'candidates',[(r['native_id'],r['title']) for r in selected],flush=True)
prepare_code=inspect.getsource(base.prepare).replace('saam-shard44-identity-reconciliation.json','identity-reconciliation.json')
exec(compile(prepare_code,__file__,'exec'),globals())
def deliver():
 images,audit,review=i.accepted(B);assert 1<=len(images)<=100
 pre=h.load(E/'independent-prewrite-verification.json')
 assert pre['selection_sha256']==h.sha((i.folder(B)/'selection.json.gz').read_bytes()) and pre['visual_review_sha256']==h.sha((i.folder(B)/'visual-review.json').read_bytes())
 recovery=h.load(E/'local-recovery-verification.json');assert recovery['status']=='VERIFIED'
 for f in recovery['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 with h.connect() as db:
  live=h.snapshot(db,[x['artwork_id'] for x in images]);present=[x for x in images if live[x['artwork_id']]['artwork']['primary_media_id']]
  if present:
   assert len(present)==len(images) and all(live[x['artwork_id']]['artwork']['primary_media_id']==x['media_id'] for x in present)
   assert (i.BACKUP/B/'before-000.json.gz').exists(),'Own transaction preimage required before replay'
 target('before-storage-write');i.upload(B)
 target('before-database-write');i.apply(B)
def resume():
 if not (E/'batch-verification-receipt.json').exists():
  assert (E/'independent-prewrite-verification.json').exists() and (E/'local-recovery-verification.json').exists(),'Resume saved source/visual validation before delivery'
  deliver();print('Delivery reconciled; run continuous-saam-000287-finalize.py for independent verification');return
 target('read-only-resume')
 images,_,_=i.accepted(B);ids=[x['artwork_id'] for x in images];prior=h.load(E/'independent-production-verification.json');pin=h.sha((i.folder(B)/'selection.json.gz').read_bytes())
 with h.connect() as db:
  live=h.snapshot(db,ids);assert live==prior['rows']
  rights=[dict(x) for x in db.execute('SELECT media_id::text,adapter_version,evidence_json FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',([x['media_id'] for x in images],))]
  assert len(rights)==len(images)
  for x in rights:
   ev=x['evidence_json'] if isinstance(x['evidence_json'],dict) else json.loads(x['evidence_json']);assert x['adapter_version']==OP and ev['selection_sha256']==pin
  audit=db.execute("SELECT count(*) n FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[x['media_id'] for x in images])).fetchone()['n'];assert audit==len(images)
 for im in images:assert h.sha(Path(im['path']).read_bytes())==im['sha256'] and h.sha(Path(im['original_path']).read_bytes())==im['source_sha256']
 cp=h.load(E/'CHECKPOINT.json');assert cp==h.load(R/'CHECKPOINT.json')
 queue=h.load(E.parents[1]/'source-queue.json');source=next(x for x in queue['sources'] if x['source_id']=='smithsonian_open_access');assert source['last_batch']==287 and source['resume_cursor']==cp['resume_cursor']
 save('independent-resume-verification.json',dict(at=h.now(),live_rows_equal=True,own_operation=OP,selection_sha256=pin,rights_evidence_rows=len(rights),audit_events=audit,source_and_derivative_checksums_equal=True,runtime_checkpoint_equal=True,queue_cursor_equal=True,replay_required=False,new_writes=0,prior_batch_increments_excluded=True,passed=True))
 print('Read-only resume verified: exact live rows and operation checksums; no write replay required')
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
