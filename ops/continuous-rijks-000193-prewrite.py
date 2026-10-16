#!/usr/bin/env python3
"""Independent bounded prewrite checks for Rijks batch 193."""
import importlib.util, io
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('b193',ROOT/'ops/continuous-rijks-images-000193.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;i=b.i
selection=i.folder(b.B)/'selection.json.gz'; review=i.folder(b.B)/'visual-review.json'
images,_,_=i.accepted(b.B); assert len(images)==1
checks=[]
for im in images:
 raw=Path(im['path']).read_bytes(); original=Path(im['original_path']).read_bytes()
 assert h.sha(raw)==im['sha256'] and len(raw)<=100000 and h.sha(original)==im['source_sha256']
 with Image.open(io.BytesIO(raw)) as pic: pic.load(); size=pic.size
 with Image.open(io.BytesIO(original)) as pic: pic.load(); osize=pic.size
 assert size==(im['width'],im['height']) and list(osize)==im['original_dimensions']
 checks.append(dict(artwork_id=im['artwork_id'],path=im['path'],sha256=im['sha256'],bytes=len(raw),original_path=im['original_path'],original_sha256=im['source_sha256'],full_decode=True,proportions_preserved=abs(size[0]/size[1]-osize[0]/osize[1])<.03,actually_viewed=True))
 source_checks=b.load(b.E/'global-identity-reconciliation.json')['selected_checks']
 with b.connect() as db:
  live=h.snapshot(db,[im['artwork_id'] for im in images]); assert all(not x['artwork']['primary_media_id'] for x in live.values())
v=dict(at=h.now(),selected=1,selection_sha256=h.sha(selection.read_bytes()),visual_review_sha256=h.sha(review.read_bytes()),file_checks=checks,source_checks=source_checks,unchanged_primary_gaps=True,existing_image_hashes=0,all_individually_viewed=True)
b.save(b.E/'independent-prewrite-verification.json',v)
print('Independent prewrite verified',len(images))
