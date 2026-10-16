#!/usr/bin/env python3
"""Record actual individual visual decisions and verify selected files before writes."""
import importlib.util,io,json
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('b64','ops/continuous-fng-images-000064.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i;h=b.h
notes=[
'Three women and cherubs around a red-draped couch beneath green curtains; complete supplied painting.',
'Group in a dark wooded landscape, seated woman holding a floral crown above a kneeling figure; naturally dark scene remains legible, full vertical composition.',
'Old waterside mill, boat and figures with horses on a snowy path; full vertical painting.',
'Pale fjord landscape with distant sails and mountains; full sheet including bottom inscription preserved.',
'Bust portrait of woman in a large white lace bonnet and blue shawl; full supplied pastel composition.',
'Artist working at an easel inside a furnished studio; full sheet and supplied bottom photographic colour strip and inventory label retained without cropping.',
'Oval portrait miniature of a wigged man in blue; entire gold pendant frame and hanging loop retained.',
'Standing long-haired man in red-brown drapery and lace with extended hand; full painting with dark background preserved.',
'Figures around a table with harp, musical pages and food; full horizontal composition.',
'Oval portrait of a woman in lace veil; signature and 1841 inscription at lower left, complete oval and surrounding supplied margins retained.',
'Bust portrait of woman in ornate gold-patterned dress and large lace ruff; full rectangular painting and supplied surface condition retained.',
'Portrait of grey-haired man in brown coat with hand at hip; complete supplied gold frame retained.',
'Interior with Jupiter, wing-helmeted Mercury and elderly hosts, bird near foreground; complete supplied vertical painting.',
'Left-facing man in cap smoking a short pipe, green coat; complete supplied panel with visible edge wear retained.',
'Boat party on calm morning water; complete supplied ornate frame and horizontal painted composition retained.'
]
audit=h.load(i.folder(b.B)/'quality-audit.json');assert len(audit['prepared_images'])==len(notes)==15 and not audit['identity_holds'] and not audit['preparation_holds']
rows=i.selected(b.B)['rows'];decs=[]
for im,note in zip(audit['prepared_images'],notes):
 row=next(r for r in rows if r['artwork_id']==im['artwork_id'])
 raw=Path(im['path']).read_bytes();orig=Path(im['original_path']).read_bytes()
 assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(orig)==im['source_sha256']
 with Image.open(io.BytesIO(raw)) as pic:pic.verify()
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(orig)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'];assert abs(pic.width/pic.height-im['width']/im['height'])<.03
 decs.append(dict(artwork_id=im['artwork_id'],native_id=row['native_id'],sha256=im['sha256'],artist=im['artist'],title=im['title'],decision='accept',viewed_individually=True,tool='functions tools.view_image',viewed_path=im['path'],note=note,flags_reviewed=im['flags'],flag_resolution='source_display_placeholder is the forced-review marker. Actual authentic reproduction viewed; no placeholder or substituted detail found.'))
review=dict(at=h.now(),batch=b.B,batch_quality_decision='accept',decisions=decs,scope='All 15 prepared derivatives individually viewed in this turn. Source originals completely decoded; not claimed visually viewed.')
b.save(i.folder(b.B)/'visual-review.json',review);b.save(b.E/'actual-visual-review.json',review)
print('Recorded 15 actual individual visual decisions; technical checks passed')
