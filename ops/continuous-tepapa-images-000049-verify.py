#!/usr/bin/env python3
"""Independent read-only batch-49 source, production, file and public verification."""
import base64,fcntl,gzip,hashlib,importlib.util,io,json,re,sys
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-tepapa-images-000049.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i
lock=(b.RUNTIME/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
images,audit,review=i.accepted(b.B);assert len(images)==3
ids=[im['artwork_id'] for im in images];expected={im['artwork_id']:im for im in images}
pin=b.h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());rv=b.h.sha((i.folder(b.B)/'visual-review.json').read_bytes())
prewrite='prewrite' in sys.argv
before=b.load(b.E/'tepapa-bounded-gap-input.json.gz')['states'] if prewrite else b.load(i.BACKUP/b.B/'before-000.json.gz');assert all(before[aid]['artwork']['primary_media_id'] is None for aid in ids)
source=[];files=[]
policyrc=b.load(b.E/'source-captures/tepapa-api-policy.receipt.json');polraw=gzip.decompress((b.ROOT/policyrc['body_path']).read_bytes());assert b.h.sha(polraw)==policyrc['sha256'] and policyrc['status']==200
assert '"No Known Copyright Restrictions" or "Creative Commons 0", you may use the media object as you choose' in BeautifulSoup(polraw,'html.parser').get_text(' ',strip=True)
for row in i.selected(b.B)['rows']:
 aid=row['artwork_id'];im=expected[aid];rc=row['image']['receipt'];raw=gzip.decompress((b.ROOT/rc['body_path']).read_bytes());assert b.h.sha(raw)==rc['sha256'] and rc['status']==200
 # Parse the captured native payload directly, independently of the selector.
 sp=BeautifulSoup(raw,'html.parser');objs=[]
 for script in sp.select('script'):
  if script.text.startswith('self.__next_f.push('):
   flight=json.loads(script.text[len('self.__next_f.push('):-1])
   if len(flight)>1 and isinstance(flight[1],str) and '"entity":{"results":' in flight[1]:
    for part in json.loads(flight[1].split(':',1)[1]):
     if isinstance(part,list) and isinstance(part[-1],dict) and 'entity' in part[-1]:objs.append(part[-1]['entity']['results'])
 assert len(objs)==1;obj=objs[0];photo=obj['hasRepresentation'][0]
 assert obj==row['image']['source'] and str(obj['id'])==row['current_source_id'] and obj['identifier']==row['identity_reconciliation']['source_inventory']
 assert obj['title'].replace('’',"'")==row['title'].replace('’',"'") and int(obj['production'][0]['verbatimCreatedDate'])==row['first']==row['last']<=1955
 assert photo['rights']==dict(type='Right',title='No Known Copyright Restrictions',allowsDownload=True)
 assert 'Unrestricted' in photo['facetPermissionType'] and 'Downloadable' in photo['facetPermissionType']
 assert photo['previewUrl']==sp.select_one('meta[property="og:image"]')['content']==row['image']['native_media_url']
 redirect=row['image']['redirect_receipt'];assert redirect['status']==303 and redirect['url']==photo['previewUrl'] and redirect['location']==im['source_image_url']
 assert str(photo['id']) in im['source_image_url'] and im['source_image_url'].endswith('/preview')
 note=json.loads(row['identity_citation']['evidence_note']);nrc=note['source_receipt'];prior=gzip.decompress((b.ROOT/nrc['body_path']).read_bytes());assert b.h.sha(prior)==nrc['sha256'];ent=json.loads(prior)['entities'][row['native_id']];assert ent==note['raw_source_record']['entity']
 assert ent['claims']['P217'][0]['mainsnak']['datavalue']['value']==obj['identifier']
 assert re.search(r'collections\.tepapa\.govt\.nz/[Oo]bject/'+row['current_source_id'],json.dumps(ent))
 variant=row['identity_reconciliation'].get('creator_variant')
 if variant:
  cr=variant['source']['receipt'];cb=gzip.decompress((b.ROOT/cr['body_path']).read_bytes());assert b.h.sha(cb)==cr['sha256'];ce=json.loads(cb)['entities']['Q1335286'];assert ce==variant['source']['entity'];assert obj['production'][0]['contributor']['title'] in [v['value'] for v in ce['aliases']['en']]
  for prop,key in [('P569','birthDate'),('P570','deathDate')]:assert ce['claims'][prop][0]['mainsnak']['datavalue']['value']['time'][1:11]==obj['production'][0]['contributor'][key]
 else:assert b.h.norm(obj['production'][0]['contributor']['title'])==b.h.norm(row['creator_label'])
 for d in row['identity_reconciliation']['checked_dimensions']:
  assert d['source'] in obj['observedDimension'];assert abs(float(d['source'][d['field']])/10-float(d['wikidata_cm']))<.11
 source.append(dict(artwork_id=aid,native_id=row['current_source_id'],wikidata_id=row['native_id'],source_inventory=obj['identifier'],source_sha256=rc['sha256'],historical_source_sha256=nrc['sha256'],source_plan_sha256=note['plan_sha256'],policy_sha256=policyrc['sha256'],source_media=photo,official_redirect=redirect,source_caption=obj['caption'],same_physical_object=True,creator_alias_independently_verified=bool(variant)))
 raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes();assert b.h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and b.h.sha(original)==im['source_sha256']
 with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.format=='JPEG' and pic.size==(im['width'],im['height'])
 with Image.open(io.BytesIO(original)) as pic:
  pic.load();assert list(pic.size)==im['original_dimensions'];assert abs(pic.width/pic.height-im['width']/im['height'])<.03
  assert abs(pic.width/pic.height-float(photo['width'])/float(photo['height']))<.03
 files.append(dict(artwork_id=aid,path=im['path'],bytes=len(raw),sha256=im['sha256'],original_path=im['original_path'],original_sha256=im['source_sha256'],complete_decode=True,proportions_preserved=True,prepared_image_actually_viewed=True,original_separately_viewed=False))
