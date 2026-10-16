#!/usr/bin/env python3
"""Record actual individual visual decisions and verify selected files before writes."""
import importlib.util,io,json
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('b70','ops/continuous-fng-images-000077.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i;h=b.h
notes=['Oval portrait miniature of a white-haired clergyman, full gold oval frame and hanging ring on neutral backing retained; aged mottled surface is source condition, face legible.', 'Full standing turbaned older man in a dark coat on a green field, inscriptions at right and multilayer borders on yellow paper; complete supplied sheet retained.', 'Male artist in red-brown drapery holding a small oval portrait, other hand at lower right; full supplied vertical painting and dark background retained.', 'Oval royal portrait with white fur-trimmed robe, complete ornate gold frame with lions, crown, trumpets and leaves retained; no frame crop.', 'Cimon nursing at Pero’s breast beside a barred window, full supplied vertical Roman Charity composition; dark passages and all supplied edges retained.', 'Royal equestrian portrait on rearing dark horse beside water, clouds behind; all painted edges and source mount/background slivers retained, not cropped.', 'Anglers, dog and pond beneath tall trees and cloudy sky, complete supplied landscape and narrow wooden edge preserved; dark foreground figures visible.', 'Seated queen in black dress and white sleeves beside column and crown, black drapery above; full supplied vertical portrait retained.', 'Rocky Normandy shore with distant figures, sea and cloudy sky; full landscape, foreground pools and lower-left signature preserved.', 'Long-haired young man looking back in red drapery, full supplied dark portrait and narrow surrounding edge retained; face and clothing legible.', 'Nautilus cup, fallen glass, knife and peeled lemon on draped table; full supplied still life with curling peel to the bottom edge retained.']
audit=h.load(i.folder(b.B)/'quality-audit.json');assert len(audit['prepared_images'])==len(notes)==11 and not audit['identity_holds'] and not audit['preparation_holds']
rows=i.selected(b.B)['rows'];decs=[]
for im,note in zip(audit['prepared_images'],notes):
 row=next(r for r in rows if r['artwork_id']==im['artwork_id'])
 raw=Path(im['path']).read_bytes();orig=Path(im['original_path']).read_bytes()
 assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(orig)==im['source_sha256']
 with Image.open(io.BytesIO(raw)) as pic:pic.verify()
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(orig)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'];assert abs(pic.width/pic.height-im['width']/im['height'])<.03
 decs.append(dict(artwork_id=im['artwork_id'],native_id=row['native_id'],sha256=im['sha256'],artist=im['artist'],title=im['title'],decision='accept',viewed_individually=True,tool='functions tools.view_image',viewed_path=im['path'],note=note,flags_reviewed=im['flags'],flag_resolution='source_display_placeholder is the forced-review marker. Actual authentic reproduction viewed; no placeholder or substituted detail found.'))
review=dict(at=h.now(),batch=b.B,batch_quality_decision='accept',decisions=decs,scope='All 11 prepared derivatives individually viewed in this turn. Source originals completely decoded; not claimed visually viewed.')
b.save(i.folder(b.B)/'visual-review.json',review);b.save(b.E/'actual-visual-review.json',review)
print('Recorded 11 actual individual visual decisions; technical checks passed')
