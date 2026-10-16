#!/usr/bin/env python3
"""One bounded Princeton Greek/Byzantine image continuation. No scheduler."""
import csv, fcntl, gzip, importlib.util, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base26','continuous-image-batch-000002.py');i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000026'
RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000026'
B='princeton-000';MID='4ec6f6ac-08d1-5081-8b76-571b89611eda';SID='f986bdc8-5be5-5bd3-bb20-eeec73f25551'
i.OP='continuous-primary-images-20261011-b000026';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
POLICY='https://artmuseum.princeton.edu/art/our-collections/image-use-and-access'
i.CFG['princeton']=dict(mid=MID,scheme='princeton-object',name='Princeton University Art Museum',rights='unknown',license='Source rights label unspecified',policy=POLICY,host='media.artmuseum.princeton.edu')
old_uid=i.m.uid;i.m.uid=lambda k:SID if k=='source/princeton' else old_uid(k)
for p in [E,RUNTIME,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(p,v):
 if p.exists():return load(p)
 h.save(p,v);return v
def target(write=False):
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
APPROVAL=dict(policy_reference='docs/ARTLINE_IMAGE_USE.md#greek-painter-continuation--20-september-2026',scope='Selected authentic museum reproductions in the Greek-linked collection, including works held abroad; creation by 1955. Applied here only to explicit East Greek and Byzantine source cultures/periods.',user_approval=True,copyright_holder_licence=False,source_rights_rewritten=False,provider_wide_approval=False)
def reconcile():
 save(E/'production-target-reconciliation.json',target())
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(registry.open()));assert len(reg)==111
 paths=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 save(E/'required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=p,sha256=h.sha((ROOT/p).read_bytes()),bytes=len((ROOT/p).read_bytes())) for p in paths],registry_path=str(registry),registry_sha256=h.sha(registry.read_bytes()),registry_records=111,registry=reg,precedence='Current production authorization; real local catalogue read-only. Original 111-source registry retained. External supervisor untouched.'))
 save(E/'source-register.json',dict(at=h.now(),registry_path=str(registry),registry_sha256=h.sha(registry.read_bytes()),registry_records=111,source=[r for r in reg if r['source_id']=='princeton_art_museum'],policy=APPROVAL,remaining_gaps='Only eight selected existing object gaps researched from a 60-row bounded candidate keyset; no collection-wide coverage claim.'))
 q=load(E.parents[1]/'source-queue.json');save(E/'source-queue-before.json',q)
 save(E/'source-access-holds.json',dict(at=h.now(),inherited=[r for r in q['sources'] if 'hold' in r['status'] or '403' in r['status']],new_hold=load(E/'source-captures/princeton-policy.receipt.json'),scope='artmuseum.princeton.edu website returned 403; no further website requests. Documented public object API and separate IIIF service accessible; not alternate routes to restricted website content.',rights_hold='Saint Peter: source did not explicitly mark public domain; no general Princeton approval inferred. Russian (?) plaque and American Mirror outside Greek-linked extension.'))
 stop=ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json';save(E/'completed-campaign-stop-preservation.json',dict(path=str(stop.relative_to(ROOT)),sha256=h.sha(stop.read_bytes()),separate_campaign=i.OP,restarted=False))
 # Earlier batch must be live, checksum attributed, and excluded from this increment.
 old=E.parent/'000025';receipt=load(old/'batch-verification-receipt.json');ids=receipt.get('production_ids') or receipt.get('artwork_ids')
 if not ids:
  p=load(old/'chicago-byzantine/plan.json.gz');ids=[r['artwork_id'] for r in p['records']]
 with connect() as db:
  states=h.snapshot(db,ids)
  assert len(states)==11
  notes=[dict(r) for r in db.execute("SELECT entity_id::text,field_name,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name LIKE 'continuous%%b000025'",(ids,))]
 save(E/'prior-batch-live-reconciliation.json',dict(at=h.now(),batch=25,ids=ids,live_rows=len(states),citations=notes,previous_receipt_sha256=h.sha((old/'batch-verification-receipt.json').read_bytes()),increments_for_batch26=0))
 save(E/'authorization.json',dict(at=h.now(),production_image_updates_authorized=True,local_database_read_only=True,approval=APPROVAL))
def maker_keys(o):
 return [{k:v.get(k) for k in ['id','displayname','prefix','suffix','role']} for v in o.get('makers',[])]
def prepare():
 reconcile()
 if (i.folder(B)/'selection.json.gz').exists():return finish()
 pool=load(E/'bounded-gap-input.json')['rows'];oids={'34177','25042','28540','27251','24622','17354','21911','30700'}
 candidates=[r for r in pool if r['external_id'] in oids];ids=[r['id'] for r in candidates]
 with connect() as db:
  before=h.snapshot(db,ids)
  notes=[dict(r) for r in db.execute("SELECT entity_id::text,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='museum_expansion_reviewed_metadata'",(ids,))]
  ext=[dict(r) for r in db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='princeton-object' AND external_id=ANY(%s)",(list(oids),))]
 save(E/'preparation-production-snapshot.json.gz',dict(at=h.now(),before=before,citations=notes,global_native_identifiers=ext))
 chosen=[];checks=[]
 for a in candidates:
  oid=a['external_id'];rc=load(E/'source-captures'/(oid+'.receipt.json'));body=gzip.decompress((E/'source-captures'/(oid+'.body.gz')).read_bytes());assert rc['status']==200 and h.sha(body)==rc['sha256'];o=json.loads(body);reason=None
  try:
   cultures=[v['culture'] for v in o.get('cultureterms',[])];periods=[v['period'] for v in o.get('periodterms',[])]
   assert 'Greek' in cultures or 'Byzantine' in cultures+periods,'Outside documented Greek-linked collection source extension; no explicit per-image public-domain label'
   p=before[a['id']]['artwork'];assert p['primary_media_id'] is None and p['status']!='archived'
   assert [r['entity_id'] for r in ext if r['external_id']==oid]==[a['id']],'Global native identity conflict'
   assert (str(o['objectid']),o['objectnumber'],o['displaytitle'],o['datebegin'],o['dateend'],o['displaydate'])==(oid,p['accession_number'],p['title'],p['creation_year_start'],p['creation_year_end'],p['date_display']),'Current source identity/date conflict'
   prior=[json.loads(x['evidence_note'])['facts'] for x in notes if x['entity_id']==a['id']];assert len(prior)==1;f=prior[0]
   for k in ['dimensions','medium','creditline']:assert o.get(k)==f['source_fields'].get(k),'Source physical identity/provenance changed: '+k
   assert maker_keys(o)==maker_keys(f['source_fields']),'Source creator qualification changed'
   assert f['creator_label']==p['unlinked_creator_label'] and not before[a['id']]['creators'],'Source anonymous/qualified label mismatch'
   assert o['dateend']<=1955 and str(o['nowebuse']).lower()=='false' and str(o['campuscollections']).lower()=='false'
   primary=[v for v in o['media'] if v['isprimary']==1 and v['mediatypeid']==1];assert len(primary)==1 and o['primaryimage']==[primary[0]['uri']]
   assert primary[0]['uri'].startswith('https://media.artmuseum.princeton.edu/iiif/3/collection/')
   assert not o.get('restrictions') and not primary[0].get('restrictions'),'Explicit source restriction needs individual treatment'
   path=E/'source-captures'/(oid+'.body.gz');im=primary[0]['uri']+'/full/!1200,1200/0/default.jpg'
   chosen.append(dict(artwork_id=a['id'],native_id=oid,title=p['title'],creator_label=f['creator_label'],source_url=rc['url'],accession_number=p['accession_number'],first=p['creation_year_start'],last=p['creation_year_end'],precision=p['date_precision'],work_type=p['work_type'],provider='princeton',image=dict(image_url=im,native_url=primary[0]['uri'],source=o,receipt=rc),plan_sha256=h.sha(path.read_bytes()),plan_path=str(path),rights_basis='Source object and image restrictions fields are null; this is not an explicit public-domain licence. Selected Greek/Byzantine-linked work falls within the separately recorded Greek collection user source approval, creation by 1955. Actual source fields and credits preserved. No copyright-holder licence or current-display assertion.',approval=APPROVAL,manual_visual_required=True))
  except AssertionError as exc:reason=str(exc)
  checks.append(dict(artwork_id=a['id'],native_id=oid,outcome=reason or 'selected_exact_primary_image',source_sha256=rc['sha256']))
 save(E/'gap-reconciliation.json',dict(at=h.now(),candidate_rows=60,checked=len(checks),selected=len(chosen),rows=checks,processed_native_ids=[r['external_id'] for r in candidates],unresearched_native_ids=[r['external_id'] for r in pool if r['external_id'] not in oids],resume_after_artwork_id=None,ordering='Selected Greek/Byzantine priority objects from frozen UUID keyset; do not skip unresearched rows'))
 assert chosen
 save(i.folder(B)/'selection.json.gz',dict(provider='princeton',batch=B,rows=chosen,selection_basis='Exact existing native object gaps, physical dimensions, qualified/anonymous source labels, source dates, and unique primary image. Greek collection approval applies per object, not to all Princeton reproductions.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 finish()
def finish():
 for row in i.selected(B)['rows']:print(row['native_id'],i.prepare_one(row,B)['state'],flush=True)
 (i.ORIG/B).mkdir(parents=True,exist_ok=True);i.audit(B)
 for p in (i.folder(B)/'sheets').glob('*.json'):print('SHEET',load(p)['path'],flush=True)
original_copy=i.n.copy_rows
def copy_rows(db,table,rows):
 selected={r['artwork_id']:r for r in i.selected(B)['rows']};images={im['media_id']:im for im in i.accepted(B)[0]}
 for row in rows:
  if table not in ['media_assets','media_rights_evidence']:continue
  im=images[row['id'] if table=='media_assets' else row['media_id']];source=selected[im['artwork_id']]['image']['source']
  if table=='media_rights_evidence':
   ev=json.loads(row['evidence_json']);ev['user_approval']=APPROVAL;ev['actual_source_rights']=dict(object_restrictions=source.get('restrictions'),reproduction_credit=source.get('creditlinerepro'),media=[v for v in source['media'] if v['isprimary']==1]);row['evidence_json']=json.dumps(ev,ensure_ascii=False)
  else:
   credit='; '.join(v for v in [selected[im['artwork_id']]['creator_label'],source.get('creditline'),source.get('creditlinerepro'),'Image courtesy of the Princeton University Art Museum'] if v)
   row['creator_credit']=credit;row['attribution_text']=credit+'. Full supplied source frame preserved; proportional resizing and JPEG compression.'
 return original_copy(db,table,rows)
i.n.copy_rows=copy_rows
def deliver():
 images,_,_=i.accepted(B);ids=[r['artwork_id'] for r in images];assert 1<=len(ids)<=100
 with connect() as db:
  states=h.snapshot(db,ids);present=[r for r in images if states[r['artwork_id']]['artwork']['primary_media_id']]
  if present:
   assert len(present)==len(images) and all(states[r['artwork_id']]['artwork']['primary_media_id']==r['media_id'] for r in images)
   assert (i.BACKUP/B/'before-000.json.gz').exists(),'Own recovery preimage required'
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791735810546','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save(E/'cloud-backup.json',backup)
 save(E/'production-target-before-storage-write.json',target(True));i.upload(B)
 save(E/'production-target-before-database-write.json',target(True));i.apply(B)
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
