#!/usr/bin/env python3
"""Persist actual individual view_image observations, then validate selected files."""
import importlib.util,io
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('b','ops/continuous-warsaw-batch-000048.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
notes={
'498687':'Complete brown-bordered board; upper Resurrection above lower Descent into Hades, diagonal procession at right and gold mandorlas agree with source narrative.',
'498530':'Complete two-register board: mounted Archangel on red horse above, solitary praying saint below facing a small icon at left; full brown border retained.',
'498617':'Whole Pokrov board on gray photographic surround; upper central Virgin with ranks of saints and lower church-interior register; irregular wood edges retained.',
'498628':'Complete horizontal Deesis board: Christ central with open book, Virgin and Baptist at sides; intact painted gold border, no component cropped out.',
'498404':'Complete Baptism board: Christ in dark river, Baptist at left, angels at right, God above; full brown border preserved.',
'498631':'Complete four-register board of saints and Marian icons, including central Burning Bush; full green outer border visible. One multi-scene inventory, not scene-level additions.',
'498524':'Complete four-field board: Nativity, Burning Bush, Nicholas and reclining relics scene; small central medallion and ornate outer border; left-edge paint loss is part of object condition.',
'498630':'Complete Trinity board: enthroned Father and Son, globe and cross between them, surrounding angels and evangelist symbols; full brown outer border.',
'498676':'Whole darkened Stroganov-school narrative board; upper Resurrection, lower Descent, rising diagonal procession and surrounding scenes; worn surface and intact photographed edges. Modest resolution limits fine-detail comparison.'}
decisions=[];files=[]
for r in i.selected(b.B)['rows']:
 im=h.load(i.folder(b.B)/'prepared'/(r['artwork_id']+'.json'));assert im['state']=='prepared'
 raw=Path(im['path']).read_bytes();orig=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(orig)==im['source_sha256']
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(orig)) as pic:pic.load();assert abs(pic.width/pic.height-im['width']/im['height'])<.03
 decisions.append(dict(artwork_id=r['artwork_id'],source_id=r['native_id'],artist=r['creator_label'],sha256=im['sha256'],decision='accept',viewed_individually=True,review_method='functions tools.view_image on each actual prepared derivative',viewed_path=im['path'],flags_reviewed=im['flags'],note=notes[r['native_id']],limitations='Native museum display rendition, 315 pixels wide. Fine lettering/conservation detail not independently resolved; no unsampled or alternative files claimed viewed.'))
 files.append(dict(artwork_id=r['artwork_id'],path=im['path'],sha256=im['sha256'],bytes=im['bytes'],complete_decode=True,original_sha256=im['source_sha256'],original_path=im['original_path'],full_source_proportions=True))
review=dict(at=h.now(),batch=b.B,batch_quality_decision='accept',decisions=decisions,actual_viewed=9,unviewed_selected_files=0,notes='Every actual selected derivative was individually opened with image viewing tool; technical checks separately cover source originals. Native main-view IDs and title/subject/composition agree. Original rights labels and museum credits retained.')
h.save(i.folder(b.B)/'visual-review.json',review);b.save('actual-visual-review.json',review);b.save('prewrite-file-verification.json',dict(at=h.now(),files=files))
assert len(i.accepted(b.B)[0])==9
print('Actual visual review and complete file checks saved for nine images')
