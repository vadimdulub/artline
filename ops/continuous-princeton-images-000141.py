#!/usr/bin/env python3
"""Bounded batch 141: one saved Princeton Late Byzantine panel image."""
import csv, fcntl, gzip, importlib.util, json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('p29',ROOT/'ops/continuous-image-batch-000029.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
i=p.i;h=p.h;connect=p.connect
E=ROOT/'docs/research/continuous-production-20261011/batches/000141'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000141'
B='princeton-001'; AID='c61e36a7-8dbe-530f-9f75-aaa2b2dea6a9'; OID='22782'
i.OP='continuous-primary-images-20261011-b000141';i.RUN=E
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
p.E=E;p.RUNTIME=R;p.B=B
for x in [E,R,i.ORIG,i.BACKUP]:x.mkdir(parents=True,exist_ok=True)

def save(name,value):
 path=E/name
 if path.exists(): return h.load(path)
 h.save(path,value);return value

def prepare():
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
 files=[ROOT/'AGENTS.md',registry,ROOT/'docs/ARTLINE_IMAGE_USE.md',ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',ROOT/'docs/LOCAL_DATA_LOCATIONS.md',E.parents[1]/'CHECKPOINT.json',E.parents[1]/'source-queue.json']
 assert len(list(csv.DictReader(registry.open())))==111
 save('required-input-verification.json',dict(at=h.now(),files=[dict(path=str(x),bytes=x.stat().st_size,sha256=h.sha(x.read_bytes())) for x in files],complete_original_registry_rows=111,supplementary_registry_review_not_substituted=True,local_catalogue_connections=0))
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
 proxy=[x for x in subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines() if x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and actual in x];assert proxy
 save('production-target-reconciliation.json',dict(at=h.now(),connection_name=actual,proxy_verified=True,proxy_port=55519,proxy_command_inspected=True,helper='ops/india-300-delivery-20261011.py',shared_ingestion_lock='artline-curated-ingestion',write=False,local_catalogue_connections=0))
 with connect() as db:
  prev=h.load(E.parent/'000107/independent-production-verification.json');live=h.snapshot(db,list(prev['after']));assert live==prev['after']
 save('batch107-live-reconciliation.json',dict(at=h.now(),snapshot_equal=True,rows=len(live),prior_increments_counted=0))
 old=ROOT/'docs/research/continuous-production-20261011/batches/000029/source-captures/22782.body.gz'
 raw=gzip.decompress(old.read_bytes());o=json.loads(raw)
 rc=p.capture('22782','https://data.artmuseum.princeton.edu/objects/22782')
 fresh=gzip.decompress((E/'source-captures/22782.body.gz').read_bytes());assert fresh==raw
 assert o['classification']=='Paintings' and o['periodterms']==[{'id':2031717,'period':'Late Byzantine'}]
 assert o['medium']=='Tempera and gold leaf on wood panel' and o['dateend']==1329
 assert not o.get('restrictions') and not o['media'][0].get('restrictions')
 with connect() as db:
  state=h.snapshot(db,[AID])[AID]
  ext=[dict(x) for x in db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='princeton-object' AND external_id=%s",(OID,))]
 if state['artwork']['primary_media_id'] is not None:
  with connect() as db:
   evidence=[dict(x) for x in db.execute("SELECT m.id::text,m.storage_path,m.checksum_sha256::text,m.byte_size,r.evidence_json,r.source_checksum FROM media_assets m LEFT JOIN media_rights_evidence r ON r.media_id=m.id WHERE m.id=%s::uuid",(state['artwork']['primary_media_id'],))]
  save('taxonomy-and-live-reconciliation.json',dict(at=h.now(),artwork_id=AID,native_id=OID,prior_hold='Exact-token taxonomy check did not recognize Late Byzantine.',resolution='Official period term Late Byzantine establishes pictorial Byzantine eligibility, but live production already has a primary image from an earlier delivery.',live_primary_media_id=state['artwork']['primary_media_id'],external_identifier=ext,existing_media_evidence=evidence,selected=0,new_programme_increment=0,source_sha256=h.sha(raw)))
  print('ALREADY_ILLUSTRATED',AID);return
 assert ext==[{'entity_id':AID,'external_id':OID}]
 save('taxonomy-and-live-reconciliation.json',dict(at=h.now(),artwork_id=AID,native_id=OID,prior_hold='Exact-token taxonomy check did not recognize Late Byzantine.',resolution='Official period term Late Byzantine plus painting classification and tempera/gold panel establish eligible pictorial Byzantine object; no broader taxonomy inference.',live_primary_media_id=None,external_identifier=ext,source_sha256=h.sha(raw)))
 row=dict(artwork_id=AID,native_id=OID,title=o['displaytitle'],creator_label='Late Byzantine, 1261–1453',source_url=rc['url'],accession_number=o['objectnumber'],first=o['datebegin'],last=o['dateend'],precision='century',work_type='painting',provider='princeton',image=dict(image_url=o['media'][0]['uri']+'/full/!1200,1200/0/default.jpg',native_url=o['media'][0]['uri'],source=o,receipt=rc),plan_sha256=h.sha((E/'source-captures/22782.body.gz').read_bytes()),plan_path=str(E/'source-captures/22782.body.gz'),rights_basis='Source object and primary image restrictions fields are null; no public-domain licence asserted. Selected Byzantine work falls within recorded Greek/Byzantine collection user source approval through 1955; actual source rights and credit retained.',approval=p.APPROVAL,manual_visual_required=True)
 h.save(i.folder(B)/'selection.json.gz',dict(provider='princeton',batch=B,rows=[row],selection_basis='Exact accession, title, date, Late Byzantine period, tempera/gold panel medium, unique primary image and live production gap.'))
 h.save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 print(OID,i.prepare_one(row,B)['state'],flush=True);(i.ORIG/B).mkdir(parents=True,exist_ok=True);i.audit(B)
 for x in (i.folder(B)/'sheets').glob('*.json'):print('SHEET',h.load(x)['path'],flush=True)

if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);prepare()
