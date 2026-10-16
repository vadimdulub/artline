#!/usr/bin/env python3
"""Independent checksum, source, production, storage, audit and delivery receipts."""
import base64, datetime, fcntl, gzip, hashlib, importlib.util, io, json
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('b','ops/continuous-fng-images-000064.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i
lock=(b.RUNTIME/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
images,audit,review=i.accepted(b.B);assert 1<=len(images)<=25
ids=[x['artwork_id'] for x in images];expected={x['artwork_id']:x for x in images}
pin=b.h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());rv=b.h.sha((i.folder(b.B)/'visual-review.json').read_bytes())
before=b.load(i.BACKUP/b.B/'before-000.json.gz');assert all(before[aid]['artwork']['primary_media_id'] is None for aid in ids)
source=[];files=[]
selection=i.selected(b.B);cap=selection['source_export']
with Path(cap['path']).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==cap['sha256']
wanted={r['native_id'] for r in selection['rows']}
export={str(o['objectId']):o for o in json.load(open(cap['path'])) if str(o['objectId']) in wanted}
for row in [r for r in selection['rows'] if r['artwork_id'] in expected]:
 im=expected[row['artwork_id']];assert any(d['artwork_id']==row['artwork_id'] and d.get('viewed_individually') is True for d in review['decisions']);rc=row['image']['receipt'];body=gzip.decompress(Path(rc['body_path']).read_bytes());assert b.h.sha(body)==rc['sha256'] and rc['status']==200
 obj=json.loads(body);assert obj==row['image']['source']==export[row['native_id']]
 assert str(obj['objectId'])==row['native_id'] and obj['yearFrom']==row['first'] and (obj.get('yearTo') or obj['yearFrom'])==row['last']<=1955
 assert b.h.norm(row['title']) in {b.h.norm(v) for v in obj['title'].values() if v}
 assert obj['responsibleOrganisation']=='Kansallisgalleria / Sinebrychoffin taidemuseo'
 assert not obj.get('parents') and not obj.get('children')
 people=[v for v in obj['people'] if v.get('role',{}).get('en')=='Artist'];assert len(people)==1 and not people[0].get('attribution')
 name=' '.join(v for v in [people[0].get('firstName'),people[0].get('familyName')] if v);assert name==row['creator_label']
 photos=[v for v in obj.get('multimedia',[]) if v.get('isRiaDisplayImage') and v.get('license')=='CC0'];assert len(photos)==1 and photos[0]==row['image']['selected_photo']
 assert 'https://kokoelma.kansallisgalleria.fi'+photos[0]['jpg']['1000']==im['source_image_url']
 note=json.loads(row['identity_citation']['evidence_note']);assert note['object_id']==row['native_id'] and note['plan_sha256']==row['plan_sha256']
 assert row['identity_reconciliation']['prior_citation']==row['identity_citation']
 source.append(dict(artwork_id=row['artwork_id'],native_id=row['native_id'],source_sha256=rc['sha256'],source_plan_sha256=row['plan_sha256'],image_selection_sha256=pin,source_inventory=obj['inventoryNumber'],source_person_id=people[0]['id'],photo_id=photos[0]['id'],photo_rights=photos[0]['license'],photographer=photos[0].get('photographer_name'),exact_cited_object_and_preferred_media=True,source_export_sha256=cap['sha256'],source_capture_date=cap['retrieved_at']))
 raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes();assert b.h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and b.h.sha(original)==im['source_sha256']
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.format=='JPEG' and pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(original)) as pic:pic.load();assert abs(pic.width/pic.height-im['width']/im['height'])<.03
 files.append(dict(artwork_id=row['artwork_id'],path=im['path'],bytes=len(raw),sha256=im['sha256'],original_path=im['original_path'],original_sha256=im['source_sha256'],complete_decode=True,proportions_preserved=True,actually_viewed=True))
