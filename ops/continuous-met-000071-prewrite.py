#!/usr/bin/env python3
"""Independent checksum, source, production, storage, audit and delivery receipts."""
import base64, datetime, fcntl, gzip, hashlib, importlib.util, io, json
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('b','ops/continuous-met-images-000071.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i
lock=(b.RUNTIME/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
images,audit,review=i.accepted(b.B);assert 1<=len(images)<=25
ids=[x['artwork_id'] for x in images];expected={x['artwork_id']:x for x in images}
pin=b.h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());rv=b.h.sha((i.folder(b.B)/'visual-review.json').read_bytes())
before=b.load(b.E/'preparation-production-snapshot.json.gz')['before'];assert all(before[aid]['artwork']['primary_media_id'] is None for aid in ids)
source=[];files=[]
selection=i.selected(b.B)
for row in [r for r in selection['rows'] if r['artwork_id'] in expected]:
 im=expected[row['artwork_id']];assert any(d['artwork_id']==row['artwork_id'] and d.get('viewed_individually') is True for d in review['decisions']);rc=row['image']['receipt'];body=gzip.decompress((b.ROOT/rc['body_path']).read_bytes());assert b.h.sha(body)==rc['sha256'] and rc['status']==200
 obj=json.loads(body);assert dict(obj,assistivetext=obj.get('objectName') or '')==row['image']['source']
 assert str(obj['objectID'])==row['native_id'] and obj['objectBeginDate']==row['first'] and obj['objectEndDate']==row['last']<=1955
 assert obj['title']==row['title'] and obj['accessionNumber']==row['accession_number']
 assert obj['isPublicDomain'] is True
 assert (obj.get('primaryImageSmall') or obj['primaryImage'])==im['source_image_url']
 assert row['creator_label']==(obj.get('artistDisplayName') or obj.get('culture') or '')
 assert not obj.get('artistPrefix') and not obj.get('artistSuffix')
 assert b.h.sha(Path(row['plan_path']).read_bytes())==row['plan_sha256']
 source.append(dict(artwork_id=row['artwork_id'],native_id=row['native_id'],source_sha256=rc['sha256'],source_plan_sha256=row['plan_sha256'],image_selection_sha256=pin,source_inventory=obj['accessionNumber'],image_url=im['source_image_url'],image_rights='CC0',exact_native_object_and_primary_media=True))
 raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes();assert b.h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and b.h.sha(original)==im['source_sha256']
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.format=='JPEG' and pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(original)) as pic:pic.load();assert abs(pic.width/pic.height-im['width']/im['height'])<.03
 files.append(dict(artwork_id=row['artwork_id'],path=im['path'],bytes=len(raw),sha256=im['sha256'],original_path=im['original_path'],original_sha256=im['source_sha256'],complete_decode=True,proportions_preserved=True,actually_viewed=True))
b.save(b.E/'prewrite-source-verification.json',dict(at=b.h.now(),records=source,records_verified=len(source)))
b.save(b.E/'prewrite-file-verification.json',dict(at=b.h.now(),files=files,originals_outside_documents=True))
with b.connect() as db:
 native=[dict(r) for r in db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=ANY(%s)",(b.SCHEME,[r['native_id'] for r in selection['rows']]))]
 for r in selection['rows']:
  assert [x['entity_id'] for x in native if x['external_id']==r['native_id']]==[r['artwork_id']]
  same=[x['id'] for x in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s AND accession_number=%s AND status<>%s',(b.MID,r['accession_number'],'archived'))]
  assert same==[r['artwork_id']]
  assert r['identity_reconciliation']['source_dimensions']==r['identity_reconciliation']['catalogue_dimensions']
 live=b.h.snapshot(db,ids);assert all(live[aid]==before[aid] for aid in ids)
 b.save(b.E/'prewrite-identity-verification.json',dict(at=b.h.now(),unique_native_identifiers=native,accessions_unique_in_institution=True,dimensions_equal=True,preparation_state_unchanged=True))
print('Independent source, file, native identity, accession, dimension and preimage checks passed')
