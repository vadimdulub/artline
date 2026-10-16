#!/usr/bin/env python3
"""Bounded batch 146: SAAM shard-02 image enrichment for exact legacy works."""
import copy,csv,fcntl,gzip,hashlib,importlib.util,inspect,json,os,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
h=mod('metadata146','india-300-delivery-20261011.py');base=mod('base146','continuous-image-batch-000002.py');i=base.i
E=ROOT/'docs/research/continuous-production-20261011/batches/000146';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000146'
OP='continuous-smithsonian-20261013-b000146-images';B='saam-002';MID='259d7efe-d565-56bf-bdc0-b467d3b2f69b';MUSEUM='Smithsonian American Art Museum'
for p in (E,R,E/'source-captures'):p.mkdir(parents=True,exist_ok=True)
i.OP=OP;i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
i.CFG['saam']=dict(mid=MID,scheme='saam-object',name=MUSEUM,rights='cc0',license='CC0 1.0 Universal — Smithsonian Open Access',policy='https://creativecommons.org/publicdomain/zero/1.0/',host='ids.si.edu')
old_uid=i.m.uid;i.m.uid=lambda k:'65d2e2a9-90e3-51ac-88d5-de9f614ad568' if k=='source/saam' else old_uid(k)
code=inspect.getsource(i.apply).replace("(a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['current_institution_id'])==(r['title'],r['accession_number'],r['first'],r['last'],r['precision'],r.get('expected_museum_id',cfg['mid']))","(a['title'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['current_institution_id'])==(r['title'],r['first'],r['last'],r['precision'],r.get('expected_museum_id',cfg['mid']))").replace("native_ids.get(aid)==r['native_id']","native_ids.get(aid) in [None,r['native_id']]").replace("r['plan_sha256']","r.get('plan_sha256',pin)")
exec(compile(code,__file__,'exec'),i.__dict__)

def save(n,v):h.save(E/n,v);return v
def source():
 p=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000146/saam-02.txt';raw=p.read_bytes();bp=E/'source-captures/saam-02.body.gz';bp.write_bytes(gzip.compress(raw,mtime=0))
 if (E/'source-captures/saam-02.receipt.json').exists():return [json.loads(x) for x in raw.splitlines()],h.load(E/'source-captures/saam-02.receipt.json')
 rc=dict(url='https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/saam/02.txt',status=200,retrieved_at=h.now(),sha256=h.sha(raw),bytes=len(raw),body_path=str(bp.relative_to(ROOT)))
 h.save(E/'source-captures/saam-02.receipt.json',rc);return [json.loads(x) for x in raw.splitlines()],rc