b.save(b.E/'independent-source-verification.json',dict(at=b.h.now(),records=source,records_verified=len(source)))
b.save(b.E/'independent-file-verification.json',dict(at=b.h.now(),files=files,originals_outside_documents=True))
with b.connect() as db:
 after=b.h.snapshot(db,ids)
 rows=[dict(r) for r in db.execute('SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256::text,ma.storage_path,ma.byte_size,ma.rights_status,ma.creator_credit,mre.adapter_version,mre.source_checksum,mre.source_image_url,mre.evidence_json FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence mre ON mre.media_id=ma.id WHERE a.id=ANY(%s::uuid[])',(ids,))]
 assert len(rows)==len(ids)
 for r in rows:
  aid=r['id'];im=expected[aid];ev=r['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
  assert r['primary_media_id']==im['media_id'] and r['checksum_sha256']==im['sha256'] and r['storage_path']==im['storage_path'] and r['byte_size']==im['bytes']
  assert r['adapter_version']==i.OP and ev['selection_sha256']==pin and ev['batch_visual_review_sha256']==rv
  assert r['source_checksum']==next(x['source_sha256'] for x in source if x['artwork_id']==aid) and r['source_image_url']==im['source_image_url']
  assert r['rights_status']=='cc0' and ev['actual_photo_rights']['license']=='CC0'
  selected=next(x for x in selection['rows'] if x['artwork_id']==aid)
  assert ev['identity_citation']==selected['identity_citation'] and ev['identity_reconciliation']==selected['identity_reconciliation']
  assert ev['original_catalogue_plan_sha256']==selected['plan_sha256']
  assert selected['source_credit']==r['creator_credit']
  assert ev['visual_review']['decision']=='accept' and ev['visual_review']['viewed_individually'] is True
  assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in i.IGNORE)
  assert after[aid]['creators']==before[aid]['creators'] and after[aid]['holdings']==before[aid]['holdings']
  assert len(after[aid]['attachments'])==len(before[aid]['attachments'])+1 and any(a['media_id']==im['media_id'] for a in after[aid]['attachments'])
 search=db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[]) AND primary_media_id=ANY(%s::uuid[])',(ids,[im['media_id'] for im in images])).fetchone()['n'];assert search==len(ids)
 events=[dict(r) for r in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[im['media_id'] for im in images]))]
 for aid in ids:
  matching=[r for r in events if r['entity_id']==aid and r['before_json']['primary_media_id'] is None and r['after_json']['primary_media_id']==expected[aid]['media_id']];assert len(matching)==1
  assert matching[0]['before_json']==before[aid]['artwork']
b.save(b.E/'independent-production-verification.json',dict(at=b.h.now(),rows=rows,verified_new_primary_images=len(ids),transaction_preimages=str(i.BACKUP/b.B/'before-000.json.gz'),preimage_sha256=b.h.sha((i.BACKUP/b.B/'before-000.json.gz').read_bytes()),selection_sha256=pin,visual_review_sha256=rv,metadata_creators_holdings_and_status_preserved=True,search_documents=search,after=after))
b.save(b.E/'independent-audit-history-verification.json',dict(at=b.h.now(),events=events,locked_preimages_match=True))
credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=i.storage.Client(project='artline-508319',credentials=credentials);bucket=client.bucket(i.d.core.BUCKET);storage=[];public=[]
for im in images:
 blob=bucket.blob(im['storage_path'].lstrip('/'));blob.reload();raw=Path(im['path']).read_bytes();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode() and blob.metadata['sha256']==im['sha256'] and blob.metadata['operation']==i.OP
 storage.append(dict(artwork_id=im['artwork_id'],storage_path=blob.name,generation=blob.generation,bytes=blob.size,sha256=blob.metadata['sha256'],operation=blob.metadata['operation'],md5_verified=True))
 url='https://artlines.org'+im['storage_path'];r=i.session().get(url,timeout=(15,60));r.raise_for_status();assert b.h.sha(r.content)==im['sha256']
 api='https://artlines.org/api/backend/v1/atlas/artworks/'+im['artwork_id'];a=i.session().get(api,timeout=(15,60));a.raise_for_status();assert im['storage_path'] in a.text
 public.append(dict(artwork_id=im['artwork_id'],image_url=url,sha256=im['sha256'],api_url=api,image_status=r.status_code,api_status=a.status_code))
b.save(b.E/'independent-storage-verification.json',dict(at=b.h.now(),checks=storage))
b.save(b.E/'independent-public-verification.json',dict(at=b.h.now(),rows=public))
counts=dict(new_painters=0,new_artworks=0,newly_illustrated=len(ids),alternate_images=0,museum_links=0)
b.save(b.E/'batch-verification-receipt.json',dict(at=b.h.now(),verified_counts=counts,production_ids=ids,selection_sha256=pin,visual_review_sha256=rv,attribution='All selected locked transaction preimages have no primary media; current rights evidence carries this campaign adapter and exact selection/source/visual checksums. Audit preimages equal locked backups. Earlier campaign objects and images excluded.',production_target=b.target(),verified_public_images=len(ids),verified_api_rows=len(ids)))

allids=[r['id'] for r in b.load(b.E/'fng-bounded-gap-input.json')['rows']]
heldids=[aid for aid in allids if aid not in ids]
with b.connect() as db:
 heldnow=b.h.snapshot(db,heldids)
 for aid in heldids:
  old=b.load(b.E/'preparation-production-snapshot.json.gz')['before'][aid]
  assert heldnow[aid]==old
 b.save(b.E/'independent-held-objects-verification.json',dict(at=b.h.now(),ids=heldids,unchanged=True,held_primary_images_attached=0))
stop=b.load(b.E/'completed-campaign-stop-preservation.json');assert b.h.sha((b.ROOT/stop['path']).read_bytes())==stop['sha256']
b.save(b.E/'independent-campaign-stop-verification.json',dict(at=b.h.now(),stop_file_unchanged=True,separate_campaign=i.OP))
print(json.dumps(counts))
