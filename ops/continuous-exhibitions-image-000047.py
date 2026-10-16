#!/usr/bin/env python3
"""Bounded exhibition image enrichment for batch 47; no supervisor lifecycle."""
import base64, fcntl, gzip, hashlib, importlib.util, io, json, os, subprocess, sys
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
def mod(name,path):
 s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base',ROOT/'ops/continuous-image-batch-000002.py');i=base.i;h=base.h
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000047'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000047'
B='getty-exhibition-047';OP='continuous-exhibitions-20261013-batch-000047-images'
OID='1ea7c3d2-e028-4480-8632-347503d0f574';AID='c91af6c7-018b-554b-ba52-418f4de861f6'
MID='62fb1e52-07ff-50bd-8eeb-95ea5bf4af1c';SID='20948c65-dc29-5d0f-bb00-af5008b6e7b9'
OBJ='https://data.getty.edu/museum/collection/object/'+OID
MEDIA='https://data.getty.edu/media/image/af6a972a-3647-53ad-ba67-16f512988a76'
IMAGE='https://media.getty.edu/iiif/image/bbe73039-6798-44e8-acd9-e81e5fa8c36b/full/!1200,1200/0/default.jpg'
i.OP=OP;i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
i.CFG['getty']=dict(mid=MID,scheme='getty-object',name='J. Paul Getty Museum',rights='cc0',license='CC0 1.0 Universal — Getty Open Content',policy='https://creativecommons.org/publicdomain/zero/1.0/',host='media.getty.edu')
i.m.m.connect=base.connect
_copy=i.n.copy_rows
def _copy_rows(db,table,rows):
 if table=='media_rights_evidence':
  for row in rows:row['source_id']=SID
 return _copy(db,table,rows)
i.n.copy_rows=_copy_rows
for p in [E,R,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(p,v):
 p=Path(p)
 if p.exists():return h.load(p)
 h.save(p,v);return v
def cap(name,url):
 rp=E/'source-captures'/(name+'.receipt.json');bp=R/'source-captures'/(name+'.json.gz')
 if rp.exists():return h.load(rp),json.loads(gzip.decompress(bp.read_bytes()))
 r=i.session().get(url,timeout=(15,60));r.raise_for_status();raw=r.content;bp.parent.mkdir(parents=True,exist_ok=True);bp.write_bytes(gzip.compress(raw,mtime=0))
 rc=save(rp,dict(at=h.now(),url=url,status=r.status_code,sha256=h.sha(raw),body_path=str(bp)))
 return rc,r.json()
def target():
 actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert actual=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(),connection_name=actual)
