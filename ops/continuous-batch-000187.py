#!/usr/bin/env python3
"""Batch 187: reconcile exhausted French reserve, then rotate to Tretyakov discovery."""
import copy,csv,datetime,fcntl,gzip,hashlib,json,os,subprocess,urllib.request
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000187'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000187'
Q=E.parents[1]/'source-queue.json'
REG=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
URL='https://my.tretyakov.ru/app/masterpiece'
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def load(p):
 p=Path(p); return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n')
def connect():
 secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
 kw=psycopg.conninfo.conninfo_to_dict(secret);kw.update(host='127.0.0.1',port='55519',sslmode='disable',connect_timeout=20)
 return psycopg.connect(**kw,autocommit=True,row_factory=dict_row,options='-c default_transaction_read_only=on -c statement_timeout=60000')

E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True)
required=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
registry=list(csv.DictReader(REG.open()));assert len(registry)==111
save(E/'required-input-verification.json',dict(at=now(),files=[dict(path=p,sha256=sha((ROOT/p).read_bytes()),bytes=(ROOT/p).stat().st_size) for p in required],registry=dict(path=str(REG),sha256=sha(REG.read_bytes()),rows=len(registry)),latest_hold_ledgers=[str(p.relative_to(ROOT)) for p in sorted(E.parent.glob('*/source-access-holds.json'))[-10:]],precedence='Current batch instructions and production authorization applied; local catalogue read-only; Translation prohibited.'))
helper=ROOT/'ops/india-300-delivery-20261011.py';proxy=subprocess.check_output(['ps','aux'],text=True);pline=next(x for x in proxy.splitlines() if '/tmp/artline-cloud-sql-proxy' in x and '--port 55519' in x);assert 'artline-508319:europe-west1:artline-postgres' in pline
planp=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';plan=load(planp);rows=plan['rows'];assert len(rows)==188
prior=load(E.parent/'000043/independent-french-reserve-evidence-verification.json');assert len(prior['records'])==188
with connect() as db:
 target=db.execute("select current_database() db,current_setting('transaction_read_only') read_only").fetchone();assert target['db']=='artline' and target['read_only']=='on'
 ids=[r['artwork_id'] for r in rows]
 live=[dict(x) for x in db.execute("select id::text,title,accession_number,primary_media_id::text,status from artworks where id=any(%s::uuid[]) order by id",(ids,))]
 cites=[dict(x) for x in db.execute("select entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 from citations where entity_type='artwork' and entity_id=any(%s::uuid[]) and field_name='french_printmaking_source_identity' order by entity_id",(ids,))]
 assert len(live)==len(cites)==188 and all(x['primary_media_id'] and x['status']!='archived' for x in live)
 assert all(x['plan_sha256']==sha(planp.read_bytes()) for x in cites)
