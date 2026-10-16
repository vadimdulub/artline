"""Independent batch verification and narrowly scoped queue checkpoint."""
import runpy,json,fcntl,datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup
v=runpy.run_path('ops/continuous-lacma-000120-delivery.py');globals().update({k:v[k] for k in ['h','b','E','R','ROOT','save','PHASE','FIELD']})
p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']]
prepath=h.BACKUP/PHASE/'locked-before.json.gz';pre=h.load(prepath);assert pre['artworks']=={} and pre['plan_sha256']==pin
source=[]
for r in p['records']:
 raw=(ROOT/r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256']
 t=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
 assert all(x in t for x in [r['title'],r['creator_label'],r['date_display'],r['accession_number'],r['medium'],r['dimensions'],r['credit']])
 assert r['first']<=r['last']<=1970 and not r['before']
 source.append(dict(artwork_id=r['artwork_id'],source_url=r['source_url'],source_sha256=r['evidence']['sha256'],native_id=r['source_id'],accession=r['accession_number'],passed=True))
save('independent-source-verification.json',dict(at=h.now(),records=source,plan_sha256=pin))
with h.connect() as db:
 after=h.snapshot(db,ids);assert len(after)==2
 notes=[dict(x) for x in db.execute("SELECT entity_id::text,source_url,evidence_note::jsonb note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,FIELD))];assert len(notes)==2
 for r in p['records']:
  state=after[r['artwork_id']];a=state['artwork'];n=next(x for x in notes if x['entity_id']==a['id'])
  assert (a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['medium_text'],a['dimensions_text'],a['date_precision'])==(r['title'],r['accession_number'],r['first'],r['last'],r['medium'],r['dimensions'],r['precision'])
  assert a['status']=='review' and a['primary_media_id'] is None and a['current_institution_id']==r['institution_id'] and not state['attachments']
  assert len(state['creators'])==1 and state['creators'][0]['artist_id']==r['artist_id']
  assert len(state['holdings'])==1 and state['holdings'][0]['review_state']=='accepted' and state['holdings'][0]['claim_type']=='holding'
  ev=json.loads(state['holdings'][0]['evidence_note']);assert ev['confidence']>=.8 and ev['source_sha256']==r['evidence']['sha256']
  assert n['note']['plan_sha256']==pin and n['note']['evidence']['sha256']==r['evidence']['sha256']
  assert db.execute('SELECT count(*) n FROM artworks WHERE accession_number=%s',(r['accession_number'],)).fetchone()['n']==1
  assert db.execute("SELECT entity_id::text FROM external_identifiers WHERE scheme='museum-native-lacma' AND external_id=%s",(r['source_id'],)).fetchone()['entity_id']==a['id']
 holds=[v['holdings'][0]['id'] for v in after.values()]
 events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_id=ANY(%s::uuid[]) AND action='insert'",(ids+holds,))]
 assert len(events)==4 and all(x['before_json'] is None for x in events)
 for aid,old in pre['artists'].items():assert db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(aid,)).fetchone()['v']==old
 prior=h.load(E/'production-reconciliation.json')['states'];assert h.snapshot(db,list(prior))==prior
 variants=h.load(E/'russian-title-variant-reconciliation.json')['states'];assert h.snapshot(db,list(variants))==variants
 assert db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==2
save('independent-production-verification.json',dict(at=h.now(),plan_sha256=pin,after=after,citations=notes,transaction_preimages=dict(path=str(prepath),sha256=h.sha(prepath.read_bytes())),verified_new_artworks=2,verified_museum_links=2,existing_artists_and_candidate_works_unchanged=True,images_changed=0))
save('independent-audit-history-verification.json',dict(at=h.now(),events=events,empty_transaction_preimages=True,programme_source_and_plan_checksums_verified=True))
public=[]
for r in p['records']:
 url='https://artlines.org/api/backend/v1/atlas/artworks/'+r['artwork_id'];res=requests.get(url,timeout=40);assert res.status_code==200
 assert r['title'] in res.text and r['source_url'] in res.text and 'Los Angeles County Museum of Art' in res.text
 save('public-api-'+r['artwork_id']+'.json',res.json());public.append(dict(artwork_id=r['artwork_id'],url=url,status=200,sha256=h.sha(res.content)))
save('independent-public-verification.json',dict(at=h.now(),records=public))
counts=dict(new_painters=0,new_artworks=2,newly_illustrated=0,alternate_images=0,museum_links=2)
next_task='Reconcile the seven captured LACMA candidates by exact accessions and global creator/title identity, prioritizing four dated Mexican paintings 198584,158374,165148,167381. Keep 148372 joint attribution and likely existing match explicit; 28991 has conflicting source dates,22450 has open after1507 date. Native image rights remain unresolved; do not repeat unchanged WikiArt queries.'
save('research-holds.json',dict(at=h.now(),records=[dict(native_id=n,reason=reason) for n,reason in [('28991','Museum date conflicts with image caption; no year bounds inferred.'),('22450','Open after1507 creation date; workshop label and versions require review.'),('148372','Likely existing1691 Virgin of Guadalupe record1494fb90-25b6-5bd2-a20b-a4e366fca27b; joint makers require identity reconciliation.'),('198584','Captured dated metadata; global identity and creator reconciliation pending.'),('158374','Captured dated metadata; global identity and creator reconciliation pending.'),('165148','Captured dated metadata; global identity and creator reconciliation pending.'),('167381','Captured dated metadata; global identity and creator reconciliation pending.')]],image_holds=['40124','59982'],image_basis='LACMA native rights not established; exact WikiArt discovery returned no results. No image download or attachment.'))
save('source-access-holds.json',dict(at=h.now(),inherited_ledger='docs/research/continuous-production-20261011/batches/000119/source-access-holds.json',lacma_object_status='Nine HTTP200 native pages captured',lacma_terms='web tool unavailable at https://www.lacma.org/terms-use; permission not inferred',native_image_requests=0,retries=0))
qp=E.parents[1]/'source-queue.json'
with qp.with_suffix('.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);old=h.load(qp);new=json.loads(json.dumps(old));r=next(s for s in new['sources'] if s['source_id']=='lacma')
 r.update(status='two_russian_review_paintings_and_holdings_verified_seven_captured_candidates_pending',last_checked_at=h.now(),last_batch=120,checkpoint=str((E/'CHECKPOINT.json').relative_to(ROOT)),policy_reference='Original111-source CSV lacma; docs/ARTLINE_IMAGE_USE.md',access_status='Native object pages HTTP200; image rights unresolved',resume_cursor=dict(processed_native_ids=['40124','59982'],captured_pending_ids=['28991','22450','198584','148372','158374','165148','167381'],next_step=next_task),verified_counts=counts)
 r.setdefault('evidence_paths',[]).extend([str((E/n).relative_to(ROOT)) for n in ['independent-source-verification.json','independent-production-verification.json','independent-public-verification.json','research-holds.json']])
 r.setdefault('research_history',[]).append(dict(batch=120,verified_counts=counts,at=h.now()))
 assert all(a==z for a,z in zip(old['sources'],new['sources']) if a['source_id']!='lacma')
 save('source-queue-before.json',old);tmp=qp.with_name('source-queue.b120.tmp');tmp.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n');tmp.replace(qp);assert h.load(qp)==new
 save('independent-queue-verification.json',dict(at=h.now(),changed_source_ids=['lacma'],unrelated_entries_preserved=True,queue_sha256=h.sha(qp.read_bytes())))
now=h.now();start=h.load(E/'production-target-verification.json')['at'];receipt=dict(batch=120,at=now,outcome='progress',verified_counts=counts,discovered=9,selected=2,prepared_metadata=2,imported=2,verified=2,production_ids=ids,metadata_plan_sha256=pin,images_selected=0,storage_writes=0,directory_entries_added=0,prior107_reconciled=True,prior109_reconciled=True,local_catalogue_connections=0,measured_runtime_seconds=(datetime.datetime.fromisoformat(now)-datetime.datetime.fromisoformat(start)).total_seconds(),runtime_scope='From first persisted production-target check',next_task=next_task)
save('batch-verification-receipt.json',receipt);cp=dict(receipt,status='complete',supervisor_unmodified=True);save('CHECKPOINT.json',cp);h.save(R/'worker-checkpoint.json',cp)
print(json.dumps(receipt))
