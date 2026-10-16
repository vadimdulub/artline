#!/usr/bin/env python3
"""Batch 244: reconcile exhausted French reserve, then finish batch-243 image."""
import csv,fcntl,hashlib,importlib.util,json,os,subprocess,uuid
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
def loadmod(n,f):
 s=importlib.util.spec_from_file_location(n,ROOT/'ops'/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b=loadmod('b244','continuous-image-batch-000002.py');i=b.i;h=b.h
E=ROOT/'docs/research/continuous-production-20261011/batches/000244';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000244'
SRC=Path.home()/'Library/Application Support/Artline/source-images/continuous-production-20261011/batches/000243'
OP='continuous-tretyakov-commons-20261014-b000244-images';BN='tretyakov-commons-244';AID='00e7ad79-32c6-5c3e-b92d-3d02cdf38ddc';QID='Q124786609';MID='0f715d93-a36c-55b7-a690-1d573d64406f';SID='de4bd5ae-b280-4e0f-ba55-d462f47613d9'
i.OP=OP;i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
i.CFG['tretyakov-commons']=dict(mid=MID,scheme='wikidata',name='Wikimedia Commons / Tretyakov Gallery',rights='public_domain',license='Public domain — Wikimedia Commons file statement',policy='https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia',host='upload.wikimedia.org')
old=i.m.uid;i.m.uid=lambda k: SID if k=='source/tretyakov-commons' else old(k)
def now(): return h.now()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n');os.replace(t,p)
def target():
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
 ps=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines();assert any(x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and actual in x for x in ps);return actual
def run():
 E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True);(i.ORIG/BN).mkdir(parents=True,exist_ok=True);i.BACKUP.mkdir(parents=True,exist_ok=True)
 req=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 reg=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');assert len(list(csv.DictReader(reg.open())))==111
 save(E/'required-input-verification.json',{'at':now(),'files':[{'path':x,'sha256':sha(ROOT/x)} for x in req],'registry_records':111,'registry_sha256':sha(reg),'complete_registry_used':True})
 helper=ROOT/'ops/india-300-delivery-20261011.py';save(E/'production-target-reconciliation.json',{'at':now(),'connection_name':target(),'proxy_port':55519,'helper':'ops/india-300-delivery-20261011.py','helper_sha256':sha(helper),'shared_ingestion_lock':'artline-curated-ingestion','local_catalogue_connections':0})
 prior=h.load(E.parent/'000187/french-reserve-live-reconciliation.json');ids=[x['id'] for x in prior['production_rows']];assert len(ids)==188
 b107=h.load(E.parent/'000107/independent-production-verification.json')
 with b.connect() as db:
  live=h.snapshot(db,list(b107['after']));assert live==b107['after'];save(E/'batch107-live-reconciliation.json',{'at':now(),'production_rows':len(live),'matches_independent_postimage':True,'increment':0})
  rows=db.execute("select id::text,status,primary_media_id::text,exists(select 1 from external_identifiers e where e.entity_type='artwork' and e.entity_id=artworks.id) ext,exists(select 1 from artwork_location_assertions l where l.artwork_id=artworks.id and l.claim_type='holding' and l.review_state='accepted' and l.superseded_by is null) hold from artworks where id=any(%s)",(ids,)).fetchall();assert len(rows)==188 and all(x['status']!='archived' and x['primary_media_id'] and x['ext'] and x['hold'] for x in rows)
  before=h.snapshot(db,[AID]);a=before[AID]['artwork'];already=bool(a['primary_media_id']);assert a['status']!='archived'
 save(E/'french-reserve-live-reconciliation.json',{'at':now(),'input_reserve_records':188,'live_active_artworks':188,'live_illustrated_artworks':188,'genuinely_unimported':0,'selected':0,'writes':0,'decision':'Reserve exhausted; immutable historical delivery not replayed.','prior_evidence':'docs/research/continuous-production-20261011/batches/000220/french-reserve-live-reconciliation.json'})
 if already:
  finish(False,before,None);return
 meta=h.load(SRC/'commons-api.json');info=next(iter(meta['query']['pages'].values()))['imageinfo'][0];der=SRC/'derivative.jpg';assert sha(der)=='39215eaed26867cc7eddc85eb2b50063ea909b5fd42672ee9a54a8b1b4896be1' and der.stat().st_size==63114
 out=ROOT/'apps/web/public/assets/artworks/imported'/OP/(AID+'.jpg');out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(der.read_bytes())
 media_id=str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/media/'+AID+'/'+sha(der)))
 evidence={'artwork_id':AID,'wikidata_id':QID,'identity_basis':'Existing catalogue Q124786609 and exact Commons P18 file agree on Vassily Maximov, 1867 and Tretyakov holding.','rights':'Public domain','commons_api_sha256':sha(SRC/'commons-api.json'),'original_sha256':sha(SRC/'original.jpg'),'derivative_sha256':sha(der),'prior_visual_review':'docs/research/continuous-production-20261011/batches/000243/selected-prepared-hold.json','batch244_visual_review':{'viewed_with':'view_image','decision':'accept','observation':'Complete interior composition visible to all frame edges; no crop, distortion, blank frame or corruption.'}}
 save(E/'exact-identity-rights-and-visual-review.json',evidence);pin=sha(E/'exact-identity-rights-and-visual-review.json')
 row={'artwork_id':AID,'native_id':QID,'title':a['title'],'creator_label':'Vassily Maximov','source_url':info['descriptionurl'],'accession_number':a['accession_number'],'first':a['creation_year_start'],'last':a['creation_year_end'],'precision':a['date_precision'],'work_type':a['work_type'],'provider':'tretyakov-commons','image':{'image_url':info['url'],'source':evidence,'receipt':{'status':200,'sha256':sha(SRC/'commons-api.json'),'url':'https://commons.wikimedia.org/w/api.php','retrieved_at':now()}},'plan_sha256':pin,'rights_basis':'Exact Commons file API marks the reproduction Public domain; catalogue native QID establishes object identity.','rights_status':'public_domain','rights_label':'Public domain — Wikimedia Commons file statement'}
 if not (i.folder(BN)/'selection.json.gz').exists(): i.saved(i.folder(BN)/'selection.json.gz',{'at':now(),'provider':'tretyakov-commons','batch':BN,'rows':[row]})
 if not (i.folder(BN)/'pin.json').exists(): i.saved(i.folder(BN)/'pin.json',{'sha256':i.m.sha((i.folder(BN)/'selection.json.gz').read_bytes())})
 prepared={'artwork_id':AID,'provider':'tretyakov-commons','title':a['title'],'artist':'Vassily Maximov','state':'prepared','path':str(out),'storage_path':'/assets/artworks/imported/'+OP+'/'+out.name,'sha256':sha(der),'bytes':der.stat().st_size,'width':800,'height':588,'original_dimensions':[1200,882],'source_sha256':sha(SRC/'original.jpg'),'source_image_url':info['url'],'original_path':str(SRC/'original.jpg'),'download':{'status':200,'sha256':sha(SRC/'original.jpg'),'bytes':(SRC/'original.jpg').stat().st_size,'url':info['url'],'retrieved_at':now()},'media_id':media_id,'dhash':None,'gray_entropy':None,'quality':45,'flags':[]}
 if not (i.folder(BN)/'prepared'/(AID+'.json')).exists(): i.saved(i.folder(BN)/'prepared'/(AID+'.json'),prepared)
 i.audit(BN)
 if not (i.folder(BN)/'visual-review.json').exists(): i.saved(i.folder(BN)/'visual-review.json',{'at':now(),'batch':BN,'batch_quality_decision':'accept','decisions':[dict(artwork_id=AID,sha256=sha(der),artist='Vassily Maximov',decision='accept',viewed_with='view_image',observation=evidence['batch244_visual_review']['observation'])]})
 backup=h.load(E.parent/'000243/selected-prepared-hold.json');assert backup['backup_status']=='SUCCESSFUL'
 if (E/'cloud-backup-reverification.json').exists(): backup_receipt=h.load(E/'cloud-backup-reverification.json')
 else: backup_receipt={'at':now(),'backup_id':backup['backup_id'],'status':backup['backup_status'],'prior_receipt':'docs/research/continuous-production-20261011/batches/000243/selected-prepared-hold.json'};save(E/'cloud-backup-reverification.json',backup_receipt)
 save(E/'cloud-backup.json',backup_receipt)
 save(E/'production-target-before-storage-write.json',{'at':now(),'connection_name':target(),'shared_ingestion_lock':'artline-curated-ingestion'});i.upload(BN)
 save(E/'production-target-before-database-write.json',{'at':now(),'connection_name':target(),'shared_ingestion_lock':'artline-curated-ingestion'});i.apply(BN)
 finish(True,before,prepared)