b.save(b.E/'independent-source-verification.json',dict(at=b.h.now(),records=source,records_verified=len(source),api_requests=0,unknown_fields_preserved=True))
b.save(b.E/'independent-file-verification.json',dict(at=b.h.now(),files=files,originals_outside_documents=True))
if prewrite:
 with b.connect() as db:
  live=b.h.snapshot(db,ids);assert all(live[aid]==before[aid] for aid in ids)
 b.save(b.E/'independent-prewrite-verification.json',dict(at=b.h.now(),source_records_verified=len(source),files_verified=len(files),primary_gaps_rechecked=len(ids),selection_sha256=pin,visual_review_sha256=rv,no_existing_primary_replaced=True,production_target=b.target()))
 print('Independent prewrite verification passed for',len(ids));sys.exit(0)
with b.connect() as db:
 after=b.h.snapshot(db,ids)
 rows=[dict(r) for r in db.execute('SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256::text,ma.storage_path,ma.byte_size,ma.rights_status,ma.license_url,ma.creator_credit,ma.attribution_text,mre.adapter_version,mre.source_checksum,mre.source_record_id,mre.source_image_url,mre.evidence_json FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence mre ON mre.media_id=ma.id WHERE a.id=ANY(%s::uuid[])',(ids,))];assert len(rows)==len(ids)
 selected={r['artwork_id']:r for r in i.selected(b.B)['rows']}
 for r in rows:
  aid=r['id'];im=expected[aid];sel=selected[aid];ev=r['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
  assert r['primary_media_id']==im['media_id'] and r['checksum_sha256']==im['sha256'] and r['storage_path']==im['storage_path'] and r['byte_size']==im['bytes']
  assert r['adapter_version']==i.OP and ev['selection_sha256']==pin and ev['batch_visual_review_sha256']==rv
  assert r['source_checksum']==sel['image']['receipt']['sha256'] and r['source_image_url']==im['source_image_url'] and r['source_record_id']==sel['current_source_id']
  assert r['rights_status']=='restricted' and r['license_url']==b.POLICY and r['creator_credit']==sel['image']['source']['caption'] and 'New Zealand' in r['attribution_text']
  assert ev['user_authorization']['copyright_holder_licence'] is False and ev['visual_review']['viewed_individually'] is True
  assert ev['identity_citation']==sel['identity_citation'] and ev['identity_reconciliation']==sel['identity_reconciliation'] and ev['original_catalogue_plan_sha256']==sel['plan_sha256']
  assert all(after[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in i.IGNORE)
  assert after[aid]['creators']==before[aid]['creators'] and after[aid]['holdings']==before[aid]['holdings']
  assert len(after[aid]['attachments'])==len(before[aid]['attachments'])+1 and any(a['media_id']==im['media_id'] for a in after[aid]['attachments'])
 search=db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[]) AND primary_media_id=ANY(%s::uuid[])',(ids,[im['media_id'] for im in images])).fetchone()['n'];assert search==len(ids)
 events=[dict(r) for r in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[im['media_id'] for im in images]))]
 for aid in ids:
  matching=[r for r in events if r['entity_id']==aid and r['before_json']['primary_media_id'] is None and r['after_json']['primary_media_id']==expected[aid]['media_id']];assert len(matching)==1 and matching[0]['before_json']==before[aid]['artwork']
 staged=b.load(b.E/'tepapa-bounded-gap-input.json.gz');heldids=[r['id'] for r in staged['rows'] if r['id'] not in ids];held=b.h.snapshot(db,heldids);assert all(held[aid]==staged['states'][aid] for aid in heldids)
