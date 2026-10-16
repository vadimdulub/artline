import importlib.util,fcntl
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000292.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']]
 files=[b.E/b.PHASE/'applied.json']+list((i.folder(b.B)/'applied').glob('*.json'))+list((i.folder(b.B)/'uploads').glob('*.json'));before_files={str(x):h.sha(x.read_bytes()) for x in files}
 with h.connect() as db:
  before=h.snapshot(db,ids);audits=[dict(x) for x in db.execute("SELECT id::text FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(ids,))]
 b.apply();b.deliver()
 with h.connect() as db:
  after=h.snapshot(db,ids);assert before==after
  assert audits==[dict(x) for x in db.execute("SELECT id::text FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(ids,))]
  assert db.execute('SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==4
  labels=[dict(x) for x in db.execute('SELECT artwork_id::text,view_label FROM artwork_media WHERE artwork_id=ANY(%s::uuid[])',(ids,))]
  assert all(x['view_label']=='Complete supplied painted front' for x in labels)
  media=[dict(x) for x in db.execute('SELECT e.evidence_json FROM artworks a JOIN media_rights_evidence e ON e.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,))]
  import json
  for x in media:
   ev=json.loads(x['evidence_json']) if isinstance(x['evidence_json'],str) else x['evidence_json'];assert ev['user_approval']==h.load(b.E/'authorization.json')
 assert before_files=={str(x):h.sha(x.read_bytes()) for x in files}
 b.save('independent-resume-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,production_ids=ids,live_rows_before_after_equal=True,audit_rows_before_after_equal=True,receipt_checksums_unchanged=before_files,replayed_additions=0,new_credits_claimed=0,attachment_view_labels=labels,user_approval_separate_from_source_rights=True,supervisor_modified=False))
 print('Resume produced zero mutations; all live rows, audit events and receipts unchanged; view labels verified')
