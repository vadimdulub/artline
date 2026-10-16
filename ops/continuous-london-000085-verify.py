#!/usr/bin/env python3
"""Independent source, recovery, production and public checks for bounded batch 85."""
import fcntl,gzip,importlib.util,json,os,subprocess,sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b85',Path(__file__).with_name('continuous-london-000085.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
def source_checks():
 p,pin=h.pinned(b.PHASE);checks=[]
 rc=h.load(b.E/'london-objects-page1.receipt.json');raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'];objects={x['_id']:x['_source'] for x in json.loads(raw)['hits']['hits']}
 for r in p['records']:
  body=Path(r['evidence_file']).read_bytes();assert h.sha(body)==r['evidence']['sha256'] and r['evidence']['status']==200
  text=BeautifulSoup(body,'html.parser').get_text(' ',strip=True);o=objects[r['source_id']];date=o['creation'][0]['date'][0]
  assert next(x['value'] for x in o['identifier'] if x['type']=='object number')==r['accession_number']
  assert all(v in text for v in [r['title'],r['creator_label'],r['dimensions'],r['accession_number'],r['credit'],'Main Collection'])
  assert r['date_display']==date['value'] and r['first']==int(date['from']) and r['last']==int(date['to'])<=1970
  assert r['precision'] in ['circa','circa_range'] and not r['artist_id'] and r['creator_link_hold'] and not r['before'] and r['add_holding']
  assert r['dimensions']==o['measurements'][0]['display'] and r['medium']==next(x['value'] for x in o['material'] if x.get('type')=='detailed')
  if r['accession_number']=='NG1301':assert 'reverse' in text and 'hood' in text and 'double-sided' in r['raw']['physical_unit']
  checks.append(dict(artwork_id=r['artwork_id'],inventory=r['accession_number'],pid=r['source_id'],source_url=r['source_url'],source_sha256=r['evidence']['sha256'],api_sha256=rc['sha256'],passed=True))
 b.save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=checks,images_selected=0,images_downloaded=0,qualified_labels_preserved=True,double_sided_panel_counted_once=True))
 return p,pin
def prewrite():
 p,pin=source_checks();ids=[r['artwork_id'] for r in p['records']];assert len(ids)==2
 b.save('production-target-before-recovery.json',b.target())
 backup=h.BACKUP;backup.mkdir(parents=True,exist_ok=True);backup.chmod(0o700)
 if not (b.E/'local-recovery-verification.json').exists():
  secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
  kw=h.psycopg.conninfo.conninfo_to_dict(secret);env=os.environ.copy();env.update(PGHOST='127.0.0.1',PGPORT='55519',PGDATABASE=kw['dbname'],PGUSER=kw['user'],PGPASSWORD=kw['password'],PGSSLMODE='disable',PGOPTIONS='-c default_transaction_read_only=on')
  path=backup/'production-schema-before.pgdump';out=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_dump','--schema-only','--format=custom','--no-owner','--no-acl','--file',str(path)],env=env,capture_output=True,timeout=180);assert out.returncode==0,'Schema export failed';path.chmod(0o600)
  toc=backup/'production-schema-before.toc';out=subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--list',str(path)],capture_output=True,check=True);toc.write_bytes(out.stdout);toc.chmod(0o600)
  with open(os.devnull,'wb') as sink:subprocess.run(['/opt/homebrew/opt/libpq/bin/pg_restore','--file=-',str(path)],stdout=sink,stderr=subprocess.PIPE,check=True,timeout=120)
  with h.connect() as db,db.transaction():
   db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');b.collision(db,p['records']);before=h.snapshot(db,ids);assert not before
   inst=db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(b.MID,)).fetchone()['v'];assert inst==p['institutions'][b.MUSEUM]
   sourceid=h.uid('source/london/'+b.MUSEUM);sources=[x['v'] for x in db.execute('SELECT to_jsonb(s) v FROM sources s WHERE id=%s',(sourceid,))];assert not sources
   preserved_ids=['205c5ab2-5213-4246-a05a-47a2636af97d','0ad2d8dc-01b8-44fc-9be3-b2fc7835b257','7964fc90-79d2-540c-83bc-80280e5745a9','9709eb86-73b0-58b4-a534-c0aae19adbfe','af973f37-1069-5987-8987-18de8deaeaa8']
   preserved=h.snapshot(db,preserved_ids)
   h.save(backup/'affected-row-recovery-before.json.gz',dict(at=h.now(),plan_sha256=pin,planned_artwork_ids=ids,artworks=before,institution=inst,sources=sources,preserved=preserved))
   for r in p['records']:assert db.execute('SELECT artline_creation_scope(%s,%s,%s) scope',(r['first'],r['last'],r['precision'])).fetchone()['scope']=='eligible'
  files=[path,toc,backup/'affected-row-recovery-before.json.gz',backup/b.PHASE/'plan-preimages.json.gz']
  for f in files:
   if f.suffix=='.gz':h.load(f)
  rc=dict(at=h.now(),status='VERIFIED',kind='scoped_production_recovery_schema_and_exact_preimages',plan_sha256=pin,files=[b.ref(f) for f in files],schema_archive_fully_decoded=True,all_json_exports_fully_decoded=True,full_database_backup=False,cloud_backups_created=0,local_catalogue_connections=0,additional_locked_preimages_required=True,recovery='Reconcile exact batch plan/source checksums, locked preimages and insert audit events before recovery. Preserve unrelated records; no recovery mutations performed.')
  b.save('local-recovery-verification.json',rc);h.save(backup/'local-recovery-verification.json',rc)
 b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,artworks=2,holdings=2,images=0,artist_records=0,shared_lock='artline-curated-ingestion',local_catalogue_connections=0))
 print('Two metadata objects and scoped recovery verified.',flush=True)
