#!/usr/bin/env python3
"""Prove replay of metadata and image entry points changes nothing."""
import fcntl,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-shuzo-000079.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 rc=h.load(b.E/'batch-verification-receipt.json');ids=rc['production_ids'];p,pin=h.pinned(b.PHASE);assert pin==rc['metadata_plan_sha256']
 with h.connect() as db:
  before=h.snapshot(db,ids);artist=db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(b.ARTIST,)).fetchone()['v'];inst=db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(b.MID,)).fetchone()['v']
  count=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids+[b.ARTIST,b.MID],)).fetchone()['n']
  notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s AND entity_id=ANY(%s::uuid[])",(b.FIELD,ids)).fetchall();assert len(notes)==4 and all(r['pin']==pin for r in notes)
  rights=db.execute('SELECT evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(b.OP,)).fetchall();assert len(rights)==4
  for x in rights:
   ev=x['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev;assert ev['selection_sha256']==rc['image_selection_sha256'] and ev['batch_visual_review_sha256']==rc['visual_review_sha256']
 b.apply();b.deliver()
 with h.connect() as db:
  assert h.snapshot(db,ids)==before
  assert db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(b.ARTIST,)).fetchone()['v']==artist
  assert db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(b.MID,)).fetchone()['v']==inst
  aftercount=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids+[b.ARTIST,b.MID],)).fetchone()['n'];assert count==aftercount
 credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=i.storage.Client(project='artline-508319',credentials=credentials);bucket=client.bucket(i.d.core.BUCKET);checks=[]
 for row in h.load(b.E/'independent-storage-verification.json')['records']:
  blob=bucket.blob(row['path']);blob.reload();assert str(blob.generation)==str(row['generation']);checks.append(dict(path=row['path'],generation=blob.generation,unchanged=True))
 b.save('independent-resume-verification.json',dict(at=h.now(),metadata_and_image_entrypoints_replayed=True,persisted_plan_and_rights_pins_reconciled_before_replay=True,artworks_unchanged=True,artist_unchanged=True,institution_unchanged=True,audit_count_before=count,audit_count_after=aftercount,storage=checks,replay_increments={k:0 for k in rc['verified_counts']}))
 print('Actual metadata/image replay: zero changes')
