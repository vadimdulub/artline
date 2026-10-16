#!/usr/bin/env python3
"""Independent file/source/live/audit/storage/delivery checks for batch 31."""
import base64,fcntl,gzip,hashlib,importlib.util,io,json,sys
from pathlib import Path
from PIL import Image,ImageOps
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('batch31','ops/continuous-nationalmuseum-images-000031.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i;E=b.E
BATCHES=['nationalmuseum-000','nationalmuseum-small-001']
def collect():
 result=[]
 for batch in BATCHES:
  images,audit,review=i.accepted(batch);rows={r['artwork_id']:r for r in i.selected(batch)['rows']};pin=h.sha((i.folder(batch)/'selection.json.gz').read_bytes());rv=h.sha((i.folder(batch)/'visual-review.json').read_bytes())
  assert pin==h.load(i.folder(batch)/'pin.json')['sha256']
  for im in images:result.append((batch,rows[im['artwork_id']],im,pin,rv))
 assert len(result)==len({x[1]['artwork_id'] for x in result})==5
 return result
def sources():
 checks=[];files=[]
 for batch,r,im,pin,rv in collect():
  aid=r['artwork_id'];rc=r['image']['receipt'];raw=gzip.decompress((b.ROOT/rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200;m=json.loads(raw);assert m==r['image']['source'];props=m['properties'];v=lambda k:props[k]['value']
  nr=h.load(E/'source-captures'/('object-'+r['native_id']+'.receipt.json'));nrraw=gzip.decompress((b.ROOT/nr['body_path']).read_bytes());assert h.sha(nrraw)==nr['sha256'] and nr['status']==200
  obj=json.loads(BeautifulSoup(nrraw,'html.parser').select_one('#__NEXT_DATA__').string)['props']['pageProps']['data']['item'];assert obj==h.load(b.OLD/'objects'/(r['native_id']+'.json'))
  assert v('inventarienummer')==[r['accession_number']]==[obj['ObjInventoryNumberTxt']]
  assert v('titel_en')==[r['title']]==[obj['ObjTitleMainTxt']] and v('titel')==[obj['ObjTitleMainTxt_sv']]
  assert v('konstnar')==['Okänd'] and obj['ObjPersonRefTxt']==r['creator_label']=='Unknown'
  assert int(obj['ObjFromYearTxt'])==r['first'] and int(obj['ObjToYearTxt'])==r['last']<=1970
  assert v('licens')==r['rights_label'] and r['rights_status']==('public_domain' if v('licens')=='Public Domain' else 'cc_by_sa') and v('photocreditline')==r['source_credit']
  prc=r['rights_policy_receipt'];policy=gzip.decompress((b.ROOT/prc['body_path']).read_bytes());assert h.sha(policy)==prc['sha256'] and b'https://creativecommons.org/licenses/by-sa/4.0/' in policy
  rendition=next(x for x in m['downloadables'] if 'https://media.nationalmuseum.se'+x['url']==im['source_image_url']);assert rendition['templateName'] in ['Full JPEG','Small_Powerpoint_web']
  assert im['source_image_url']==r['image']['image_url']
  local=Path(im['path']);assert local.is_relative_to(b.ROOT/'apps/web/public/assets/artworks/imported'/i.OP)
  data=local.read_bytes();original=Path(im['original_path']).read_bytes();assert len(data)==im['bytes']<=100000 and h.sha(data)==im['sha256'] and h.sha(original)==im['source_sha256']
  assert Path(im['original_path']).is_relative_to(Path.home()/'Library/Application Support/Artline/source-images')
  with Image.open(io.BytesIO(data)) as pic:pic.load();assert pic.format=='JPEG' and pic.size==(im['width'],im['height'])
  with Image.open(io.BytesIO(original)) as pic:
   pic.load();pic=ImageOps.exif_transpose(pic);assert pic.size==tuple(im['original_dimensions']);assert abs(pic.width/pic.height-im['width']/im['height'])<.003
   assert rendition['dimensions']==str(pic.width)+'x'+str(pic.height)+' px'
  decision=next(x for x in h.load(i.folder(batch)/'visual-review.json')['decisions'] if x['artwork_id']==aid);assert decision['viewed_individually'] and decision['decision']=='accept' and decision['sha256']==im['sha256']
  checks.append(dict(artwork_id=aid,native_id=r['native_id'],media_id=m['id'],inventory=r['accession_number'],title=r['title'],source_sha256=rc['sha256'],museum_object_sha256=nr['sha256'],rights_label=r['rights_label'],license_url=r['license_url'],credit=r['source_credit'],source_rendition=rendition['templateName'],selection_sha256=pin,visual_review_sha256=rv,actual_visual_review=True))
  files.append(dict(artwork_id=aid,source_sha256=im['source_sha256'],source_path=im['original_path'],derivative_sha256=im['sha256'],bytes=im['bytes'],complete_decode=True,proportions_preserved=True,actually_viewed=True))
 with h.connect() as db:
  for _,r,im,_,_ in collect():
   matches=[dict(x) for x in db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=%s",(['nationalmuseum-object','museum-native-nationalmuseum-object','nationalmuseum-sweden-object'],r['native_id']))]
   assert {x['entity_id'] for x in matches}=={r['artwork_id']}
 b.save(E/'independent-image-source-verification.json',dict(at=h.now(),records=checks,verified=5,direct_image_access_hold_preserved=True,licence_policy_sha256=h.load(E/'source-captures/rights-and-reproductions.receipt.json')['sha256']))
 b.save(E/'independent-file-verification.json',dict(at=h.now(),records=files,verified=5))
 print('Source, identity, rights, full decode, proportions and visual evidence verified for 5 images.',flush=True)
def verify():
 sources();images=collect();ids=[x[1]['artwork_id'] for x in images];pins={};rows=[];events=[];preimages=[]
 with h.connect() as db:
  after=h.snapshot(db,ids)
  for batch,r,im,pin,rv in images:
   aid=r['artwork_id'];bp=i.BACKUP/batch/'before-000.json.gz';before=h.load(bp);old=before[aid];assert old['artwork']['primary_media_id'] is None and old['artwork']['status']!='archived'
   rs=dict(db.execute('SELECT a.id::text,a.primary_media_id::text,ma.checksum_sha256::text,ma.storage_path,ma.byte_size,ma.rights_status,ma.creator_credit,ma.license_label,ma.license_url,ma.attribution_text,mre.adapter_version,mre.source_checksum,mre.source_image_url,mre.policy_url,mre.evidence_json FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id JOIN media_rights_evidence mre ON mre.media_id=ma.id WHERE a.id=%s',(aid,)).fetchone());ev=rs['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
   assert rs['primary_media_id']==im['media_id'] and rs['checksum_sha256']==im['sha256'] and rs['byte_size']==im['bytes'] and rs['storage_path']==im['storage_path']
   assert rs['adapter_version']==i.OP and ev['selection_sha256']==pin and ev['batch_visual_review_sha256']==rv and ev['original_catalogue_plan_sha256']==r['plan_sha256']
   assert rs['source_checksum']==r['image']['receipt']['sha256'] and rs['source_image_url']==im['source_image_url']
   assert rs['rights_status']==r['rights_status'] and rs['license_label']==r['rights_label'] and rs['license_url']==rs['policy_url']==r['license_url'] and r['source_credit'] in rs['creator_credit']
   assert ev['actual_rights_label']==r['rights_label'] and ev['rights_policy_receipt']==r['rights_policy_receipt'] and ev['visual_review']['viewed_individually']
   if r['rights_label']=='CC BY-SA':assert 'Derivative distributed under CC BY-SA 4.0; no additional restrictions.' in rs['attribution_text']
   assert all(after[aid]['artwork'][k]==v for k,v in old['artwork'].items() if k not in i.IGNORE)
   assert after[aid]['holdings']==old['holdings'] and after[aid]['creators']==old['creators']
   assert len(after[aid]['attachments'])==len(old['attachments'])+1 and any(x['media_id']==im['media_id'] for x in after[aid]['attachments'])
   audit=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=%s AND action='update' AND after_json->>'primary_media_id'=%s",(aid,im['media_id']))]
   assert len(audit)==1 and audit[0]['before_json']==old['artwork'] and audit[0]['after_json']==after[aid]['artwork'];events.extend(audit)
   assert db.execute('SELECT primary_media_id::text FROM artwork_search_documents WHERE id=%s',(aid,)).fetchone()['primary_media_id']==im['media_id']
   rows.append(rs);pins[batch]=dict(selection_sha256=pin,visual_review_sha256=rv);preimages.append(dict(artwork_id=aid,path=str(bp),sha256=h.sha(bp.read_bytes()),primary_media_before=None))
  previous=h.load(b.OLD/'independent-image-production-verification.json')['final_rows'];allten=h.snapshot(db,list(previous))
  for aid,old in previous.items():
   if aid not in ids:assert allten[aid]==old
   else:
    assert all(allten[aid]['artwork'][k]==v for k,v in old['artwork'].items() if k not in i.IGNORE)
    assert allten[aid]['creators']==old['creators'] and allten[aid]['holdings']==old['holdings']
 b.save(E/'independent-production-verification.json',dict(at=h.now(),rows=rows,verified_newly_illustrated=5,attribution_preimages=preimages,pins=pins,metadata_holdings_and_creators_preserved=True,other_five_previous_batch_rows_unchanged=True,search_documents_verified=True))
 b.save(E/'independent-audit-history-verification.json',dict(at=h.now(),events=events,locked_preimages_equal_audit_preimages=True))
 creds=i.d.core.GcloudCredentials();creds.refresh(None);client=i.storage.Client(project='artline-508319',credentials=creds);storage=[];public=[]
 for _,r,im,_,_ in images:
  raw=Path(im['path']).read_bytes();blob=client.bucket(i.d.core.BUCKET).blob(im['storage_path'].lstrip('/'));blob.reload();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode() and blob.metadata['sha256']==im['sha256'] and blob.metadata['operation']==i.OP
  storage.append(dict(artwork_id=im['artwork_id'],storage_path=blob.name,generation=blob.generation,bytes=blob.size,sha256=im['sha256'],operation=blob.metadata['operation'],md5_verified=True))
  url='https://artlines.org'+im['storage_path'];resp=i.session().get(url,timeout=(15,45));resp.raise_for_status();assert h.sha(resp.content)==im['sha256']
  au='https://artlines.org/api/backend/v1/atlas/artworks/'+im['artwork_id'];api=i.session().get(au,timeout=(15,45));api.raise_for_status();assert im['storage_path'] in api.text
  b.save(E/'public-api-responses'/(im['artwork_id']+'.json'),api.json())
  public.append(dict(artwork_id=im['artwork_id'],image_url=url,image_status=resp.status_code,sha256=im['sha256'],api_url=au,api_status=api.status_code))
 b.save(E/'independent-storage-verification.json',dict(at=h.now(),records=storage,verified=5))
 b.save(E/'independent-public-verification.json',dict(at=h.now(),records=public,verified=5))
 counts=dict(new_painters=0,new_artworks=0,newly_illustrated=5,alternate_images=0,museum_links=0)
 b.save(E/'batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,pins=pins,production_target=b.target(),attribution='Five previously empty primaries in locked transaction preimages; unique programme/source/review checksum-bound rights rows; one exact matching audit update per object; fresh read-only live state, cloud object metadata and public SHA-256 independently checked. All prior artwork/museum additions and French reserve campaign excluded.'))
 print(json.dumps(counts),flush=True)
if __name__=='__main__':
 with (b.R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
