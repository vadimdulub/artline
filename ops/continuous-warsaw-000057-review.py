#!/usr/bin/env python3
"""Persist actual per-image review and independent prewrite file/identity checks."""
import fcntl,gzip,importlib.util,io,json
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('b','ops/continuous-warsaw-batch-000057.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;i=b.i;E=b.E
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p,pin=h.pinned(b.PHASE)
observations={
'498434':'Full pendant with suspension tab and three angels seated at the table; ornamental border intact. No placeholder or crop. Small cast has ample source background, preserved.',
'498563':'Complete brass and blue/white enamel plaque with two mounted figures moving right; Trinity in upper medallion. Outer edges and upper tab retained.',
'498354':'Whole openwork cross with central Crucifixion, standing lateral figures, surrounding feast scenes and cherubin-shaped finials; complete outline retained.',
'498581':'Opened hinged brass triptych, all three joined parts visible. Central mounted Saint George and dragon, upper Trinity and Mandylion, four side feast panels. Count as one inventory, not separate wings.',
'499388':'Complete brass Feodorovskaya Mother and Child plaque with ornamental border and three cherub-shaped finials around upper Trinity. Worn relief is source condition.',
'498582':'Complete small Hodegetria/Smolensk brass plaque with tab, broad rectangular border and Mother and Child. Heavily worn facial features match source condition description, not a low-information placeholder.',
'498611':'Complete surviving eight-point star-shaped painted panel showing Luke holding closed book on left and John writing on right. Intact surviving outline and gold border visible. Source calls this a possible iconostasis fragment; it is a physical panel, not a detail crop or asserted whole iconostasis.'}
checks=[];decisions=[]
for row in i.selected(b.B)['rows']:
 im=h.load(i.folder(b.B)/'prepared'/(row['artwork_id']+'.json'));assert im['state']=='prepared'
 raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes()
 assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
 assert h.sha(original)==im['source_sha256'] and '/Documents/' not in im['original_path']
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.size==(im['width'],im['height']) and pic.format=='JPEG'
 with Image.open(io.BytesIO(original)) as pic:pic.load();assert abs(pic.width/pic.height-im['width']/im['height'])<.03
 decision=dict(artwork_id=row['artwork_id'],source_id=row['native_id'],sha256=im['sha256'],decision='accept',viewed_individually=True,viewed_path=im['path'],tool='functions tools.view_image',observations=observations[row['native_id']],flag_resolution='Manual visual gate reviewed individually; actual museum object and complete supplied composition confirmed. Any fragment wording refers to surviving object, not cropped image.',identity_confidence=.99,confidence_basis='Exact native inventory/image link plus source title, dimensions, materials, subject, date and observed complete physical object; editorial judgment, not calibrated probability.')
 decisions.append(decision);checks.append(dict(artwork_id=row['artwork_id'],sha256=im['sha256'],bytes=im['bytes'],complete_decode=True,proportions_preserved=True,original_sha256=im['source_sha256'],original_path=im['original_path']))
review=dict(at=h.now(),batch_quality_decision='accept',reviewer='Codex actual image viewing',decisions=decisions,all_selected_files_individually_viewed=True,sample_only_files=[],limitations='Source rendition width 315 px limits tiny inscription/paint-detail assessment. Actual object composition, edges and catalogue correspondence reviewed; no claim of viewing absent alternate sides.')
h.save(i.folder(b.B)/'visual-review.json',review);b.save('actual-visual-review.json',review);b.save('prewrite-file-verification.json',dict(at=h.now(),files=checks,plan_sha256=pin))
# Confirm exact inventories and historical numbers without conflating acquisition lots.
hist=sorted({str(v['number']) for r in p['records'] for v in r['raw']['extraNumPatterns']})
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 prior=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE accession_number=ANY(%s)',(hist,))];assert not prior
 assert not h.snapshot(db,[r['artwork_id'] for r in p['records']])
b.save('independent-historical-inventory-verification.json',dict(at=h.now(),historical_inventory_labels=hist,global_current_accession_matches=prior,interpretation='13552/06 repeats in multiple distinct source inventories; it is not used alone to merge physical objects. Current IK inventories, native image IDs, dimensions and composition distinguish individual casts and panel.',all_selected_new_ids_absent=True))
old=h.load(E.parent/'000052/research-review.json')['records'];pending=next(x for x in h.load(E/'source-queue-before.json')['sources'] if x['source_id']=='national_museum_warsaw')['resume_cursor']['pending_native_ids_current_page']
reasons={
'498561':'End-of-century cast is potentially eligible; retain exact late-century wording and resolve same-title 498434/other Trinity casting identities before a future plan.',
'498275':'1830 and E.U. goldsmith identity may concern the silver cover; compound IK 418/a-b requires component chronology and role review, not attribution of painting to goldsmith.',
'498307':'Literal 4. ćw. XIX/XX w. combines quarter-century and transition wording; do not invent exact date bounds.',
'498516':'Six separate cast plaques assembled on one board, two missing crosses; resolve any component catalogue identities and assembly chronology before selecting the ensemble.',
'498420':'Signed P.F. Burmistrow reverse dates the cross 9 February 1896; source says lateral figures differ stylistically. Resolve global named creator identity and component authorship/chronology, do not assign all parts automatically.',
'498578':'Mid nineteenth century is eligible in principle; preserve wording and use documented circa-range convention on future selection rather than invent an exact year.',
'498402':'XVIII/XIX transition wording plus substantial repainting needs documented creation-versus-repainting interpretation.',
'498533':'Compound inventory/cover; source questions whether image is podokładnia. Resolve material/version and XIX/XX transition bounds.',
'498529':'Compound inventory/cover; source questions podokładnica. Resolve exact physical components and XIX/XX transition bounds.',
'498614':'Surviving circular panel, XVIII/XIX wording with nineteenth-century repainting and later reverse paint. Resolve physical creation range separately from restoration.',
'498569':'Painting and elaborate cover share a-b inventory; reconcile both components and full supplied views before ensemble image/metadata selection.'}
records=[]
for r in old:
 if r['source_id'] not in pending:continue
 oid=r['source_id'];o,rc=b.capture(int(oid))
 selected=int(oid) in b.SELECTED
 records.append(dict(source_id=oid,accession=o['noEvidence'],title=o['title'],source_date=o['createDates'],source_creators=o['authors'],source_sha256=rc['sha256'],selected=selected,decision='resolved_for_selected_import' if selected else 'held_for_targeted_editorial_reconciliation',basis=observations[oid] if selected else reasons[oid],new_provider_request=False,hold_is_not_categorical_exclusion=True))
assert len(records)==18
b.save('page-three-editorial-dispositions.json',dict(at=h.now(),records=records,selected=7,held=11,source_date_not_photograph_date=True,no_directory_coverage_claim=True,next_discovery_page=4,unchanged_holds_not_to_be_retried=True))
b.save('web-tool-access-observations.json',dict(at=h.now(),urls=['https://cyfrowe.mnw.art.pl/pl/zbiory/498611','https://cyfrowe.mnw.art.pl/pl/zbiory/498563'],surface='web open',outcome='Tool reports not accessible; no HTTP code or provider denial supplied. No repeated web request. Saved official API capture is independently checksum-verified; seven selected native media returned HTTP 200.',provider_hold_created=False))
print('Seven actual individual visual decisions, file checks, historical inventory check and all 18 editorial dispositions saved')
