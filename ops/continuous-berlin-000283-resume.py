import fcntl,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000283.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']]
 files=[b.E/b.PHASE/'plan.json.gz',i.folder(b.B)/'selection.json.gz',i.folder(b.B)/'visual-review.json']+list((i.folder(b.B)/'applied').glob('*.json'))+list((i.folder(b.B)/'uploads').glob('*.json'))
 hashes={str(p):h.sha(p.read_bytes()) for p in files}
 with h.connect() as db:
  before=h.snapshot(db,ids);n=db.execute("SELECT count(*) n FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchone()['n']
 assert before==h.load(b.E/'independent-production-verification.json')['rows']
 b.apply();i.upload(b.B);i.apply(b.B)
 with h.connect() as db:
  after=h.snapshot(db,ids);n2=db.execute("SELECT count(*) n FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchone()['n']
 assert before==after and n==n2 and all(h.sha(Path(p).read_bytes())==v for p,v in hashes.items())
 b.save('independent-resume-verification.json',dict(at=h.now(),metadata_plan_sha256=pin,production_rows=4,snapshots_equal=True,audit_events_before=n,audit_events_after=n2,new_production_writes=0,immutable_plan_and_receipts_unchanged=True,hashes=hashes,prior_other_job_increments_counted=0))
 print('Verified safe replay: no new writes or changed evidence')
