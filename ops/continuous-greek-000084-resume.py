#!/usr/bin/env python3
"""Reconcile exact persisted attribution before replaying the completed batch."""
import importlib.util,fcntl,json
from pathlib import Path
s=importlib.util.spec_from_file_location('b84',Path(__file__).with_name('continuous-greek-batch-000084.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=h.load(b.E/'batch-verification-receipt.json');ids=receipt['production_ids'];p,pin=h.pinned(b.PHASE);images,_,_=i.accepted(b.B)
 assert pin==receipt['metadata_plan_sha256']
 with h.connect() as db:
  before=h.snapshot(db,ids);events=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']
  notes=db.execute("SELECT evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,b.FIELD)).fetchall();assert len(notes)==len(ids) and all(x['pin']==pin for x in notes)
  rights=db.execute('SELECT e.adapter_version,e.evidence_json FROM artworks a JOIN media_rights_evidence e ON e.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,)).fetchall()
  for r in rights:
   ev=r['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev;assert r['adapter_version']==b.OP and ev['selection_sha256']==receipt['image_selection_sha256']
 assert h.load(h.BACKUP/b.PHASE/'locked-before.json.gz')['artworks']=={}
 assert all(r['artwork']['primary_media_id'] is None for r in h.load(i.BACKUP/b.B/'before-000.json.gz').values())
 b.apply();b.deliver()
 with h.connect() as db:
  after=h.snapshot(db,ids);later=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']
 assert before==after and events==later
 credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=i.storage.Client(project='artline-508319',credentials=credentials);bucket=client.bucket(i.d.core.BUCKET);storage=[]
 for r in h.load(b.E/'independent-storage-verification.json')['records']:
  blob=bucket.blob(r['path']);blob.reload();assert str(blob.generation)==str(r['generation']);storage.append(dict(path=blob.name,generation=blob.generation,unchanged=True))
 b.save('independent-resume-verification.json',dict(at=h.now(),unchanged_snapshot=True,audit_events_before=events,audit_events_after=later,storage=storage,attribution_reconciled_before_replay=True,replay_increments={k:0 for k in receipt['verified_counts']}))
 print('Idempotent replay verified: zero changes')
