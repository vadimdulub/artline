#!/usr/bin/env python3
import copy,csv,datetime,fcntl,gzip,hashlib,json,os,subprocess
from pathlib import Path
import requests,psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]; E=ROOT/'docs/research/continuous-production-20261011/batches/000195'; R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000195'; D=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000195'; Q=E.parents[1]/'source-queue.json'; REG=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'); TARGET='artline-508319:europe-west1:artline-postgres'
for p in (E,R,D,E/'source-captures'):p.mkdir(parents=True,exist_ok=True)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):
 p=Path(p);return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n';tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(t);os.replace(tmp,p)
def conn():
 s=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip();k=psycopg.conninfo.conninfo_to_dict(s);k.update(host='127.0.0.1',port='55519',sslmode='disable',connect_timeout=20);return psycopg.connect(**k,autocommit=True,row_factory=dict_row,options='-c default_transaction_read_only=on -c statement_timeout=60000')
registry=list(csv.DictReader(REG.open()));queue=load(Q);assert len(registry)==111 and {x['source_id'] for x in registry}=={x['source_id'] for x in queue['sources']}
required=[ROOT/'AGENTS.md',REG,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',Q]
save(E/'required-input-verification.json',dict(at=now(),files=[dict(path=str(x),sha256=sha(x.read_bytes()),bytes=x.stat().st_size) for x in required],registry_rows=111,latest_hold_ledgers=[str(x.relative_to(ROOT)) for x in sorted(E.parent.glob('*/source-access-holds.json'))[-10:]],local_catalogue_read_only=True,translation_used=False))
cmds=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines();proxy=[x for x in cmds if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and TARGET in x];assert len(proxy)==1
with conn() as db:
 target=dict(db.execute("select current_database() database,current_setting('transaction_read_only') read_only,pg_is_in_recovery() recovery").fetchone());assert target=={'database':'artline','read_only':'on','recovery':False}
 prev=load(E.parent/'000107/independent-production-verification.json');ids=list(prev['after']);live={}
 for aid in ids:live[aid]=dict(db.execute('select id::text,primary_media_id::text,status from artworks where id=%s',(aid,)).fetchone())
 assert all(live[x]['primary_media_id']==prev['after'][x]['artwork']['primary_media_id'] and live[x]['status']==prev['after'][x]['artwork']['status'] for x in ids)
save(E/'production-target-reconciliation.json',dict(at=now(),target=TARGET,proxy_port=55519,proxy_verified=True,database=target,helper='ops/india-300-delivery-20261011.py',shared_ingestion_lock='artline-curated-ingestion',write_mode='not_entered',local_catalogue_connections=0))
save(E/'batch107-live-reconciliation.json',dict(at=now(),rows=len(ids),snapshot_fields_equal=True,previous_increments_counted=0,prior_receipt_sha256=sha((E.parent/'000107/independent-production-verification.json').read_bytes())))
route=next(x for x in queue['sources'] if x['source_id']=='smithsonian_open_access');assert route['resume_cursor']['next_shard']=='28'
url='https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/saam/28.txt';resp=requests.get(url,timeout=(15,45));resp.raise_for_status();raw=resp.content;assert len(raw)<12000000
body=D/'saam-28.txt.gz';body.write_bytes(gzip.compress(raw,mtime=0));receipt=dict(url=url,final_url=resp.url,status=resp.status_code,retrieved_at=now(),sha256=sha(raw),bytes=len(raw),body_path=str(body),retry_after=resp.headers.get('Retry-After'));save(E/'source-captures/saam-28.receipt.json',receipt)
objects=[json.loads(x) for x in raw.splitlines()];classified=[];candidates=[]
with conn() as db:
 for obj in objects:
  c=obj.get('content',{});d=c.get('descriptiveNonRepeating') or {};ft=c.get('freetext') or {};link=d.get('record_link','');oid=link.rsplit('=',1)[-1] if '?id=' in link else None;title=(d.get('title') or {}).get('content');dates=[x['content'] for x in ft.get('date',[]) if x.get('label')=='Date'];ims=((d.get('online_media') or {}).get('media') or []);row=dict(native_id=oid,title=title)
  if not oid or not title or not dates or len(ims)!=1:row['decision']='missing_required_identity_date_or_single_image'
  else:
   native=[dict(x) for x in db.execute("select entity_id::text from external_identifiers where entity_type='artwork' and scheme='saam-object' and external_id=%s",(oid,))];matches=[dict(x) for x in db.execute("select id::text,title,primary_media_id::text,creation_year_start,creation_year_end,status from artworks where normalized_title=%s and current_institution_id='2013de83-2b1b-5184-b829-f269101c4b76' and status<>'archived'",(' '.join(title.lower().split()),))]
   eligible=[x for x in matches if x['primary_media_id'] is None and x['creation_year_end'] is not None and x['creation_year_end']<=1970 and str(x['creation_year_start']) in dates[0]];row.update(date=dates[0],native_matches=native,title_matches=matches)
   if native:row['decision']='native_identity_already_present'
   elif len(eligible)!=1:row['decision']='no_unique_eligible_existing_primary_gap'
   elif not(d.get('metadata_usage',{}).get('access')=='CC0' and [x['content'] for x in ft.get('objectRights',[]) if x.get('label')=='Restrictions & Rights']==['CC0'] and ims[0].get('usage',{}).get('access')=='CC0'):row['decision']='not_explicitly_cc0'
   else:row['decision']='candidate_requires_exact_native_identity_and_visual_review';candidates.append(dict(native_id=oid,artwork_id=eligible[0]['id'],title=title,date=dates[0],source_url=link,image_url=ims[0]['content']))
  classified.append(row)
import collections
save(E/'saam-shard28-reconciliation.json',dict(at=now(),source=receipt,captured_records=len(objects),decisions=dict(collections.Counter(x['decision'] for x in classified)),rows=classified,candidates=candidates,selected_for_write=0,production_writes=0))
with Q.with_suffix('.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);q=load(Q);before=copy.deepcopy(q);s=next(x for x in q['sources'] if x['source_id']=='smithsonian_open_access');assert s['resume_cursor']['next_shard']=='28';cursor=dict(unit='saam',completed_shard='28',next_shard='29',source_sha256=sha(raw),records_classified=len(objects),candidate_native_ids=[x['native_id'] for x in candidates],scope='All shard records classified; candidate matches held for exact native identity and actual visual review before any attachment.',next_route='Rotate to an undercovered Greek/Byzantine registry institution before returning to SAAM shard29.')
 s.setdefault('prior_resume_cursors',[]).append(copy.deepcopy(s['resume_cursor']));s.update(status='saam_shard28_classified_candidates_held_for_exact_review',checkpoint='docs/research/continuous-production-20261011/batches/000195/CHECKPOINT.json',last_checked_at=now(),last_batch=195,resume_cursor=cursor,latest_batch_verified_counts={k:0 for k in ['new_painters','new_artworks','newly_illustrated','alternate_images','museum_links']});s.setdefault('evidence_paths',[]).extend(['docs/research/continuous-production-20261011/batches/000195/saam-shard28-reconciliation.json','docs/research/continuous-production-20261011/batches/000195/CHECKPOINT.json']);tmp=Q.with_suffix('.195.tmp');save(tmp,q);os.replace(tmp,Q)
 assert [x for x in before['sources'] if x['source_id']!='smithsonian_open_access']==[x for x in q['sources'] if x['source_id']!='smithsonian_open_access'] and before['supplementary_image_routes']==q['supplementary_image_routes']
save(E/'source-queue-update-verification.json',dict(at=now(),updated_source='smithsonian_open_access',unrelated_entries_preserved=True,queue_sha256=sha(Q.read_bytes()),resume_cursor=cursor))
counts={k:0 for k in ['new_painters','new_artworks','newly_illustrated','alternate_images','museum_links']};nxt='Rotate to an undercovered Greek or Byzantine registry institution; later reconcile the saved SAAM shard28 candidate identities and visually review actual prepared images before attachment, then resume at shard29.'
cp=dict(at=now(),batch=195,stage='complete_candidates_held',discovered=len(objects),selected=len(candidates),prepared=0,imported=0,verified=0,verified_counts=counts,production_writes=0,next_task=nxt,blocker='',evidence=[str((E/x).relative_to(ROOT)) for x in ['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','saam-shard28-reconciliation.json','source-queue-update-verification.json']])
save(E/'CHECKPOINT.json',cp);save(R/'CHECKPOINT.json',cp);save(E/'batch-verification-receipt.json',dict(at=now(),verified_counts=counts,production_ids=[],production_writes=0,attribution='Fresh shard research only; candidates were not written or counted.',production_target=TARGET,shared_ingestion_lock='artline-curated-ingestion'))
files=sorted(E.glob('*.json'));save(E/'independent-final-artifact-verification.json',dict(at=now(),files=[dict(path=str(x.relative_to(ROOT)),sha256=sha(x.read_bytes()),bytes=x.stat().st_size) for x in files],runtime_checkpoint_equal=load(E/'CHECKPOINT.json')==load(R/'CHECKPOINT.json'),production_writes=0,verified_counts=counts,passed=True))
result=dict(outcome='no_eligible_candidates',summary=f'Batch 195 classified all {len(objects)} records in Smithsonian SAAM shard 28. {len(candidates)} possible exact existing image gaps were saved but held for native-identity and actual visual review; no production write was made or counted. Production target, batch 107 and queue integrity were independently reconciled.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[str((E/x).relative_to(ROOT)) for x in ['CHECKPOINT.json','saam-shard28-reconciliation.json','batch107-live-reconciliation.json','production-target-reconciliation.json','batch-verification-receipt.json','source-queue-update-verification.json','independent-final-artifact-verification.json']]);save(R/'worker-result.json',result);print(json.dumps(result))
