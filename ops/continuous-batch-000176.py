#!/usr/bin/env python3
"""One selected NGA/WikiArt image batch. External supervisor remains unchanged."""
import ast,copy,csv,datetime,fcntl,gzip,html,importlib.util,io,json,os,re,subprocess,sys
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base176','continuous-image-batch-000002.py');h=base.h;i=base.i
E=ROOT/'docs/research/continuous-production-20261011/batches/000176'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000176'
B='wikiart-nga-000';OP='continuous-ngaustralia-wikiart-20261013-b000176'
MID='8a40bd5a-e130-57ee-af68-0c921b602c95';TARGET='artline-508319:europe-west1:artline-postgres'
i.OP=OP;i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP;i.CFG['wikiart']['scheme']='nga-australia-object'
for p in [E,R,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(name,value):h.save(E/name,value);return value
def rel(p):return str(Path(p).relative_to(ROOT))
def target(stage):
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual==TARGET
 name='production-target-'+stage+'.json'
 if (E/name).exists():name='production-target-'+stage+'-recheck-'+str(len(list(E.glob('production-target-'+stage+'-recheck-*.json')))+1).zfill(3)+'.json'
 return save(name,dict(base.target(stage.startswith('before-')),connection_name=actual,helper='ops/india-300-delivery-20261011.py',shared_ingestion_lock='artline-curated-ingestion',local_catalogue_connections=0))
def preflight():
 target('reconciliation');reg=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');registry=list(csv.DictReader(reg.open()));queue=h.load(E.parents[1]/'source-queue.json');assert len(registry)==111 and {x['source_id'] for x in registry}=={x['source_id'] for x in queue['sources']}
 paths=[ROOT/'AGENTS.md',reg,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json',ROOT/'docs/research/creators-deep-continuation-20261011/source-registry-review.json']
 for p in paths:p.read_text()
 save('required-input-verification.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in paths],registry_rows=111,complete_original_registry=registry,supplementary_review_not_replacement=True,local_catalogue_connections=0))
 save('source-queue-preimage.json',queue)
 holds=[]
 for p in [E.parent/'000141/source-access-holds.json',E.parent/'000171/research-holds.json',E.parent/'000174/inherited-holds-verification.json',E.parent/'000175/failures-and-holds-final.json']:
  value=h.load(p);holds.append(dict(path=rel(p),sha256=h.sha(p.read_bytes()),read_complete=True))
 relevant=[]
 for p in (ROOT/'docs/research').glob('**/access-holds/*.json'):
  v=h.load(p)
  if 'wikiart' in str(p) or 'wikiart' in json.dumps(v).lower():relevant.append(dict(path=rel(p),sha256=h.sha(p.read_bytes()),data=v))
 save('inherited-holds-verification.json',dict(at=h.now(),files=holds,wikiart_holds=relevant,all111_queue_sources_read=True,store_route_not_requested=True,saam_unchanged=True))
 stop=ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json';h.load(stop)
 save('campaign-stop-preservation.json',dict(at=h.now(),path=rel(stop),sha256=h.sha(stop.read_bytes()),separate_campaign=OP,restarted=False))
 with h.connect() as db:
  prior=h.load(E.parent/'000107/independent-production-verification.json');assert h.snapshot(db,list(prior['after']))==prior['after']
  own=[dict(x) for x in db.execute('SELECT media_id::text,adapter_version,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(OP,))];assert not own or (i.folder(B)/'selection.json.gz').exists(),'Unknown own write must be reconciled'
 save('batch107-live-reconciliation.json',dict(at=h.now(),rows=len(prior['after']),snapshot_equal=True,prior_receipt_sha256=h.sha((E.parent/'000107/independent-production-verification.json').read_bytes()),prior_increments_counted=0))
 save('own-write-reconciliation.json',dict(at=h.now(),previous_own_rows=own,unknown_previous_writes=0))
 holdrows=[]
 for name in ['nga-terms','nga-sample']:
  rc=h.load(E/(name+'-receipt.json'));raw=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==403;holdrows.append(dict(rc,retry_allowed=False))
 save('source-access-holds.json',dict(at=h.now(),museum_surfaces=holdrows,web_tool='Both museum routes inaccessible through web tool; direct requests returned403. No retries.',indigenous_cultural_rights_gate='Original registry ICIP notices remain hard media gates; native records unreviewable and images not selected. Only four named Tom Roberts paintings on independently approved WikiArt selected; no Indigenous-maker records downloaded.',google_services='Cloud SQL, Secret Manager/authentication, existing proxy and Storage only; archived partner captures read locally without any Google Arts & Culture request; Translation not used.'))
 print('Preflight: original111 registry; batch107 live match; distinct campaign; museum403 held; no previous own writes.',flush=True)
def prepare():
 gaps=h.load(E/'gap-input.json.gz');rows=[];proof=[]
 with h.connect() as db:
  for path in sorted((E/'objects').glob('*.json')):
   aid=path.stem;p=h.load(path);live=h.snapshot(db,[aid])[aid];assert live==gaps['before'][aid] and live['artwork']['primary_media_id'] is None;a=live['artwork']
   c=next(c for c in gaps['citations'] if c['entity_id']==aid);note=json.loads(c['evidence_note']);f=note['source_record']['facts'];prior=h.load(E/'prior-source'/(aid+'.json'));obj=prior['object'];cap=obj['capture'];original=ROOT/prior['path'];assert h.sha(original.read_bytes())==prior['sha256'];raw=gzip.decompress((ROOT/cap['body_path']).read_bytes());assert h.sha(raw)==cap['receipt']['sha256'] and cap['receipt']['status']==200
   for ref in obj['index']['index_refs']:
    rp=ROOT/ref['path'];assert h.sha(rp.read_bytes())==ref['sha256'];h.load(rp)
   plan=ROOT/'docs/research/museum-expansion-20261006/native/ngaustralia/ngaustralia-gac-additions-001-plan.json.gz';assert h.sha(plan.read_bytes())==note['plan_sha256']
   assert h.norm(f['creator_label'])==h.norm(p['creator'])=='tom roberts'
   assert h.norm(f['title'])==h.norm(a['title']);assert h.norm(p['title'])==h.norm(a['title']) or aid=='0f21cb05-6032-557f-bc7c-4968b5dfebac'
   assert a['creation_year_start']<=p['date']['first']<=p['date']['last']<=a['creation_year_end']<=1955
   assert p['rights_label']=='Public domain' and p['rights_status']=='public_domain' and a['work_type']=='painting'
   native=[x for x in gaps['identifiers'] if x['entity_id']==aid and x['scheme']=='nga-australia-object'];assert len(native)==1 and native[0]['external_id']==f['native_object_id']
   recon=h.load(E/'reconciliation'/(aid+'.json'));assert len(recon['title_candidates'])==1 and recon['title_candidates'][0]['id']==aid and not recon['existing_media'];assert all(x['entity_id']==aid for x in recon['native_identifiers'])
   fields={x['label']:x['value'] for x in obj['parsed']['fields']};assert fields['Creator']==f['creator_label'] and fields['Title']==a['title'];assert obj['parsed']['publisher_heading']=='National Gallery of Australia Canberra, Australia';assert f['native_object_id'] in fields['External Link'] or f['native_object_id'] in json.dumps(obj['parsed']['fields'])
   ds=re.fullmatch(r'w(\d+) x h(\d+) cm',fields['Physical Dimensions']);assert ds;ratio=int(ds[1])/int(ds[2])
   basis='Exact NGA native IRN '+f['native_object_id']+' and museum-published original object/index capture hashes verified against persisted source citation and original catalogue plan. WikiArt title, Tom Roberts identity and dated painting agree; global exact-title/native-ID/source-URL/image comparisons identify only this existing primary gap. Supplied legacy dimensions have unreliable units so remain unknown, but their width/height ratio is additional composition evidence. No museum image rights inferred. WikiArt omits dimensions and holding, which remain explicit limitations. '
   if aid=='0f21cb05-6032-557f-bc7c-4968b5dfebac':basis+='WikiArt inserts the article "the" in title; museum description specifies high horizon and artist painting low in creek scene, to verify visually. '
   if aid=='12829a02-5075-55e7-b9ff-f94815c48c4f':basis+='WikiArt1894 lies within existing museum1893–94; preserve catalogue range unchanged. '
   rows.append(dict(artwork_id=aid,native_id=f['native_object_id'],current_source_id=p['source_id'],title=a['title'],creator_label=p['creator'],source_url=p['source_url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type='painting',provider='wikiart',expected_museum_id=MID,rights_status=p['rights_status'],rights_label=p['rights_label'],rights_basis=p['rights_basis'],image=dict(image_url=p['image_url'],source=dict(p,original_museum_capture=prior,persisted_source_citation=c),receipt=p['receipt']),plan_sha256=note['plan_sha256'],identity_confidence=.95,identity_basis=basis,manual_visual_required=True,source_frame_ratio=ratio))
   proof.append(dict(artwork_id=aid,native_id=f['native_object_id'],source_capture=cap,source_capture_sha256=h.sha(raw),original_catalogue_plan_sha256=note['plan_sha256'],source_reference=prior['path'],source_reference_sha256=prior['sha256'],global_reconciliation=recon,source_dimensions_literal=fields['Physical Dimensions'],source_frame_ratio=ratio,unit_correction_not_invented=True,date_scope_evidence=fields['Date Created'],wikiart_date=p['date'],confidence=.95,visual_identity_pending=True))
 assert 0<len(rows)<=100
 save('exact-identity-decisions.json',dict(at=h.now(),rows=proof,confidence=.95,selected=len(rows),metadata_updates=0))
 save('authorization.json',dict(at=h.now(),production_images_authorized=True,user_approval='WikiArt source approval6 October2026; current bounded production image enrichment authorization.',policy_reference='docs/ARTLINE_IMAGE_USE.md#user-approved-wikiart-source-policy--6-october-2026',copyright_holder_licence=False,actual_rights_preserved=True,local_catalogue_read_only=True))
 h.save(i.folder(B)/'selection.json.gz',dict(provider='wikiart',batch=B,rows=rows,selected_before_image_download=True));h.save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for row in rows:print(row['title'],i.prepare_one(row,B),flush=True)
 i.audit(B)
 print('Prepared, actual original/derivative visual review required.',flush=True)
def prewrite():
 images,audit,review=i.accepted(B);ids={im['artwork_id'] for im in images};rows={r['artwork_id']:r for r in i.selected(B)['rows'] if r['artwork_id'] in ids};assert len(images)==len(rows)==3 and not audit['identity_holds'];checks=[]
 for im in images:
  r=rows[im['artwork_id']];rc=r['image']['receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
  sp=BeautifulSoup(raw,'html.parser');md=json.loads(sp.select_one('.wiki-layout-painting-info-bottom[ng-init]')['ng-init'].split('=',1)[1].strip());assert md['_id']==r['current_source_id'] and md['artistName']==r['creator_label'];assert r['first']<=int(md['year'])<=r['last'];assert sp.select_one('img[itemprop=image]')['src']==im['source_image_url'];assert sp.select_one('.copyright-wrapper .copyright').get_text(' ',strip=True)==r['rights_label']
  assert h.sha(Path(im['path']).read_bytes())==im['sha256'] and im['bytes']==Path(im['path']).stat().st_size<=100000;assert h.sha(Path(im['original_path']).read_bytes())==im['source_sha256']
  for path in [im['path'],im['original_path']]:
   with Image.open(path) as pic:pic.verify()
   with Image.open(path) as pic:pic.load()
  assert abs(im['width']/im['height']-r['source_frame_ratio'])<.035,'Source ratio mismatch requires individual review'
  assert abs(im['width']/im['height']-im['original_dimensions'][0]/im['original_dimensions'][1])<.01
  decision=next(x for x in review['decisions'] if x['artwork_id']==im['artwork_id']);assert decision['viewed_individually'] and decision['original_individually_viewed'] and decision['sha256']==im['sha256']
  checks.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],bytes=im['bytes'],original_sha256=im['source_sha256'],complete_decode=True,source_ratio_difference=abs(im['width']/im['height']-r['source_frame_ratio']),actually_viewed=True,source_receipt_sha256=rc['sha256']))
 save('independent-source-file-and-visual-verification.json',dict(at=h.now(),checks=checks,selection_sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes()),visual_review_sha256=h.sha((i.folder(B)/'visual-review.json').read_bytes()),passed=True))
 target('before-recovery')
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791897658924','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save('cloud-backup.json',backup)
 with h.connect() as db:
  before=h.snapshot(db,list(rows));assert before=={aid:h.load(E/'gap-input.json.gz')['before'][aid] for aid in rows};h.save(i.BACKUP/'affected-row-recovery-before.json.gz',dict(at=h.now(),before=before,selection_sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 h.save(i.BACKUP/'image-selection.json.gz',i.selected(B));i.BACKUP.chmod(0o700)
 save('local-recovery-verification.json',dict(at=h.now(),status='VERIFIED',existing_cloud_backup=backup['id'],cloud_backups_created=0,files=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in [i.BACKUP/'affected-row-recovery-before.json.gz',i.BACKUP/'image-selection.json.gz']],additional_locked_preimages_required=True,local_catalogue_connections=0))
def deliver():
 assert h.load(E/'independent-source-file-and-visual-verification.json')['passed'];assert h.load(E/'local-recovery-verification.json')['status']=='VERIFIED'
 target('before-storage-write');i.upload(B);target('before-database-write');i.apply(B)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
