#!/usr/bin/env python3
"""Read-only independent production/source/public verification and safe resume proof."""
import fcntl,importlib.util,json,gzip,requests
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-pola-000081.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']];assert len(ids)==len(set(ids))==9
 pre=h.load(h.BACKUP/b.PHASE/'locked-before.json.gz');assert pre['plan_sha256']==pin and not pre['artworks'] and not pre['new_institution_preimages'] and not pre['new_source_preimages']
 source=[]
 for r in p['records']:
  raw=Path(r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256'];text=BeautifulSoup(raw,'html.parser').select_one('main').get_text(' ',strip=True)
  assert all(v in text for v in [r['raw']['original_title'],r['raw']['yearLabel']['ja'],r['raw']['medium'][0]['ja'],r['dimensions'],'岸田劉生','ポーラ美術館が収蔵する'])
  source.append(dict(artwork_id=r['artwork_id'],native_id=r['source_id'],native_url=r['source_url'],source_sha256=r['evidence']['sha256'],shuzo_id=r['raw']['shuzo_id'],shuzo_sha256=r['shuzo_receipt']['sha256'],passed=True))
 b.save('independent-source-verification.json',dict(at=h.now(),records=source,plan_sha256=pin,all_nine_exact_inventory_sources_verified=True,images_selected=0,images_downloaded=0,actual_visual_reviews=0))
 target=b.target()
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids);assert len(after)==9
  notes=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,source_url,evidence_note::jsonb note FROM citations WHERE field_name=%s AND entity_id=ANY(%s::uuid[])",(b.FIELD,ids))];assert len(notes)==9
  ext=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))];assert len(ext)==18
  for r in p['records']:
   aid=r['artwork_id'];a=after[aid]['artwork'];n=next(x for x in notes if x['entity_id']==aid)
   assert (a['title'],a['alternate_title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['date_display'],a['work_type'],a['medium_text'],a['dimensions_text'])==(r['title'],r['raw']['original_title'],r['accession_number'],r['first'],r['last'],r['precision'],r['date_display'],h.worktype(r),r['medium'],r['dimensions'])
   assert a['status']=='review' and a['published_at'] is None and a['research_candidate'] is True and a['current_institution_id']==b.MID and a['primary_media_id'] is None and a['unlinked_creator_label'] is None
   assert len(after[aid]['creators'])==1 and after[aid]['creators'][0]['artist_id']==b.ARTIST and after[aid]['attachments']==[]
   assert n['note']['plan_sha256']==pin and n['note']['evidence']['sha256']==r['evidence']['sha256'] and n['note']['shuzo_receipt']['sha256']==r['shuzo_receipt']['sha256'] and n['source_url']==r['source_url'] and n['source_record_id']==r['source_id']
   assert {x['scheme']:x['external_id'] for x in ext if x['entity_id']==aid}=={b.SCHEME:r['source_id'],'shuzo-work':r['raw']['shuzo_id']}
   held=after[aid]['holdings'];assert len(held)==1 and held[0]['claim_type']=='holding' and held[0]['review_state']=='accepted' and held[0]['institution_id']==b.MID and held[0]['display_state'] is None and held[0]['gallery'] is None
   hev=json.loads(held[0]['evidence_note']);assert hev['confidence']>=.8 and hev['source_sha256']==r['evidence']['sha256'] and hev['inventory']==r['accession_number']
   assert db.execute('SELECT count(*) n FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(b.MID,r['accession_number'])).fetchone()['n']==1
   assert db.execute('SELECT artline_creation_scope(%s,%s,%s) scope',(r['first'],r['last'],r['precision'])).fetchone()['scope']=='eligible'
  events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='insert'",(ids,))];assert len(events)==9
  for x in events:
   r=next(r for r in p['records'] if r['artwork_id']==x['entity_id']);assert x['before_json'] is None and x['after_json']['accession_number']==r['accession_number'] and x['after_json']['status']=='review' and x['after_json']['primary_media_id'] is None
  holding_ids=[x['holdings'][0]['id'] for x in after.values()];holding_events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_id=ANY(%s::uuid[]) AND action='insert'",(holding_ids,))];assert len(holding_events)==9 and all(not x['before_json'] for x in holding_events)
  artist=db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(b.ARTIST,)).fetchone()['v'];assert artist==pre['artists'][b.ARTIST]==p['artists'][b.ARTIST]
  institution=db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(b.MID,)).fetchone()['v'];assert institution['name']==b.MUSEUM and institution['website_url']=='https://www.polamuseum.or.jp/' and institution['status']=='review'
  assert db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==9
  preserved=h.load(h.BACKUP/'affected-row-recovery-before.json.gz')['preserved'];assert h.snapshot(db,list(preserved))==preserved
  prior=h.load(b.E/'prior-batch-live-reconciliation.json')['states'];assert h.snapshot(db,list(prior))==prior
  assert db.execute('SELECT count(*) n FROM media_rights_evidence WHERE adapter_version=%s',(b.OP,)).fetchone()['n']==0
  assert not db.execute('SELECT id FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(b.MID,'002-0088')).fetchall()
  count=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids+[b.MID,b.ARTIST],)).fetchone()['n']
  query_plan=db.execute('EXPLAIN (FORMAT JSON) SELECT id FROM artworks WHERE current_institution_id=%s AND status<>%s ORDER BY id LIMIT 50',(b.MID,'archived')).fetchone()
 b.save('independent-production-verification.json',dict(at=h.now(),target=target,plan_sha256=pin,transaction_preimages=b.ref(h.BACKUP/b.PHASE/'locked-before.json.gz'),after=after,citations=notes,external_identifiers=ext,verified_new_artworks=9,verified_holdings=9,prior_campaign_objects_counted=0,new_review_objects=True,new_institution=institution,existing_artist=artist,query_plan=query_plan,load_test_limit='Scoped production query inspected; no assertion of ten-million-row load validation.'))
 b.save('independent-audit-history-verification.json',dict(at=h.now(),artwork_insert_events=events,holding_insert_events=holding_events,empty_locked_preimages=True,own_plan_checksum_persisted=True,own_source_checksums_persisted=True))
 b.save('independent-preservation-verification.json',dict(at=h.now(),existing_creator_works_unchanged=len(preserved),previous_batch_unchanged=len(prior),existing_artist_unchanged=True,grouped_cover_held=True,images_created=0,local_catalogue_connections=0))
 public=[]
 for r in p['records']:
  url='https://artlines.org/api/backend/v1/atlas/artworks/'+r['artwork_id'];res=requests.get(url,timeout=(15,60));assert res.status_code==200,(r['artwork_id'],res.status_code);obj=res.json();assert r['title'] in res.text and r['source_url'] in res.text and b.MUSEUM in res.text
  b.save('public-api-'+r['artwork_id']+'.json',obj);public.append(dict(artwork_id=r['artwork_id'],url=url,status=res.status_code,sha256=h.sha(res.content),title_and_native_source_and_museum_present=True))
 b.save('independent-public-verification.json',dict(at=h.now(),records=public,verified=9))
 # Call real apply entrypoint after receipt/plan reconciliation; it must return without a transaction.
 b.apply()
 with h.connect() as db:
  assert h.snapshot(db,ids)==after and db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(b.ARTIST,)).fetchone()['v']==artist and db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(b.MID,)).fetchone()['v']==institution
  count_after=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids+[b.MID,b.ARTIST],)).fetchone()['n'];assert count_after==count
 b.save('independent-resume-verification.json',dict(at=h.now(),apply_entrypoint_replayed=True,own_plan_and_source_checksums_reconciled=True,artworks_unchanged=True,artist_unchanged=True,institution_unchanged=True,audit_count_before=count,audit_count_after=count_after,replay_increments=0))
 counts=dict(new_painters=0,new_artworks=9,newly_illustrated=0,alternate_images=0,museum_links=9)
 b.save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,metadata_plan_sha256=pin,production_target=target,verified_public_api_rows=9,attribution='Exact batch plan/source citation checksums, empty locked transaction preimages and matching artwork/holding insert audit events independently establish nine new programme objects and holdings. Prior campaigns excluded.',images_selected=0,image_holds=9,new_institutions=1,existing_artist_reused=b.ARTIST))
 print(json.dumps(counts))
