import importlib.util,csv,json,gzip,fcntl,subprocess
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000088.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 q=h.load(b.E.parents[1]/'source-queue.json');b.save('source-queue-before.json',q)
 inputs=[b.ROOT/'AGENTS.md',Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'),b.ROOT/'docs/ARTLINE_IMAGE_USE.md',b.ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md',b.ROOT/'docs/LOCAL_DATA_LOCATIONS.md',b.E.parents[1]/'CHECKPOINT.json',b.E.parents[1]/'source-queue.json',b.E.parent/'000087/CHECKPOINT.json',b.E.parent/'000087/source-access-holds.json',b.ROOT/'ops/india-300-delivery-20261011.py']
 reg=list(csv.DictReader(inputs[1].open()));assert len(reg)==111 and {x['source_id'] for x in reg}=={x['source_id'] for x in q['sources']}
 b.save('required-input-reconciliation.json',dict(at=h.now(),inputs=[dict(path=str(p),sha256=h.sha(p.read_bytes()),bytes=p.stat().st_size) for p in inputs],registry=reg,precedence='Current user approvals, one bounded batch, external supervisor unmodified, local catalogue read only.'))
 b.save('production-target-reconciliation.json',b.target())
 rc=h.load(b.E.parent/'000087/batch-verification-receipt.json');prev=h.load(b.E.parent/'000087/independent-production-verification.json')
 with h.connect() as db:
  live=h.snapshot(db,rc['production_ids']);assert live==prev['after']
  notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name='continuous_mplus_object_evidence_b000087' AND entity_id=ANY(%s::uuid[])",(rc['production_ids'],)).fetchall();assert len(notes)==21 and all(x['pin']==rc['metadata_plan_sha256'] for x in notes)
  own=db.execute('SELECT entity_id::text FROM citations WHERE field_name=%s',(b.FIELD,)).fetchall();assert not own
 b.save('prior-batch-live-reconciliation.json',dict(at=h.now(),previous_batch_verified=True,prior_batch=87,verified_rows=21,persisted_plan_checksum_verified=True,current_batch_citations=own,new_increments=0))
 reserve=b.mod('reserve88','continuous-reserve-warsaw-000052-research.py');reserve.E=b.E;reserve.reserve()
 pp=b.ROOT/'docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz';p=h.load(pp);pin=h.sha(pp.read_bytes());ids=[r['artwork_id'] for r in p['rows']]
 with h.connect() as db:
  live=h.snapshot(db,ids);cit=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb->>'plan_sha256' plan_sha256 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='french_printmaking_source_identity'",(ids,))];assert len(live)==len(cit)==188 and all(x['plan_sha256']==pin for x in cit)
  for row in p['rows']:
   a=live[row['artwork_id']]['artwork'];im=p['images'][row['artwork_id']];assert a['accession_number']==row['accession_number'] and a['primary_media_id']==im['media_id'] and a['status']!='archived';assert all(a[k]==v for k,v in row['date'].items())
 b.save('french-reserve-live-reconciliation.json',dict(at=h.now(),inspected=188,already_imported_and_illustrated=188,unimported=0,new_programme_increments=0,plan_sha256=pin,source_citations=cit,live_rows=live,selected=0,physical_date_holds_preserved=['80082','80437','81054'],next_action='Athens page3; no historical plan mutation or replay.'))
 hold=b.E.parent/'000087/source-access-holds.json';b.save('source-access-holds.json',dict(at=h.now(),inherited_ledger=str(hold),inherited_sha256=h.sha(hold.read_bytes()),provider_holds_preserved=True,held_provider_requests=0,new_holds=[]))
 cur=next(x for x in q['sources'] if x['source_id']=='national_gallery_athens')['resume_cursor'];req=cur['documented_next_request'];assert cur['next_page']==3 and req['form']['page']==3
 fp=b.E/'parthenis-page3-capture.json'
 if fp.exists():raw=Path(h.load(fp)['body_path']).read_bytes()
 else:
  b.i.provider_slot('www.nationalgallery.gr');r=b.i.session().post(req['url'],data=req['form'],timeout=(15,45));raw=r.content;path=b.S/'parthenis-page3.json';path.write_bytes(raw);b.save(fp.name,dict(url=req['url'],method='POST',form=req['form'],status=r.status_code,retrieved_at=h.now(),sha256=h.sha(raw),body_path=str(path),retry_after=r.headers.get('Retry-After')));assert r.status_code==200
 obj=json.loads(raw);b.save('parthenis-page3.json',obj);print('PAGE',str(obj)[:1200])
