#!/usr/bin/env python3
"""Reconcile delivered image attribution, replay, and prove zero increments."""
import importlib.util,fcntl,json
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-fng-images-000077.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
with (b.RUNTIME/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=h.load(b.E/'batch-verification-receipt.json');ids=receipt['production_ids'];images,_,_=i.accepted(b.B)
 assert h.sha((i.folder(b.B)/'selection.json.gz').read_bytes())==receipt['selection_sha256']
 assert h.sha((i.folder(b.B)/'visual-review.json').read_bytes())==receipt['visual_review_sha256']
 pre=h.load(i.BACKUP/b.B/'before-000.json.gz');assert all(pre[aid]['artwork']['primary_media_id'] is None for aid in ids)
 with b.connect() as db:
  before=h.snapshot(db,ids);events=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']
  rights=db.execute('SELECT a.id::text,e.adapter_version,e.evidence_json FROM artworks a JOIN media_rights_evidence e ON e.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,)).fetchall();assert len(rights)==len(ids)
  for r in rights:
   ev=r['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
   assert r['adapter_version']==i.OP and ev['selection_sha256']==receipt['selection_sha256'] and ev['batch_visual_review_sha256']==receipt['visual_review_sha256']
 b.deliver()
 with b.connect() as db:
  after=h.snapshot(db,ids);later=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']
 assert before==after and events==later
 credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=i.storage.Client(project='artline-508319',credentials=credentials);bucket=client.bucket(i.d.core.BUCKET);storage=[]
 for r in h.load(b.E/'independent-storage-verification.json')['checks']:
  blob=bucket.blob(r['storage_path']);blob.reload();assert str(blob.generation)==str(r['generation']);storage.append(dict(path=blob.name,generation=blob.generation,unchanged=True))
 b.save(b.E/'independent-resume-verification.json',dict(at=h.now(),unchanged_snapshot=True,audit_events_before=events,audit_events_after=later,storage=storage,attribution_reconciled_before_replay=True,replay_increments={k:0 for k in receipt['verified_counts']}))
 print('Idempotent replay verified: zero changes')
