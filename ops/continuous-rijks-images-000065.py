#!/usr/bin/env python3
"""One bounded Rijks reserve continuation. No supervisor or local catalogue writes."""
import ast, collections, csv, fcntl, importlib.util, io, json, os, shutil, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('base65',ROOT/'ops/continuous-image-batch-000002.py')
base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
i=base.i;h=base.h;connect=base.connect;load=h.load
E=ROOT/'docs/research/continuous-production-20261011/batches/000065'
RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000065'
B='rijks-065';OLD=base.OLD/'batches/rijks-044';MID=i.CFG['rijks']['mid']
i.OP='continuous-primary-images-20261011-b000065';i.RUN=E
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for p in [E,RUNTIME,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)

def save(p,v):
 if p.exists():return load(p)
 h.save(p,v);return v

def target(write=False):
 assert os.environ.get('ARTLINE_SWISS_INDIA_PROXY_PORT','55519')=='55519'
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
 assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)

def sourcecheck(row):
 rc=row['image']['receipt'];raw=Path(rc['path']).read_bytes()
 assert h.sha(raw)==rc['sha256'] and rc['status']==200
 src=row['image']['source']
 assert src['rights']==['http://creativecommons.org/publicdomain/mark/1.0/']
 assert src['native_id']==row['native_id'] and src['accession']==row['accession_number'] and src['title']==row['title']
 assert src['source_images']==[row['image']['native_url']]
 assert row['image']['image_url']==row['image']['native_url'].replace('/full/max/','/full/!1200,1200/')
 records=ET.fromstring(raw).findall('.//{http://www.openarchives.org/OAI/2.0/}record')
 assert any(h.sha(ET.tostring(x))==src['record_xml_sha256'] for x in records)
 assert h.sha(Path(row['plan_path']).read_bytes())==row['plan_sha256']
 return dict(artwork_id=row['artwork_id'],native_id=row['native_id'],source_sha256=rc['sha256'],record_xml_sha256=src['record_xml_sha256'],catalogue_plan_sha256=row['plan_sha256'],exact_native_image=True,rights=src['rights'])