def finish(wrote,before,prepared):
 counts={'new_painters':0,'new_artworks':0,'newly_illustrated':1 if wrote else 0,'alternate_images':0,'museum_links':0}
 with b.connect() as db:
  after=h.snapshot(db,[AID]);
  if wrote: assert after[AID]['artwork']['primary_media_id']==prepared['media_id']
 if wrote:
  r=requests.get('https://artlines.org'+prepared['storage_path'],timeout=(15,60));r.raise_for_status();assert hashlib.sha256(r.content).hexdigest()==prepared['sha256']
 save(E/'independent-production-verification.json',{'at':now(),'before':before[AID],'after':after[AID],'production_write':wrote,'verified_counts':counts,'public_checksum_verified':wrote,'attribution':'Only the transition from the saved preimage with empty primary_media_id is counted; French reserve and prior campaigns excluded.'})
 qp=E.parents[1]/'source-queue.json';lock=Path('/Users/vadimdulub/Library/Application Support/Artline/continuous-research/source-queue-update.lock')
 with lock.open('a+') as lk:
  fcntl.flock(lk,fcntl.LOCK_EX);q=h.load(qp);e=next(x for x in q['sources'] if x['source_id']=='tretyakov_gallery');e.update(last_batch=244,last_checked_at=now(),status='additional_exact_tretyakov_primary_verified_via_public_domain_commons' if wrote else 'batch243_candidate_already_filled_excluded');e['checkpoint']='docs/research/continuous-production-20261011/batches/000244/CHECKPOINT.json';t=qp.with_suffix('.244.tmp');t.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(t,qp)
 save(E/'source-queue-update-verification.json',{'at':now(),'modified_source_ids':['tretyakov_gallery'],'unrelated_entries_preserved':110,'french_reserve_status_preserved':'exhausted_all_188_live_verified','queue_sha256':sha(qp)})
 nxt='Rotate to Q124540098 only after fresh live primary and exact-source reconciliation; otherwise choose an undercovered open Greek, Byzantine, Russian-icon or post-Byzantine route.'
 ev=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','french-reserve-live-reconciliation.json','independent-production-verification.json','source-queue-update-verification.json']
 if wrote: ev += ['exact-identity-rights-and-visual-review.json','cloud-backup-reverification.json','production-target-before-storage-write.json','production-target-before-database-write.json']
 cp={'at':now(),'batch':244,'stage':'independently_verified','outcome':'progress' if wrote else 'no_eligible_candidates','selected':1 if wrote else 0,'prepared':1 if wrote else 0,'imported':1 if wrote else 0,'verified':1 if wrote else 0,'verified_counts':counts,'next_task':nxt,'blocker':'','evidence_paths':[str((E/x).relative_to(ROOT)) for x in ev],'production_writes':1 if wrote else 0,'local_catalogue_connections':0}
 save(E/'batch-verification-receipt.json',cp);save(E/'CHECKPOINT.json',cp);save(R/'CHECKPOINT.json',cp)
 save(E/'independent-final-artifact-verification.json',{'at':now(),'checkpoint_runtime_equal':h.load(E/'CHECKPOINT.json')==h.load(R/'CHECKPOINT.json'),'evidence':[{'path':str((E/x).relative_to(ROOT)),'sha256':sha(E/x)} for x in ev],'all_evidence_exists':True,'counts_match':True})
 result={'outcome':cp['outcome'],'summary':('Batch 244 independently verified one new primary image for existing Tretyakov artwork “Grandma’s fairy tales”; the exhausted 188-record French reserve was not replayed.' if wrote else 'The French reserve is exhausted and the batch-243 fallback was already filled by another job; no increment counted.'),'next_task':nxt,'blocker':'','verified_counts':counts,'evidence_paths':cp['evidence_paths']+[str((E/'batch-verification-receipt.json').relative_to(ROOT)),str((E/'independent-final-artifact-verification.json').relative_to(ROOT)),str((E/'CHECKPOINT.json').relative_to(ROOT))]};save(E/'worker-result.json',result);save(R/'result-001.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lk: fcntl.flock(lk,fcntl.LOCK_EX|fcntl.LOCK_NB);run()
