#!/usr/bin/env python3
"""Scoped, audited correction of batch172's native image summary only."""
import importlib.util,json,gzip,copy,fcntl
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from psycopg.types.json import Jsonb
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('b172',ROOT/'ops/continuous-batch-000172.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;E=b.E

def run():
 source=E/'identity-review-supplement.json';original=h.load(source);corrected=copy.deepcopy(original);checked=[]
 rows=b.i.selected(b.B)['rows']
 for r in corrected['rows']:
  row=next(x for x in rows if x['native_id']==r['native_id']);image=row['image']['source']['content']['descriptiveNonRepeating']['online_media']['media'][0]
  native=parse_qs(urlsplit(row['image']['image_url']).query)['id'][0];assert native==image['idsId']
  body=gzip.decompress(Path(r['current_native_page_receipt']['body_path']).read_bytes());assert h.sha(body)==r['current_native_page_receipt']['sha256'] and native in body.decode()
  prior=gzip.decompress((ROOT/r['previous_capture']['previous_source_capture']).read_bytes());assert h.sha(prior)==r['previous_capture']['previous_source_capture_sha256'] and native in prior.decode()
  assert r['native_image_id']=='deliveryService';r['native_image_id']=native;checked.append(dict(artwork_id=r['artwork_id'],native_id=r['native_id'],native_image_id=native,source_image_url=row['image']['image_url'],current_and_original_page_agree=True))
 corrected.update(correction_at=h.now(),supersedes_summary_path=str(source.relative_to(ROOT)),supersedes_summary_sha256=h.sha(source.read_bytes()),correction_reason='native_image_id summary parsed the endpoint path instead of query id; exact native source IDs and original URLs already persisted correctly; no object or image substitution')
 dest=E/'identity-review-supplement-v2.json';h.save(dest,corrected);pin=h.sha(dest.read_bytes());images,_,_=b.i.accepted(b.B);mids=[x['media_id'] for x in images]
 backup=b.i.BACKUP/'native-image-summary-before.json.gz'
 b.target('before-evidence-correction-write')
 with b.i.m.m.connect(write=True) as db:
  db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(b.i.m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  before=[dict(x) for x in db.execute('SELECT to_jsonb(e) v FROM media_rights_evidence e WHERE media_id=ANY(%s::uuid[]) ORDER BY media_id FOR UPDATE',(mids,))];assert len(before)==3
  if all((json.loads(x['v']['evidence_json']) if isinstance(x['v']['evidence_json'],str) else x['v']['evidence_json']).get('identity_review_supplement_correction_sha256')==pin for x in before):print('Correction already applied; verify only')
  else:
   h.save(backup,dict(at=h.now(),before=before,correction_sha256=pin))
   for x in before:
    record=x['v'];assert record['adapter_version']==b.OP;ev=json.loads(record['evidence_json']) if isinstance(record['evidence_json'],str) else record['evidence_json'];assert ev['identity_review_supplement_sha256']==h.sha(source.read_bytes())
    ev['native_identity_review']=corrected;ev['identity_review_supplement_correction_sha256']=pin;ev['identity_review_supplement_correction_reference']=str(dest.relative_to(ROOT))
    db.execute('UPDATE media_rights_evidence SET evidence_json=%s WHERE media_id=%s AND adapter_version=%s',(json.dumps(ev,ensure_ascii=False),record['media_id'],b.OP))
    after=dict(db.execute('SELECT to_jsonb(e) v FROM media_rights_evidence e WHERE media_id=%s',(record['media_id'],)).fetchone())['v']
    db.execute("INSERT INTO audit_log(actor_user_id,action,entity_type,entity_id,before_json,after_json) VALUES(%s,'update','media_rights_evidence',%s,%s,%s)",(b.i.m.ACTOR,record['media_id'],Jsonb(record),Jsonb(after)))
   db.commit()
 with h.connect() as db:
  after=[dict(x) for x in db.execute('SELECT to_jsonb(e) v FROM media_rights_evidence e WHERE media_id=ANY(%s::uuid[]) ORDER BY media_id',(mids,))]
  audit=[dict(x) for x in db.execute("SELECT entity_id::text,before_json,after_json FROM audit_log WHERE entity_type='media_rights_evidence' AND entity_id=ANY(%s::uuid[]) AND after_json->>'adapter_version'=%s",(mids,b.OP))]
 assert len(after)==len(audit)==3
 for x in after:
  ev=x['v']['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
  assert ev['identity_review_supplement_correction_sha256']==pin and ev['native_identity_review']==corrected
  event=next(a for a in audit if a['entity_id']==x['v']['media_id']);assert event['after_json']==x['v']
 h.save(E/'independent-evidence-correction-verification.json',dict(at=h.now(),source_summary_sha256=h.sha(source.read_bytes()),corrected_summary_sha256=pin,source_image_id_checks=checked,preimage_path=str(backup),preimage_sha256=h.sha(backup.read_bytes()),after=after,audit=audit,verified=True,additional_artwork_or_image_increments=0,scope='Only batch172 evidence summary corrected; exact source captures, selection, images and catalogue records preserved'))
 print('Corrected and independently audited3 native image ID summaries')
if __name__=='__main__':
 with (b.R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);run()
