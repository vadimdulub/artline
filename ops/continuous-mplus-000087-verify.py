#!/usr/bin/env python3
"""Independent source, attribution, production, recovery and public checks."""
import fcntl,gzip,importlib.util,json,os,subprocess,sys
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('b87',Path(__file__).with_name('continuous-mplus-000087.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
def source_checks():
 p,pin=h.pinned(b.PHASE);checks=[]
 rc=h.load(b.E/'dataset-objects.receipt.json');raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256']
 csvrows={r['id']:r for r in list(b.csv.DictReader(b.io.StringIO(raw.decode('utf-8-sig'))))}
 cr=h.load(b.E/'dataset-creators.receipt.json');craw=gzip.decompress(Path(cr['body_path']).read_bytes());assert h.sha(craw)==cr['sha256']
 creators={r['id']:r for r in b.csv.DictReader(b.io.StringIO(craw.decode('utf-8-sig')))}
 readme=gzip.decompress(Path(h.load(b.E/'dataset-readme.receipt.json')['body_path']).read_bytes()).decode();assert 'CC0' in readme and 'Images are not included' in readme
 for r in p['records']:
  body=Path(r['evidence_file']).read_bytes();assert h.sha(body)==r['evidence']['sha256'] and r['evidence']['status']==200
  o=json.loads(body);c=csvrows[r['source_id']];creator=creators[str(o['constituents'][0]['id'])]
  assert str(o['id'])==r['source_id'] and o['objectNumber']==c['objectNumber']==r['accession_number']
  assert o['title']['en']==c['title']==r['title'] and o['title']['zh-hant']==r['raw']['original_title']
  assert o['displayDate']['en']==r['date_display'] and o['beginDate']==r['first'] and o['endDate']==r['last']<=1970
  assert 0<r['first']<=r['last'] and 'Painting' in o['classification']['category']['en']
  assert r['dimensions']==c['dimension'] and h.norm(r['dimensions'])==h.norm(o['dimension']['en']) and r['medium']==o['medium']['en']
  assert r['credit']==o['creditLine']['en'] and 'M+, Hong Kong' in r['credit'] and not b.re.search('loan|lent by',r['credit'],b.re.I)
  assert r['creator_label']==creator['name'] and creator==r['raw']['source_creator'] and o['constituents'][0]['role']['en']=='Artist'
  assert not r['before'] and r['add_holding'] and r['holding_confidence']>=.8
  if r['artist_id']:
   a=p['artists'][r['artist_id']];assert a['status']!='archived'
  checks.append(dict(artwork_id=r['artwork_id'],inventory=r['accession_number'],native_id=r['source_id'],source_url=r['source_url'],source_sha256=r['evidence']['sha256'],csv_sha256=rc['sha256'],creator_sha256=cr['sha256'],passed=True))
 b.save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=checks,images_selected=0,images_downloaded=0,source_text_metadata_cc0=True,image_rights_excluded=True,source_bounds_preserved=True))
 return p,pin
def prewrite():
 p,pin=source_checks();ids=[r['artwork_id'] for r in p['records']]
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
   mids=[i['id'] for i in p['new_institutions']];inst=[x['v'] for x in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=ANY(%s::uuid[])',(mids,))];assert not inst
   sourceid=h.uid('source/mplus/'+b.MUSEUM);sources=[x['v'] for x in db.execute('SELECT to_jsonb(s) v FROM sources s WHERE id=%s',(sourceid,))];assert not sources
   old=h.load(b.E/'prior-batch-live-reconciliation.json')['live'];assert h.snapshot(db,list(old))==old
   artists={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(list(p['artists']),))};assert artists==p['artists']
   h.save(backup/'affected-row-recovery-before.json.gz',dict(at=h.now(),plan_sha256=pin,planned_artwork_ids=ids,artworks=before,institutions=inst,sources=sources,artists=artists,previous_batch=old))
   for r in p['records']:assert db.execute('SELECT artline_creation_scope(%s,%s,%s) scope',(r['first'],r['last'],r['precision'])).fetchone()['scope']=='eligible'
  files=[path,toc,backup/'affected-row-recovery-before.json.gz',backup/b.PHASE/'plan-preimages.json.gz']
  for f in files:
   if f.suffix=='.gz':h.load(f)
  rc=dict(at=h.now(),status='VERIFIED',kind='scoped_production_recovery_schema_and_exact_preimages',plan_sha256=pin,files=[b.ref(f) for f in files],schema_archive_fully_decoded=True,all_json_exports_fully_decoded=True,full_database_backup=False,cloud_backups_created=0,local_catalogue_connections=0,additional_locked_preimages_required=True,recovery='Reconcile exact batch plan/source checksums, locked preimages and insert audit events before recovery. Preserve unrelated records; no recovery mutations performed.')
  b.save('local-recovery-verification.json',rc);h.save(backup/'local-recovery-verification.json',rc)
 b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,artworks=len(ids),holdings=len(ids),images=0,new_artist_records=0,shared_lock='artline-curated-ingestion',local_catalogue_connections=0))
 print('Source metadata and scoped recovery verified:',len(ids),flush=True)
