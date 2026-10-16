#!/usr/bin/env python3
"""Independent production, provenance, files, storage and public delivery checks."""
import base64,datetime,fcntl,gzip,hashlib,importlib.util,io,json
from pathlib import Path
from PIL import Image
import requests
s=importlib.util.spec_from_file_location('b','ops/continuous-saam-new-000274.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i;E=b.E
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']];locked=h.load(h.BACKUP/b.PHASE/'locked-before.json.gz');assert locked['artworks']=={} and locked['plan_sha256']==pin
images,audit,review=i.accepted(b.B);assert len(images)==len(ids)==2;expected={x['artwork_id']:x for x in images};ipin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());rv=h.sha((i.folder(b.B)/'visual-review.json').read_bytes());ibefore=h.load(i.BACKUP/b.B/'before-000.json.gz')
sources=h.load(E/'independent-source-verification.json');assert sources['plan_sha256']==pin and len(sources['records'])==2
files=[];source_images=[]
for r in i.selected(b.B)['rows']:
 im=expected[r['artwork_id']];rc=r['image']['receipt'];body=gzip.decompress((b.ROOT/rc['body_path']).read_bytes());assert rc['status']==200 and h.sha(body)==rc['sha256'];objects=[json.loads(x) for x in body.splitlines()];o=r['image']['source'];assert o in objects
 d=o['content']['descriptiveNonRepeating'];source_im=d['online_media']['media'];assert len(source_im)==1 and source_im[0]['usage']['access']=='CC0' and source_im[0]['content']==im['source_image_url']
 meta=next(x for x in p['records'] if x['artwork_id']==r['artwork_id']);assert o==meta['raw']['object'] and meta['source_id']==r['native_id'] and r['plan_sha256']==pin
 raw=Path(im['path']).read_bytes();orig=Path(im['original_path']).read_bytes();assert len(raw)==im['bytes']<=100000 and h.sha(raw)==im['sha256'] and h.sha(orig)==im['source_sha256'];assert '/Documents/' not in im['original_path']
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.format=='JPEG' and pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(orig)) as pic:pic.load();assert abs(pic.width/pic.height-im['width']/im['height'])<.03
 decision=next(x for x in review['decisions'] if x['artwork_id']==r['artwork_id']);assert decision['viewed_individually'] and decision['sha256']==im['sha256']
 files.append(dict(artwork_id=r['artwork_id'],path=im['path'],bytes=im['bytes'],sha256=im['sha256'],original_path=im['original_path'],original_sha256=im['source_sha256'],complete_decode=True,proportions_preserved=True,actually_viewed=True))
 source_images.append(dict(artwork_id=r['artwork_id'],native_id=r['native_id'],source_checksum=rc['sha256'],image_url=im['source_image_url'],source_rights='CC0',actual_credit_text=meta['credit'],catalogue_plan_sha256=pin))
