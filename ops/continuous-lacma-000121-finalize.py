"""Persist verified batch121 result; modify only researched source queue entries."""
import runpy,json,fcntl,datetime
v=runpy.run_path('ops/continuous-lacma-000121-delivery.py');globals().update({k:v[k] for k in ['h','E','R','ROOT','save','PHASE']})
p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']]
prod=h.load(E/'independent-production-verification.json');public=h.load(E/'independent-public-verification.json');audit=h.load(E/'independent-audit-history-verification.json')
assert prod['verified_new_artworks']==prod['verified_museum_links']==4 and len(public['records'])==4 and len(audit['events'])==8
counts=dict(new_painters=0,new_artworks=4,newly_illustrated=0,alternate_images=0,museum_links=4)
next_task='Resume Getty Byzantine discovery at saved offset150, size50, skipping processed slugs and excluding non-pictorial objects; reconcile exact native identities before selecting eligible metadata or permitted images. French reserve is exhausted (188 already delivered). Preserve LACMA date/version holds28991,22450,148372. Reconcile or create supported canonical profiles for Antonio de Torres, Miguel González and Nicolás Enríquez in a future bounded creator batch; four new works retain exact unlinked source labels. Do not repeat held native image requests.'
save('research-holds.json',dict(at=h.now(),prior_ledger='docs/research/continuous-production-20261011/batches/000120/research-holds.json',held_native_ids=['28991','22450','148372'],creator_profile_followup=['Antonio de Torres','Miguel González','Nicolás Enríquez'],images_unresolved_native_ids=['198584','158374','165148','167381'],reason='Native LACMA image rights unresolved. Named creators retained as exact labels; no incorrect or placeholder artist links.'))
save('source-access-holds.json',dict(at=h.now(),inherited_ledger='docs/research/continuous-production-20261011/batches/000120/source-access-holds.json',new_provider_requests=0,image_downloads=0,provider_holds_unchanged=True))
reg=h.load(E/'required-input-verification.json')['registry'];save('source-register.json',dict(at=h.now(),sources=[x for x in reg if x['source_id'] in ['lacma','yale_lux']],policy_reference='docs/ARTLINE_IMAGE_USE.md',access_status='Reuse checksum-bound official HTTP200 object captures; no new requests',remaining_gaps=next_task))
qp=E.parents[1]/'source-queue.json'
with qp.with_suffix('.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);old=h.load(qp);new=json.loads(json.dumps(old))
 for r in new['sources']:
  if r['source_id'] not in ['lacma','yale_lux']:continue
  r.update(last_checked_at=h.now(),last_batch=121,checkpoint=str((E/'CHECKPOINT.json').relative_to(ROOT)))
  if r['source_id']=='lacma':
   r['status']='four_additional_review_paintings_and_holdings_verified_three_prior_identity_date_holds'
   r.setdefault('prior_resume_cursors',[]).append(r.get('resume_cursor'))
   r['resume_cursor']=dict(processed_native_ids=['40124','59982','198584','158374','165148','167381'],held_native_ids=['28991','22450','148372'],creator_profile_followup=['Antonio de Torres','Miguel González','Nicolás Enríquez'],next_step=next_task)
   r['latest_batch_verified_counts']=counts
   ev=['independent-source-verification.json','independent-production-verification.json','independent-public-verification.json','research-holds.json']
  else:
   r['status']='french_reserve_exhausted_188_already_imported_illustrated_live_verified'
   r.setdefault('resume_cursor',{})['french_reserve_batch121']=dict(inspected=188,unimported=0,next_step='Do not select this exhausted reserve without a documented live-state change.')
   ev=['french-reserve-live-reconciliation.json','independent-reserve-evidence-verification.json','reserve-actual-visual-sample.json']
  r.setdefault('evidence_paths',[]).extend(str((E/n).relative_to(ROOT)) for n in ev)
  r.setdefault('research_history',[]).append(dict(batch=121,at=h.now(),scope='LACMA four new metadata records' if r['source_id']=='lacma' else 'Read-only French reserve reconciliation',verified_counts=counts if r['source_id']=='lacma' else {k:0 for k in counts}))
 assert all(a==z for a,z in zip(old['sources'],new['sources']) if a['source_id'] not in ['lacma','yale_lux'])
 save('source-queue-before.json',old);tmp=qp.with_name('source-queue.b121.tmp');tmp.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n');tmp.replace(qp);assert h.load(qp)==new
 save('independent-queue-verification.json',dict(at=h.now(),changed_source_ids=['lacma','yale_lux'],unrelated_entries_preserved=True,queue_sha256=h.sha(qp.read_bytes())))
now=h.now();start=h.load(E/'production-target-verification.json')['at'];receipt=dict(batch=121,at=now,outcome='progress',verified_counts=counts,reserve_inspected=188,reserve_unimported=0,reserve_counts_excluded=True,selected=4,prepared_metadata=4,imported=4,verified=4,production_ids=ids,metadata_plan_sha256=pin,images_selected=0,storage_writes=0,prior107_reconciled=True,prior120_reconciled=True,local_catalogue_connections=0,measured_runtime_seconds=(datetime.datetime.fromisoformat(now)-datetime.datetime.fromisoformat(start)).total_seconds(),runtime_scope='From first persisted production-target check',next_task=next_task)
save('batch-verification-receipt.json',receipt);cp=dict(receipt,status='complete',supervisor_unmodified=True);save('CHECKPOINT.json',cp);h.save(R/'worker-checkpoint.json',cp)
print(json.dumps(receipt))