b.save(b.E/'independent-production-verification.json',dict(at=b.h.now(),rows=rows,verified_new_primary_images=len(ids),transaction_preimages=str(i.BACKUP/b.B/'before-000.json.gz'),preimage_sha256=b.h.sha((i.BACKUP/b.B/'before-000.json.gz').read_bytes()),selection_sha256=pin,visual_review_sha256=rv,metadata_creators_holdings_and_status_preserved=True,search_documents=search,after=after))
b.save(b.E/'independent-audit-history-verification.json',dict(at=b.h.now(),events=events,locked_preimages_match=True))
b.save(b.E/'independent-held-objects-verification.json',dict(at=b.h.now(),ids=heldids,unchanged=True,held_primary_images_attached=0))
credentials=i.d.core.GcloudCredentials();credentials.refresh(None);client=i.storage.Client(project='artline-508319',credentials=credentials);bucket=client.bucket(i.d.core.BUCKET);storage=[];public=[]
for im in images:
 blob=bucket.blob(im['storage_path'].lstrip('/'));blob.reload();raw=Path(im['path']).read_bytes();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode() and blob.metadata['sha256']==im['sha256'] and blob.metadata['operation']==i.OP
 storage.append(dict(artwork_id=im['artwork_id'],storage_path=blob.name,generation=blob.generation,bytes=blob.size,sha256=blob.metadata['sha256'],operation=blob.metadata['operation'],md5_verified=True))
 url='https://artlines.org'+im['storage_path'];r=i.session().get(url,timeout=(15,60));r.raise_for_status();assert b.h.sha(r.content)==im['sha256']
 api='https://artlines.org/api/backend/v1/atlas/artworks/'+im['artwork_id'];a=i.session().get(api,timeout=(15,60));a.raise_for_status();assert im['storage_path'] in a.text
 public.append(dict(artwork_id=im['artwork_id'],image_url=url,sha256=im['sha256'],api_url=api,image_status=r.status_code,api_status=a.status_code))
b.save(b.E/'independent-storage-verification.json',dict(at=b.h.now(),checks=storage))
b.save(b.E/'independent-public-verification.json',dict(at=b.h.now(),rows=public))
counts=dict(new_painters=0,new_artworks=0,newly_illustrated=len(ids),alternate_images=0,museum_links=0)
b.save(b.E/'batch-verification-receipt.json',dict(at=b.h.now(),verified_counts=counts,production_ids=ids,selection_sha256=pin,visual_review_sha256=rv,attribution='Own locked transaction preimages and matching audit events prove null-to-own-media transitions; persisted adapter, exact selection/source/visual checksums and storage operation match. Earlier campaigns excluded. Independent checks confirm public image bytes and API associations.',production_target=b.target(),verified_public_images=len(ids),verified_api_rows=len(ids)))
print(json.dumps(counts))
