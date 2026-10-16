#!/usr/bin/env python3
"""Independent source, transaction, file, storage and public delivery checks."""
import base64, datetime, fcntl, gzip, hashlib, importlib.util, io, json
from pathlib import Path
import requests
from PIL import Image
s=importlib.util.spec_from_file_location('b','ops/continuous-warsaw-batch-000060.py')
b=importlib.util.module_from_spec(s); s.loader.exec_module(b)
h=b.h; i=b.i; E=b.E
lock=(b.R/'worker.lock').open('a+'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p,pin=h.pinned(b.PHASE); ids=[r['artwork_id'] for r in p['records']]
locked=h.load(h.BACKUP/b.PHASE/'locked-before.json.gz')
assert locked['artworks']=={} and locked['plan_sha256']==pin and len(ids)==len(p['records'])
images,audit,review=i.accepted(b.B); expected={im['artwork_id']:im for im in images}
assert set(expected)==set(ids) and not audit['identity_holds']
ipin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes())
rv=h.sha((i.folder(b.B)/'visual-review.json').read_bytes())
ibefore=h.load(i.BACKUP/b.B/'before-000.json.gz')
assert h.load(E/'independent-source-verification.json')['plan_sha256']==pin
files=[]; source_images=[]
for r in i.selected(b.B)['rows']:
    im=expected[r['artwork_id']]; rc=r['image']['receipt']
    raw=gzip.decompress(Path(rc['body_path']).read_bytes())
    assert rc['status']==200 and h.sha(raw)==rc['sha256']
    o=json.loads(raw)['data']; meta=next(x for x in p['records'] if x['artwork_id']==r['artwork_id'])
    assert o==r['image']['source']==meta['raw'] and str(o['id'])==r['native_id']
    assert o['noEvidence']==r['accession_number'] and o['title']==r['title']
    assert o['copyrights'] and all(x['name']=='DOMENA PUBLICZNA' and not x['restricted'] for x in o['copyrights'])
    imurl='https://cyfrowe-cdn.mnw.art.pl/upload/cache/multimedia_detail/'+o['image']['filePath']+'.'+o['image']['extension']
    assert imurl==im['source_image_url'] and o['image']['position']==1
    derivative=Path(im['path']).read_bytes(); original=Path(im['original_path']).read_bytes()
    assert len(derivative)==im['bytes']<=100000 and h.sha(derivative)==im['sha256'] and h.sha(original)==im['source_sha256']
    assert '/Documents/' not in im['original_path']
    with Image.open(io.BytesIO(derivative)) as pic:
        pic.load(); assert pic.format=='JPEG' and pic.size==(im['width'],im['height'])
    with Image.open(io.BytesIO(original)) as pic:
        pic.load(); assert abs(pic.width/pic.height-im['width']/im['height'])<.03
    decision=next(x for x in review['decisions'] if x['artwork_id']==r['artwork_id'])
    assert decision['viewed_individually'] and decision['sha256']==im['sha256'] and decision['decision']=='accept'
    files.append(dict(artwork_id=r['artwork_id'],path=im['path'],bytes=im['bytes'],sha256=im['sha256'],original_path=im['original_path'],original_sha256=im['source_sha256'],complete_decode=True,proportions_preserved=True,actually_viewed=True))
    source_images.append(dict(artwork_id=r['artwork_id'],source_id=r['native_id'],source_checksum=rc['sha256'],image_url=imurl,source_image_id=o['image']['id'],source_rights=o['copyrights'],catalogue_plan_sha256=pin))
