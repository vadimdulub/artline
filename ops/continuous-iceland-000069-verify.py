#!/usr/bin/env python3
"""Independent production, audit, attribution, public delivery and replay checks."""
import fcntl, importlib.util, json, requests
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b69',Path(__file__).with_name('continuous-iceland-000069.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']]
pre=h.load(h.BACKUP/b.PHASE/'locked-before.json.gz');assert pre['plan_sha256']==pin and pre['artworks']=={} and pre['new_artist_preimages']==[] and pre['new_institution_preimages']==[]
tx=h.load(h.BACKUP/b.PHASE/'transaction-after.json.gz');assert tx['plan_sha256']==pin
sources=[]
for r in p['records']:
    raw=Path(r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256'] and r['evidence']['status']==200
    o=json.loads(BeautifulSoup(raw,'html.parser').select_one('#__NEXT_DATA__').string)['props']['pageProps']['content'];d=o['sarpur']
    assert (d['name'],d['listasafnidId'],d['year'],d['size'],d['artists'][0]['name'])==(r['title'],r['accession_number'],r['date_display'],r['dimensions'],r['creator_label'])
    assert d['objectID']==r['raw']['sarpur_object_id'] and r['last']<=1970
    sources.append(dict(artwork_id=r['artwork_id'],source_id=r['source_id'],source_url=r['source_url'],source_sha256=r['evidence']['sha256'],inventory=r['accession_number'],sarpur_id=d['objectID'],image_downloaded=False))
b.save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=sources,verified=4))
with h.connect() as db,db.transaction():
    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids)
    assert after==tx['artworks'] and len(after)==4
    citations=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb note FROM citations WHERE entity_type='artwork' AND field_name=%s AND entity_id=ANY(%s::uuid[])",(b.FIELD,ids))];assert len(citations)==4
    for r in p['records']:
        st=after[r['artwork_id']];a=st['artwork'];note=next(x['note'] for x in citations if x['entity_id']==a['id'])
        assert note['plan_sha256']==pin and note['evidence']['sha256']==r['evidence']['sha256'] and note['raw']['sarpur_object_id']==r['raw']['sarpur_object_id']
        assert (a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['medium_text'],a['dimensions_text'],a['work_type'])==(r['title'],r['accession_number'],r['first'],r['last'],r['precision'],r['medium'],r['dimensions'],'painting')
        assert a['status']=='review' and a['published_at'] is None and a['research_candidate'] and a['current_institution_id']==b.MID and a['primary_media_id'] is None and st['attachments']==[]
        assert len(st['creators'])==1 and st['creators'][0]['artist_id']==r['artist_id'] and st['creators'][0]['attribution_role']=='primary' and a['unlinked_creator_label'] is None
        assert len(st['holdings'])==1
        hold=st['holdings'][0];ev=json.loads(hold['evidence_note']);assert hold['claim_type']=='holding' and hold['review_state']=='accepted' and hold['institution_id']==b.MID and hold['context']=='collection' and ev['source_sha256']==r['evidence']['sha256'] and ev['confidence']>=.8
        ext=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(b.SCHEME,r['source_id'])).fetchall();assert ext==[{'entity_id':a['id']}]
        assert db.execute('SELECT count(*) n FROM artworks WHERE accession_number=%s',(r['accession_number'],)).fetchone()['n']==1
    artist=db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(b.NEW_ARTIST,)).fetchone()['v']
    for k,v in p['new_artists'][0].items():assert artist[k]==v,(k,artist[k],v)
    acit=db.execute("SELECT evidence_note::jsonb note FROM citations WHERE entity_type='artist' AND entity_id=%s AND field_name='continuous_iceland_creator_evidence_b000069'",(b.NEW_ARTIST,)).fetchone()['note'];assert acit['plan_sha256']==pin and acit['source_sha256']==next(r['evidence']['sha256'] for r in p['records'] if r['source_id']=='li-791')
    assert db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artist' AND scheme='sarpur-artist' AND external_id='56534'").fetchall()==[dict(entity_id=b.NEW_ARTIST)]
    inst=db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(b.MID,)).fetchone()['v'];assert inst['name']==b.MUSEUM and inst['status']=='review'
    old=h.load(b.E/'preserved-existing-before.json.gz')['artworks'];assert h.snapshot(db,list(old))==old
    existing_artists={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(list(p['artists']),))};assert existing_artists==p['artists']
    allids=ids+[b.NEW_ARTIST,b.MID]+[st['holdings'][0]['id'] for st in after.values()]
    audits=[dict(x) for x in db.execute("SELECT entity_type,entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_id=ANY(%s::uuid[]) ORDER BY created_at",(allids,))]
    inserts=[e for e in audits if e['action']=='insert']
    for aid in [x for x in allids if x!=b.MID]:
        events=[e for e in inserts if e['entity_id']==aid];assert len(events)==1 and not events[0]['before_json'] and events[0]['after_json']['id']==aid
    search=db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['n'];assert search==4
    events_count=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(allids,)).fetchone()['n']
