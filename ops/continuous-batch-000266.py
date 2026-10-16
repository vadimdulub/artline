#!/usr/bin/env python3
"""Batch 266: bounded fresh MIA primary-gap research after the saved cursor."""
import copy,csv,fcntl,gzip,hashlib,importlib.util,json,os,subprocess
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=module('delivery','india-300-delivery-20261011.py'); mia=module('mia','overnight-mia-images.py')
E=ROOT/'docs/research/continuous-production-20261011/batches/000266';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000266'
MID='9d7ff4ab-bbef-5ecc-836c-f7ed18b6bda9'; TARGET='artline-508319:europe-west1:artline-postgres'; AFTER='d8b208da-624b-4729-b97a-f9ee04208daa'
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);b=json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n';t=p.with_suffix(p.suffix+'.tmp');t.write_text(b);os.replace(t,p)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def target():
 cmds=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines();px=[x for x in cmds if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and TARGET in x];assert len(px)==1
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual==TARGET
 with h.connect() as db:s=dict(db.execute('select current_database() database,pg_is_in_recovery() recovery').fetchone())
 assert s=={'database':'artline','recovery':False};save(E/'production-target-reconciliation.json',{'at':h.now(),'connection_name':actual,'proxy_port':55519,'proxy_command_verified':True,'database':s,'helper':'ops/india-300-delivery-20261011.py','helper_sha256':sha(ROOT/'ops/india-300-delivery-20261011.py'),'shared_ingestion_lock':'artline-curated-ingestion','write_transaction_entered':False,'local_catalogue_connections':0})
