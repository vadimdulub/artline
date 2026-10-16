#!/usr/bin/env python3
"""Independent persisted attribution, source facts, audit and public API checks."""
import fcntl,importlib.util,json
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-vgm-batch-000108.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p,pin=h.pinned(b.PHASE);assert len(p['records'])==1;r=p['records'][0];aid=r['artwork_id']
 before=h.load(h.BACKUP/b.PHASE/'locked-before.json.gz');assert before['plan_sha256']==pin and before['artworks']=={}
 raw,rc,text=b.page('object-'+b.ACC);cat,crc,ct=b.page('vgm-cat30');assert h.sha(raw)==r['evidence']['sha256'] and h.sha(cat)==r['catalogue_receipt']['sha256']
 assert all(v in text for v in [b.ACC,r['title'],r['creator_label'],r['dimensions'],'1888','pencil and pen and ink on paper','Vincent van Gogh Foundation','on permanent loan'])
 assert r['medium'] in cat.decode() and r['first']==r['last']==1888 and r['precision']=='exact' and r['artist_id']==b.ARTIST
 b.save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,source_sha256=h.sha(raw),catalogue_sha256=h.sha(cat),native_id=b.ACC,fields_match=True,owner='Vincent van Gogh Foundation',relationship='permanent loan custody at Van Gogh Museum',current_display_claim=False,images_selected=0,images_visually_viewed=0))
 checked=b.target()
 with h.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,[aid]);assert len(after)==1;a=after[aid]['artwork']
  for key,val in dict(title=r['title'],accession_number=b.ACC,creation_year_start=1888,creation_year_end=1888,date_display='1888',date_precision='exact',medium_text=r['medium'],dimensions_text=r['dimensions'],current_institution_id=b.MID,status='review',primary_media_id=None,work_type='drawing',published_at=None,research_candidate=True).items():assert a[key]==val,(key,a[key],val)
  assert len(after[aid]['creators'])==1 and after[aid]['creators'][0]['artist_id']==b.ARTIST and not after[aid]['attachments']
  notes=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,source_url,evidence_note::jsonb note FROM citations WHERE entity_type='artwork' AND field_name=%s AND entity_id=%s",(b.FIELD,aid))];assert len(notes)==1;n=notes[0];assert n['note']['plan_sha256']==pin and n['note']['evidence']['sha256']==h.sha(raw) and n['note']['catalogue_receipt']['sha256']==h.sha(cat) and n['source_record_id']==b.ACC
  ext=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=%s",(aid,))];assert len(ext)==1 and ext[0]['external_id']==b.ACC and ext[0]['canonical_url']==b.URL
  holds=after[aid]['holdings'];assert len(holds)==1;hold=holds[0];ev=json.loads(hold['evidence_note']);assert hold['claim_type']=='holding' and hold['review_state']=='accepted' and hold['institution_id']==b.MID and hold['display_state'] is None and hold['gallery'] is None and ev['confidence']>=.8 and 'permanent-loan' in ev['scope'] and 'owner Vincent van Gogh Foundation' in ev['scope']
  events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_id=ANY(%s::uuid[]) AND action='insert'",([aid,hold['id']],))];assert len(events)==2 and all(x['before_json'] is None for x in events)
  assert db.execute('SELECT count(*) n FROM artworks WHERE accession_number=%s',(b.ACC,)).fetchone()['n']==1
  assert db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=%s',(aid,)).fetchone()['n']==1
  inst=db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(b.MID,)).fetchone()['v'];artist=db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(b.ARTIST,)).fetchone()['v'];assert inst==before['institutions'][b.MID] and artist==before['artists'][b.ARTIST]
  recovery=h.load(h.BACKUP/'affected-row-recovery-before.json.gz');assert h.snapshot(db,list(recovery['preserved']))==recovery['preserved']
  audit_count=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',([aid,hold['id']],)).fetchone()['n']
 b.save('independent-production-verification.json',dict(at=h.now(),target=checked,plan_sha256=pin,locked_preimages=b.ref(h.BACKUP/b.PHASE/'locked-before.json.gz'),after=after,citations=notes,external_identifiers=ext,verified_new_artworks=1,verified_museum_links=1,prior_campaign_increments=0,existing_artist_institution_and_eight_gaps_preserved=True))
 b.save('independent-audit-history-verification.json',dict(at=h.now(),events=events,empty_transaction_preimages=True,persisted_source_and_plan_checksums=True))
 url='https://artlines.org/api/backend/v1/atlas/artworks/'+aid;res=requests.get(url,timeout=(15,40));assert res.status_code==200
 obj=res.json();assert r['title'] in res.text and b.URL in res.text and b.MUSEUM in res.text
 b.save('public-api-'+aid+'.json',obj);b.save('independent-public-verification.json',dict(at=h.now(),artwork_id=aid,url=url,status=res.status_code,sha256=h.sha(res.content),title_source_and_museum_verified=True))
 b.apply()
 with h.connect() as db:
  assert h.snapshot(db,[aid])==after
  newcount=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',([aid,hold['id']],)).fetchone()['n'];assert newcount==audit_count
 b.save('independent-resume-verification.json',dict(at=h.now(),own_plan_reconciled_before_replay=True,replay_increments=0,unchanged_rows=True,audit_count_before=audit_count,audit_count_after=newcount))
 counts=dict(new_painters=0,new_artworks=1,newly_illustrated=0,alternate_images=0,museum_links=1)
 b.save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=[aid],metadata_plan_sha256=pin,attribution='Persisted own-plan/source citation checksums, empty locked transaction preimages and one artwork/one holding insert audit independently verified; previous batch and other campaigns excluded.',images=0,visual_review='No images selected or viewed.',museum_connection='Permanent-loan custody; Foundation ownership remains explicit.',public_api_verified=True,local_catalogue_connections=0))
 print(json.dumps(counts))
