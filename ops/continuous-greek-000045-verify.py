#!/usr/bin/env python3
"""Independent read-only checks of batch 45, with attribution and delivery evidence."""
import base64,fcntl,gzip,hashlib,importlib.util,io,json
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b45',Path(__file__).with_name('continuous-greek-batch-000045.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']];assert len(ids)==len(set(ids))==17
images,audit,review=i.accepted(b.B);assert len(images)==11;ims={im['artwork_id']:im for im in images};selection=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());vp=h.sha((i.folder(b.B)/'visual-review.json').read_bytes())
pre=h.load(h.BACKUP/b.PHASE/'locked-before.json.gz');assert pre['plan_sha256']==pin and pre['artworks']=={}
ipre=h.load(i.BACKUP/b.B/'before-000.json.gz');assert set(ipre)==set(ims) and all(x['artwork']['primary_media_id'] is None for x in ipre.values())
sources=[];files=[]
for r in p['records']:
 raw=Path(r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256'] and r['evidence']['status']==200
 sp=BeautifulSoup(raw,'html.parser');head=sp.select_one('h1.artwork');date=head.span.get_text(' ',strip=True);head.span.extract();assert head.get_text(' ',strip=True).rstrip(',').strip()==r['title'];assert date==r['date_display'];assert r['accession_number'] in sp.select_one('.artwork-no').get_text();assert sp.select_one('p.artist').get_text(' ',strip=True)==r['creator_label'];assert r['last']<=1970
 imgtag=sp.select_one('.img-magnifier-container img');assert (imgtag.get('data-zoom-image') or imgtag['src'])==r['raw']['image_url']
 sources.append(dict(artwork_id=r['artwork_id'],source_url=r['source_url'],source_sha256=r['evidence']['sha256'],inventory=r['accession_number'],date=r['date_display'],creator_label=r['creator_label'],image_selected=r['artwork_id'] in ims))
 if r['artwork_id'] not in ims:assert r['last']>1955;continue
 im=ims[r['artwork_id']];assert r['last']<=1955;raw=Path(im['path']).read_bytes();orig=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and h.sha(orig)==im['source_sha256'] and len(raw)==im['bytes']<=100000
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.format=='JPEG' and pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(orig)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'] and abs(pic.width/pic.height-im['width']/im['height'])<.03
 visual=next(x for x in review['decisions'] if x['artwork_id']==r['artwork_id']);assert visual['sha256']==im['sha256'] and visual['viewed_individually']
 files.append(dict(artwork_id=r['artwork_id'],path=im['path'],original_path=im['original_path'],sha256=im['sha256'],source_sha256=im['source_sha256'],bytes=len(raw),complete_decode=True,proportions_preserved=True,derivative_individually_viewed=True,original_separately_viewed=False))
b.save('independent-source-verification.json',dict(at=h.now(),records=sources,verified=17));b.save('independent-file-verification.json',dict(at=h.now(),records=files,verified=11))
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=h.snapshot(db,ids)
 citations=[dict(x) for x in db.execute("SELECT entity_id::text,evidence_note::jsonb note FROM citations WHERE entity_type='artwork' AND field_name=%s AND entity_id=ANY(%s::uuid[])",(b.FIELD,ids))];assert len(citations)==17
 media=[dict(x) for x in db.execute('SELECT a.id::text,a.primary_media_id::text,m.storage_path,m.checksum_sha256::text,m.byte_size,m.rights_status,e.adapter_version,e.source_checksum,e.source_record_id,e.evidence_json FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=m.id WHERE a.id=ANY(%s::uuid[])',(ids,))];assert len(media)==11
 for r in p['records']:
  aid=r['artwork_id'];a=after[aid]['artwork'];assert (a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['medium_text'],a['dimensions_text'],a['work_type'])==(r['title'],r['accession_number'],r['first'],r['last'],r['precision'],r['medium'],r['dimensions'],h.worktype(r))
  assert a['status']=='review' and a['published_at'] is None and a['current_institution_id']==b.MID;assert a['unlinked_creator_label']==r['creator_label'] and after[aid]['creators']==[]
  note=next(x['note'] for x in citations if x['entity_id']==aid);assert note['plan_sha256']==pin and note['evidence']['sha256']==r['evidence']['sha256']
  holdings=after[aid]['holdings'];assert len(holdings)==1 and holdings[0]['claim_type']=='holding' and holdings[0]['review_state']=='accepted' and holdings[0]['institution_id']==b.MID;hev=json.loads(holdings[0]['evidence_note']);assert hev['confidence']>=.8 and hev['source_sha256']==r['evidence']['sha256']
  assert db.execute('SELECT count(*) n FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(b.MID,r['accession_number'])).fetchone()['n']==1
  if aid in ims:
   assert a['primary_media_id']==ims[aid]['media_id'];assert all(a[k]==v for k,v in ipre[aid]['artwork'].items() if k not in i.IGNORE);assert after[aid]['holdings']==ipre[aid]['holdings'];assert len(after[aid]['attachments'])==1
  else:assert a['primary_media_id'] is None and after[aid]['attachments']==[]
 for row in media:
  aid=row['id'];im=ims[aid];ev=row['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
  assert row['adapter_version']==b.OP and ev['selection_sha256']==selection and ev['original_catalogue_plan_sha256']==pin and ev['batch_visual_review_sha256']==vp
  assert row['storage_path']==im['storage_path'] and row['checksum_sha256']==im['sha256'] and row['byte_size']==im['bytes'] and row['rights_status']=='restricted';assert ev['visual_review']['viewed_individually']
 insert_events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='insert'",(ids,))];assert len(insert_events)==17
 for e in insert_events:assert not e['before_json'] and e['after_json']['id']==e['entity_id'] and e['after_json']['status']=='review'
 image_events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(list(ims),[im['media_id'] for im in images]))];assert len(image_events)==11
 for e in image_events:assert e['before_json']==ipre[e['entity_id']]['artwork'] and e['before_json']['primary_media_id'] is None
 search=db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[])',(ids,)).fetchone()['n'];assert search==17
 holding_ids=[x['id'] for state in after.values() for x in state['holdings']];holding_events=[dict(x) for x in db.execute("SELECT entity_type,entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_id=ANY(%s::uuid[]) AND action='insert'",(holding_ids,))];assert len(holding_events)==17
