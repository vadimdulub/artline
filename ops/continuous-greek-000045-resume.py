#!/usr/bin/env python3
"""Read-only reconciliation plus idempotent replay of this exact persisted plan."""
import importlib.util,json,fcntl
from pathlib import Path
s=importlib.util.spec_from_file_location('b45',Path(__file__).with_name('continuous-greek-batch-000045.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']]
 with h.connect() as db:
  before=h.snapshot(db,ids);events=[dict(x) for x in db.execute('SELECT id::text FROM audit_log WHERE entity_id=ANY(%s::uuid[]) ORDER BY id',(ids,))]
 b.apply();b.deliver()
 with h.connect() as db:
  after=h.snapshot(db,ids);events2=[dict(x) for x in db.execute('SELECT id::text FROM audit_log WHERE entity_id=ANY(%s::uuid[]) ORDER BY id',(ids,))]
 assert before==after and events==events2
 b.save('independent-resume-verification.json',dict(at=h.now(),metadata_plan_sha256=pin,snapshot_sha256=h.sha(json.dumps(before,sort_keys=True,default=str).encode()),artwork_ids=ids,unchanged_snapshot=True,unchanged_audit_events=True,replay_increments=dict(new_painters=0,new_artworks=0,newly_illustrated=0,alternate_images=0,museum_links=0)))
 print('Exact plan replay verified: zero changes')
