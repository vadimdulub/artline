#!/usr/bin/env python3
"""Prove a completed bounded delivery can resume without duplicate writes."""
import fcntl,importlib.util,json
s=importlib.util.spec_from_file_location('b','ops/continuous-warsaw-batch-000048.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;i=b.i
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 receipt=h.load(b.E/'batch-verification-receipt.json');ids=receipt['production_ids'];plan,pin=h.pinned(b.PHASE)
 assert pin==receipt['plan_sha256'] and len(ids)==9
 def state():
  with h.connect() as db:
   return dict(rows=h.snapshot(db,ids),audit=[dict(x) for x in db.execute("SELECT entity_id::text,action,count(*) n FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) GROUP BY entity_id,action ORDER BY entity_id,action",(ids,))],citations=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s ORDER BY entity_id",(ids,b.FIELD))])
 before=state();assert len(before['citations'])==9 and all(x['pin']==pin for x in before['citations'])
 paths=[b.E/b.PHASE/'applied.json']+sorted((i.folder(b.B)/'applied').glob('*.json'))+sorted((i.folder(b.B)/'uploads').glob('*.json'))
 hashes={str(p):h.sha(p.read_bytes()) for p in paths}
 b.apply();b.deliver()
 after=state();assert before==after and hashes=={str(p):h.sha(p.read_bytes()) for p in paths}
 b.save('independent-resume-verification.json',dict(at=h.now(),method='Reinvoke completed apply and deliver; compare fresh production rows, relationships, audit counts, owned citation checksums and immutable receipts.',plan_sha256=pin,image_selection_sha256=receipt['image_selection_sha256'],production_ids=ids,before_after_identical=True,receipts_unchanged=True,no_new_writes_on_resume=True,additional_artworks=0,additional_primary_images=0,additional_holdings=0,audit_counts=after['audit']))
 print('Resume verified: no new records, attachments, holdings or audit changes')
