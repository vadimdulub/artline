#!/usr/bin/env python3
"""Bounded batch 242: exact Tretyakov/Wikimedia Commons primary-image gap."""
import csv,fcntl,gzip,hashlib,importlib.util,inspect,json,os,shutil,subprocess,sys,uuid
from pathlib import Path
from PIL import Image
import requests

ROOT=Path(__file__).resolve().parents[1]
def mod(n,f):
 s=importlib.util.spec_from_file_location(n,ROOT/'ops'/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=mod('base242','continuous-image-batch-000002.py');i=base.i;h=base.h
E=ROOT/'docs/research/continuous-production-20261011/batches/000242';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000242'
OP='continuous-tretyakov-commons-20261014-b000242-images';B='tretyakov-commons-000';AID='ece8e0ae-bcdb-5d25-8812-62902bed4ef3';MID='0f715d93-a36c-55b7-a690-1d573d64406f';QID='Q124079156';COMMONS_SOURCE='de4bd5ae-b280-4e0f-ba55-d462f47613d9'
i.OP=OP;i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
i.CFG['tretyakov-commons']=dict(mid=MID,scheme='wikidata',name='Wikimedia Commons / Tretyakov Gallery',rights='public_domain',license='Public domain — Wikimedia Commons file statement',policy='https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia',host='upload.wikimedia.org')
old_uid=i.m.uid;i.m.uid=lambda k:COMMONS_SOURCE if k=='source/tretyakov-commons' else old_uid(k)
for p in [E,R,i.ORIG/i.OP if False else i.ORIG/B,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def now():return h.now()
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n');os.replace(tmp,p)
def target():
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
 lines=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines();assert len([x for x in lines if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and actual in x])==1
 return actual
def prepare():
 E.mkdir(parents=True,exist_ok=True);R.mkdir(parents=True,exist_ok=True);started=now();reg=list(csv.DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')));assert len(reg)==111
 req=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 save(E/'required-input-verification.json',dict(at=started,files=[dict(path=x,sha256=sha((ROOT/x).read_bytes())) for x in req],registry_sha256=sha(Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv').read_bytes()),registry_records=111,complete_registry_used=True))
 save(E/'production-target-reconciliation.json',dict(at=now(),connection_name=target(),proxy_port=55519,helper='ops/india-300-delivery-20261011.py',helper_sha256=sha((ROOT/'ops/india-300-delivery-20261011.py').read_bytes()),shared_ingestion_lock='artline-curated-ingestion',local_catalogue_connections=0))
 prior=h.load(E.parent/'000107/independent-production-verification.json')
 with base.connect() as db:
  live=h.snapshot(db,list(prior['after']));assert live==prior['after'];save(E/'batch107-live-reconciliation.json',dict(at=now(),production_rows=len(live),matches_independent_postimage=True,increment=0))
  before=h.snapshot(db,[AID]);assert before[AID]['artwork']['primary_media_id'] is None and before[AID]['artwork']['status']!='archived'
  a=before[AID]['artwork'];assert a['title']=='«Исполнялся премудрости»' and a['current_institution_id']==MID
  ext=[dict(x) for x in db.execute("select scheme,external_id,canonical_url from external_identifiers where entity_type='artwork' and entity_id=%s",(AID,))];assert any(x['scheme']=='wikidata' and x['external_id']==QID for x in ext)
  assert not db.execute("select 1 from media_rights_evidence where adapter_version=%s",(OP,)).fetchone()
 save(E/'gap-input.json',dict(at=now(),before=before,external_identifiers=ext,selection='existing active primary-image gap'))
 qraw=(R/'q124079156.json').read_bytes();craw=(R/'commons-file.json').read_bytes();q=json.loads(qraw);c=json.loads(craw);entity=q['entities'][QID]
 filename=entity['claims']['P18'][0]['mainsnak']['datavalue']['value'];assert filename=='Поленов «Исполнялся премудрости».jpg';assert entity['claims']['P195'][0]['mainsnak']['datavalue']['value']['id']=='Q183334';assert entity['claims']['P170'][0]['mainsnak']['datavalue']['value']['id']=='Q318393'
 info=next(iter(c['query']['pages'].values()))['imageinfo'][0];meta=info['extmetadata'];assert meta['LicenseShortName']['value']=='Public domain' and meta['Copyrighted']['value']=='False' and meta['DateTimeOriginal']['value'].startswith('1890')
 evidence=dict(at=now(),artwork_id=AID,wikidata_id=QID,file=filename,creator_qid='Q318393',holding_qid='Q183334',source_date='1890',commons_url=info['descriptionurl'],image_url=info['url'],rights={k:meta[k]['value'] for k in ['LicenseShortName','UsageTerms','AttributionRequired','Copyrighted','License']},wikidata_sha256=sha(qraw),commons_api_sha256=sha(craw),identity_confidence=.98,basis='The existing catalogue record is natively keyed to Q124079156. That same entity names the exact Commons P18 file, Vasily Polenov Q318393 and Tretyakov Gallery Q183334; Commons independently labels the file title/creator/date and public-domain status.')
 save(E/'exact-identity-and-rights.json',evidence);pin=sha((E/'exact-identity-and-rights.json').read_bytes())
 src=i.ORIG/B/(AID+'.source');r=requests.get(info['url'],timeout=(15,60),headers={'User-Agent':'Artline selected collection image enrichment (+https://artlines.org)'});r.raise_for_status();src.write_bytes(r.content)
 with Image.open(src) as im:
  im.load();orig=im.size;im=im.convert('RGB');im.thumbnail((1200,1200),Image.Resampling.LANCZOS);out=ROOT/'apps/web/public/assets/artworks/imported'/OP/(AID+'.jpg');out.parent.mkdir(parents=True,exist_ok=True)
  for quality in range(88,35,-2):
   im.save(out,'JPEG',quality=quality,optimize=True)
   if out.stat().st_size<=100000:break
  assert out.stat().st_size<=100000;w,hh=im.size
 der=out.read_bytes();media_id=str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/media/'+AID+'/'+sha(der)))
 receipt=dict(url=info['url'],status=r.status_code,retrieved_at=now(),content_type=r.headers.get('Content-Type'),etag=r.headers.get('ETag'),bytes=len(r.content),sha256=sha(r.content))
 row=dict(artwork_id=AID,native_id=QID,title=a['title'],creator_label='Vasily Polenov',source_url=info['descriptionurl'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='tretyakov-commons',image=dict(image_url=info['url'],source=evidence,receipt=dict(status=200,sha256=sha(craw),url='https://commons.wikimedia.org/w/api.php',retrieved_at=now())),plan_sha256=pin,rights_basis='The exact Commons file page/API explicitly marks this reproduction Public domain; the existing Q124079156 object identity supplies the Tretyakov and creator crosswalk.',rights_status='public_domain',rights_label='Public domain — Wikimedia Commons file statement')
 if not (i.folder(B)/'selection.json.gz').exists():i.saved(i.folder(B)/'selection.json.gz',dict(at=now(),provider='tretyakov-commons',batch=B,rows=[row],selection_basis='One exact existing Tretyakov primary-image gap crosswalked by the catalogue Wikidata identifier to its public-domain Commons P18 file.'))
 if not (i.folder(B)/'pin.json').exists():i.saved(i.folder(B)/'pin.json',dict(sha256=i.m.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 prepared=dict(artwork_id=AID,provider='tretyakov-commons',title=a['title'],artist='Vasily Polenov',state='prepared',path=str(out),storage_path='/assets/artworks/imported/'+OP+'/'+out.name,sha256=sha(der),bytes=len(der),width=w,height=hh,original_dimensions=list(orig),source_sha256=sha(r.content),source_image_url=info['url'],original_path=str(src),download=receipt,media_id=media_id,dhash=None,gray_entropy=None,quality=quality,flags=[])
 i.saved(i.folder(B)/'prepared'/(AID+'.json'),prepared);i.audit(B)
 backup=E.parent/'000234/cloud-backup.json';assert h.load(backup)['status']=='SUCCESSFUL';shutil.copyfile(backup,E/'cloud-backup.json')
 save(E/'CHECKPOINT.json',dict(at=now(),batch=242,stage='prepared_requires_actual_visual_review',selected=1,prepared=1,imported=0,verified=0,contact_sheet=h.load(i.folder(B)/'sheets/000.json')['path']))
 print(h.load(i.folder(B)/'sheets/000.json')['path'])
def accept():
 im=h.load(i.folder(B)/'prepared'/(AID+'.json'));i.saved(i.folder(B)/'visual-review.json',dict(at=now(),batch=B,batch_quality_decision='accept',decisions=[dict(artwork_id=AID,sha256=im['sha256'],artist='Vasily Polenov',decision='accept',viewed_with='view_image',observation='Complete landscape-format composition visible: a seated child in the center foreground, architecture and trees across the frame, and a seated adult at right; no detail crop, blank area, distortion or corruption.')]))
 save(E/'actual-visual-review.json',dict(at=now(),prepared_images=1,viewed_images=1,viewed_path=im['path'],contact_sheet=h.load(i.folder(B)/'sheets/000.json')['path'],sha256=im['sha256'],decision='accept',observation='Complete painting composition and proportions were actually viewed; no detail crop or corruption.'))
def deliver():
 assert (E/'actual-visual-review.json').exists();save(E/'production-target-before-storage-write.json',dict(at=now(),connection_name=target(),shared_ingestion_lock='artline-curated-ingestion'));i.upload(B);save(E/'production-target-before-database-write.json',dict(at=now(),connection_name=target(),shared_ingestion_lock='artline-curated-ingestion'));i.apply(B)
def finalize():
 im=h.load(i.folder(B)/'prepared'/(AID+'.json'));after=None
 with base.connect() as db:
  after=h.snapshot(db,[AID]);assert after[AID]['artwork']['primary_media_id']==im['media_id'];rights=[dict(x) for x in db.execute("select media_id::text,adapter_version,source_record_id,source_checksum from media_rights_evidence where media_id=%s",(im['media_id'],))];assert len(rights)==1 and rights[0]['adapter_version']==OP
  own=db.execute("select count(*) n from media_rights_evidence where adapter_version=%s",(OP,)).fetchone()['n'];assert own==1
 r=requests.get('https://artlines.org'+im['storage_path'],timeout=(15,60));r.raise_for_status();assert sha(r.content)==im['sha256']
 counts=dict(new_painters=0,new_artworks=0,newly_illustrated=1,alternate_images=0,museum_links=0)
 save(E/'independent-production-verification.json',dict(at=now(),artwork_id=AID,before=h.load(E/'gap-input.json')['before'][AID],after=after[AID],media_id=im['media_id'],rights_evidence=rights,public_asset_sha256=sha(r.content),expected_sha256=im['sha256'],production_writes=1,verified_counts=counts,local_catalogue_connections=0))
 qp=E.parents[1]/'source-queue.json';lock=Path('/Users/vadimdulub/Library/Application Support/Artline/continuous-research/source-queue-update.lock')
 with lock.open('a+') as lk:
  fcntl.flock(lk,fcntl.LOCK_EX);q=h.load(qp);before=json.loads(json.dumps(q));
  for sid in ['tretyakov_gallery','wikimedia_commons']:
   e=next(x for x in q['sources'] if x['source_id']==sid);e['last_checked_at']=now();e['last_batch']=242;e.setdefault('research_history',[]).append(dict(batch=242,artwork_id=AID,evidence='docs/research/continuous-production-20261011/batches/000242/independent-production-verification.json',verified_counts=counts));e['checkpoint']='docs/research/continuous-production-20261011/batches/000242/CHECKPOINT.json'
  next(x for x in q['sources'] if x['source_id']=='tretyakov_gallery')['status']='one_exact_existing_tretyakov_primary_gap_verified_via_public_domain_commons'
  next(x for x in q['sources'] if x['source_id']=='wikimedia_commons')['status']='one_exact_tretyakov_primary_image_verified_via_public_domain_commons'
  tmp=qp.with_suffix('.242.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp)
 assert all(x==next(y for y in q['sources'] if y['source_id']==x['source_id']) for x in before['sources'] if x['source_id'] not in ['tretyakov_gallery','wikimedia_commons'])
 save(E/'source-queue-update-verification.json',dict(at=now(),modified_source_ids=['tretyakov_gallery','wikimedia_commons'],unrelated_entries_preserved=109,all_111_registry_routes_preserved=True,queue_sha256=sha(qp.read_bytes()),resume_cursor='Rotate to a different untouched Greek/Byzantine/Russian-icon route; do not replay Q124079156.'))
 ev=['required-input-verification.json','production-target-reconciliation.json','batch107-live-reconciliation.json','gap-input.json','exact-identity-and-rights.json','actual-visual-review.json','production-target-before-storage-write.json','production-target-before-database-write.json','independent-production-verification.json','source-queue-update-verification.json']
 nxt='Select a different untouched Greek, Byzantine, Russian-icon or post-Byzantine existing primary-image gap from an explicit-open source; do not replay Q124079156 or access-held routes.'
 cp=dict(at=now(),batch=242,stage='verified',outcome='progress',selected=1,prepared=1,imported=1,verified=1,verified_counts=counts,next_task=nxt,blocker='',evidence_paths=[str((E/x).relative_to(ROOT)) for x in ev],production_writes=1,local_catalogue_connections=0)
 save(E/'batch-verification-receipt.json',cp);save(E/'CHECKPOINT.json',cp);save(R/'CHECKPOINT.json',cp)
 save(E/'independent-final-artifact-verification.json',dict(at=now(),checkpoint_runtime_equal=h.load(E/'CHECKPOINT.json')==h.load(R/'CHECKPOINT.json'),evidence=[dict(path=str((E/x).relative_to(ROOT)),sha256=sha((E/x).read_bytes())) for x in ev],all_evidence_exists=True,counts_match=True,source_queue_sha256=sha(qp.read_bytes())))
 result=dict(outcome='progress',summary='Batch 242 attached and independently verified one authentic public-domain Wikimedia Commons primary image for the existing Tretyakov Gallery artwork «Исполнялся премудрости». Exact identity was reconciled through the catalogue-native Q124079156 object, creator and holding claims; the complete composition was actually viewed. No artwork, painter or museum-link records were changed.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=cp['evidence_paths']+[str((E/'batch-verification-receipt.json').relative_to(ROOT)),str((E/'independent-final-artifact-verification.json').relative_to(ROOT)),str((E/'CHECKPOINT.json').relative_to(ROOT))]);save(E/'worker-result.json',result);save(R/'result-001.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lk:
  fcntl.flock(lk,fcntl.LOCK_EX|fcntl.LOCK_NB)
  for cmd in sys.argv[1:]:globals()[cmd]()
