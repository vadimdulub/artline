#!/usr/bin/env python3
"""Record actual image viewing and independently verify each prepared file."""
import fcntl,importlib.util,io
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-warsaw-batch-000060.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
observations={
'455222':'Crowned standing Mother and Child in mandorla above star, landscape and small side saints. Full painted board and border visible; wear and cracks retained.',
'455236':'Hodegetria Mother and Child with restored ochre surrounding field and trefoil-shaped old painted area. Museum full supplied rectangular composition retained, matching current 50 x 38.5 cm proportions. Source describes historic alteration and 2008-09 conservation; no artificial reconstruction or detail substitution.',
'498353':'Complete cast cross with Crucifixion, paired lateral saints and blue/white enamel. Entire openwork outline retained with background. One physical cross, not separate figures.',
'498400':'Mounted winged Michael on red horse, spear toward abyss, book and horn; Christ medallion above. Whole dark board and gilded interior frame, including projecting upper medallion, retained.',
'498403':'Kneeling Dorofei before Mother-and-Child icon at upper left; four border saints and full dark board retained. Thin gold inner frame intact.',
'498430':'Whole rectangular brass plaque with Mother and Child in eight-point star, surrounding angels and corners with scenes; blue and white enamel preserved. Large source background retained.',
'498545':'Single multi-scene board: Deesis across top and two Marian images below. Complete board outline and source wear visible; counts once.',
'498573':'Crucifixion on central inset painted wooden cross with lateral standing figures and upper inscription. Complete outer rectangle retained; one composite historic inventory object, not separately counted inset.',
'498597':'Entire brass Deesis plaque, enthroned Christ surrounded by saints and kneeling figures, triangular openwork border with enamel. No missing image edges.',
'498620':'Mother embraces standing Child inside painted room. Full golden border and board perimeter visible, red garment and background preserved.',
'498624':'Seated bound Christ with thorn crown in architectural cell; light from upper left. Complete board and brown border visible.',
'498685':'Vladimir Mother and Child with touching faces, two standing side saints and broad brown border. Full rectangular board, gold background and source condition retained.',
'499384':'Complete long brass eight-ended cross with Crucifixion, upper Father and dove, blue/white enamel and lower skull. Full physical outline visible; no reverse view claim.',
'499389':'Worn brass plaque with unidentified bishop holding book and upper Mandylion tab. Entire outline visible; weak facial detail is documented casting condition, not placeholder.',
'499466':'Opened joined cast triptych with central Nicholas, upper Trinity/cherubim/Mandylion and two wings of feast scenes. All connected parts and outline retained; one object, not three records.'}
files=[];decisions=[]
for r in i.selected(b.B)['rows']:
 im=h.load(i.folder(b.B)/'prepared'/(r['artwork_id']+'.json'));assert im['state']=='prepared';raw=Path(im['path']).read_bytes();orig=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and h.sha(orig)==im['source_sha256'] and len(raw)==im['bytes']<=100000
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.format=='JPEG' and pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(orig)) as pic:pic.load();assert abs(pic.width/pic.height-im['width']/im['height'])<.03
 assert '/Documents/' not in im['original_path']
 decisions.append(dict(artwork_id=r['artwork_id'],source_id=r['native_id'],artist=r['creator_label'],sha256=im['sha256'],decision='accept',viewed_individually=True,viewed_path=im['path'],tool='functions tools.view_image',observations=observations[r['native_id']],flag_resolution='Individual actual derivative viewed; complete supplied museum composition and native inventory association accepted.',identity_confidence=.99,confidence_basis='Exact native object/image, inventory, dimensions, source description and observed physical composition; editorial judgment, not calibrated probability.'))
 files.append(dict(artwork_id=r['artwork_id'],sha256=im['sha256'],bytes=im['bytes'],complete_decode=True,proportions_preserved=True,original_sha256=im['source_sha256'],original_path=im['original_path']))
assert len(decisions)==15
review=dict(at=h.now(),batch_quality_decision='accept',reviewer='Codex actual image viewing',decisions=decisions,all_selected_files_individually_viewed=True,sample_only_files=[],limitations='Museum source images are 315 px wide. Compositions and complete supplied frames reviewed; no claim to inspect absent reverse views or tiny illegible inscriptions. Originals decoded and hashed; derivatives individually visually viewed.')
h.save(i.folder(b.B)/'visual-review.json',review);b.save('actual-visual-review.json',review);b.save('prewrite-file-verification.json',dict(at=h.now(),files=files,plan_sha256=h.pinned(b.PHASE)[1]))
print('15 actual per-image visual decisions and complete file checks saved')