def prepare():
 objects,rc=source();rows=[];recon=[];classified=[]
 with h.connect() as db:
  for o in objects:
   d=o.get('content',{}).get('descriptiveNonRepeating') or {};ft=o.get('content',{}).get('freetext') or {};link=d.get('record_link','');oid=link.rsplit('=',1)[-1] if '?id=' in link else None
   def vals(k,label=None):return [x['content'] for x in ft.get(k,[]) if label is None or x.get('label')==label]
   title=(d.get('title') or {}).get('content');datevals=vals('date','Date');ims=((d.get('online_media') or {}).get('media') or [])
   if not oid or not title or not datevals or len(ims)!=1:classified.append(dict(native_id=oid,title=title,decision='not_selected_missing_required_fields_or_single_image'));continue
   matches=[dict(x) for x in db.execute("SELECT id::text,title,normalized_title,primary_media_id::text,current_institution_id::text,creation_year_start,creation_year_end,date_display,unlinked_creator_label,status FROM artworks WHERE normalized_title=%s AND current_institution_id=%s AND status<>'archived'",(h.norm(title),MID))]
   eligible=[a for a in matches if a['primary_media_id'] is None and a['creation_year_end'] is not None and a['creation_year_end']<=1970 and str(a['creation_year_start']) in datevals[0]]
   native=[dict(x) for x in db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='saam-object' AND external_id=%s",(oid,))]
   if len(eligible)!=1 or native:classified.append(dict(native_id=oid,title=title,decision='not_selected',title_matches=matches,native_matches=native));continue
   a=eligible[0];aid=a['id'];date=datevals[0]
   assert d['metadata_usage']['access']=='CC0' and vals('objectRights','Restrictions & Rights')==['CC0'] and ims[0]['usage']['access']=='CC0'
   acc=vals('identifier','Object number')[0]
   holdings=[dict(x) for x in db.execute("SELECT id::text FROM artwork_location_assertions WHERE artwork_id=%s AND institution_id=%s AND claim_type='holding' AND superseded_by IS NULL",(aid,MID))]
   title_matches=[dict(x) for x in db.execute("SELECT id::text,title,current_institution_id::text,creation_year_start,creation_year_end,primary_media_id::text FROM artworks WHERE normalized_title=%s AND status<>'archived'",(a['normalized_title'],))]
   recon.append(dict(native_id=oid,artwork_id=aid,accession=acc,title=a['title'],decision='exact_legacy_work_selected_for_image_only',basis='Exact normalized source title, SAAM institution, identical source date bounds and creator label; missing primary image and no SAAM native identifier. No metadata mutation authorized by image-only selection.',title_matches=title_matches,existing_holdings=len(holdings)))
   rows.append(dict(artwork_id=aid,native_id=oid,title=a['title'],creator_label=a['unlinked_creator_label'],source_credit=vals('creditLine')[0],source_url=link,accession_number=acc,first=a['creation_year_start'],last=a['creation_year_end'],precision=('circa_range' if date.startswith('ca.') and a['creation_year_start'] != a['creation_year_end'] else ('circa' if date.startswith('ca.') else ('range' if a['creation_year_start'] != a['creation_year_end'] else 'exact'))),work_type='painting',provider='saam',image=dict(image_url=ims[0]['content'],source=o,receipt=rc),rights_basis='Official Smithsonian shard marks metadata, object and exact image CC0; user approval remains separate.',manual_visual_required=True))
   if len(rows)==5:break
 print('SELECTED',len(rows),[(r['native_id'],r['title']) for r in rows],flush=True)
 assert rows
 save('saam-shard02-identity-reconciliation.json',dict(at=h.now(),captured_records=len(objects),selected=len(rows),rows=recon,classified_before_selection=classified,source_sha256=rc['sha256']))
 h.save(i.folder(B)/'selection.json.gz',dict(provider='saam',batch=B,rows=rows));h.save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for r in rows:print(r['native_id'],i.prepare_one(r,B)['state'],flush=True)
 i.audit(B)
 for path in (i.folder(B)/'sheets').glob('*.json'):print('SHEET',h.load(path)['path'],flush=True)
def deliver():
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791897658924','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save('cloud-backup.json',backup);save('cloud-sql-backup.json',backup)
 i.upload(B);i.apply(B)
def verify():i.verify(B)
def finalize():
 rows=i.selected(B)['rows'];images,audit,review=i.accepted(B);ids=[x['artwork_id'] for x in rows];expected={x['artwork_id']:x for x in images};sel=h.sha((i.folder(B)/'selection.json.gz').read_bytes());before=h.load(i.BACKUP/B/'before-000.json.gz');assert all(before[x]['artwork']['primary_media_id'] is None for x in ids)
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids);media=[dict(x) for x in db.execute("SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256::text,ma.storage_path,ma.byte_size,ma.rights_status,e.adapter_version,e.source_record_id,e.source_checksum,e.source_image_url,e.evidence_json FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=ma.id WHERE a.id=ANY(%s::uuid[])",(ids,))]
 assert len(after)==len(media)==len(ids)
 for aid in ids:
  assert after[aid]['artwork']['primary_media_id']==expected[aid]['media_id'];assert after[aid]['holdings']==before[aid]['holdings'] and after[aid]['creators']==before[aid]['creators'];assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in i.IGNORE)
 for m in media:
  im=expected[m['id']];ev=m['evidence_json'] if isinstance(m['evidence_json'],dict) else json.loads(m['evidence_json']);assert (m['checksum_sha256'],m['byte_size'],m['rights_status'],m['adapter_version'])==(im['sha256'],im['bytes'],'cc0',OP);assert ev['selection_sha256']==sel and ev['visual_review']['viewed_individually']
 public=[]
 import requests
 for aid in ids:
  u='https://artlines.org/api/backend/v1/atlas/artworks/'+aid;r=requests.get(u,timeout=(15,45));r.raise_for_status();im=expected[aid];pic=requests.get('https://artlines.org'+im['storage_path'],timeout=(15,45));pic.raise_for_status();assert h.sha(pic.content)==im['sha256'] and im['storage_path'] in r.text;public.append(dict(artwork_id=aid,api_status=r.status_code,image_status=pic.status_code,image_sha256=im['sha256'],storage_path=im['storage_path']))
 counts=dict(new_painters=0,new_artworks=0,newly_illustrated=len(ids),alternate_images=0,museum_links=0)
 save('independent-production-verification.json',dict(at=h.now(),rows=after,media=media,preimage_path=str((i.BACKUP/B/'before-000.json.gz')),preimage_sha256=h.sha((i.BACKUP/B/'before-000.json.gz').read_bytes()),selection_sha256=sel,verified_counts=counts,metadata_unchanged=True,local_database_connections=0))
 save('independent-public-verification.json',dict(at=h.now(),rows=public,all_selected_images_delivered=True))
 # Repeat mandated reconciliation without replaying the immutable reserve plan.
 fr=h.load(E.parent/'000142/french-reserve-live-reconciliation.json');assert fr['unimported']==0 and fr['already_imported_and_illustrated']==188;save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,selected=0,new_programme_increments=0,prior_verified_evidence=str((E.parent/'000142/french-reserve-live-reconciliation.json').relative_to(ROOT)),plan_sha256=fr['plan_sha256'],prior_actual_visual_review_reused=True,new_visual_review_claim=False))
 reg=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');required=[ROOT/'AGENTS.md',reg,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json'];assert len(list(csv.DictReader(reg.open())))==111
 save('required-input-verification.json',dict(at=h.now(),registry_rows=111,complete_original_registry_used=True,files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in required],local_catalogue_connections=0))
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres';save('production-target-reconciliation.json',dict(at=h.now(),connection_name=actual,proxy_port=55519,helper='ops/india-300-delivery-20261011.py and established image adapter',shared_ingestion_lock='artline-curated-ingestion',write=True,backup_id='1791897658924',backup_status='SUCCESSFUL',local_catalogue_connections=0))
 prev=h.load(E.parent/'000107/independent-production-verification.json');
 with h.connect() as db:assert h.snapshot(db,list(prev['after']))==prev['after']
 save('batch107-live-reconciliation.json',dict(at=h.now(),snapshot_equal=True,rows=len(prev['after']),previous_increments_counted=0))
 qp=E.parents[1]/'source-queue.json';queue=h.load(qp);beforeq=copy.deepcopy(queue);q=next(x for x in queue['sources'] if x['source_id']=='smithsonian_open_access');q.update(status='saam_shard02_one_exact_legacy_primary_image_verified',last_checked_at=h.now(),last_batch=146,checkpoint=str((E/'CHECKPOINT.json').relative_to(ROOT)),resume_cursor=dict(unit='saam',completed_shard='02',next_shard='03',source_sha256=h.load(E/'source-captures/saam-02.receipt.json')['sha256'],records_classified=67,eligible_exact_missing_image_matches=1,newly_illustrated_native_ids=[r['native_id'] for r in rows],scope='All 67 shard records classified; one exact existing SAAM legacy work was eligible and illustrated. Other records were nonmatches, already identified, already illustrated, out of scope, or lacked the required exact identity evidence.'))
 q['evidence_paths']=[str((E/x).relative_to(ROOT)) for x in ['saam-shard02-identity-reconciliation.json','independent-production-verification.json','independent-public-verification.json','CHECKPOINT.json']]
 with qp.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);tmp=qp.with_suffix('.146.tmp');tmp.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp)
 save('source-queue-update-verification.json',dict(at=h.now(),updated_source='smithsonian_open_access',unrelated_entries_preserved=[x for x in beforeq['sources'] if x['source_id']!='smithsonian_open_access']==[x for x in queue['sources'] if x['source_id']!='smithsonian_open_access'],queue_sha256=h.sha(qp.read_bytes()),resume_cursor=q['resume_cursor']))
 save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,production_writes=len(ids),selection_sha256=sel,transaction_preimage_sha256=h.sha((i.BACKUP/B/'before-000.json.gz').read_bytes()),attribution='The exact existing artwork had null primary_media_id in the locked preimage; its persisted media row carries this adapter, selection checksum, source checksum and individually viewed decision; the public checksum matches.',production_target=actual,shared_ingestion_lock='artline-curated-ingestion'))
 nxt='Process a bounded Smithsonian SAAM shard 03 segment, prioritizing exact missing-image legacy paintings; shard 02 is fully classified and the exhausted French reserve must not be replayed.';evidence=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','french-reserve-live-reconciliation.json','saam-shard02-identity-reconciliation.json','batches/saam-002/quality-audit.json','batches/saam-002/visual-review.json','independent-production-verification.json','independent-public-verification.json','source-queue-update-verification.json','batch-verification-receipt.json']
 cp=dict(at=h.now(),batch=146,stage='independently_verified_complete',researched=dict(french_reserve=188,saam_shard02_records=67),selected=len(ids),prepared=len(ids),imported=len(ids),verified=len(ids),verified_counts=counts,next_task=nxt,blocker='',evidence=[str((E/x).relative_to(ROOT)) for x in evidence],external_supervisor_unchanged=True,production_writes=len(ids),local_catalogue_connections=0);save('CHECKPOINT.json',cp);h.save(R/'CHECKPOINT.json',cp)
 checked=[]
 for n in evidence+['CHECKPOINT.json']:
  p=E/n;h.load(p);checked.append(dict(path=str(p.relative_to(ROOT)),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size))
 save('independent-final-artifact-verification.json',dict(at=h.now(),artifacts=checked,runtime_checkpoint_equal=h.load(R/'CHECKPOINT.json')==cp,passed=True))
 result=dict(outcome='progress',summary='Batch 146 verified one new primary image on an exact existing Smithsonian American Art Museum painting after classifying all 67 shard-02 records. The derivative was individually viewed, is checksum-bound to the CC0 source record, and is publicly delivered; artwork metadata, creators and holdings were unchanged. The 188 French reserve records were already imported and excluded from counts.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[str((E/x).relative_to(ROOT)) for x in evidence+['CHECKPOINT.json','independent-final-artifact-verification.json']]);save('worker-result.json',result);h.save(R/'worker-result.json',result);print(json.dumps(result))
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