b.save('independent-production-verification.json',dict(at=h.now(),plan_sha256=pin,after=after,new_artist=artist,new_institution=inst,citations=citations,artist_citation=acit,search_documents=search,empty_transaction_preimages=str(h.BACKUP/b.PHASE/'locked-before.json.gz'),preserved_existing_artworks=len(old),preserved_existing_artists=len(existing_artists)))
b.save('independent-audit-history-verification.json',dict(at=h.now(),records=audits,insert_events=len(inserts),empty_preimages_verified=True,institution_audit_limit='Established schema has no institution audit trigger. Empty locked institution preimage, pinned insert plan and independently captured live institution postimage document its creation; no institution audit event claimed.'))
public=[]
for aid in ids:
    url='https://artlines.org/api/backend/v1/atlas/artworks/'+aid;r=requests.get(url,timeout=(15,50));assert r.status_code==200
    payload=r.json();serialized=json.dumps(payload,ensure_ascii=False);record=next(x for x in p['records'] if x['artwork_id']==aid)
    assert record['title'] in serialized and record['source_url'] in serialized and b.MUSEUM in serialized
    b.save('public-api-'+aid+'.json',payload);public.append(dict(artwork_id=aid,url=url,status=r.status_code,response_sha256=h.sha(r.content),title_present=True,source_and_museum_present=True))
b.save('independent-public-verification.json',dict(at=h.now(),records=public,verified=4))
b.save('independent-no-image-changes-verification.json',dict(at=h.now(),artwork_ids=ids,new_primary_images=0,new_alternate_images=0,attachments=0,downloads=0,storage_writes=0,actual_visual_reviews=0,reason='Official image rights permission hold; no exact approved-source alternative established. No file or visual inspection is claimed.'))
# Exercise the actual recovery entry point, then compare live state and audit counts.
b.apply()
with h.connect() as db:
    assert h.snapshot(db,ids)==after
    assert db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(b.NEW_ARTIST,)).fetchone()['v']==artist
    assert db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=%s',(b.MID,)).fetchone()['v']==inst
    later=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(allids,)).fetchone()['n'];assert later==events_count
counts=dict(new_painters=1,new_artworks=4,newly_illustrated=0,alternate_images=0,museum_links=4)
b.save('independent-resume-verification.json',dict(at=h.now(),actual_apply_entrypoint_replayed=True,persisted_citation_plan_checked_before_replay=True,unchanged_artworks=True,unchanged_artist=True,unchanged_institution=True,audit_count_before=events_count,audit_count_after=later,replay_increments={k:0 for k in counts}))
b.save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,new_artist_id=b.NEW_ARTIST,new_institution_id=b.MID,metadata_plan_sha256=pin,production_target=b.target(),attribution='Four artwork inserts, one artist insert and four holding inserts independently verified against empty locked transaction preimages, exact persisted source/plan checksums and insert audit history. Public API confirms delivery. No prior campaign or replay counted.',verified_public_records=4,image_files_selected=0))
print(json.dumps(counts))
