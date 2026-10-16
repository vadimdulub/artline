#!/usr/bin/env python3
"""Independent source, audit, live and public verification; no production writes."""
import fcntl,importlib.util,json
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('b178',Path(__file__).with_name('continuous-batch-000178.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
with (b.R/'worker.lock').open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']];n=len(ids);assert 0<n<=25
    prepath=h.BACKUP/b.PHASE/'locked-before.json.gz';pre=h.load(prepath);assert pre['artworks']=={} and pre['plan_sha256']==pin
    b.save('production-target-independent-verification.json',b.target())
    discovery=h.load(b.E/'discovery.json');rc=discovery['index_capture'];raw=Path(rc['body_path']).read_bytes();assert h.sha(raw)==rc['sha256'] and rc['status']==200
    index,nexturl=b.native.index_rows(raw,rc['url']);assert index==discovery['rows']
    sources=[]
    for r in p['records']:
        rc=r['evidence'];raw=Path(rc['body_path']).read_bytes();assert h.sha(raw)==rc['sha256'] and rc['status']==200
        parsed=b.native.fields(raw);assert parsed==r['raw']['native_fields'];idx=r['raw']['index'];assert idx in index
        facts,reason=b.native.facts(parsed,idx);assert not reason
        for key,fkey in [('title','title'),('medium','medium'),('dimensions','dimensions'),('accession_number','accession'),('first','first'),('last','last'),('precision','date_precision'),('source_url','source_url')]:assert r[key]==facts[fkey],(r['source_id'],key)
        assert 0<r['first']<=r['last']<=1970 and r['artist_id'] and not r['before']
        assert r['credit']==parsed['fields']['Credit Line'] and r['creator_label']==idx['creator']
        sources.append(dict(artwork_id=r['artwork_id'],source_id=r['source_id'],source_url=r['source_url'],sha256=rc['sha256'],native_index_and_object_facts_verified=True))
    with h.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids);assert len(after)==n
        notes=[dict(x) for x in db.execute("SELECT entity_id::text,source_id::text,source_record_id,source_url,evidence_note::jsonb note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,b.FIELD))];assert len(notes)==n
        holdids=[]
        for r in p['records']:
            state=after[r['artwork_id']];a=state['artwork'];note=next(x for x in notes if x['entity_id']==a['id'])
            for k,v in dict(title=r['title'],accession_number=r['accession_number'],creation_year_start=r['first'],creation_year_end=r['last'],date_precision=r['precision'],date_display=r['date_display'],medium_text=r['medium'],dimensions_text=r['dimensions'],status='review',primary_media_id=None,current_institution_id=b.MID,research_candidate=True,work_type='painting',published_at=None).items():assert a[k]==v,(a['id'],k)
            assert not state['attachments'] and len(state['creators'])==1 and state['creators'][0]['artist_id']==r['artist_id'] and state['creators'][0]['attribution_role']=='primary'
            assert len(state['holdings'])==1;hold=state['holdings'][0];holdids.append(hold['id']);assert hold['institution_id']==b.MID and hold['claim_type']=='holding' and hold['context']=='collection' and hold['review_state']=='accepted' and hold['display_state'] is None and hold['superseded_by'] is None
            ev=json.loads(hold['evidence_note']);assert ev['confidence']>=.8 and ev['source_sha256']==r['evidence']['sha256'] and ev['inventory']==r['accession_number']
            assert note['note']['plan_sha256']==pin and note['note']['evidence']['sha256']==r['evidence']['sha256'] and note['source_record_id']==r['source_id'] and note['source_url']==r['source_url']
            assert db.execute('SELECT adapter_key FROM sources WHERE id=%s',(note['source_id'],)).fetchone()['adapter_key']==b.OP
            owners=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(b.SCHEME,r['source_id'])).fetchall();assert len(owners)==1 and owners[0]['entity_id']==a['id']
            creator=db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(r['artist_id'],)).fetchone()['v'];assert creator==p['artists'][r['artist_id']]
            assert h.norm(creator['display_name'])==h.norm(r['creator_label']) or db.execute('SELECT 1 FROM artist_aliases WHERE artist_id=%s AND lower(alias)=lower(%s)',(r['artist_id'],r['creator_label'])).fetchone()
        events=[dict(x) for x in db.execute("SELECT entity_id::text,entity_type,action,before_json,after_json,created_at FROM audit_log WHERE entity_id=ANY(%s::uuid[]) AND action='insert'",(ids+holdids,))];assert len(events)==2*n and all(x['before_json'] is None for x in events)
        for r in p['records']:
            ev=next(x for x in events if x['entity_id']==r['artwork_id']);assert ev['after_json']['title']==r['title'] and ev['after_json']['accession_number']==r['accession_number'] and ev['after_json']['status']=='review'
        assert db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==n
        recovery=h.load(h.BACKUP/'affected-preimages.json.gz');assert h.snapshot(db,list(recovery['existing']))==recovery['existing']
        for iid,inst in pre['institutions'].items():assert db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(iid,)).fetchone()['v']==inst
        for aid,artist in pre['artists'].items():assert db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(aid,)).fetchone()['v']==artist
    b.save('independent-source-verification.json',dict(at=h.now(),rows=sources,plan_sha256=pin,index_sha256=discovery['index_capture']['sha256'],qualified_dates_and_creator_roles_verified=True))
    b.save('independent-production-verification.json',dict(at=h.now(),after=after,citations=notes,plan_sha256=pin,verified_new_artworks=n,verified_museum_links=n,locked_preimage=dict(path=str(prepath),sha256=h.sha(prepath.read_bytes())),local_catalogue_connections=0))
    b.save('independent-audit-history-verification.json',dict(at=h.now(),events=h.safe(events),empty_transaction_preimages=True,programme_source_and_plan_checksums_verified=True,new_insert_events=2*n))
    b.save('independent-existing-preservation-verification.json',dict(at=h.now(),existing_works_unchanged=len(recovery['existing']),existing_creators_unchanged=len(pre['artists']),existing_institutions_unchanged=len(pre['institutions']),existing_images_unchanged=True))
    public=[]
    for r in p['records']:
        url='https://artlines.org/api/backend/v1/atlas/artworks/'+r['artwork_id'];res=requests.get(url,timeout=(15,45));assert res.status_code==200
        body=res.json();assert r['title'] in res.text and r['source_url'] in res.text and b.MUSEUM in res.text and r['creator_label'] in res.text
        b.save('public-api-'+r['artwork_id']+'.json',body);public.append(dict(artwork_id=r['artwork_id'],url=url,status=200,sha256=h.sha(res.content),title_creator_source_holding_present=True))
    b.save('independent-public-verification.json',dict(at=h.now(),rows=public,verified_artworks=n))
    image=h.load(b.E/'image-research-decision.json');assert image['images_downloaded']==image['images_prepared']==image['storage_writes']==0 and image['actually_viewed_files']==[]
    b.save('independent-image-non-delivery-verification.json',dict(at=h.now(),source_decision_sha256=h.sha((b.E/'image-research-decision.json').read_bytes()),images_downloaded=0,images_prepared=0,storage_writes=0,visual_reviews_claimed=0,provider_hold_preserved=True))
    counts=dict(new_painters=0,new_artworks=n,newly_illustrated=0,alternate_images=0,museum_links=n)
    b.save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,plan_sha256=pin,locked_preimage_sha256=h.sha(prepath.read_bytes()),production_target='artline-508319:europe-west1:artline-postgres',shared_ingestion_lock='artline-curated-ingestion',attribution='Empty locked artwork preimages, persisted own programme source adapter and source/plan checksums, two insert audit events per object, independent live and public API verification; prior French reserve additions excluded.',limitations=['Native image host403 hold preserved; no images downloaded or visually reviewed.','Page40 only; full museum catalogue and image coverage incomplete.','Unresolved date, creator and version cases retained in discovery ledger.']))
    with h.connect() as db:assert h.snapshot(db,ids)==after
    b.save('independent-read-only-resume-verification.json',dict(at=h.now(),plan_sha256=pin,live_rows_equal=True,attribution_verified=True,new_writes=0,replay_increments={k:0 for k in counts}))
    print(json.dumps(counts),flush=True)
