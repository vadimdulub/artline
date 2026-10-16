#!/usr/bin/env python3
"""Verify idempotent resumption against live snapshots and immutable receipts."""
import fcntl, importlib.util, json
s=importlib.util.spec_from_file_location('b','ops/continuous-warsaw-batch-000060.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;i=b.i;E=b.E
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']]
receipt=h.load(E/'batch-verification-receipt.json');assert receipt['plan_sha256']==pin and set(ids)==set(receipt['production_ids'])
def state():
    with h.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        return h.snapshot(db,ids),[dict(x) for x in db.execute('SELECT entity_type,entity_id::text,action,count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[]) GROUP BY entity_type,entity_id,action ORDER BY entity_type,entity_id,action',(ids,))]
before,audit_before=state()
paths=[E/b.PHASE/'plan.json.gz',E/b.PHASE/'applied.json',i.folder(b.B)/'selection.json.gz',i.folder(b.B)/'visual-review.json',i.folder(b.B)/'applied/000.json',h.BACKUP/b.PHASE/'locked-before.json.gz',i.BACKUP/b.B/'before-000.json.gz']
paths+=list((i.folder(b.B)/'prepared').glob('*.json'))+list((i.folder(b.B)/'uploads').glob('*.json'))
hashes={str(f):h.sha(f.read_bytes()) for f in paths}
b.stage();b.images();b.apply();b.deliver()
after,audit_after=state()
assert before==after and audit_before==audit_after
assert hashes=={str(f):h.sha(f.read_bytes()) for f in paths}
b.save('independent-resume-verification.json',dict(at=h.now(),production_ids=ids,metadata_plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],replayed_steps=['stage','images','apply','deliver'],live_snapshots_equal=True,audit_counts_before=audit_before,audit_counts_after=audit_after,immutable_file_checksums=hashes,new_production_increments_on_resume=0,local_database_connections=0))
print('Resume verified: no duplicate records, media, audit events or changed immutable files')