b.save('independent-file-verification.json',dict(at=h.now(),files=files));b.save('independent-image-source-verification.json',dict(at=h.now(),rows=source_images,selection_sha256=ipin))
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids);assert len(after)==len(ids)
 notes=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,evidence_note::jsonb note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,b.FIELD))];assert len(notes)==2 and all(x['note']['plan_sha256']==pin for x in notes)
 inserts=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='insert'",(ids,))];assert len(inserts)==2 and {x['entity_id'] for x in inserts}==set(ids)
 image_events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[x['media_id'] for x in images]))]
 media=[dict(x) for x in db.execute('SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256::text,ma.storage_path,ma.byte_size,ma.rights_status,ma.creator_credit,e.adapter_version,e.source_checksum,e.source_image_url,e.evidence_json FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=ma.id WHERE a.id=ANY(%s::uuid[])',(ids,))];assert len(media)==2
 for r in p['records']:
  aid=r['artwork_id'];state=after[aid];a=state['artwork'];note=next(x for x in notes if x['entity_id']==aid);assert note['source_record_id']==r['source_id'] and note['note']['evidence']['sha256']==r['evidence']['sha256']
  assert a['status']=='review' and a['published_at'] is None and a['research_candidate'] and a['current_institution_id']==b.MID
  fields=['title','accession_number','date_display','creation_year_start','creation_year_end','date_precision','dimensions_text','medium_text','work_type','unlinked_creator_label'];want=[r['title'],r['accession_number'],r['date_display'],r['first'],r['last'],r['precision'],r['dimensions'],r['medium'],h.worktype(r),None if r['artist_id'] else r['creator_label']];assert [a[k] for k in fields]==want
  if r['artist_id']:assert len(state['creators'])==1 and state['creators'][0]['artist_id']==r['artist_id'] and state['creators'][0]['attribution_role']=='primary'
  else:assert not state['creators']
  holding=state['holdings'];assert len(holding)==1 and holding[0]['claim_type']=='holding' and holding[0]['review_state']=='accepted' and holding[0]['institution_id']==b.MID;ev=json.loads(holding[0]['evidence_note']);assert ev['source_sha256']==r['evidence']['sha256'] and ev['confidence']>=.8
  native=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(r['scheme'],r['source_id'])).fetchall();assert native==[dict(entity_id=aid)]
  assert db.execute('SELECT count(*) n FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(b.MID,r['accession_number'])).fetchone()['n']==1
  event=next(x for x in inserts if x['entity_id']==aid);assert event['before_json'] in [None,{}] and event['after_json']['title']==r['title'] and event['after_json']['primary_media_id'] is None
  im=expected[aid];mr=next(x for x in media if x['id']==aid);ev=mr['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
  assert a['primary_media_id']==mr['primary_media_id']==im['media_id'] and (mr['checksum_sha256'],mr['storage_path'],mr['byte_size'])==(im['sha256'],im['storage_path'],im['bytes'])
  assert mr['rights_status']=='cc0' and mr['adapter_version']==i.OP and ev['selection_sha256']==ipin and ev['batch_visual_review_sha256']==rv and ev['original_catalogue_plan_sha256']==pin
  assert mr['source_checksum']==next(x['source_checksum'] for x in source_images if x['artwork_id']==aid) and mr['source_image_url']==im['source_image_url'] and r['credit'] in mr['creator_credit']
  assert ev['visual_review']['viewed_individually'] and ev['visual_review']['decision']=='accept';assert len(state['attachments'])==1 and state['attachments'][0]['media_id']==im['media_id']
  if r['source_id']=='24673':assert 'combined front and back' in state['attachments'][0]['view_label']
  before=ibefore[aid];assert before['artwork']['primary_media_id'] is None;assert all(a[k]==v for k,v in before['artwork'].items() if k not in i.IGNORE);assert state['holdings']==before['holdings'] and state['creators']==before['creators']
  events=[x for x in image_events if x['entity_id']==aid and x['before_json']==before['artwork'] and x['after_json']['primary_media_id']==im['media_id']];assert len(events)==1
 artists={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(list(p['artists']),))};assert artists==p['artists']
 scope=[dict(x) for x in db.execute('SELECT id::text,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope FROM artworks WHERE id=ANY(%s::uuid[])',(ids,))];assert all(x['scope']=='eligible' for x in scope)
 search=db.execute('SELECT count(*) n FROM artworks a JOIN artwork_search_documents s ON s.id=a.id WHERE a.id=ANY(%s::uuid[]) AND s.title=a.title AND s.status=a.status AND s.primary_media_id IS NOT DISTINCT FROM a.primary_media_id',(ids,)).fetchone()['n'];assert search==2
b.save('independent-production-verification.json',dict(at=h.now(),rows=after,citations=notes,media=media,plan_sha256=pin,selection_sha256=ipin,creation_scope=scope,search_documents=search,new_review_artworks=2,new_primary_images=2,accepted_holdings=2,existing_artists_preserved=artists,transaction_preimages=str(h.BACKUP/b.PHASE/'locked-before.json.gz'),preimages_sha256=h.sha((h.BACKUP/b.PHASE/'locked-before.json.gz').read_bytes()),image_preimages=str(i.BACKUP/b.B/'before-000.json.gz'),image_preimages_sha256=h.sha((i.BACKUP/b.B/'before-000.json.gz').read_bytes()),empty_new_object_preimages_verified=True,local_database_connections=0))
b.save('independent-audit-history-verification.json',dict(at=h.now(),inserts=inserts,image_updates=image_events,locked_preimages_equal=True))
credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=i.storage.Client(project='artline-508319',credentials=credentials);bucket=client.bucket(i.d.core.BUCKET);storage=[];public=[]
for im in images:
 blob=bucket.blob(im['storage_path'].lstrip('/'));blob.reload();raw=blob.download_as_bytes();assert h.sha(raw)==im['sha256'];assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode() and blob.metadata['sha256']==im['sha256'] and blob.metadata['operation']==i.OP
 storage.append(dict(artwork_id=im['artwork_id'],path=blob.name,generation=blob.generation,bytes=blob.size,sha256=blob.metadata['sha256'],operation=blob.metadata['operation'],md5_verified=True))
b.save('independent-storage-verification.json',dict(at=h.now(),checks=storage))
for aid in ids:
 url='https://artlines.org/api/backend/v1/atlas/artworks/'+aid;r=requests.get(url,timeout=(15,45));r.raise_for_status();a=r.json();assert a['id']==aid and a['title']==after[aid]['artwork']['title'];im=expected[aid];assert im['storage_path'] in r.text
 u='https://artlines.org'+im['storage_path'];pic=requests.get(u,timeout=(15,45));pic.raise_for_status();assert h.sha(pic.content)==im['sha256']
 public.append(dict(artwork_id=aid,url=url,status=r.status_code,response_sha256=h.sha(r.content),image_url=u,image_status=pic.status_code,image_sha256=im['sha256']))
b.save('independent-public-verification.json',dict(at=h.now(),rows=public,all_two_review_artworks_public=True,all_two_images_delivered=True))
counts=dict(new_painters=0,new_artworks=2,newly_illustrated=2,alternate_images=0,museum_links=2)
b.save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,plan_sha256=pin,image_selection_sha256=ipin,visual_review_sha256=rv,production_target=b.target(),attribution='Two IDs absent in own locked metadata preimages; two persisted citation plan/source checksums and insertion audit events. Two image preimages lacked primary media; own rights adapter/selection/source checksums, exact audit preimages, storage operation and public checksums independently verified. All 188 earlier French reserve deliveries excluded.'))
print(json.dumps(dict(verified_counts=counts,all_checks_passed=True)))