def prepare():
 if (i.folder(B)/'selection.json.gz').exists():
  assert h.sha((i.folder(B)/'selection.json.gz').read_bytes())==load(i.folder(B)/'pin.json')['sha256']
  print('Pinned selection already exists; review/reconcile before delivery');return
 started=save(E/'started.json',dict(at=h.now(),batch=65))
 paths=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json','docs/research/continuous-production-20261011/batches/000064/CHECKPOINT.json','docs/research/continuous-production-20261011/batches/000063/source-access-holds.json']
 rp=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(rp.open()));assert len(reg)==111
 save(E/'required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=p,sha256=h.sha((ROOT/p).read_bytes())) for p in paths],registry_path=str(rp),registry_sha256=h.sha(rp.read_bytes()),registry_records=111,complete_registry=reg,precedence='Current source-specific approvals; local catalogue remains read-only; external supervisor unchanged.'))
 q=save(E/'source-queue-before.json',load(E.parents[1]/'source-queue.json'))
 route=next(r for r in q['sources'] if r['source_id']=='rijksmuseum');cursor=route['resume_cursor']['position'];assert cursor==100
 stops=[p for p in base.OLD.glob('*stop*.json')]
 save(E/'completed-campaign-stop-preservation.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in stops],separate_campaign=i.OP,restarted=False))
 save(E/'source-access-holds.json',dict(at=h.now(),inherited_ledger=paths[-1],inherited_queue='source-queue-before.json',registry_route='rijksmuseum',access='No Rijks access hold recorded. Reuse archived source records and selected prepared native public-domain reproductions; no provider downloads.',unchanged_held_providers_requested=0))
 save(E/'source-register.json',dict(at=h.now(),source=next(r for r in reg if r['source_id']=='rijksmuseum'),policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',registry_sha256=h.sha(rp.read_bytes()),access_status='Official OAI captures and prepared native image receipts reused; complete checksums verified',remaining_gaps='Only bounded existing reserve gaps; no institution completeness claim'))
 save(E/'production-target-reconciliation.json',target())
 candidates=load(OLD/'selection.json.gz')['rows'];prior=load(OLD/'quality-audit.json')
 window=list(enumerate(candidates))[cursor:cursor+400];ids=[r['artwork_id'] for _,r in window]
 with connect() as db:
  own=[dict(r) for r in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))]
  assert not own,'Earlier own writes require pinned-plan reconciliation'
  prev=load(E.parent/'000064/batch-verification-receipt.json')
  previous=[dict(r) for r in db.execute('SELECT a.id::text,a.primary_media_id::text,e.adapter_version,e.evidence_json FROM artworks a JOIN media_rights_evidence e ON e.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(prev['production_ids'],))]
  assert len(previous)==prev['verified_counts']['newly_illustrated']==15
  for r in previous:
   ev=r['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
   assert r['adapter_version']=='continuous-primary-images-20261011-b000064' and ev['selection_sha256']==prev['selection_sha256']
  save(E/'prior-batch-live-reconciliation.json',dict(at=h.now(),previous_batch=64,rows=previous,previous_increments=0,current_campaign_rows=own))
  states=h.snapshot(db,ids)
  native=[dict(r) for r in db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=ANY(%s)",(i.CFG['rijks']['scheme'],[r['native_id'] for _,r in window]))]
  inventories=[dict(r) for r in db.execute('SELECT id::text,accession_number FROM artworks WHERE current_institution_id=%s AND accession_number=ANY(%s)',(MID,[r['accession_number'] for _,r in window]))]
  selected=[];checks=[];creator_count=collections.Counter();sourcechecks=[];plan_cache={};copy=[]
  for pos,r in window:
   reason=None;aid=r['artwork_id'];im=load(OLD/'prepared'/(aid+'.json'));st=states.get(aid);a=st['artwork'] if st else {}
   try:
    assert st and a['status']!='archived','missing_or_archived'
    assert not a['primary_media_id'],'already_illustrated'
    assert aid not in prior['identity_holds'],'immutable_prior_identity_hold'
    assert im['state']=='prepared','prior_preparation_hold'
    assert not im['flags'],'prior_flag_requires_separate_review'
    if creator_count[r['creator_label']]>=5:
     reason='creator_variety_deferred';raise ValueError(reason)
    assert r['work_type'] in ['print','painting','drawing','watercolor'] and r['last']<=1955,'outside_selection_scope'
    assert (a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['current_institution_id'])==(r['title'],r['accession_number'],r['first'],r['last'],r['precision'],MID),'identity_fields_changed'
    assert [x['entity_id'] for x in native if x['external_id']==r['native_id']]==[aid],'global_native_identity_conflict'
    assert [x['id'] for x in inventories if x['accession_number']==r['accession_number']]==[aid],'duplicate_inventory_conflict'
    if r['plan_path'] not in plan_cache:plan_cache[r['plan_path']]=load(Path(r['plan_path']))
    old=next(x for x in plan_cache[r['plan_path']]['new_artworks'] if x['artwork_id']==aid)
    assert a['unlinked_creator_label']==old['creator_label'],'creator_label_changed'
    assert a['dimensions_text']==old['dimensions'],'physical_dimensions_changed'
    assert a['medium_text']==old['medium'],'medium_changed'
    assert not st['creators'] and not old['links'],'New creator reconciliation required'
    assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=%s',(im['sha256'],)).fetchone(),'existing_media_checksum'
    raw=Path(im['path']).read_bytes();orig=Path(im['original_path']).read_bytes()
    assert h.sha(raw)==im['sha256'] and len(raw)<=100000 and h.sha(orig)==im['source_sha256']
    with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
    with Image.open(io.BytesIO(orig)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'];assert abs(pic.width/pic.height-im['width']/im['height'])<.03
    sourcechecks.append(sourcecheck(r));selected.append(r);copy.append(im);creator_count[r['creator_label']]+=1
   except (AssertionError,ValueError,KeyError) as exc:reason=str(exc) or type(exc).__name__
   checks.append(dict(artwork_id=aid,native_id=r['native_id'],position=pos,creator_label=r['creator_label'],reason=reason or 'selected_exact_native_gap'))
   if len(selected)==20:break
 save(E/'reserve-reconciliation.json',dict(at=h.now(),start_position=cursor,window_limit=400,rows=checks,selected=len(selected),resume_position=checks[-1]['position']+1,creator_counts=dict(creator_count),deferred_positions=[r['position'] for r in checks if r['reason']=='creator_variety_deferred']))
 save(E/'preparation-production-snapshot.json.gz',dict(at=h.now(),before={r['artwork_id']:states[r['artwork_id']] for r in selected}))
 save(E/'global-identity-reconciliation.json',dict(at=h.now(),native=native,inventories=inventories,selected_checks=sourcechecks,selection_count=len(selected)))
 assert selected,'No eligible reserve gaps'
 save(i.folder(B)/'selection.json.gz',dict(at=h.now(),provider='rijks',batch=B,rows=selected,selection_basis='Existing image gaps from bounded reserve positions with max five per creator; exact native inventory, source dimensions, unlinked creator labels, dates and public-domain image evidence.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for r,im in zip(selected,copy):
  raw=Path(im['path']).read_bytes();sp=im['storage_path'].replace('illustrated-300k-20261011',i.OP);dest=ROOT/'apps/web/public'/sp.lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True)
  if dest.exists():assert h.sha(dest.read_bytes())==im['sha256']
  else:dest.write_bytes(raw)
  save(i.folder(B)/'prepared'/(r['artwork_id']+'.json'),dict(im,path=str(dest),storage_path=sp,media_id=i.uid('media/'+r['artwork_id']+'/'+im['sha256'])))
 save(E/'reserve-evidence-reuse.json',dict(at=h.now(),selection_sha256=h.sha((OLD/'selection.json.gz').read_bytes()),quality_audit_sha256=h.sha((OLD/'quality-audit.json').read_bytes()),prior_visual_review_exists=(OLD/'visual-review.json').exists(),prior_review_claimed=False,originals_preserved=True,provider_downloads=0,requires_new_actual_visual_review=True))
 (i.ORIG/B).mkdir(parents=True,exist_ok=True);i.audit(B)
 print('Selected',len(selected),'creators',dict(creator_count),flush=True)
 for p in (i.folder(B)/'sheets').glob('*.json'):print('SHEET',load(p)['path'],flush=True)

def locked_preconditions(before):
 prior=load(E/'preparation-production-snapshot.json.gz')['before']
 for aid,st in before.items():
  if st['artwork']['primary_media_id'] is None:assert st==prior[aid],'Selected record changed since identity reconciliation'

# Established transaction code, same advisory lock and immutable receipts; use local recovery.
raw=(ROOT/'ops/illustrated-300k-20261011.py').read_text()
node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='apply')
code=ast.get_source_segment(raw,node)
code=code.replace("m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL'","m.load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace('before=d.snapshot(db,ids)','before=d.snapshot(db,ids);locked_preconditions(before)')
i.locked_preconditions=locked_preconditions
exec(compile(code,__file__,'exec'),i.__dict__)

def deliver():
 pre=load(E/'independent-prewrite-verification.json');assert pre['selection_sha256']==h.sha((i.folder(B)/'selection.json.gz').read_bytes());assert pre['visual_review_sha256']==h.sha((i.folder(B)/'visual-review.json').read_bytes())
 rc=load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED'
 for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
 images,_,_=i.accepted(B);ids=[im['artwork_id'] for im in images];assert 1<=len(ids)<=100
 with connect() as db:
  live=h.snapshot(db,ids);present=[aid for aid in ids if live[aid]['artwork']['primary_media_id']]
  if present:
   assert len(present)==len(ids)
   preimage=load(i.BACKUP/B/'before-000.json.gz');assert all(preimage[aid]['artwork']['primary_media_id'] is None for aid in ids)
   for im in images:
    assert live[im['artwork_id']]['artwork']['primary_media_id']==im['media_id']
    ev=db.execute('SELECT adapter_version,evidence_json FROM media_rights_evidence WHERE media_id=%s',(im['media_id'],)).fetchone();assert ev['adapter_version']==i.OP
    payload=ev['evidence_json'];payload=json.loads(payload) if isinstance(payload,str) else payload
    assert payload['selection_sha256']==pre['selection_sha256'] and payload['batch_visual_review_sha256']==pre['visual_review_sha256']
 save(E/'production-target-before-storage-write.json',target(True));i.upload(B)
 save(E/'production-target-before-database-write.json',target(True));i.apply(B)

if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