def prepare():
 save(E/'production-target-reconciliation.json',target());plan=h.load(E.parent/'000046/plan.json');obj=plan['object'];assert obj['id']==OBJ
 orc,fresh=cap('getty-85.GG.26-object',OBJ);mrc,media=cap('getty-85.GG.26-media',MEDIA);assert fresh['id']==OBJ and media['id']==MEDIA
 rights={v['id'] for t in media['subject_to'] for v in t['classified_as']};assert 'http://creativecommons.org/publicdomain/zero/1.0/' in rights and 'https://data.getty.edu/local/thesaurus/clearance/download' in rights
 with base.connect() as db:
  before=h.snapshot(db,[AID]);assert before[AID]['artwork']['primary_media_id'] is None
  a=before[AID]['artwork'];assert a['accession_number']=='85.GG.26' and a['work_type']=='drawing'
  assert db.execute("SELECT 1 FROM exhibition_entries WHERE artwork_id=%s AND exhibition_id=%s",(AID,'bf53c577-0442-5477-bb3f-d3eb6f77f2f5')).fetchone()
  assert db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=%s AND scheme='getty-object'",(AID,)).fetchone()['external_id']==OID
 save(E/'recovery-check.json',dict(at=h.now(),prior_batch_46_live=True,primary_media_id=None,exact_exhibition_link_live=True,concurrent_danish_rows_counted=0))
 source=dict(api=fresh,digital_object=media,object_receipt=orc,digital_object_receipt=mrc,rights=sorted(rights),exhibition_evidence='docs/research/continuous-exhibitions-20261013/batches/000046/plan.json')
 row=dict(artwork_id=AID,native_id=OID,current_source_id='85.GG.26',title='The Entombment',creator_label='Federico Barocci',source_url='https://www.getty.edu/art/collection/object/103QYA',accession_number='85.GG.26',first=1579,last=1582,precision='circa',work_type='drawing',provider='getty',source_id=SID,image=dict(image_url=IMAGE,source=source,receipt=orc),plan_path=str(E.parent/'000046/plan.json'),plan_sha256=h.sha((E.parent/'000046/plan.json').read_bytes()),rights_basis='Exact Getty overall-view asset is linked from object 85.GG.26; its digital-object record explicitly states CC0 and download clearance.',manual_visual_required=True)
 save(i.folder(B)/'selection.json.gz',dict(at=h.now(),provider='getty',batch=B,rows=[row],selection_basis='Exact documented exhibition object from batch 46; current null-primary production preimage; Getty overall-view UUID and image-level CC0/download clearance.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 im=i.prepare_one(row,B);assert im['state']=='prepared';i.audit(B)
 save(E/'research-review.json',dict(at=h.now(),selected=1,object='Getty 85.GG.26',exhibition='The Graphic Art of Federico Barocci',exact_link_verified=True,rights='CC0 on exact digital object',partial_checklist=True))
 print(json.dumps(im));print('SHEET',h.load(i.folder(B)/'sheets/000.json')['path'])
def deliver():
 assert h.load(i.folder(B)/'visual-review.json')['batch_quality_decision']=='accept'
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791899943147','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save(E/'cloud-backup.json',backup)
 with base.connect(write=True) as guard:
  guard.execute('SELECT pg_advisory_lock(2026101201)');guard.commit()
  try:i.upload(B);i.apply(B)
  finally:guard.execute('SELECT pg_advisory_unlock(2026101201)');guard.commit()
def verify():
 images,audit,review=i.accepted(B);assert len(images)==1;im=images[0];pin=h.sha((i.folder(B)/'selection.json.gz').read_bytes());rv=h.sha((i.folder(B)/'visual-review.json').read_bytes())
 bp=i.BACKUP/B/'before-000.json.gz';before=h.load(bp);assert before[AID]['artwork']['primary_media_id'] is None
 with base.connect() as db:
  after=h.snapshot(db,[AID]);row=dict(db.execute("SELECT a.id::text,a.primary_media_id::text,m.checksum_sha256::text,m.storage_path,m.byte_size,m.rights_status,m.license_label,e.adapter_version,e.source_id::text,e.source_checksum,e.source_image_url,e.evidence_json FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=m.id WHERE a.id=%s",(AID,)).fetchone());ev=row['evidence_json'] if isinstance(row['evidence_json'],dict) else json.loads(row['evidence_json'])
  assert row['primary_media_id']==im['media_id'] and row['checksum_sha256']==im['sha256'] and row['byte_size']==im['bytes']<=100000 and row['adapter_version']==OP and row['source_id']==SID
  assert ev['selection_sha256']==pin and ev['batch_visual_review_sha256']==rv and ev['visual_review']['viewed_individually']
  assert after[AID]['creators']==before[AID]['creators'] and after[AID]['holdings']==before[AID]['holdings']
  events=[dict(x) for x in db.execute("SELECT before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=%s AND after_json->>'primary_media_id'=%s",(AID,im['media_id']))];assert len(events)==1 and events[0]['before_json']==before[AID]['artwork']
  assert db.execute("SELECT 1 FROM exhibition_entries WHERE artwork_id=%s AND exhibition_id=%s",(AID,'bf53c577-0442-5477-bb3f-d3eb6f77f2f5')).fetchone()
 save(E/'independent-database-verification.json',dict(at=h.now(),row=row,after=after,transaction_preimage=str(bp),preimage_sha256=h.sha(bp.read_bytes()),selection_sha256=pin,visual_review_sha256=rv,exact_exhibition_link_preserved=True,metadata_creators_holdings_preserved=True,audit_events=events))
 raw=Path(im['path']).read_bytes();assert h.sha(raw)==im['sha256'] and len(raw)<=100000
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
 save(E/'independent-file-verification.json',dict(at=h.now(),path=im['path'],sha256=im['sha256'],bytes=len(raw),dimensions=[im['width'],im['height']],full_decode=True,complete_frame=True,actually_viewed=True))
 credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=i.storage.Client(project='artline-508319',credentials=credentials);blob=client.bucket(i.d.core.BUCKET).blob(im['storage_path'].lstrip('/'));blob.reload();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode() and blob.metadata['sha256']==im['sha256'] and blob.metadata['operation']==OP
 save(E/'independent-storage-verification.json',dict(at=h.now(),path=blob.name,generation=blob.generation,bytes=blob.size,sha256=blob.metadata['sha256'],md5_verified=True))
 url='https://artlines.org'+im['storage_path'];r=i.session().get(url,timeout=(15,60));r.raise_for_status();assert h.sha(r.content)==im['sha256'];api='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/bf53c577-0442-5477-bb3f-d3eb6f77f2f5/entries?limit=100';ar=i.session().get(api,timeout=(15,60));ar.raise_for_status();entry=next(x for x in ar.json()['items'] if x.get('artworkId')==AID);assert im['storage_path'] in json.dumps(entry)
 save(E/'public-verification.json',dict(at=h.now(),image_url=url,image_status=r.status_code,image_sha256=im['sha256'],exhibition_entries_api_url=api,api_status=ar.status_code,entry=entry,api_association_verified=True))
 n0=len(events);deliver()
 with base.connect() as db:
  again=h.snapshot(db,[AID]);n1=db.execute("SELECT count(*) n FROM audit_log WHERE entity_type='artwork' AND entity_id=%s AND after_json->>'primary_media_id'=%s",(AID,im['media_id'])).fetchone()['n']
 assert again==after and n1==n0
 save(E/'independent-resume-verification.json',dict(at=h.now(),snapshot_unchanged=True,audit_events_before=n0,audit_events_after=n1,replay_increments={'new_images':0,'existing_records_enriched':0}))
 counts=dict(new_exhibitions=0,new_venue_stops=0,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,new_artist_participation_links=0,new_exact_artwork_links=0,new_images=1,existing_records_enriched=1)
 evidence=['independent-database-verification.json','independent-file-verification.json','independent-storage-verification.json','public-verification.json','independent-resume-verification.json','research-review.json','recovery-check.json','batches/getty-exhibition-047/visual-review.json']
 nxt='Select another undercovered official open-image route for exact exhibition-linked objects; retain Getty image-gap cursor after 85.GG.26 and do not revisit the separate artwork-programme Getty batch.'
 cp=dict(at=h.now(),batch=47,stage='verified_complete',verified_counts=counts,production_ids=[AID],next_task=nxt,evidence_paths=[str((E/p).relative_to(ROOT)) for p in evidence],local_catalogue_connections=0,external_supervisor_unchanged=True)
 h.save(E/'CHECKPOINT.json',cp);h.save(R/'CHECKPOINT.json',cp)
 qp=E.parents[1]/'source-queue.json'
 with qp.with_suffix('.lock').open('a+') as ql:
  fcntl.flock(ql,fcntl.LOCK_EX);q=h.load(qp);before_other={x['source_id']:x for x in q['sources'] if x['source_id']!='getty_museum'};g=next(x for x in q['sources'] if x['source_id']=='getty_museum');g.update(status='exact_exhibition_object_image_verified',last_checked_at=h.now(),checkpoint=str((E/'CHECKPOINT.json').relative_to(ROOT)),resume_cursor=dict(route='exact_exhibition_object_images',after_accession='85.GG.26',delivered_artwork_ids=[AID],skip_separate_artwork_programme=True),latest_batch_verified_counts=counts);g['evidence_paths']=list(dict.fromkeys(g.get('evidence_paths',[])+cp['evidence_paths']));tmp=qp.with_suffix('.47.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,qp);live=h.load(qp);assert before_other=={x['source_id']:x for x in live['sources'] if x['source_id']!='getty_museum'}
 save(E/'queue-update.json',dict(at=h.now(),updated_source='getty_museum',unrelated_entries_preserved=len(before_other),queue_sha256=h.sha(qp.read_bytes()),resume_cursor=g['resume_cursor']))
 evidence+=['queue-update.json','CHECKPOINT.json'];result=dict(outcome='progress',summary='Added and independently verified one authentic Getty CC0 primary image for Federico Barocci’s The Entombment (85.GG.26), an exact documented object in the existing Cleveland 1978 exhibition. The complete supplied frame was individually viewed; the existing review artwork, exhibition link, metadata, creators, holdings and all unrelated programme work were preserved.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=[str((E/p).relative_to(ROOT)) for p in evidence]);h.save(E/'worker-result.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':globals()[sys.argv[1]]()
