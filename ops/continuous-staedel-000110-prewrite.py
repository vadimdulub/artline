import importlib.util,io,json,csv
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('b','ops/continuous-staedel-images-000110.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);b.configure();i=b.i;h=b.h
notes=[
'Gold-ground panel of St Victor surrounded by soldiers under red arcades; raised figure above, intact supplied panel edges and lower abrasion retained.',
'Three brightly dressed Japanese dolls on draped table, two green apples at lower left, bottle behind; entire supplied still-life composition and lower-right signature retained.',
'Abstract landscape with curved red form at left, blue polygon at right, pale textured background; all supplied support edges and lower-right signature visible.',
'Full horizontal composition of fairies dancing in ring around alder tree beside water; dark tones remain legible, no detail crop.',
'Woman in dark dress touching caged male lion, roaring lioness at left; complete supplied cage wagon composition and lower-right signature preserved.',
'Deer beside broad lake under golden sunset, boat in reeds at lower left; complete landscape and sky preserved.',
'Snow-covered church ruins viewed through dark vaulted arch, columns at right and distant tower at left; all supplied edges preserved.'
]
audit=h.load(i.folder(b.B)/'quality-audit.json');ims=audit['prepared_images'];assert len(ims)==7 and not audit['identity_holds']
decisions=[dict(artwork_id=im['artwork_id'],sha256=im['sha256'],artist=im['artist'],decision='accept',viewed_individually=True,tool='functions tools.view_image',path=im['path'],original_separately_viewed=False,notes=note,flags_resolved=im['flags']) for im,note in zip(ims,notes)]
b.save('batches/'+b.B+'/visual-review.json',dict(at=h.now(),batch=b.B,batch_quality_decision='accept',decisions=decisions,flag_resolution='Generic preparation marks manual_visual_required as source_display_placeholder. All seven actual prepared files individually viewed and are authentic complete paintings, not placeholders.'))
ids=[im['artwork_id'] for im in ims];gap=h.load(b.E/'gap-input.json.gz')
with b.connect() as db:
 assert h.snapshot(db,ids)=={aid:gap['before'][aid] for aid in ids}
 assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=ANY(%s)',([im['sha256'] for im in ims],)).fetchall()
 assert not db.execute('SELECT media_id FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,)).fetchall()
for im in ims:
 for p,dims,digest in [(im['path'],[im['width'],im['height']],im['sha256']),(im['original_path'],im['original_dimensions'],im['source_sha256'])]:
  raw=Path(p).read_bytes();assert h.sha(raw)==digest
  with Image.open(io.BytesIO(raw)) as v:v.load();assert list(v.size)==dims
 assert im['bytes']<=100000
 assert abs(im['width']/im['height']-im['original_dimensions'][0]/im['original_dimensions'][1])<.005
b.save('independent-prewrite-verification.json',dict(at=h.now(),selection_sha256=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes()),visual_review_sha256=h.sha((i.folder(b.B)/'visual-review.json').read_bytes()),source_records=7,files_verified=7,unchanged_preimages=True,duplicate_checks_passed=True,shared_ingestion_lock='artline-curated-ingestion',passed=True))
latest=b.E.parent/'000109/source-access-holds.json'
b.save('latest-source-hold-reconciliation.json',dict(at=h.now(),inherited_ledger=str(latest),sha256=h.sha(latest.read_bytes()),records=h.load(latest),held_requests=0,staedel_route_available=True))
b.save('PREWRITE-CHECKPOINT.json',dict(at=h.now(),batch=110,stage='visually_reviewed_prewrite_verified',selected=7,production_changes=0,next_task='Create scoped recovery, verify production target, upload and attach seven images transactionally; independently verify attribution and delivery.'))
print('Seven images visually reviewed and prewrite validated')
