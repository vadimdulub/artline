#!/usr/bin/env python3
"""Independently validate batch290 source, file and live preimage evidence."""
import importlib.util,fcntl,gzip,io,json,re
from pathlib import Path
from PIL import Image
from urllib.parse import urlsplit,parse_qs
s=importlib.util.spec_from_file_location('b','ops/continuous-batch-000290.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
images,audit,review=i.accepted(b.B);rows=i.selected(b.B)['rows'];assert len(images)==len(rows)==1
expected={im['artwork_id']:im for im in images};ids=list(expected)
pin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());vpin=h.sha((i.folder(b.B)/'visual-review.json').read_bytes())
prior={x['snapshot']['artwork']['id']:x['snapshot'] for x in h.load(b.E/'identity-reconciliation.json')['rows'] if 'snapshot' in x}
source=h.load(b.E/'identity-review-supplement.json');assert len(source['rows'])==len(ids)
verified=[]
for row in rows:
 aid=row['artwork_id'];im=expected[aid];obj=row['image']['source'];d=obj['content']['descriptiveNonRepeating'];ft=obj['content']['freetext'];rc=row['image']['receipt'];raw=gzip.decompress((b.ROOT/rc['body_path']).read_bytes())
 assert h.sha(raw)==rc['sha256'] and obj in [json.loads(x) for x in raw.splitlines()]
 values=lambda k,label=None:[x['content'] for x in ft.get(k,[]) if label is None or x['label']==label]
 assert values('objectType')==['Painting'] and values('objectRights')==['CC0'] and d['metadata_usage']['access']=='CC0'
 assert values('identifier','Object number')==[row['accession_number']] and values('name','Artist')==[row['creator_label']]
 assert d['title']['content']==row['title'] and values('date','Date')==['1896'] and (row['first'],row['last'],row['precision'])==(1896,1896,'exact')
 assert parse_qs(urlsplit(d['record_link']).query)['id']==[row['native_id']]
 media=d['online_media']['media'];assert len(media)==1 and media[0]['usage']['access']=='CC0' and media[0]['content']==im['source_image_url']
 assert parse_qs(urlsplit(im['source_image_url']).query)['id']==[media[0]['idsId']] and urlsplit(im['source_image_url']).hostname=='ids.si.edu'
 current=next(x for x in source['rows'] if x['artwork_id']==aid);crc=current['current_native_page_receipt'];body=gzip.decompress(Path(crc['body_path']).read_bytes());assert h.sha(body)==crc['sha256'] and media[0]['idsId'] in body.decode()
 decision=next(x for x in review['decisions'] if x['artwork_id']==aid);assert decision['sha256']==im['sha256'] and decision['viewed_individually'] and decision['original_separately_viewed']
 payload=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes();assert h.sha(payload)==im['sha256'] and len(payload)==im['bytes']<=100000 and h.sha(original)==im['source_sha256']
 assert Path(im['original_path']).is_relative_to(Path.home()/'Library/Application Support/Artline/source-images')
 with Image.open(io.BytesIO(payload)) as pic:pic.load();assert pic.format=='JPEG' and pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(original)) as pic:
  pic.load();assert list(pic.size)==im['original_dimensions'];assert abs(pic.width/pic.height-im['width']/im['height'])<.005
  dims=re.search(r'\(([0-9.]+) x ([0-9.]+) cm\)',values('physicalDescription','Dimensions')[0]);assert dims;assert abs(float(dims[2])/float(dims[1])-pic.width/pic.height)<.03
 assert prior[aid]['artwork']['primary_media_id'] is None
 verified.append(dict(artwork_id=aid,native_id=row['native_id'],accession=row['accession_number'],original_sha256=im['source_sha256'],derivative_sha256=im['sha256'],bytes=im['bytes'],source_sha256=rc['sha256'],current_source_sha256=crc['sha256'],exact_native_image=media[0]['idsId'],complete_decoding=True,complete_composition_actual_review=True,metadata_and_holdings_unchanged=True))
with h.connect() as db:
 live=h.snapshot(db,ids);assert all(live[aid]==prior[aid] for aid in ids)
 assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=ANY(%s)',([x['sha256'] for x in images],)).fetchall()
 for row in rows:
  owners=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='saam-object' AND external_id=%s",(row['native_id'],)).fetchall();assert all(x['entity_id']==row['artwork_id'] for x in owners)
  assert not db.execute('SELECT id FROM artworks WHERE current_institution_id=%s AND accession_number=%s AND id<>%s',(b.MID,row['accession_number'],row['artwork_id'])).fetchall()
b.save('independent-prewrite-verification.json',dict(at=h.now(),selection_sha256=pin,visual_review_sha256=vpin,records=verified,unchanged_live_preimages=True,null_primary_ids=ids,duplicate_checksums=0,exact_physical_identity_verified=True,source_and_actual_visual_review_verified=True,local_catalogue_connections=0))
print('Independent prewrite passed: one exact source, actual visual decisions, byte checks and unchanged live gaps')
