"""Independent post-transaction source, row, attribution, audit and API checks."""
import importlib.util,json,gzip,fcntl,requests
from pathlib import Path
s=importlib.util.spec_from_file_location('batch109',Path(__file__).with_name('continuous-mds-batch-000109.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p,pin=h.pinned(b.PHASE);rows=p['records'];ids=[r['artwork_id'] for r in rows]
 before_path=h.BACKUP/b.PHASE/'locked-before.json.gz';before=h.load(before_path);assert before['plan_sha256']==pin and before['artworks']=={} and not before['artists']
 src=[]
 for r in rows:
  raw=Path(r['evidence_file']).read_bytes();rc=r['evidence'];assert h.sha(raw)==rc['sha256'] and gzip.decompress(Path(rc['body_path']).read_bytes())==raw
  txt=b.b.BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
  assert all(x in txt for x in [r['title'],r['accession_number'],r['date_display'],'NRM - Pictorial Collection (Railway)','CC BY','Science Museum Group'])
  assert (r['first'],r['last'],r['precision'])==((1960,1960,'exact') if r['accession_number']=='1997-8474' else (1840,1840,'circa'))
  src.append(dict(artwork_id=r['artwork_id'],source_id=r['source_id'],sha256=h.sha(raw),fields_match=True,creation_scope_verified=True,original_creator_label=r['creator_label'],image_licence_not_inferred=True))
 b.save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=src,images_selected=0,metadata_licence='CC BY',attribution='Science Museum Group via Museum Data Service'))
 target=b.target()
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids);assert len(after)==2
  notes=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,source_url,evidence_note::jsonb note FROM citations WHERE entity_type='artwork' AND field_name=%s AND entity_id=ANY(%s::uuid[])",(b.FIELD,ids))];assert len(notes)==2
  ext=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))];assert len(ext)==2
  for r in rows:
   a=after[r['artwork_id']]['artwork'];state=after[r['artwork_id']]
   for k,v in dict(title=r['title'],accession_number=r['accession_number'],creation_year_start=r['first'],creation_year_end=r['last'],date_precision=r['precision'],date_display=r['date_display'],status='review',published_at=None,primary_media_id=None,work_type='painting',current_institution_id=b.MID,research_candidate=True,unlinked_creator_label=r['creator_label'],dimensions_text=None).items():assert a[k]==v,(k,a[k],v)
   assert not state['creators'] and not state['attachments'];assert len(state['holdings'])==1
   hold=state['holdings'][0];ev=json.loads(hold['evidence_note']);assert hold['claim_type']=='holding' and hold['institution_id']==b.MID and hold['review_state']=='accepted' and hold['display_state'] is None and hold['gallery'] is None and ev['confidence']>=.8 and ev['source_sha256']==r['evidence']['sha256']
   n=next(x for x in notes if x['entity_id']==r['artwork_id']);assert n['note']['plan_sha256']==pin and n['note']['evidence']['sha256']==r['evidence']['sha256'] and n['source_record_id']==r['source_id'] and n['note']['raw']['attribution']==r['raw']['attribution']
   x=next(x for x in ext if x['entity_id']==r['artwork_id']);assert x['external_id']==r['source_id'] and x['canonical_url']==r['source_url']
   assert db.execute('SELECT count(*) n FROM artworks WHERE accession_number=%s',(r['accession_number'],)).fetchone()['n']==1
  inst=db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(b.MID,)).fetchone()['v'];assert inst==before['institutions'][b.MID]
  old=h.load(b.E/'preserved-existing-before.json.gz')['artworks'];assert h.snapshot(db,list(old))==old
  audit_ids=ids+[a['holdings'][0]['id'] for a in after.values()]
  audit=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_id=ANY(%s::uuid[]) AND action='insert'",(audit_ids,))];assert len(audit)==4 and all(x['before_json'] is None for x in audit)
  ac=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(audit_ids,)).fetchone()['n']
  assert db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==2
 b.save('independent-production-verification.json',dict(at=h.now(),target=target,plan_sha256=pin,transaction_preimage_sha256=h.sha(before_path.read_bytes()),after=after,citations=notes,external_identifiers=ext,verified_new_artworks=2,verified_museum_links=2,existing_institution_and_related_artworks_preserved=True,prior_campaign_increments=0))
 b.save('independent-audit-history-verification.json',dict(at=h.now(),events=audit,empty_transaction_preimages=True,persisted_source_and_plan_checksums_verified=True))
 apis=[]
 for r in rows:
  url='https://artlines.org/api/backend/v1/atlas/artworks/'+r['artwork_id'];res=requests.get(url,timeout=(15,40));assert res.status_code==200
  obj=res.json();assert r['title'] in res.text and r['source_url'] in res.text and b.MUSEUM in res.text
  b.save('public-api-'+r['artwork_id']+'.json',obj);apis.append(dict(artwork_id=r['artwork_id'],url=url,status=res.status_code,sha256=h.sha(res.content),title_source_and_museum_verified=True))
 b.save('independent-public-verification.json',dict(at=h.now(),records=apis,errors=[]))
 b.apply()
 with h.connect() as db:
  assert h.snapshot(db,ids)==after;ac2=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(audit_ids,)).fetchone()['n'];assert ac2==ac
 b.save('independent-resume-verification.json',dict(at=h.now(),own_plan_reconciled_before_replay=True,replay_increments=0,unchanged_rows=True,audit_count_before=ac,audit_count_after=ac2))
 counts=dict(new_painters=0,new_artworks=2,newly_illustrated=0,alternate_images=0,museum_links=2)
 b.save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,metadata_plan_sha256=pin,attribution='Own persisted plan/source citation checksums; empty locked transaction preimages; two artwork and two holding insert audit rows; independent production/API verification. Prior reserve and batches107/108 excluded.',images=0,storage_writes=0,local_catalogue_connections=0,public_api_verified=True))
 print(json.dumps(counts))