save(E/'production-target-reconciliation.json',dict(at=now(),proxy=dict(port=55519,target='artline-508319:europe-west1:artline-postgres',verified=True),database=target,helper=dict(path=str(helper.relative_to(ROOT)),sha256=sha(helper.read_bytes())),shared_lock='artline-curated-ingestion',write_mode='not_entered_no_candidates',local_catalogue_connections=0))
save(E/'french-reserve-live-reconciliation.json',dict(at=now(),inspected=188,already_imported_and_illustrated=188,genuinely_unimported=0,selected=0,production_rows=live,source_citations=cites,immutable_plan_sha256=sha(planp.read_bytes()),prior_visual_evidence_path='docs/research/continuous-production-20261011/batches/000043/independent-french-reserve-evidence-verification.json',prior_visual_evidence_sha256=sha((E.parent/'000043/independent-french-reserve-evidence-verification.json').read_bytes()),prior_review_reused_without_new_view_claim=True,holds_preserved=['80082','80437','81054'],new_programme_increments=0))
req=urllib.request.Request(URL,headers={'User-Agent':'ArtlineResearch/1.0'})
with urllib.request.urlopen(req,timeout=45) as res: body=res.read();status=res.status;ctype=res.headers.get('Content-Type');etag=res.headers.get('ETag')
cap=R/'tretyakov-masterpiece-index.html.gz';cap.write_bytes(gzip.compress(body))
completed=set(next(x for x in load(Q)['sources'] if x['source_id']=='tretyakov_gallery')['resume_cursor']['completed_source_ids'])
save(E/'independent-source-verification.json',dict(at=now(),provider='tretyakov_gallery',url=URL,status=status,content_type=ctype,etag=etag,bytes=len(body),sha256=sha(body),capture_path=str(cap),capture_sha256=sha(cap.read_bytes()),server_rendered_payload='window.__NUXT__=' in body.decode('utf-8','replace'),previously_completed_ids_confirmed=sorted(x for x in completed if x.encode() in body),registry_policy=dict(ingestion_mode='manual_review',automated_image_download='never',image_rights='rights-managed unless explicitly released'),objects_selected=0,images_requested=0,production_writes=0,limitation='The 25.8 MB minified positional SSR payload is a discovery index, not yet a safely parsed object-level selection. No title/date/creator relationships inferred from positional tokens.'))
with open(str(Q)+'.lock','w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);q=load(Q);before=copy.deepcopy(q);route=next(x for x in q['sources'] if x['source_id']=='tretyakov_gallery');route['status']='official_masterpiece_index_refreshed_structured_extraction_pending';route['checkpoint']='docs/research/continuous-production-20261011/batches/000187/CHECKPOINT.json';route['last_checked_at']=now();route['evidence_paths']=list(dict.fromkeys(route.get('evidence_paths',[])+['docs/research/continuous-production-20261011/batches/000187/independent-source-verification.json','docs/research/continuous-production-20261011/batches/000187/french-reserve-live-reconciliation.json']));route['resume_cursor']['next_route']='official_masterpiece_SSR_structured_extraction';route['resume_cursor']['index_sha256']=sha(body);route['resume_cursor']['next_step']='Parse the captured SSR payload with the pinned Nuxt schema, select a bounded next icon/object shard excluding all completed and held IDs, then fetch individual official records. Do not download Tretyakov images.';tmp=Q.with_suffix('.187.tmp');save(tmp,q);os.replace(tmp,Q)
save(E/'source-queue-update-verification.json',dict(at=now(),source_id='tretyakov_gallery',before_sha256=sha(json.dumps(before,sort_keys=True).encode()),after_sha256=sha(json.dumps(q,sort_keys=True).encode()),unrelated_entries_preserved=all(a==b for a,b in zip(before['sources'],q['sources']) if a['source_id']!='tretyakov_gallery'),resume_cursor=route['resume_cursor']))
counts={k:0 for k in ['new_painters','new_artworks','newly_illustrated','alternate_images','museum_links']};nxt='Parse the checksum-pinned Tretyakov SSR capture with its exact Nuxt schema and inspect a bounded next icon shard, excluding the 20 completed/held IDs; metadata only unless an image is explicitly released.'
cp=dict(at=now(),batch=187,stage='complete_no_eligible_candidates',discovered=188,selected=0,prepared=0,imported=0,verified_counts=counts,holds=dict(french_reserve_already_imported=188,tretyakov_structured_extraction_pending=True),next_task=nxt,blocker='',evidence=[str((E/x).relative_to(ROOT)) for x in ['required-input-verification.json','production-target-reconciliation.json','french-reserve-live-reconciliation.json','independent-source-verification.json','source-queue-update-verification.json']])
save(E/'CHECKPOINT.json',cp);save(E/'batch-verification-receipt.json',cp);save(R/'CHECKPOINT.json',cp)
files=[p for p in sorted(E.glob('*.json')) if p.name!='independent-final-artifact-verification.json'];save(E/'independent-final-artifact-verification.json',dict(at=now(),files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p.read_bytes())) for p in files],runtime_checkpoint_equal=load(E/'CHECKPOINT.json')==load(R/'CHECKPOINT.json'),production_writes=0,verified_counts=counts))
result=dict(outcome='no_eligible_candidates',summary='All 188 French reserve records are already live and illustrated with their checksum-bound citations, so replay was excluded. Rotated to Tretyakov: refreshed and checksum-pinned the official index, but its minified positional SSR payload requires schema-safe extraction before new object selection; no unsafe inference or write was made.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=cp['evidence']+[str((E/'batch-verification-receipt.json').relative_to(ROOT)),str((E/'independent-final-artifact-verification.json').relative_to(ROOT)),str((E/'CHECKPOINT.json').relative_to(ROOT))]);save(R/'worker-result.json',result);print(json.dumps(result))
