"""Reconcile exact live delivery before idempotent replay; no new programme counts."""
import fcntl, importlib.util, json
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-athens-images-000278.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i
with (b.RUNTIME/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 images,_,_=i.accepted(b.B);ids=[x['artwork_id'] for x in images];media=[x['media_id'] for x in images]
 verified=b.load(b.E/'independent-production-verification.json');pin=b.h.sha((i.folder(b.B)/'selection.json.gz').read_bytes())
 with b.connect() as db:
  before=b.h.snapshot(db,ids);assert before==verified['after']
  rights=[dict(x) for x in db.execute('SELECT media_id::text,adapter_version,evidence_json FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',(media,))];assert len(rights)==len(ids)
  for r in rights:
   ev=r['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
   assert r['adapter_version']==i.OP and ev['selection_sha256']==pin
  audits=db.execute("SELECT count(*) n FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchone()['n']
 b.deliver()
 with b.connect() as db:
  after=b.h.snapshot(db,ids);assert after==before
  assert db.execute("SELECT count(*) n FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchone()['n']==audits
 b.save(b.E/'independent-resume-verification.json',dict(at=b.h.now(),selection_sha256=pin,production_ids=ids,exact_live_states_equal=True,live_own_rights_plan_verified=True,audit_events_unchanged=True,new_production_increments_on_resume=0,real_local_connections=0))
 print('Reconciled idempotent replay: zero new changes')
