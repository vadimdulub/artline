#!/usr/bin/env python3
"""Independent, scoped prewrite/postwrite/replay checks for bounded batch 59."""
import base64, fcntl, hashlib, importlib.util, io, json, sys
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('w59',Path(__file__).with_name('continuous-getty-images-000059.py'))
w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
i=w.i;h=w.h;E=w.E

def input_checks():
 images,audit,review=i.accepted(w.B);ids=[im['artwork_id'] for im in images]
 assert 1<=len(ids)<=100 and len(set(ids))==len(ids)
 rows={r['artwork_id']:r for r in i.selected(w.B)['rows']}
 pin=h.sha((i.folder(w.B)/'selection.json.gz').read_bytes());rv=h.sha((i.folder(w.B)/'visual-review.json').read_bytes())
 assert pin==w.load(i.folder(w.B)/'pin.json')['sha256']
 decisions={r['artwork_id']:r for r in review['decisions']}
 files=[];sources=[]
 for im in images:
  aid=im['artwork_id'];r=rows[aid];d=decisions[aid]
  assert d['decision']=='accept' and d['viewed_individually'] and d['sha256']==im['sha256']
  raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes()
  assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(original)==im['source_sha256']
  assert Path(im['path']).resolve().is_relative_to((w.ROOT/'apps/web/public/assets/artworks/imported'/i.OP).resolve())
  assert Path(im['original_path']).resolve().is_relative_to(i.ORIG.resolve())
  with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.format=='JPEG' and pic.size==(im['width'],im['height'])
  with Image.open(io.BytesIO(original)) as pic:pic.load();assert pic.size==tuple(im['original_dimensions']) and abs(pic.width/pic.height-im['width']/im['height'])<.03
  assert h.sha(Path(r['plan_path']).read_bytes())==r['plan_sha256']
  src=r['image']['source'];n=src['native'];obj=src['api'];media=src['digital_object']
  soup=BeautifulSoup(w.body(r['image']['receipt']),'html.parser');assert json.loads(soup.select_one('script[type="application/ld+json"]').get_text())==n
  assert json.loads(w.body(src['api_receipt']))==obj and json.loads(w.body(src['digital_object_receipt']))==media
  assert n['name']==r['title'] and w.contents(obj['identified_by'],w.AAT+'300312355')==[r['accession_number']]
  assert obj['id']==w.API+r['native_id'] and n['license']==w.CC0
  assert n['thumbnailUrl'].replace('/full/!300,300/','/full/!1200,1200/')==im['source_image_url']
  assert src['main_view']['id'].split('/full/')[0]==n['thumbnailUrl'].split('/full/')[0]
  rights={v['id'] for t in media.get('subject_to',[]) for v in t.get('classified_as',[])}
  assert w.CC0 in rights and w.LOCAL+'clearance/download' in rights
  assert any(ap['id']==n['thumbnailUrl'].split('/full/')[0] for d in media['digitally_shown_by'] for ap in d['access_point'])
  sources.append(dict(artwork_id=aid,native_id=r['native_id'],source_sha256=r['image']['receipt']['sha256'],source_plan_sha256=r['plan_sha256'],digital_object_sha256=src['digital_object_receipt']['sha256'],rights=sorted(rights),physical_identity_and_native_image_verified=True))
  files.append(dict(artwork_id=aid,path=im['path'],sha256=im['sha256'],bytes=im['bytes'],original_path=im['original_path'],original_sha256=im['source_sha256'],full_decode=True,proportions_preserved=True,actually_viewed=True,visual_note=d['note']))
 return images,ids,rows,pin,rv,sources,files

def prewrite():
 images,ids,rows,pin,rv,sources,files=input_checks()
 with w.connect() as db:
  before=h.snapshot(db,ids);old=w.load(E/'bounded-gap-input.json.gz')['before']
  assert all(before[aid]==old[aid] and before[aid]['artwork']['primary_media_id'] is None for aid in ids)
  assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=ANY(%s)',([im['sha256'] for im in images],)).fetchall()
 w.save(E/'independent-prewrite-verification.json',dict(at=h.now(),selected=len(ids),selection_sha256=pin,visual_review_sha256=rv,source_checks=sources,file_checks=files,all_live_primary_gaps_unchanged=True,existing_hash_collisions=0,all_images_actually_viewed=True))
 print('Prewrite passed',len(ids),flush=True)