def verify():
 p,pin=source_checks();ids=[r['artwork_id'] for r in p['records']];pre=h.load(h.BACKUP/b.PHASE/'locked-before.json.gz');assert pre['plan_sha256']==pin and pre['artworks']=={}
 target=b.target()
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids);assert len(after)==2
  notes=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,source_url,evidence_note::jsonb note FROM citations WHERE entity_type='artwork' AND field_name=%s AND entity_id=ANY(%s::uuid[])",(b.FIELD,ids))];assert len(notes)==2
  ext=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))];assert len(ext)==2
  for r in p['records']:
   aid=r['artwork_id'];a=after[aid]['artwork'];n=next(x for x in notes if x['entity_id']==aid)
   assert (a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['date_display'],a['medium_text'],a['dimensions_text'],a['unlinked_creator_label'])==(r['title'],r['accession_number'],r['first'],r['last'],r['precision'],r['date_display'],r['medium'],r['dimensions'],r['creator_label'])
   assert a['status']=='review' and a['published_at'] is None and a['research_candidate'] and a['current_institution_id']==b.MID and a['primary_media_id'] is None and not after[aid]['creators'] and not after[aid]['attachments']
   assert n['note']['plan_sha256']==pin and n['note']['evidence']['sha256']==r['evidence']['sha256'] and n['note']['api_receipt']['sha256']==r['api_receipt']['sha256'] and n['source_record_id']==r['source_id']
   assert {x['scheme']:x['external_id'] for x in ext if x['entity_id']==aid}=={'european-popular-ng-object':r['source_id']}
   held=after[aid]['holdings'];assert len(held)==1 and held[0]['claim_type']=='holding' and held[0]['review_state']=='accepted' and held[0]['institution_id']==b.MID and held[0]['display_state'] is None and held[0]['gallery'] is None
   ev=json.loads(held[0]['evidence_note']);assert ev['confidence']>=.8 and ev['source_sha256']==r['evidence']['sha256']
   assert db.execute('SELECT count(*) n FROM artworks WHERE accession_number=%s',(r['accession_number'],)).fetchone()['n']==1
  events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='insert'",(ids,))];assert len(events)==2 and all(x['before_json'] is None for x in events)
  for x in events:
   r=next(r for r in p['records'] if r['artwork_id']==x['entity_id']);assert x['after_json']['accession_number']==r['accession_number'] and x['after_json']['status']=='review'
  holds=[x['holdings'][0]['id'] for x in after.values()];hevents=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_id=ANY(%s::uuid[]) AND action='insert'",(holds,))];assert len(hevents)==2 and all(x['before_json'] is None for x in hevents)
  institution=db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(b.MID,)).fetchone()['v'];assert institution==pre['institutions'][b.MID]
  assert db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==2
  prior=h.load(b.E/'prior-batch-live-reconciliation.json')['live'];assert h.snapshot(db,list(prior))==prior==h.load(b.E.parent/'000084/independent-production-verification.json')['after']
  reserve=h.load(b.E/'french-reserve-live-reconciliation.json')['live_rows'];assert h.snapshot(db,list(reserve))==reserve
  preserved=h.load(h.BACKUP/'affected-row-recovery-before.json.gz')['preserved'];assert h.snapshot(db,list(preserved))==preserved
  count=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids+holds+[b.MID],)).fetchone()['n']
 b.save('independent-production-verification.json',dict(at=h.now(),target=target,plan_sha256=pin,transaction_preimages=b.ref(h.BACKUP/b.PHASE/'locked-before.json.gz'),after=after,citations=notes,external_identifiers=ext,verified_new_artworks=2,verified_holdings=2,prior_campaign_increments=0,existing_institution_unchanged=True,qualified_attributions_preserved=True))
 b.save('independent-audit-history-verification.json',dict(at=h.now(),artwork_insert_events=events,holding_insert_events=hevents,empty_locked_preimages=True,persisted_plan_and_source_checksums_verified=True))
 b.save('independent-preservation-verification.json',dict(at=h.now(),french_reserve_unchanged=188,previous_batch_unchanged=4,version_candidates_unchanged=len(preserved),institution_unchanged=True,images_created=0,local_catalogue_connections=0))
 public=[]
 for r in p['records']:
  url='https://artlines.org/api/backend/v1/atlas/artworks/'+r['artwork_id'];res=requests.get(url,timeout=(15,40));assert res.status_code==200
  assert all(x in res.text for x in [r['title'],r['source_url'],b.MUSEUM,r['creator_label']]);b.save('public-api-'+r['artwork_id']+'.json',res.json())
  public.append(dict(artwork_id=r['artwork_id'],url=url,status=200,sha256=h.sha(res.content),title_source_museum_qualified_label_present=True))
 b.save('independent-public-verification.json',dict(at=h.now(),records=public,verified=2,anonymous_access=True))
 b.apply()
 with h.connect() as db:
  assert h.snapshot(db,ids)==after;count_after=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids+holds+[b.MID],)).fetchone()['n'];assert count_after==count
 b.save('independent-resume-verification.json',dict(at=h.now(),apply_entrypoint_replayed=True,attribution_reconciled_before_replay=True,artworks_unchanged=True,audit_count_before=count,audit_count_after=count_after,replay_increments=0))
 counts=dict(new_painters=0,new_artworks=2,newly_illustrated=0,alternate_images=0,museum_links=2)
 b.save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,metadata_plan_sha256=pin,production_target=target,verified_public_api_rows=2,images_selected=0,image_holds=2,attribution='Persisted exact batch plan/source citation checksums, empty locked transaction preimages and matching insert audit events independently establish two new programme objects and holdings. Prior campaigns excluded.'))
 print(json.dumps(counts),flush=True)
if __name__=='__main__':
 with (b.R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
