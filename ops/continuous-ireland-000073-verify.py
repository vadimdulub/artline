#!/usr/bin/env python3
"""Independent batch 73 production attribution, media, public delivery and replay."""
import fcntl, hashlib, importlib.util, io, json
from pathlib import Path
import requests
from PIL import Image
from google.cloud import storage
s=importlib.util.spec_from_file_location('b73',Path(__file__).with_name('continuous-ireland-000073.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']]
pre=h.load(h.BACKUP/b.PHASE/'locked-before.json.gz');assert pre['plan_sha256']==pin and pre['artworks']=={}
tx=h.load(h.BACKUP/b.PHASE/'transaction-after.json.gz');assert tx['plan_sha256']==pin
selection=i.selected(b.B);ispin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());assert h.load(i.folder(b.B)/'pin.json')['sha256']==ispin
imgs,audit,review=i.accepted(b.B);assert len(imgs)==1 and len(review['decisions'])==1 and review['decisions'][0]['viewed_individually']
im=imgs[0];image_aid=im['artwork_id'];image_pre=h.load(i.BACKUP/b.B/'before-000.json.gz')
assert image_pre[image_aid]['artwork']['primary_media_id'] is None
sources=[]
for r in p['records']:
    raw=Path(r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256']
    parsed=b.native.fields(raw);facts,reason=b.native.facts(parsed,r['index_record']);assert not reason
    assert (r['title'],r['accession_number'],r['creator_label'],r['dimensions'])==(facts['title'],facts['accession'],facts['creator_label'],facts['dimensions'])
    sources.append(dict(artwork_id=r['artwork_id'],source_id=r['source_id'],source_sha256=r['evidence']['sha256'],inventory=r['accession_number'],date=r['date_display'],creator=r['creator_label']))
with h.connect() as db,db.transaction():
    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids);assert len(after)==2
    notes=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb note FROM citations WHERE entity_type='artwork' AND field_name=%s AND entity_id=ANY(%s::uuid[])",(b.FIELD,ids))];assert len(notes)==2
    for r in p['records']:
        st=after[r['artwork_id']];a=st['artwork'];note=next(x['note'] for x in notes if x['entity_id']==a['id']);old=tx['artworks'][a['id']]
        assert note['plan_sha256']==pin and note['evidence']['sha256']==r['evidence']['sha256'] and note['source_id']==r['source_id']
        assert {k:v for k,v in a.items() if k not in i.IGNORE}=={k:v for k,v in old['artwork'].items() if k not in i.IGNORE}
        assert st['creators']==old['creators'] and st['holdings']==old['holdings']
        assert (a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['medium_text'],a['dimensions_text'],a['work_type'])==(r['title'],r['accession_number'],r['first'],r['last'],r['precision'],r['medium'],r['dimensions'],'painting')
        assert a['status']=='review' and a['published_at'] is None and a['research_candidate'] and a['current_institution_id']==b.MID
        if r['source_id']=='8923':assert a['unlinked_creator_label']==r['creator_label'] and st['creators']==[] and a['primary_media_id'] is None and st['attachments']==[]
        else:
            assert len(st['creators'])==1 and st['creators'][0]['artist_id']==r['artist_id'] and a['unlinked_creator_label'] is None
            assert a['primary_media_id']==im['media_id'] and len(st['attachments'])==1 and st['attachments'][0]['media_id']==im['media_id']
        assert len(st['holdings'])==1
        hold=st['holdings'][0];ev=json.loads(hold['evidence_note']);assert hold['claim_type']=='holding' and hold['review_state']=='accepted' and hold['institution_id']==b.MID and hold['context']=='collection' and ev['source_sha256']==r['evidence']['sha256'] and ev['confidence']>=.8
        assert db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(b.SCHEME,r['source_id'])).fetchall()==[dict(entity_id=a['id'])]
        assert db.execute('SELECT count(*) n FROM artworks WHERE accession_number=%s',(r['accession_number'],)).fetchone()['n']==1
    old=h.load(b.E/'preserved-existing-before.json.gz')['artworks'];assert h.snapshot(db,list(old))==old
    artists={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(list(p['artists']),))};assert artists==p['artists']
    media=db.execute('SELECT to_jsonb(m) v FROM media_assets m WHERE id=%s',(im['media_id'],)).fetchone()['v']
    assert (media['checksum_sha256'],media['storage_path'],media['byte_size'],media['width'],media['height'],media['rights_status'])==(im['sha256'],im['storage_path'],im['bytes'],239,299,'cc_by')
    assert media['source_page_url']==selection['rows'][0]['source_url'] and media['license_url']=='https://creativecommons.org/licenses/by/4.0/' and 'National Gallery of Ireland' in media['attribution_text']
    rights=db.execute('SELECT to_jsonb(r) v FROM media_rights_evidence r WHERE media_id=%s',(im['media_id'],)).fetchone()['v'];ev=rights['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
    assert ev['selection_sha256']==ispin and ev['original_catalogue_plan_sha256']==pin and ev['batch_visual_review_sha256']==h.sha((i.folder(b.B)/'visual-review.json').read_bytes())
    assert ev['native_source']['native_inventory']=='NGI.488' and ev['native_source']['commons_creator'].startswith('Jan Baptist') and rights['source_id']=='de4bd5ae-b280-4e0f-ba55-d462f47613d9'
    assert rights['source_checksum']==h.load(b.E/'commons-weenix-capture.json')['sha256'] and rights['source_image_url']==im['source_image_url']
    allids=ids+[v['holdings'][0]['id'] for v in after.values()]+[im['media_id']]
    audits=[dict(x) for x in db.execute('SELECT entity_type,entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_id=ANY(%s::uuid[]) ORDER BY created_at',(allids,))]
    for aid in allids[:-1]:
        events=[e for e in audits if e['entity_id']==aid and e['action']=='insert'];assert len(events)==1 and not events[0]['before_json'] and events[0]['after_json']['id']==aid
    image_events=[e for e in audits if e['entity_id']==image_aid and e['action']=='update' and e['before_json']['primary_media_id'] is None and e['after_json']['primary_media_id']==im['media_id']]
    assert len(image_events)==1 and image_events[0]['before_json']==image_pre[image_aid]['artwork'] and image_events[0]['after_json']==after[image_aid]['artwork']
    media_audit_triggers=[dict(x) for x in db.execute("SELECT trigger_name,action_statement FROM information_schema.triggers WHERE event_object_table='media_assets' AND action_statement ILIKE '%%audit%%'")];assert not media_audit_triggers
    search=db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['n'];assert search==2
    n_audit=len(audits)
b.save('independent-production-verification.json',dict(at=h.now(),plan_sha256=pin,image_selection_sha256=ispin,after=after,citations=notes,media=media,rights_evidence=rights,source_checks=sources,search_documents=search,empty_transaction_preimages=str(h.BACKUP/b.PHASE/'locked-before.json.gz'),image_null_primary_preimage=str(i.BACKUP/b.B/'before-000.json.gz'),preserved_existing_artworks=len(old),preserved_existing_artists=len(artists),other_campaign_and_replay_increments_excluded=True))
b.save('independent-audit-history-verification.json',dict(at=h.now(),records=audits,verified_insert_events=4,verified_primary_image_update_events=1,image_events=image_events,empty_preimages_verified=True,media_asset_audit_triggers=media_audit_triggers,limitation='Existing schema does not audit media_assets inserts. Primary image transition is independently audited on artwork with exact null-primary preimage and exact live postimage; rights and storage evidence verify media provenance. No nonexistent media insert event claimed.'))
raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes()
assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(original)==im['source_sha256']
assert hashlib.sha1(original).hexdigest()=='56a666c1ab84024922f7f954966b572cacb68ebb'
for data in [raw,original]:
    with Image.open(io.BytesIO(data)) as picture:picture.load();assert picture.size==(239,299)
creds=i.d.core.GcloudCredentials();creds.refresh(None);client=storage.Client(project='artline-508319',credentials=creds);blob=client.bucket(i.d.core.BUCKET).blob(im['storage_path'].lstrip('/'));blob.reload()
assert blob.size==len(raw) and blob.metadata['sha256']==im['sha256'] and blob.metadata['operation']==i.OP
storage_bytes=blob.download_as_bytes();assert h.sha(storage_bytes)==im['sha256']
b.save('independent-file-storage-verification.json',dict(at=h.now(),artwork_id=image_aid,media_id=im['media_id'],original_sha256=h.sha(original),original_sha1=hashlib.sha1(original).hexdigest(),original_path=im['original_path'],source_dimensions=[239,299],derivative_dimensions=[239,299],derivative_sha256=h.sha(raw),bytes=len(raw),full_decodes=2,storage_bucket=i.d.core.BUCKET,storage_path=im['storage_path'],generation=blob.generation,storage_sha256=h.sha(storage_bytes),actual_visual_views=1))
public=[]
for aid in ids:
    url='https://artlines.org/api/backend/v1/atlas/artworks/'+aid;response=requests.get(url,timeout=(15,50));assert response.status_code==200
    payload=response.json();serialized=json.dumps(payload,ensure_ascii=False);r=next(x for x in p['records'] if x['artwork_id']==aid)
    assert r['title'] in serialized and r['source_url'] in serialized and b.MUSEUM in serialized
    if aid==image_aid:assert im['storage_path'] in serialized
    else:assert 'After Guercino' in serialized
    b.save('public-api-'+aid+'.json',payload);public.append(dict(artwork_id=aid,url=url,status=200,response_sha256=h.sha(response.content),title_source_holding_visible=True,qualified_creator_visible=aid!=image_aid,image_visible=aid==image_aid))
url='https://artlines.org'+im['storage_path'];response=requests.get(url,timeout=(15,50));assert response.status_code==200 and h.sha(response.content)==im['sha256']
with Image.open(io.BytesIO(response.content)) as picture:picture.load();assert picture.size==(239,299)
b.save('independent-public-verification.json',dict(at=h.now(),records=public,verified_artworks=2,image_url=url,image_status=200,image_sha256=h.sha(response.content),image_bytes=len(response.content),image_fully_decoded=True))
b.apply();b.target(True);i.apply(b.B)
with h.connect() as db:
    assert h.snapshot(db,ids)==after
    assert db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(allids,)).fetchone()['n']==n_audit
counts=dict(new_painters=0,new_artworks=2,newly_illustrated=1,alternate_images=0,museum_links=2)
b.save('independent-resume-verification.json',dict(at=h.now(),metadata_apply_replayed=True,image_apply_replayed=True,persisted_source_and_rights_plan_checksums_verified=True,artworks_unchanged=True,audit_events_before=n_audit,audit_events_after=n_audit,replay_increments={k:0 for k in counts}))
b.save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,plan_sha256=pin,image_selection_sha256=ispin,visual_review_sha256=h.sha((i.folder(b.B)/'visual-review.json').read_bytes()),production_target=b.target(),attribution='Two distinct artwork and holding insert audit events, empty locked metadata preimages and own persisted citation plan checksums; one null-primary image preimage and own persisted rights selection/plan checksums independently verified. Prior campaigns and replay excluded.',limitations=['One 239 x 299 Commons source reproduction; fine details not assessed.','Official museum image-ordering host HTTP 403 remains held.','After Guercino remains anonymous-maker copy, unillustrated.','Michel landscape remains held for exact physical-version reconciliation.']))
print(json.dumps(counts))
