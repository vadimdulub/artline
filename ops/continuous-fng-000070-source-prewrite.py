#!/usr/bin/env python3
"""Independent checksum, source, production, storage, audit and delivery receipts."""
import base64, datetime, fcntl, gzip, hashlib, importlib.util, io, json
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('b','ops/continuous-fng-images-000070.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i
lock=(b.RUNTIME/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
images,audit,review=i.accepted(b.B);assert 1<=len(images)<=25
ids=[x['artwork_id'] for x in images];expected={x['artwork_id']:x for x in images}
pin=b.h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());rv=b.h.sha((i.folder(b.B)/'visual-review.json').read_bytes())
before=b.load(b.E/'preparation-production-snapshot.json.gz')['before'];assert all(before[aid]['artwork']['primary_media_id'] is None for aid in ids)
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
b.save(b.E/'prewrite-source-verification.json',dict(at=b.h.now(),records=source,records_verified=len(source)))
b.save(b.E/'prewrite-file-verification.json',dict(at=b.h.now(),files=files,originals_outside_documents=True))
print('Independent source and every-file checks passed before write')
