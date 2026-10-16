#!/usr/bin/env python3
"""Read-only receipt reconciliation; never replays a completed transaction."""
import fcntl, importlib.util, json
from pathlib import Path

s=importlib.util.spec_from_file_location('batch180',Path(__file__).with_name('continuous-greek-batch-000180.py'))
b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=h.load(b.E/'batch-verification-receipt.json');p,pin=h.pinned(b.PHASE)
 assert pin==receipt['metadata_plan_sha256']
 proof=h.load(b.E/'independent-production-verification.json')
 images,audit,review=i.accepted(b.B)
 assert h.sha((i.folder(b.B)/'selection.json.gz').read_bytes())==receipt['image_selection_sha256']
 assert h.sha((i.folder(b.B)/'visual-review.json').read_bytes())==receipt['visual_review_sha256']
 b.target()
 with h.connect() as db:
  assert h.snapshot(db,receipt['production_ids'])==proof['after']
  notes=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s",(b.FIELD,))]
  assert len(notes)==4 and all(x['pin']==pin for x in notes)
  painter=h.load(b.E/'independent-new-painter-verification.json')
  assert db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(b.NEW_ARTIST,)).fetchone()['v']==painter['artist']
  rights=[dict(x) for x in db.execute('SELECT adapter_version,evidence_json FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',([x['media_id'] for x in images],))]
  assert len(rights)==4
  for x in rights:
   ev=json.loads(x['evidence_json']) if isinstance(x['evidence_json'],str) else x['evidence_json']
   assert x['adapter_version']==b.OP and ev['selection_sha256']==receipt['image_selection_sha256'] and ev['original_catalogue_plan_sha256']==pin
 for im in images:
  assert h.sha(Path(im['path']).read_bytes())==im['sha256'] and h.sha(Path(im['original_path']).read_bytes())==im['source_sha256']
 assert h.load(h.BACKUP/b.PHASE/'locked-before.json.gz')['artworks']=={}
 assert h.load(h.BACKUP/b.PHASE/'locked-before.json.gz')['new_artist_preimages']==[]
 out=dict(at=h.now(),passed=True,live_rows_equal=True,painter_equal=True,own_source_and_rights_plan_pins_verified=True,empty_metadata_transaction_preimages=True,new_production_writes=0,replay_required=False,previous_campaign_increments=0,local_catalogue_connections=0)
 name='independent-read-only-resume-verification.json'
 if (b.E/name).exists():name='independent-read-only-resume-recheck-'+str(len(list(b.E.glob('independent-read-only-resume-recheck-*.json')))+1).zfill(3)+'.json'
 b.save(name,out);print(json.dumps(out))