def verify():
 images,ids,rows,pin,rv,sources,files=input_checks();expected={im['artwork_id']:im for im in images}
 bp=i.BACKUP/w.B/'before-000.json.gz';before=w.load(bp)
 assert all(before[aid]['artwork']['primary_media_id'] is None for aid in ids)
 with w.connect() as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  after=h.snapshot(db,ids)
  live=[dict(r) for r in db.execute('SELECT a.id::text,a.primary_media_id::text,m.checksum_sha256::text,m.storage_path,m.byte_size,m.rights_status,m.license_label,m.creator_credit,e.adapter_version,e.source_checksum,e.source_image_url,e.evidence_json,e.source_id::text FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=m.id WHERE a.id=ANY(%s::uuid[])',(ids,))]
  assert len(live)==len(ids)
  for r in live:
   aid=r['id'];im=expected[aid];ev=json.loads(r['evidence_json']) if isinstance(r['evidence_json'],str) else r['evidence_json']
   assert (r['primary_media_id'],r['checksum_sha256'],r['storage_path'],r['byte_size'])==(im['media_id'],im['sha256'],im['storage_path'],im['bytes'])
   assert r['adapter_version']==i.OP and ev['selection_sha256']==pin and ev['batch_visual_review_sha256']==rv
   assert r['source_checksum']==rows[aid]['image']['receipt']['sha256'] and r['source_image_url']==im['source_image_url']
   assert r['source_id']==rows[aid]['source_id'] and r['rights_status']=='cc0' and ev['actual_image_rights']['license']==w.CC0
   assert ev['native_source']==rows[aid]['image']['source'] and ev['visual_review']['viewed_individually']
   assert 'J. Paul Getty Museum' in r['creator_credit']
   assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in i.IGNORE)
   assert after[aid]['creators']==before[aid]['creators'] and after[aid]['holdings']==before[aid]['holdings']
   assert len(after[aid]['attachments'])==len(before[aid]['attachments'])+1
   assert all(a in after[aid]['attachments'] for a in before[aid]['attachments'])
   assert any(a['media_id']==im['media_id'] for a in after[aid]['attachments'])
  search=db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[]) AND primary_media_id=ANY(%s::uuid[])',(ids,[im['media_id'] for im in images])).fetchone()['n'];assert search==len(ids)
  events=[dict(r) for r in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[im['media_id'] for im in images]))]
  for aid in ids:
   ev=[r for r in events if r['entity_id']==aid and r['before_json']['primary_media_id'] is None];assert len(ev)==1 and ev[0]['before_json']==before[aid]['artwork'] and ev[0]['after_json']==after[aid]['artwork']
  allbefore=w.load(E/'bounded-gap-input.json.gz')['before'];heldids=[aid for aid in allbefore if aid not in ids];heldnow=h.snapshot(db,heldids)
  assert all(heldnow[aid]==allbefore[aid] for aid in heldids)
 w.save(E/'independent-source-verification.json',dict(at=h.now(),rows=sources))
 w.save(E/'independent-file-verification.json',dict(at=h.now(),files=files,all_files_decoded=True,all_prepared_images_individually_viewed=True))
 w.save(E/'independent-production-verification.json',dict(at=h.now(),rows=live,after=after,selection_sha256=pin,visual_review_sha256=rv,transaction_preimages=str(bp),preimage_sha256=h.sha(bp.read_bytes()),verified_new_primary_images=len(ids),metadata_creators_holdings_status_preserved=True,search_documents=search))
 w.save(E/'independent-audit-history-verification.json',dict(at=h.now(),events=events,locked_preimages_match=True))
 w.save(E/'independent-held-objects-verification.json',dict(at=h.now(),held_ids=heldids,unchanged=True))
 credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=i.storage.Client(project='artline-508319',credentials=credentials);bucket=client.bucket(i.d.core.BUCKET);storage=[];public=[]
 for im in images:
  blob=bucket.blob(im['storage_path'].lstrip('/'));blob.reload();raw=Path(im['path']).read_bytes()
  assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode() and blob.metadata['sha256']==im['sha256'] and blob.metadata['operation']==i.OP
  storage.append(dict(artwork_id=im['artwork_id'],storage_path=blob.name,generation=blob.generation,bytes=blob.size,sha256=blob.metadata['sha256'],operation=blob.metadata['operation'],md5_verified=True))
  url='https://artlines.org'+im['storage_path'];r=i.session().get(url,timeout=(15,60));r.raise_for_status();assert h.sha(r.content)==im['sha256']
  with Image.open(io.BytesIO(r.content)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
  api='https://artlines.org/api/backend/v1/atlas/artworks/'+im['artwork_id'];ar=i.session().get(api,timeout=(15,60));ar.raise_for_status();assert im['storage_path'] in ar.text
  public.append(dict(artwork_id=im['artwork_id'],image_url=url,sha256=im['sha256'],api_url=api,image_status=r.status_code,api_status=ar.status_code,full_decode=True))
 w.save(E/'independent-storage-verification.json',dict(at=h.now(),checks=storage))
 w.save(E/'independent-public-verification.json',dict(at=h.now(),rows=public))
 stop=w.load(E/'completed-campaign-stop-preservation.json');assert all(h.sha(Path(v['path']).read_bytes())==v['sha256'] for v in stop['files'])
 w.save(E/'independent-campaign-stop-verification.json',dict(at=h.now(),stop_unchanged=True,separate_campaign=i.OP))
 counts=dict(new_painters=0,new_artworks=0,newly_illustrated=len(ids),alternate_images=0,museum_links=0)
 w.save(E/'batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,selection_sha256=pin,visual_review_sha256=rv,production_target=w.target(),verified_public_images=len(ids),verified_api_rows=len(ids),attribution='Every locked transaction preimage and matching audit preimage has no primary media. Current media rights evidence carries this campaign adapter and exact selection/source/visual checksums. Only this attributable increment is counted.'))
 print(json.dumps(counts),flush=True)

def replay():
 r=w.load(E/'batch-verification-receipt.json');ids=r['production_ids'];pin=r['selection_sha256']
 with w.connect() as db:
  before=h.snapshot(db,ids);n0=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']
  evs=[dict(v) for v in db.execute('SELECT e.adapter_version,e.evidence_json FROM artworks a JOIN media_rights_evidence e ON e.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,))]
 for v in evs:
  ev=json.loads(v['evidence_json']) if isinstance(v['evidence_json'],str) else v['evidence_json'];assert v['adapter_version']==i.OP and ev['selection_sha256']==pin
 assert len(evs)==len(ids) and before==w.load(E/'independent-production-verification.json')['after']
 w.save(E/'resume-target-reconciliation.json',w.target(True));w.deliver()
 with w.connect() as db:
  after=h.snapshot(db,ids);n1=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']
 assert before==after and n0==n1
 credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=i.storage.Client(project='artline-508319',credentials=credentials);bucket=client.bucket(i.d.core.BUCKET)
 gens=[]
 for v in w.load(E/'independent-storage-verification.json')['checks']:
  blob=bucket.blob(v['storage_path']);blob.reload();assert str(blob.generation)==str(v['generation']);gens.append(dict(path=blob.name,generation=blob.generation))
 w.save(E/'independent-resume-verification.json',dict(at=h.now(),unchanged_snapshot=True,audit_events_before=n0,audit_events_after=n1,storage_generations=gens,attribution_reconciled_before_replay=True,replay_increments={k:0 for k in r['verified_counts']}))
 print('Replay verified unchanged',flush=True)

if __name__=='__main__':
 with (w.RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