b.save('independent-production-verification.json',dict(at=h.now(),after=after,citations=citations,media=media,metadata_plan_sha256=pin,image_selection_sha256=selection,visual_review_sha256=vp,metadata_preimages=str(h.BACKUP/b.PHASE/'locked-before.json.gz'),image_preimages=str(i.BACKUP/b.B/'before-000.json.gz'),verified_new_artworks=17,verified_newly_illustrated=11,verified_holdings=17,search_documents=search))
b.save('independent-audit-history-verification.json',dict(at=h.now(),artwork_insert_events=insert_events,image_update_events=image_events,holding_insert_events=holding_events,locked_preimages_match=True))
credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=i.storage.Client(project='artline-508319',credentials=credentials);bucket=client.bucket(i.d.core.BUCKET);storage=[];public=[]
for r in p['records']:
 aid=r['artwork_id'];url='https://artlines.org/api/backend/v1/atlas/artworks/'+aid;resp=i.session().get(url,timeout=(15,60));resp.raise_for_status();assert r['title'] in resp.text and r['source_url'] in resp.text;b.save('public-api-'+aid+'.json',resp.json());row=dict(artwork_id=aid,api_url=url,api_status=resp.status_code)
 if aid in ims:
  im=ims[aid];assert im['storage_path'] in resp.text;blob=bucket.blob(im['storage_path'].lstrip('/'));blob.reload();raw=Path(im['path']).read_bytes();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode() and blob.metadata['sha256']==im['sha256'] and blob.metadata['operation']==b.OP
  storage.append(dict(artwork_id=aid,path=blob.name,generation=blob.generation,bytes=blob.size,sha256=im['sha256'],operation=blob.metadata['operation'],md5_verified=True))
  iu='https://artlines.org'+im['storage_path'];ir=i.session().get(iu,timeout=(15,60));ir.raise_for_status();assert h.sha(ir.content)==im['sha256']
  with Image.open(io.BytesIO(ir.content)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
  row.update(image_url=iu,image_status=ir.status_code,sha256=im['sha256'])
 public.append(row)
b.save('independent-storage-verification.json',dict(at=h.now(),records=storage));b.save('independent-public-verification.json',dict(at=h.now(),records=public))
counts=dict(new_painters=0,new_artworks=17,newly_illustrated=11,alternate_images=0,museum_links=17)
b.save('batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,metadata_plan_sha256=pin,image_selection_sha256=selection,visual_review_sha256=vp,production_target=b.target(),verified_api_rows=17,verified_public_images=11,attribution='Own locked empty metadata preimages, exact persisted plan/source citations and insert audits establish new objects. Own null primary-media preimages, rights selection checksum and matching image update audits establish new primary images. Earlier campaigns excluded.'))
print(json.dumps(counts))
