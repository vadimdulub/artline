import fcntl,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000288.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']]
 files=[b.E/b.PHASE/'plan.json.gz',i.folder(b.B)/'selection.json.gz',i.folder(b.B)/'visual-review.json']+list((i.folder(b.B)/'applied').glob('*.json'))+list((i.folder(b.B)/'uploads').glob('*.json'))
 hashes={str(p):h.sha(p.read_bytes()) for p in files}
 with h.connect() as db:
  before=h.snapshot(db,ids);n=db.execute("SELECT count(*) n FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchone()['n']
 assert before==h.load(b.E/'independent-production-verification.json')['rows']
 b.save('production-target-before-resume-check.json',b.target())
 with h.connect() as db:
  notes=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,b.FIELD))]
  assert len(notes)==5 and all(x['pin']==pin for x in notes)
  assert h.load(h.BACKUP/b.PHASE/'locked-before.json.gz')['artworks']=={}
  images,_,_=i.accepted(b.B)
  rights=[dict(x) for x in db.execute('SELECT media_id::text,adapter_version,evidence_json FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',([im['media_id'] for im in images],))]
  assert len(rights)==5
  for r in rights:
   ev=r['evidence_json'] if isinstance(r['evidence_json'],dict) else json.loads(r['evidence_json']);assert r['adapter_version']==i.OP and ev['selection_sha256']==h.sha((i.folder(b.B)/'selection.json.gz').read_bytes())
  for im in images:
   assert before[im['artwork_id']]['artwork']['primary_media_id']==im['media_id']
   assert h.sha(Path(im['path']).read_bytes())==im['sha256'] and h.sha(Path(im['original_path']).read_bytes())==im['source_sha256']
 with h.connect() as db:
  after=h.snapshot(db,ids);n2=db.execute("SELECT count(*) n FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchone()['n']
 assert before==after and n==n2 and all(h.sha(Path(p).read_bytes())==v for p,v in hashes.items())
 b.save('independent-resume-verification.json',dict(at=h.now(),metadata_plan_sha256=pin,production_rows=5,snapshots_equal=True,audit_events_before=n,audit_events_after=n2,new_production_writes=0,immutable_plan_and_receipts_unchanged=True,hashes=hashes,prior_other_job_increments_counted=0,read_only=True,replay_required=False))
 print('Verified read-only resume: no new writes or changed evidence')
