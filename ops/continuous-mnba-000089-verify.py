#!/usr/bin/env python3
"""Independently reconcile persisted attribution, live rows, audit, storage and replay."""
import base64,fcntl,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-mnba-images-000089.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i;h=b.h
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
images,_,_=i.accepted(b.B);assert len(images)==1
ids=[im['artwork_id'] for im in images];expected={im['artwork_id']:im for im in images};selected={r['artwork_id']:r for r in i.selected(b.B)['rows']}
pin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());rv=h.sha((i.folder(b.B)/'visual-review.json').read_bytes())
preimage=i.BACKUP/b.B/'before-000.json.gz';before=h.load(preimage);assert all(before[aid]['artwork']['primary_media_id'] is None for aid in ids)
with b.connect() as db:
 after=h.snapshot(db,ids)
 rows=[dict(r) for r in db.execute('SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256::text,ma.storage_path,ma.byte_size,ma.rights_status,ma.license_label,ma.creator_credit,mre.adapter_version,mre.source_checksum,mre.source_record_id,mre.source_image_url,mre.evidence_json FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence mre ON mre.media_id=ma.id WHERE a.id=ANY(%s::uuid[])',(ids,))];assert len(rows)==len(ids)
 for r in rows:
  aid=r['id'];im=expected[aid];row=selected[aid];ev=r['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
  assert r['primary_media_id']==im['media_id'] and r['checksum_sha256']==im['sha256'] and r['storage_path']==im['storage_path'] and r['byte_size']==im['bytes']<=100000
  assert r['adapter_version']==i.OP and ev['selection_sha256']==pin and ev['batch_visual_review_sha256']==rv
  assert r['source_checksum']==row['image']['receipt']['sha256'] and r['source_image_url']==im['source_image_url'] and r['source_record_id']==row['current_source_id']
  assert r['rights_status']==row['rights_status'] and r['license_label']==row['rights_label']
  assert ev['identity']==row['identity_basis'] and ev['identity_confidence']>=.90 and ev['original_catalogue_plan_sha256']==row['plan_sha256']
  assert ev['visual_review']['decision']=='accept' and ev['visual_review']['viewed_individually'] is True
  assert ev['native_source']['commons_object_crosswalk']==row['image']['source']['commons_object_crosswalk']
  assert ev['native_source']['original_object_evidence']==row['image']['source']['original_object_evidence']
  assert row['source_credit'] in r['creator_credit']
  assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in i.IGNORE)
  assert after[aid]['creators']==before[aid]['creators'] and after[aid]['holdings']==before[aid]['holdings']
  assert len(after[aid]['attachments'])==len(before[aid]['attachments'])+1 and any(a['media_id']==im['media_id'] for a in after[aid]['attachments'])
 search=db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[]) AND primary_media_id=ANY(%s::uuid[])',(ids,[im['media_id'] for im in images])).fetchone()['n'];assert search==len(ids)
 events=[dict(r) for r in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[im['media_id'] for im in images]))]
 for aid in ids:
  matching=[r for r in events if r['entity_id']==aid and r['before_json']['primary_media_id'] is None and r['after_json']['primary_media_id']==expected[aid]['media_id']];assert len(matching)==1 and matching[0]['before_json']==before[aid]['artwork']
 initial=b.load(b.E/'gap-input.json.gz')['before'];heldids=[aid for aid in initial if aid not in ids];heldnow=h.snapshot(db,heldids);assert all(heldnow[aid]==initial[aid] for aid in heldids)
 audit_count=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']
b.save('independent-production-verification.json',dict(at=h.now(),rows=rows,verified_new_primary_images=len(ids),transaction_preimages=str(preimage),preimage_sha256=h.sha(preimage.read_bytes()),selection_sha256=pin,visual_review_sha256=rv,metadata_creators_holdings_and_status_preserved=True,search_documents=search,after=after))
b.save('independent-audit-history-verification.json',dict(at=h.now(),events=events,locked_preimages_match=True))
b.save('independent-other-gaps-verification.json',dict(at=h.now(),ids=heldids,unchanged=True,other_primary_images_attached=0))
credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=i.storage.Client(project='artline-508319',credentials=credentials);bucket=client.bucket(i.d.core.BUCKET);storage=[];public=[]
for im in images:
 blob=bucket.blob(im['storage_path'].lstrip('/'));blob.reload();raw=Path(im['path']).read_bytes();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode() and blob.metadata['sha256']==im['sha256'] and blob.metadata['operation']==i.OP
 storage.append(dict(artwork_id=im['artwork_id'],storage_path=blob.name,generation=blob.generation,bytes=blob.size,sha256=blob.metadata['sha256'],operation=blob.metadata['operation'],md5_verified=True))
 url='https://artlines.org'+im['storage_path'];r=i.session().get(url,timeout=(15,60));r.raise_for_status();assert h.sha(r.content)==im['sha256']
 api='https://artlines.org/api/backend/v1/atlas/artworks/'+im['artwork_id'];a=i.session().get(api,timeout=(15,60));a.raise_for_status();assert im['storage_path'] in a.text
 public.append(dict(artwork_id=im['artwork_id'],image_url=url,sha256=im['sha256'],api_url=api,image_status=r.status_code,api_status=a.status_code))
b.save('independent-storage-verification.json',dict(at=h.now(),checks=storage));b.save('independent-public-verification.json',dict(at=h.now(),rows=public))
counts=dict(new_painters=0,new_artworks=0,newly_illustrated=len(ids),alternate_images=0,museum_links=0)
b.save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,selection_sha256=pin,visual_review_sha256=rv,attribution='Null-primary locked preimage equals exact audit before-row; persisted rights carry own campaign, source, selection, original catalogue plan and visual-review checksums. Prior campaigns and already illustrated rows excluded.',production_target=b.target(),verified_public_images=len(ids),verified_api_rows=len(ids),limitations=['WikiArt reproduction is 750 x 555 pixels. Both it and the 879 x 651 museum-supplied Commons reference were actually viewed; fine detail and unseen margins/reverse not certified.','MNBA native HTTP403 hold preserved without requests. Museum-supplied Commons caption and reference image corroborate exact 2801 identity and 1843 creation. WikiArt unknown date and physical/pixel aspect discrepancy explicitly preserved and reviewed.','Actual WikiArt Public domain label retained separately from user approval; no independently obtained copyright-holder licence asserted.','Recovery export is schema plus affected rows, not a full database backup.']))
stop=b.load(b.E/'completed-campaign-stop-preservation.json');assert h.sha((b.ROOT/stop['path']).read_bytes())==stop['sha256']
b.save('independent-campaign-stop-verification.json',dict(at=h.now(),stop_file_unchanged=True,separate_campaign=i.OP))

# Reconcile first, then replay the exact pinned batch; this is not a new delivery.
b.deliver()
with b.connect() as db:
 after_replay=h.snapshot(db,ids);new_count=db.execute('SELECT count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']
assert after_replay==after and audit_count==new_count
for check in storage:
 blob=bucket.blob(check['storage_path']);blob.reload();assert str(blob.generation)==str(check['generation'])
b.save('independent-resume-verification.json',dict(at=h.now(),unchanged_snapshot=True,audit_events_before=audit_count,audit_events_after=new_count,unchanged_storage_generations=True,attribution_reconciled_before_replay=True,replay_increments={k:0 for k in counts}))
print(json.dumps(dict(verified_counts=counts,replay_changes=0)))