def verify():
 p,pin=source_checks();ids=[r['artwork_id'] for r in p['records']];pre=h.load(h.BACKUP/b.PHASE/'locked-before.json.gz');assert pre['plan_sha256']==pin and pre['artworks']=={}
 target=b.target();mid=p['institutions'][b.MUSEUM]['id']
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids);assert len(after)==len(ids)
  notes=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,source_url,evidence_note::jsonb note FROM citations WHERE entity_type='artwork' AND field_name=%s AND entity_id=ANY(%s::uuid[])",(b.FIELD,ids))];assert len(notes)==len(ids)
  ext=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))];assert len(ext)==len(ids)
  for r in p['records']:
   aid=r['artwork_id'];a=after[aid]['artwork'];n=next(x for x in notes if x['entity_id']==aid)
   assert (a['title'],a['alternate_title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['date_display'],a['medium_text'],a['dimensions_text'])==(r['title'],r['raw']['original_title'],r['accession_number'],r['first'],r['last'],r['precision'],r['date_display'],r['medium'],r['dimensions'])
   assert a['status']=='review' and a['published_at'] is None and a['research_candidate'] and a['current_institution_id']==mid and a['primary_media_id'] is None and not after[aid]['attachments']
   assert a['unlinked_creator_label']==(None if r['artist_id'] else r['creator_label'])
   assert [x['artist_id'] for x in after[aid]['creators']]==([r['artist_id']] if r['artist_id'] else [])
   assert n['note']['plan_sha256']==pin and n['note']['evidence']['sha256']==r['evidence']['sha256'] and n['note']['dataset_receipt']['sha256']==r['dataset_receipt']['sha256'] and n['note']['creator_receipt']['sha256']==r['creator_receipt']['sha256'] and n['source_record_id']==r['source_id']
   assert {x['scheme']:x['external_id'] for x in ext if x['entity_id']==aid}=={'museum-native-mplus':r['source_id']}
   held=after[aid]['holdings'];assert len(held)==1 and held[0]['claim_type']=='holding' and held[0]['review_state']=='accepted' and held[0]['institution_id']==mid and held[0]['display_state'] is None and held[0]['gallery'] is None
   ev=json.loads(held[0]['evidence_note']);assert ev['confidence']>=.8 and ev['source_sha256']==r['evidence']['sha256']
   assert db.execute('SELECT count(*) n FROM artworks WHERE accession_number=%s',(r['accession_number'],)).fetchone()['n']==1
  events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='insert'",(ids,))];assert len(events)==len(ids) and all(x['before_json'] is None for x in events)
  for x in events:
   r=next(r for r in p['records'] if r['artwork_id']==x['entity_id']);assert x['after_json']['accession_number']==r['accession_number'] and x['after_json']['status']=='review'
  holds=[x['holdings'][0]['id'] for x in after.values()];hevents=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_id=ANY(%s::uuid[]) AND action='insert'",(holds,))];assert len(hevents)==len(ids) and all(x['before_json'] is None for x in hevents)
  institution=db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(mid,)).fetchone()['v'];assert all(institution[k]==v for k,v in p['institutions'][b.MUSEUM].items())
  assert db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==len(ids)
  prior=h.load(b.E/'prior-batch-live-reconciliation.json')['live'];assert h.snapshot(db,list(prior))==prior
  artists={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(list(p['artists']),))};assert artists==pre['artists']
  count=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids+holds+[mid],)).fetchone()['n']
 b.save('independent-production-verification.json',dict(at=h.now(),target=target,plan_sha256=pin,transaction_preimages=b.ref(h.BACKUP/b.PHASE/'locked-before.json.gz'),after=after,citations=notes,external_identifiers=ext,verified_new_artworks=len(ids),verified_holdings=len(ids),prior_campaign_increments=0,new_institution=institution,existing_artists_unchanged=True))
 b.save('independent-audit-history-verification.json',dict(at=h.now(),artwork_insert_events=events,holding_insert_events=hevents,empty_locked_preimages=True,persisted_plan_and_source_checksums_verified=True))
 b.save('independent-preservation-verification.json',dict(at=h.now(),previous_batch_unchanged=1,existing_artists_unchanged=len(artists),images_created=0,existing_artworks_updated=0,local_catalogue_connections=0))
 public=[]
 for r in p['records']:
  url='https://artlines.org/api/backend/v1/atlas/artworks/'+r['artwork_id'];res=requests.get(url,timeout=(15,40));assert res.status_code==200
  a=res.json();text=json.dumps(a,ensure_ascii=False)
  assert all(x in text for x in [r['title'],r['source_url'],b.MUSEUM]);b.save('public-api-'+r['artwork_id']+'.json',a)
  public.append(dict(artwork_id=r['artwork_id'],url=url,status=200,sha256=h.sha(res.content),title_source_museum_present=True))
 b.save('independent-public-verification.json',dict(at=h.now(),records=public,verified=len(ids),anonymous_access=True))
 b.apply()
 with h.connect() as db:
  assert h.snapshot(db,ids)==after;count_after=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids+holds+[mid],)).fetchone()['n'];assert count_after==count
 b.save('independent-resume-verification.json',dict(at=h.now(),apply_entrypoint_replayed=True,attribution_reconciled_before_replay=True,artworks_unchanged=True,audit_count_before=count,audit_count_after=count_after,replay_increments=0))
 counts=dict(new_painters=0,new_artworks=len(ids),newly_illustrated=0,alternate_images=0,museum_links=len(ids))
 b.save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,metadata_plan_sha256=pin,production_target=target,verified_public_api_rows=len(ids),images_selected=0,image_holds=len(ids),creator_links=len([r for r in p['records'] if r['artist_id']]),attribution='Persisted exact batch plan/source/creator citation checksums, empty locked transaction preimages and matching insert audit events establish new programme objects and holdings. Prior campaigns excluded.',limitations=['Metadata-only batch; no image files selected, downloaded, prepared or viewed. M+ metadata CC0 excludes image rights.','Recovery is a schema export plus exact affected preimages, not a full database backup.','Creator labels not securely reconciled remain explicit; new painter records are not fabricated.']))
 print(json.dumps(counts),flush=True)
if __name__=='__main__':
 with (b.R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