b.save('independent-file-verification.json',dict(at=h.now(),files=files))
b.save('independent-image-source-verification.json',dict(at=h.now(),rows=source_images,selection_sha256=ipin,policy_capture=h.load(E/'policy-project.receipt.json')))
with h.connect() as db,db.transaction():
    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    after=h.snapshot(db,ids); assert len(after)==len(p['records'])
    notes=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,b.FIELD))]
    assert len(notes)==len(p['records']) and all(x['note']['plan_sha256']==pin for x in notes)
    insert_events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='insert'",(ids,))]
    assert len(insert_events)==len(p['records']) and {x['entity_id'] for x in insert_events}==set(ids)
    image_events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[x['media_id'] for x in images]))]
    media=[dict(x) for x in db.execute('SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256::text,ma.storage_path,ma.byte_size,ma.rights_status,ma.creator_credit,e.adapter_version,e.source_checksum,e.source_image_url,e.evidence_json FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=ma.id WHERE a.id=ANY(%s::uuid[])',(ids,))]
    assert len(media)==len(p['records'])
    for r in p['records']:
        aid=r['artwork_id']; state=after[aid]; a=state['artwork']; note=next(x for x in notes if x['entity_id']==aid)
        assert note['source_record_id']==r['source_id'] and note['note']['evidence']['sha256']==r['evidence']['sha256']
        assert a['status']=='review' and a['published_at'] is None and a['research_candidate'] and a['current_institution_id']==b.MID and not state['creators']
        fields=['title','accession_number','date_display','creation_year_start','creation_year_end','date_precision','dimensions_text','medium_text','unlinked_creator_label','cultural_context','work_type']
        want=[r['title'],r['accession_number'],r['date_display'],r['first'],r['last'],r['precision'],r['dimensions'],r['medium'],r['creator_label'],None,h.worktype(r)]
        assert [a[k] for k in fields]==want
        holding=state['holdings']; assert len(holding)==1 and holding[0]['claim_type']=='holding' and holding[0]['review_state']=='accepted' and holding[0]['institution_id']==b.MID
        ev=json.loads(holding[0]['evidence_note']); assert ev['source_sha256']==r['evidence']['sha256'] and ev['confidence']>=.8
        native=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(b.SCHEME,r['source_id'])).fetchall(); assert native==[dict(entity_id=aid)]
        assert db.execute('SELECT count(*) n FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(b.MID,r['accession_number'])).fetchone()['n']==1
        event=next(x for x in insert_events if x['entity_id']==aid); assert event['before_json'] in [None,{}] and event['after_json']['title']==r['title'] and event['after_json']['primary_media_id'] is None
        im=expected[aid]; mr=next(x for x in media if x['id']==aid); ev=mr['evidence_json']; ev=json.loads(ev) if isinstance(ev,str) else ev
        assert a['primary_media_id']==mr['primary_media_id']==im['media_id']
        assert (mr['checksum_sha256'],mr['storage_path'],mr['byte_size'])==(im['sha256'],im['storage_path'],im['bytes'])
        assert mr['rights_status']=='public_domain' and mr['adapter_version']==i.OP and ev['selection_sha256']==ipin and ev['batch_visual_review_sha256']==rv and ev['original_catalogue_plan_sha256']==pin
        assert mr['source_checksum']==r['api_receipt']['sha256'] and mr['source_image_url']==im['source_image_url']
        assert ev['visual_review']['viewed_individually'] and ev['visual_review']['decision']=='accept'
        assert len(state['attachments'])==1 and state['attachments'][0]['media_id']==im['media_id']
        before=ibefore[aid]; assert before['artwork']['primary_media_id'] is None
        assert all(a[k]==v for k,v in before['artwork'].items() if k not in i.IGNORE)
        assert state['holdings']==before['holdings'] and state['creators']==before['creators']
        events=[x for x in image_events if x['entity_id']==aid and x['before_json']==before['artwork'] and x['after_json']['primary_media_id']==im['media_id']]; assert len(events)==1
    scope=[dict(x) for x in db.execute('SELECT id::text,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope FROM artworks WHERE id=ANY(%s::uuid[])',(ids,))]
    assert all(x['scope']=='eligible' for x in scope)
    search=db.execute('SELECT count(*) n FROM artworks a JOIN artwork_search_documents s ON s.id=a.id WHERE a.id=ANY(%s::uuid[]) AND s.title=a.title AND s.status=a.status AND s.primary_media_id=a.primary_media_id',(ids,)).fetchone()['n']; assert search==len(p['records'])
    original=h.load(E/'institution-scope-before.json.gz'); oldids=[a['id'] for a in original]
    current={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id=ANY(%s::uuid[])',(oldids,))}
    assert current=={a['id']:a for a in original},'Existing institution catalogue changed'
b.save('independent-production-verification.json',dict(at=h.now(),rows=after,citations=notes,media=media,plan_sha256=pin,selection_sha256=ipin,creation_scope=scope,search_documents=search,new_review_artworks=len(ids),new_primary_images=len(ids),accepted_holdings=len(ids),transaction_preimages=str(h.BACKUP/b.PHASE/'locked-before.json.gz'),preimages_sha256=h.sha((h.BACKUP/b.PHASE/'locked-before.json.gz').read_bytes()),image_preimages=str(i.BACKUP/b.B/'before-000.json.gz'),image_preimages_sha256=h.sha((i.BACKUP/b.B/'before-000.json.gz').read_bytes()),empty_new_object_preimages_verified=True,local_database_connections=0,existing_institution_artworks_unchanged=len(original)))
b.save('independent-audit-history-verification.json',dict(at=h.now(),inserts=insert_events,image_updates=image_events,locked_preimages_equal=True))
credentials=i.d.core.GcloudCredentials(); credentials.refresh(None)
client=i.storage.Client(project='artline-508319',credentials=credentials); bucket=client.bucket(i.d.core.BUCKET)
storage=[]; public=[]
for im in images:
    blob=bucket.blob(im['storage_path'].lstrip('/')); blob.reload(); raw=Path(im['path']).read_bytes()
    assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode() and blob.metadata['sha256']==im['sha256'] and blob.metadata['operation']==i.OP
    storage.append(dict(artwork_id=im['artwork_id'],path=blob.name,generation=blob.generation,bytes=blob.size,sha256=blob.metadata['sha256'],operation=blob.metadata['operation'],md5_verified=True))
    aid=im['artwork_id']; url='https://artlines.org/api/backend/v1/atlas/artworks/'+aid
    response=requests.get(url,timeout=(15,45)); response.raise_for_status(); a=response.json()
    assert a['id']==aid and a['title']==after[aid]['artwork']['title'] and im['storage_path'] in response.text
    pic=requests.get('https://artlines.org'+im['storage_path'],timeout=(15,45)); pic.raise_for_status()
    assert h.sha(pic.content)==im['sha256']
    with Image.open(io.BytesIO(pic.content)) as image: image.load()
    public.append(dict(artwork_id=aid,url=url,status=response.status_code,response_sha256=h.sha(response.content),image_url=pic.url,image_status=pic.status_code,image_sha256=im['sha256'],complete_decode=True))
b.save('independent-storage-verification.json',dict(at=h.now(),checks=storage))
b.save('independent-public-verification.json',dict(at=h.now(),rows=public,all_selected_review_artworks_public=True,all_selected_images_delivered=True))
counts=dict(new_painters=0,new_artworks=len(ids),newly_illustrated=len(ids),alternate_images=0,museum_links=len(ids))
b.save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,plan_sha256=pin,image_selection_sha256=ipin,visual_review_sha256=rv,production_target=b.target(),attribution='Fifteen absent locked metadata preimages, own persisted citation plan/source checksums and insertion audit events. Fifteen null-primary image preimages, own selection/source/visual/plan rights checksums, exact audit preimages, storage operation and public bytes independently verified. Prior programme/campaign additions excluded.'))
print(json.dumps(dict(verified_counts=counts,production_ids=ids)))
