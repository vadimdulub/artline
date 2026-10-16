#!/usr/bin/env python3
"""Bounded batch 58: immutable French reserve audit, then Princeton gaps."""
import csv, fcntl, importlib.util, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('princeton55',ROOT/'ops/continuous-princeton-images-000055.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
i=b.i;h=b.h;load=b.load;connect=b.connect;target=b.target;APPROVAL=b.APPROVAL
E=ROOT/'docs/research/continuous-production-20261011/batches/000058'
RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000058'
B=b.B
b.E=E;b.RUNTIME=RUNTIME
i.OP='continuous-primary-images-20261011-b000058';i.RUN=E
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for p in [E,RUNTIME,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
save=b.save

def preflight():
 save(E/'production-target-reconciliation.json',target())
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(registry.open()))
 queue=load(E.parents[1]/'source-queue.json');assert len(reg)==len(queue['sources'])==111
 assert {x['source_id'] for x in reg}=={x['source_id'] for x in queue['sources']}
 paths=[ROOT/x for x in ['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json','ops/india-300-delivery-20261011.py','ops/illustrated-300k-20261011.py']]
 save(E/'required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in paths],registry_path=str(registry),registry_sha256=h.sha(registry.read_bytes()),registry_records=reg,registry_count=111,precedence='One externally supervised batch. Production authorized; real local catalogue read-only. No supervisor, historical plan or source hold changed.'))
 save(E/'source-queue-before.json',queue)
 priorholds=E.parent/'000057/source-access-holds.json';expanded=load(E.parent/'000056/source-access-holds.json')
 ledgers=expanded['ledgers']
 for x in ledgers:
  assert h.sha((ROOT/x['path']).read_bytes())==x['sha256']
 save(E/'source-access-holds.json',dict(at=h.now(),inherited_ledger=str(priorholds.relative_to(ROOT)),inherited_sha256=h.sha(priorholds.read_bytes()),verified_prior_ledgers=[dict(path=x['path'],sha256=x['sha256']) for x in ledgers],provider_holds_preserved=True,new_provider_holds=[],route='French saved captures and approved Princeton native API; no Yale or Princeton website requests'))
 r52=b.mod('reserve58','continuous-reserve-warsaw-000052-research.py');r52.E=E;r52.reserve()
 pp=ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';plan=load(pp);ids=[x['artwork_id'] for x in plan['rows']];pin=h.sha(pp.read_bytes())
 previous=E.parent/'000057';receipt=load(previous/'batch-verification-receipt.json');oldids=receipt['production_ids']
 with connect() as db:
  live=h.snapshot(db,ids)
  citations=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(ids,))]
  assert len(live)==len(citations)==188 and all(x['plan_sha256']==pin for x in citations)
  native=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
  for r in plan['rows']:
   a=live[r['artwork_id']]['artwork'];assert a['status']=='review' and a['accession_number']==r['accession_number'] and a['primary_media_id']==plan['images'][r['artwork_id']]['media_id']
   assert any(c['entity_id']==r['artwork_id'] and c['source_record_id']==r['native_id'] for c in citations)
  rows=[dict(x) for x in db.execute('SELECT a.id::text,a.primary_media_id::text,m.checksum_sha256::text,m.storage_path,e.adapter_version,e.evidence_json FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=m.id WHERE a.id=ANY(%s::uuid[])',(oldids,))]
  assert len(rows)==7
  pv=load(previous/'independent-production-verification.json')
  for r in rows:
   ev=r['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
   assert ev['selection_sha256']==receipt['image_selection_sha256'] and ev['batch_visual_review_sha256']==receipt['visual_review_sha256'] and '000057' in r['adapter_version']
   assert r['primary_media_id']==pv['rows'][r['id']]['artwork']['primary_media_id']
   old=next(x for x in pv['media'] if x['id']==r['id']);assert all(r[k]==old[k] for k in ['checksum_sha256','storage_path'])
  own=[dict(x) for x in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))]
  assert not own or (i.folder(B)/'selection.json.gz').exists()
 save(E/'french-reserve-live-reconciliation.json',dict(at=h.now(),plan_sha256=pin,inspected=188,already_imported_and_illustrated=188,unimported=0,selected=0,new_programme_increments=0,source_citations=citations,identifiers=native,live_rows=live,physical_date_review_preserved=['80082','80437','81054'],next_action='Princeton saved gaps. Historical reserve not replayed.'))
 save(E/'prior-batch-live-reconciliation.json',dict(at=h.now(),previous_batch=57,receipt_sha256=h.sha((previous/'batch-verification-receipt.json').read_bytes()),rows=rows,own_rights_rows=own,previous_increments_counted=0))
 p=next(s for s in queue['sources'] if s['source_id']=='princeton_art_museum');pending=p['resume_cursor']['unresearched_native_ids'][:25]
 pool=load(ROOT/p['resume_cursor']['frozen_input'])['rows'];byid={r['external_id']:r for r in pool}
 save(E/'bounded-gap-input.json',dict(at=h.now(),rows=[byid[x] for x in pending],remaining_unresearched=p['resume_cursor']['unresearched_native_ids'][25:]))
 for oid in pending:
  rc=b.capture(oid,'https://data.artmuseum.princeton.edu/objects/'+oid)
  if rc['status'] in [401,403,429]:break
  if rc['status']!=200:print(oid,'unavailable',rc['status'],flush=True);continue
  o=load(E/'source-captures'/(oid+'.body.gz'))
  print(json.dumps(dict(id=oid,title=o.get('displaytitle'),culture=o.get('cultureterms'),period=o.get('periodterms'),restrictions=o.get('restrictions'),creditlinerepro=o.get('creditlinerepro'),nowebuse=o.get('nowebuse'))),flush=True)

prepare=b.prepare;finish=b.finish;deliver=b.deliver
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