def main():
 E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True);started=h.now();target()
 reg=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');assert len(list(csv.DictReader(reg.open())))==111
 qp=E.parents[1]/'source-queue.json'; required=[ROOT/'AGENTS.md',reg,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',qp]
 holds=sorted(E.parent.glob('*/**/*hold*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:10]
 save(E/'required-input-verification.json',{'at':h.now(),'files':[{'path':str(p),'sha256':sha(p)} for p in required],'registry_rows':111,'latest_hold_ledgers':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in holds],'real_local_catalogue_read_only':True})
 p107=E.parent/'000107/independent-production-verification.json';v107=h.load(p107)
 with h.connect() as db:live=h.snapshot(db,list(v107['after']))
 assert live==v107['after'];save(E/'batch107-live-reconciliation.json',{'at':h.now(),'rows':len(live),'matches_independent_postimage':True,'increment':0})
 with h.connect() as db:
  rows=[dict(x) for x in db.execute(mia.QUERY+" AND a.current_institution_id=%s AND a.primary_media_id IS NULL AND a.creation_year_end<=1955 AND a.id>%s::uuid ORDER BY a.id LIMIT 25",(MID,AFTER))]
 sess=requests.Session();sess.headers['User-Agent']='Artline research contact research@artline.art'
 checks=[];eligible=[];fail=[]
 for a in rows:
  native=a['external_id'];url='https://search.artsmia.org/id/'+native
  try:r=sess.get(url,timeout=(15,40))
  except Exception as exc:fail.append({'native_id':native,'kind':'transient_error','error':type(exc).__name__});continue
  raw=r.content;bp=E/'source-captures'/f'{native}.body.gz';bp.parent.mkdir(parents=True,exist_ok=True);bp.write_bytes(gzip.compress(raw,mtime=0));save(E/'source-captures'/f'{native}.receipt.json',{'at':h.now(),'url':url,'status':r.status_code,'sha256':h.sha(raw),'bytes':len(raw),'body_path':str(bp.relative_to(ROOT)),'retry_after':r.headers.get('Retry-After')})
  if r.status_code in (401,403,429):fail.append({'native_id':native,'kind':'access_hold','status':r.status_code});break
  r.raise_for_status();d=r.json();reason='eligible'
  try:
   if not a['artist']:raise ValueError('Unresolved object-level creator requires anonymous/workshop identity workflow')
   image,facts=mia.source_match(a,d)
   if not image:raise ValueError('Public full image access is not established')
  except ValueError as exc:reason=str(exc)
  rec={'artwork_id':a['artwork_id'],'native_id':native,'title':a['title'],'accession_number':a['accession_number'],'reason':reason,'object_url':'https://collections.artsmia.org/art/'+native,'source_sha256':h.sha(raw)};checks.append(rec)
  if reason=='eligible':eligible.append(dict(rec,image_url=image,rights=d.get('image_copyright') or d.get('rights_type')))
 # The recorded img.artsmia.org 403 is not retried. Eligible metadata is held until the image surface changes.
 save(E/'mia-next-keyset-reconciliation.json',{'at':h.now(),'route':'existing_primary_gaps_native_api','prior_cursor':AFTER,'queried':len(rows),'researched':len(checks),'eligible_metadata':len(eligible),'rows':checks,'eligible':eligible,'failures':fail,'image_requests':0,'decision':'No image-host requests: the provider host has a recorded unchanged HTTP403 hold. No visual claim is made because no image was prepared.','next_cursor':checks[-1]['artwork_id'] if checks else AFTER,'production_writes':0})
 save(E/'actual-visual-review.json',{'at':h.now(),'prepared_images':0,'viewed_images':0,'reviewed_items':[],'claim':'No images were prepared or viewed; file checks are not represented as visual review.','prior_hold':'docs/research/continuous-production-20261011/batches/000019/access-holds/img.artsmia.org.json'})
 counts={k:0 for k in ['new_painters','new_artworks','newly_illustrated','alternate_images','museum_links']};cursor={'route':'existing_primary_gaps_native_api','after_artwork_id':checks[-1]['artwork_id'] if checks else AFTER,'window_queried':len(rows),'window_researched':len(checks),'eligible_held_for_image_surface':len(eligible),'image_surface':'img.artsmia.org','retry_allowed':False}
 with qp.with_suffix('.lock').open('a+') as lk:
  fcntl.flock(lk,fcntl.LOCK_EX);q=h.load(qp);before=copy.deepcopy(q);src=next(x for x in q['sources'] if x['source_id']=='minneapolis_institute_art');src.update(status='next_primary_gap_keyset_researched_image_surface_403_hold_preserved',last_checked_at=h.now(),last_batch=266,checkpoint=str((E/'CHECKPOINT.json').relative_to(ROOT)),resume_cursor=cursor,latest_batch_verified_counts=counts);src['evidence_paths']=src.get('evidence_paths',[])+[str((E/'mia-next-keyset-reconciliation.json').relative_to(ROOT)),str((E/'CHECKPOINT.json').relative_to(ROOT))];src['remaining_gaps']=[f"Batch266 researched {len(checks)} fresh post-cursor production gaps; {len(eligible)} metadata-eligible rows remain held because the native image surface is access-held.",'No image-host retry occurred and no visual review is claimed.','Continue after the saved UUID only after an image-access change, or rotate to an untouched explicit-open route.'];assert [x for x in before['sources'] if x['source_id']!='minneapolis_institute_art']==[x for x in q['sources'] if x['source_id']!='minneapolis_institute_art'];t=qp.with_suffix('.266.tmp');t.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(t,qp)
 save(E/'source-queue-update-verification.json',{'at':h.now(),'updated_source':'minneapolis_institute_art','unrelated_entries_preserved':True,'source_count':len(q['sources']),'resume_cursor':cursor,'queue_sha256':sha(qp)})
 nexttask='Research an untouched registry source with unauthenticated stable object IDs and explicit object-level open-image rights; do not retry the held Minneapolis image host or replay exhausted French records.'
 ev=['production-target-reconciliation.json','required-input-verification.json','batch107-live-reconciliation.json','mia-next-keyset-reconciliation.json','actual-visual-review.json','source-queue-update-verification.json'];cp={'at':h.now(),'batch':266,'stage':'bounded_research_complete_no_safe_image_delivery','researched':len(checks),'selected':len(eligible),'prepared':0,'imported':0,'verified':0,'verified_counts':counts,'next_task':nexttask,'blocker':'','evidence':[str((E/x).relative_to(ROOT)) for x in ev],'production_writes':0,'storage_writes':0,'local_catalogue_connections':0,'started_at':started,'finished_at':h.now()};save(E/'batch-verification-receipt.json',cp);save(E/'CHECKPOINT.json',cp);save(R/'CHECKPOINT.json',cp)
 result={'outcome':'progress','summary':f'Batch 266 researched {len(checks)} fresh Minneapolis primary-image gaps after the saved UUID cursor and reconciled batch 107 plus the production target. {len(eligible)} records passed native metadata identity/rights checks, but no image was requested or attached because the documented img.artsmia.org HTTP403 hold remains in force. No visual inspection is claimed, no production/Storage/local-catalogue writes occurred, and the exact next cursor is persisted.','next_task':nexttask,'blocker':'','verified_counts':counts,'evidence_paths':[str((E/x).relative_to(ROOT)) for x in ['mia-next-keyset-reconciliation.json','actual-visual-review.json','batch107-live-reconciliation.json','production-target-reconciliation.json','source-queue-update-verification.json','batch-verification-receipt.json','CHECKPOINT.json']]};save(E/'worker-result.json',result);save(R/'result-001.json',result);print(json.dumps(result))
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lk:fcntl.flock(lk,fcntl.LOCK_EX|fcntl.LOCK_NB);main()
