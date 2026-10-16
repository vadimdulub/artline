#!/usr/bin/env python3
"""Prove the verified bounded batch resumes without new writes."""
import fcntl,importlib.util,json
s=importlib.util.spec_from_file_location('b','ops/continuous-nsw-images-000043.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;i=b.i
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=h.load(b.E/'batch-verification-receipt.json');ids=receipt['production_ids']
 assert h.sha((i.folder(b.B)/'selection.json.gz').read_bytes())==receipt['selection_sha256']
 def state():
  with b.connect() as db:
   return dict(rows=h.snapshot(db,ids),audit=[dict(x) for x in db.execute("SELECT entity_id::text,action,count(*) n FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) GROUP BY entity_id,action ORDER BY entity_id,action",(ids,))],rights=[dict(x) for x in db.execute('SELECT a.id::text,m.adapter_version,m.evidence_json FROM artworks a JOIN media_rights_evidence m ON m.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(ids,))])
 before=state()
 for row in before['rights']:
  ev=row['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev;assert row['adapter_version']==i.OP and ev['selection_sha256']==receipt['selection_sha256']
 paths=list((i.folder(b.B)/'applied').glob('*.json'))+list((i.folder(b.B)/'uploads').glob('*.json'));hashes={str(p):h.sha(p.read_bytes()) for p in paths}
 b.deliver();after=state();assert before==after and hashes=={str(p):h.sha(p.read_bytes()) for p in paths}
 b.save('independent-resume-verification.json',dict(at=h.now(),method='Reinvoke completed bounded delivery with fresh target checks; compare production rows, relationships, source/selection rights evidence, audit counts and immutable upload/application receipts.',production_ids=ids,selection_sha256=receipt['selection_sha256'],before_after_identical=True,receipts_unchanged=True,no_new_writes_on_resume=True,additional_primary_images=0,audit_counts=after['audit']))
 print('Resume verified: no new rows, associations, images or audit changes')
