#!/usr/bin/env python3
"""Reconcile committed attachment preimages before an idempotent bounded replay."""
import fcntl, importlib.util, json
from pathlib import Path
s=importlib.util.spec_from_file_location('w49',Path(__file__).with_name('continuous-tepapa-images-000049.py'))
w=importlib.util.module_from_spec(s);s.loader.exec_module(w);i=w.i;h=w.h
with (w.RUNTIME/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=w.load(w.E/'batch-verification-receipt.json');ids=receipt['production_ids'];images,_,_=i.accepted(w.B)
 with w.connect() as db:
  before=h.snapshot(db,ids)
  events_before=db.execute("SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])",(ids,)).fetchone()['n']
  media_before=[dict(r) for r in db.execute('SELECT a.id::text,mre.adapter_version,mre.evidence_json FROM artworks a JOIN media_rights_evidence mre ON mre.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,))]
 for r in media_before:
  ev=r['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
  assert r['adapter_version']==i.OP and ev['selection_sha256']==receipt['selection_sha256']
 preimages=i.BACKUP/w.B/'before-000.json.gz';old=w.load(preimages);assert all(old[aid]['artwork']['primary_media_id'] is None for aid in ids)
 w.save(w.E/'resume-target-reconciliation.json',w.target(True))
 w.b.deliver()
 with w.connect() as db:
  after=h.snapshot(db,ids);events_after=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']
 assert before==after and events_before==events_after
 credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=i.storage.Client(project='artline-508319',credentials=credentials);bucket=client.bucket(i.d.core.BUCKET)
 storage=w.load(w.E/'independent-storage-verification.json')['checks'];generations=[]
 for r in storage:
  blob=bucket.blob(r['storage_path']);blob.reload();assert str(blob.generation)==str(r['generation']);generations.append(dict(storage_path=blob.name,generation=blob.generation,unchanged=True))
 w.save(w.E/'independent-resume-verification.json',dict(at=h.now(),unchanged_snapshot=True,audit_events_before=events_before,audit_events_after=events_after,storage_generations=generations,attribution_reconciled_before_replay=True,preimages_sha256=h.sha(preimages.read_bytes()),replay_increments={k:0 for k in receipt['verified_counts']}))
 print('Replay verified: no row, audit or storage-generation changes')
