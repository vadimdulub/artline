#!/usr/bin/env python3
"""Persist actual individual visual review and verify live production gaps."""
import importlib.util,io,json,fcntl
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('b65','ops/continuous-rijks-images-000065.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i;h=b.h
lock=(b.RUNTIME/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
notes=[
'Torch-lit crowd rioting in a street outside a house; complete plate, Dutch caption and broad paper margins retained.',
'Night procession dragging a coffin through the street by torchlight; plate number 3 and complete caption and paper retained.',
'Torchlit burial inside a columned church, plate number 4; complete supplied sheet with fold lines and margins.',
'Allegorical woman on a throne with two standing women and a kneeling man; separate verse below is part of the explicitly titled title-page-and-verse object. Full supplied mount and inventory annotations preserved.',
'Allegorical woman and cherub beside a monument labelled alliance with France; corresponding separate verse below. Complete title-page-and-verse object retained, distinct from volume VI.',
'Tree-lined street and maritime school with rigging, plus separate oval medallion below. Both components explicitly named by the source; full supplied mount and margins retained.',
'Horizontal river landscape with rowboat in foreground, buildings at right and sailboat at left; full plate and broad paper margins.',
'Rocky landscape with waterfall at right and two figures at lower left; complete supplied narrow-margined print, not substituted for a detail.',
'Harbour with moored sailing ships and sluice structure near centre; full horizontal plate and paper margins.',
'River landscape with bridge and figures, church and boats in distance; complete supplied plate, pencil annotation and paper margins.',
'Village landscape centred on a steep-roofed church, figures and low stone wall; full plate and surrounding paper.',
'Oval portrait of Theodorus Beza with long beard, cap and Latin caption in two columns; full printed border and lower text. Distinct plate and inscription from the next Beza portrait.',
'Oval Beza portrait with rectangular corner decoration and Dutch verse beneath; full supplied print, distinct border and lettering from the Latin-caption portrait.',
'Left-facing oval portrait of Johannes Calvin with cap, beard and Dutch verse; whole printed border and lower caption preserved.',
'Engraved Heinsius title page with two allegorical women, fleet above and shield below; complete loose-sheet reproduction. Exact source inventory kept distinct from bound-page impression.',
'Same Heinsius title-page composition photographed as a bound page, with leaf edges and book support visible. Native inventory and distinct impression retained; entire supplied frame preserved.'
]
audit=b.load(i.folder(b.B)/'quality-audit.json');assert len(audit['prepared_images'])==len(notes)==16 and not audit['identity_holds'] and not audit['preparation_holds']
rows={r['artwork_id']:r for r in i.selected(b.B)['rows']};decisions=[];files=[];sources=[]
for im,note in zip(audit['prepared_images'],notes):
 r=rows[im['artwork_id']];raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes()
 assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(original)==im['source_sha256']
 assert Path(im['path']).resolve().is_relative_to((b.ROOT/'apps/web/public/assets/artworks/imported'/i.OP).resolve())
 assert Path(im['original_path']).resolve().is_relative_to((Path.home()/'Library/Application Support/Artline/source-images').resolve())
 with Image.open(io.BytesIO(raw)) as pic:pic.verify()
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height']) and pic.format=='JPEG'
 with Image.open(io.BytesIO(original)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'] and abs(pic.width/pic.height-im['width']/im['height'])<.03
 decisions.append(dict(artwork_id=im['artwork_id'],native_id=r['native_id'],sha256=im['sha256'],artist=im['artist'],title=im['title'],decision='accept',viewed_individually=True,tool='functions tools.view_image',viewed_path=im['path'],note=note,flags_reviewed=im['flags'],physical_version_review='Exact native inventory and image; captions, mounts, separate impressions and bound-page context preserved. No composition-only substitution.'))
 files.append(dict(artwork_id=im['artwork_id'],path=im['path'],sha256=im['sha256'],bytes=len(raw),original_path=im['original_path'],original_sha256=im['source_sha256'],full_decode=True,proportions_preserved=True,actually_viewed=True))
 sources.append(b.sourcecheck(r))
review=dict(at=h.now(),batch=b.B,batch_quality_decision='accept',decisions=decisions,scope='All 16 prepared derivatives individually viewed in this turn, plus contact sheet. Original files fully decoded but not claimed individually visually inspected.',prior_visual_evidence='No prior reserve visual review exists; new decisions recorded here. Prior technical evidence remains immutable.')
b.save(i.folder(b.B)/'visual-review.json',review);b.save(b.E/'actual-visual-review.json',review)
images,_,_=i.accepted(b.B);ids=[im['artwork_id'] for im in images]
with b.connect() as db:
 live=h.snapshot(db,ids);prior=b.load(b.E/'preparation-production-snapshot.json.gz')['before'];assert all(live[aid]==prior[aid] and live[aid]['artwork']['primary_media_id'] is None for aid in ids)
 assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=ANY(%s)',([im['sha256'] for im in images],)).fetchall()
pin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());rv=h.sha((i.folder(b.B)/'visual-review.json').read_bytes())
b.save(b.E/'independent-prewrite-verification.json',dict(at=h.now(),selected=len(ids),selection_sha256=pin,visual_review_sha256=rv,file_checks=files,source_checks=sources,unchanged_primary_gaps=True,existing_image_hashes=0,all_individually_viewed=True))
print('Actual visual decisions and independent prewrite verified:',len(ids))
