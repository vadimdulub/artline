import importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000292.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
p,pin=h.pinned(b.PHASE);byid={r['artwork_id']:r for r in p['records']};a=h.load(i.folder(b.B)/'quality-audit.json');assert len(a['prepared_images'])==4 and not a['identity_holds']
notes={
'1792488':'Original and derivative individually viewed. Entire gold panel with John at left holding Gospel, naked Vasily at right, Christ above in red semicircle. Green ground with gold plants, broad gilded border and all outer edges preserved. Matches native9355 description/front5871910. Late16th-century wording retained; no exact year assigned.',
'1788649':'Original and derivative individually viewed. Full-length winged Michael in green tunic and pale mantle, holding a large globe against a yellow rocky landscape. Broad worn border and bottom panel losses retained. Matches native9354/front5871897. Closest existing Greek300358 image individually viewed: bust in armour and red mantle with raised sword on dark background; clearly a different composition and25x19cm panel.',
'1791063':'Original and derivative individually viewed. Complete October calendar icon with four horizontal registers of saints, Cyrillic heading on wide brown upper border and green panel edge. Resurrection near centre of first row and small inserted scenes agree with native11299/front5672922. All margins retained; one physical panel, not four separate works.',
'1791256':'Original and derivative individually viewed. Complete single panel with six creation roundels at upper centre, enthroned Christ and rows of saints below, narrative scenes and evangelists around outer border. Green-red edge and entire lower margin preserved. Matches native11305/front5878296. Multi-scene icon is one eighteenth-century panel, not multiple records; not the medieval Hildegard manuscript work.'}

dec=[]
for im in a['prepared_images']:
 r=byid[im['artwork_id']];assert h.sha(Path(im['path']).read_bytes())==im['sha256'] and h.sha(Path(im['original_path']).read_bytes())==im['source_sha256']
 dec.append(dict(artwork_id=im['artwork_id'],source_id=r['source_id'],sha256=im['sha256'],path=im['path'],original_path=im['original_path'],original_sha256=im['source_sha256'],decision='accept',viewed_individually=True,original_actually_viewed=True,derivative_actually_viewed=True,tool='view_image',basis=notes[r['source_id']],full_supplied_composition=True,flags_reviewed=im['flags'],flag_resolution='Manual source_display_placeholder flag inspected: authentic complete painted fronts, no placeholder or detail crop.',match_editorial_confidence=.99))
review=dict(at=h.now(),batch=b.B,batch_quality_decision='accept',decisions=dec,actually_viewed=4,originals_actually_viewed=4,derivatives_actually_viewed=4,unsampled=0,metadata_plan_sha256=pin,method='All original reproductions and prepared derivatives individually viewed with view_image; one existing collision image also viewed. No booklet viewing claimed.')
h.save(i.folder(b.B)/'visual-review.json',review);b.save('actual-visual-review.json',review)
collision=h.load(b.E/'collision-image-captures.json');assert len(collision['images'])==1
for im in collision['images']:assert h.sha(Path(im['path']).read_bytes())==im['sha256']
b.save('collision-visual-resolution.json',dict(at=h.now(),source_id='1788649',images=collision['images'],actually_viewed=1,decision='distinct_from_existing_Greek300358_composition',basis=notes['1788649'],prior_metadata_review='global-title-collision-review.json'))
for f in h.load(b.E/'local-recovery-verification.json')['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
b.save('prewrite-verification.json',dict(at=h.now(),passed=True,metadata_plan_sha256=pin,image_selection_sha256=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes()),visual_review_sha256=h.sha((i.folder(b.B)/'visual-review.json').read_bytes()),selected=4,prepared=4,images_actually_viewed=4,originals_actually_viewed=4,new_painters=0,shared_ingestion_lock='artline-curated-ingestion',recovery='Verified production schema archive plus exact affected-row preimages',prior_campaigns_not_counted=True))
print('Four original/derivative visual decisions pinned; closest existing image match excluded by viewed composition')
