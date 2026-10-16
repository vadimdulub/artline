"""Independent source/file/live-production/delivery checks; never writes catalogue rows."""
import base64,fcntl,hashlib,importlib.util,io,json,re,sys
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
s=importlib.util.spec_from_file_location('b','ops/continuous-athens-images-000278.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
with (b.RUNTIME/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 prewrite=sys.argv[1]=='prewrite';prefix='prewrite' if prewrite else 'independent'
 images,audit,review=i.accepted(b.B);assert len(images)==6;ids=[v['artwork_id'] for v in images];expected={v['artwork_id']:v for v in images}
 selection=i.selected(b.B);selected={v['artwork_id']:v for v in selection['rows']};pin=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes());vp=h.sha((i.folder(b.B)/'visual-review.json').read_bytes())
 frozen=b.load(b.E/'gap-input.json.gz');before=frozen['states'] if prewrite else b.load(i.BACKUP/b.B/'before-000.json.gz')
 assert all(before[aid]['artwork']['primary_media_id'] is None for aid in ids)
 oldplan=b.E.parent/'000228/greek-aivazovsky-objects-v1/plan.json.gz';oldpin=h.sha(oldplan.read_bytes());sources=[];files=[]
 for aid in ids:
  row=selected[aid];im=expected[aid];a=before[aid]['artwork'];rc=row['image']['receipt'];raw=Path(rc['body_path']).read_bytes();assert h.sha(raw)==rc['sha256'] and rc['status']==200
  sp=BeautifulSoup(raw,'html.parser');head=sp.select_one('h1.artwork');date=head.span.get_text(' ',strip=True);head.span.extract();title=head.get_text(' ',strip=True).rstrip(',').strip()
  assert title==a['title']==row['title'];assert date==a['date_display']==str(a['creation_year_start'])==str(a['creation_year_end']);assert int(date)<=1955
  assert sp.select_one('p.artist').get_text(' ',strip=True)==a['unlinked_creator_label']==row['creator_label']
  assert sp.select_one('p.description').get_text(' ',strip=True)==a['medium_text']+', '+a['dimensions_text']
  assert sp.select_one('.artwork-no').get_text(' ',strip=True).replace('Inv. Number','').strip()==a['accession_number']==row['accession_number']
  tag=sp.select_one('.img-magnifier-container img');assert (tag.get('data-zoom-image') or tag['src'])==im['source_image_url']==row['image']['image_url']
  note=json.loads(row['identity_citation']['evidence_note']);assert h.sha(Path(note['evidence_file']).read_bytes())==note['evidence']['sha256'];assert note['plan_sha256']==oldpin==row['plan_sha256']
  assert note['raw']['image_url']==im['source_image_url'] and note['creator_label']==row['creator_label'];assert note['source_id']==row['native_id']
  assert note['credit']==sp.select_one('p.obtainment').get_text(' ',strip=True)
  sources.append(dict(artwork_id=aid,inventory=a['accession_number'],native_id=row['native_id'],source_sha256=rc['sha256'],historical_source_sha256=note['evidence']['sha256'],original_metadata_plan_sha256=oldpin,date=date,creator_label=row['creator_label'],same_physical_native_object=True,rights_status='restricted',user_authorization_separate=True))
  raw=Path(im['path']).read_bytes();original=Path(im['original_path']).read_bytes();assert h.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000 and h.sha(original)==im['source_sha256']
  with Image.open(io.BytesIO(raw)) as pic:pic.load();assert pic.format=='JPEG' and pic.size==(im['width'],im['height'])
  with Image.open(io.BytesIO(original)) as pic:pic.load();assert list(pic.size)==im['original_dimensions'];assert abs(pic.width/pic.height-im['width']/im['height'])<.03
  visual=next(v for v in review['decisions'] if v['artwork_id']==aid);assert visual['sha256']==im['sha256'] and visual['viewed_individually'] and visual['decision']=='accept'
  files.append(dict(artwork_id=aid,path=im['path'],sha256=im['sha256'],bytes=len(raw),original_path=im['original_path'],original_sha256=im['source_sha256'],complete_decode=True,proportions_preserved=True,actual_derivative_review=True,original_separately_viewed=visual['original_separately_viewed']))
 b.save(b.E/(prefix+'-source-verification.json'),dict(at=h.now(),records=sources,records_verified=len(sources)))
 b.save(b.E/(prefix+'-file-verification.json'),dict(at=h.now(),files=files,originals_outside_documents=True))
 with b.connect() as db:
  live=h.snapshot(db,ids)
  for aid in ids:
   cs=selected[aid]['identity_citation'];found=db.execute('SELECT id::text,entity_id::text,field_name,source_url,evidence_note FROM citations WHERE id=%s',(cs['id'],)).fetchone();assert dict(found)==cs
   matches=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND ((scheme='continuous-athens-object' AND external_id=%s) OR canonical_url=%s)",(selected[aid]['native_id'],selected[aid]['source_url'])).fetchall();assert {v['entity_id'] for v in matches}=={aid}
  if prewrite:
   assert all(live[aid]==before[aid] for aid in ids)
   assert not db.execute('SELECT id FROM media_assets WHERE checksum_sha256=ANY(%s)',([im['sha256'] for im in images],)).fetchall()
   b.save(b.E/'independent-prewrite-verification.json',dict(at=h.now(),selection_sha256=pin,visual_review_sha256=vp,individually_viewed=len(ids),source_verified=len(ids),files_verified=len(ids),live_null_primary_ids=ids,duplicate_hashes=0,unchanged_preimages=True))
   print('Prewrite checks passed:6 exact gaps, sources, actual visual decisions, original/derivative files');raise SystemExit
  rows=[dict(x) for x in db.execute('SELECT a.id::text,a.primary_media_id::text,m.checksum_sha256::text,m.storage_path,m.byte_size,m.rights_status,m.creator_credit,m.license_url,e.adapter_version,e.source_record_id,e.source_checksum,e.source_image_url,e.evidence_json FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=m.id WHERE a.id=ANY(%s::uuid[])',(ids,))];assert len(rows)==len(ids)
  for x in rows:
   aid=x['id'];im=expected[aid];row=selected[aid];ev=x['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
   assert x['primary_media_id']==im['media_id'] and x['storage_path']==im['storage_path'] and x['checksum_sha256']==im['sha256'] and x['byte_size']==im['bytes']
   assert x['adapter_version']==b.OP and ev['selection_sha256']==pin and ev['batch_visual_review_sha256']==vp and ev['original_catalogue_plan_sha256']==oldpin
   assert x['source_record_id']==row['native_id'] and x['source_checksum']==row['image']['receipt']['sha256'] and x['source_image_url']==im['source_image_url']
   assert x['rights_status']=='restricted' and x['license_url']==b.POLICY and row['image']['source']['credit'] in x['creator_credit']
   assert ev['user_authorization']==b.load(b.E/'authorization.json') and ev['identity_citation']==row['identity_citation'] and ev['visual_review']['viewed_individually']
   assert all(live[aid]['artwork'][k]==v for k,v in before[aid]['artwork'].items() if k not in i.IGNORE)
   assert live[aid]['creators']==before[aid]['creators'] and live[aid]['holdings']==before[aid]['holdings']
   assert len(live[aid]['attachments'])==len(before[aid]['attachments'])+1 and any(v['media_id']==im['media_id'] for v in live[aid]['attachments'])
  events=[dict(x) for x in db.execute("SELECT entity_id::text,action,before_json,after_json,created_at FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND action='update' AND after_json->>'primary_media_id'=ANY(%s)",(ids,[im['media_id'] for im in images]))]
  for aid in ids:
   es=[x for x in events if x['entity_id']==aid and x['before_json']['primary_media_id'] is None and x['after_json']['primary_media_id']==expected[aid]['media_id']];assert len(es)==1 and es[0]['before_json']==before[aid]['artwork']
  search=db.execute('SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[]) AND primary_media_id=ANY(%s::uuid[])',(ids,[im['media_id'] for im in images])).fetchone()['n'];assert search==len(ids)
  heldids=[aid for aid in frozen['states'] if aid not in ids];held=h.snapshot(db,heldids);assert all(held[aid]==frozen['states'][aid] for aid in heldids)
 b.save(b.E/'independent-production-verification.json',dict(at=h.now(),rows=rows,after=live,verified_new_primary_images=len(ids),transaction_preimages=str(i.BACKUP/b.B/'before-000.json.gz'),preimage_sha256=h.sha((i.BACKUP/b.B/'before-000.json.gz').read_bytes()),selection_sha256=pin,visual_review_sha256=vp,metadata_creators_holdings_and_status_preserved=True,search_documents=search))
 b.save(b.E/'independent-audit-history-verification.json',dict(at=h.now(),events=events,locked_preimages_match=True))
 b.save(b.E/'independent-held-objects-verification.json',dict(at=h.now(),ids=heldids,unchanged=True,held_primary_images_attached=0))
 creds=i.d.core.GcloudCredentials();creds.refresh(None);client=i.storage.Client(project='artline-508319',credentials=creds);bucket=client.bucket(i.d.core.BUCKET);storage=[];public=[]
 for im in images:
  blob=bucket.blob(im['storage_path'].lstrip('/'));blob.reload();raw=Path(im['path']).read_bytes();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode();assert blob.metadata['sha256']==im['sha256'] and blob.metadata['operation']==b.OP
  assert h.sha(blob.download_as_bytes())==im['sha256']
  storage.append(dict(artwork_id=im['artwork_id'],path=blob.name,generation=blob.generation,sha256=im['sha256'],bytes=blob.size,operation=b.OP,md5_verified=True,download_checksum_verified=True))
  url='https://artlines.org'+im['storage_path'];r=i.session().get(url,timeout=(15,60));r.raise_for_status();assert h.sha(r.content)==im['sha256']
  with Image.open(io.BytesIO(r.content)) as pic:pic.load();assert pic.size==(im['width'],im['height'])
  api='https://artlines.org/api/backend/v1/atlas/artworks/'+im['artwork_id'];r2=i.session().get(api,timeout=(15,60));r2.raise_for_status();assert im['storage_path'] in r2.text and selected[im['artwork_id']]['source_url'] in r2.text
  b.save(b.E/('public-api-'+im['artwork_id']+'.json'),r2.json())
  public.append(dict(artwork_id=im['artwork_id'],image_url=url,image_status=r.status_code,sha256=im['sha256'],api_url=api,api_status=r2.status_code))
 b.save(b.E/'independent-storage-verification.json',dict(at=h.now(),checks=storage));b.save(b.E/'independent-public-verification.json',dict(at=h.now(),rows=public))
 counts=dict(new_painters=0,new_artworks=0,newly_illustrated=len(ids),alternate_images=0,museum_links=0)
 b.save(b.E/'batch-verification-receipt.json',dict(at=h.now(),verified_counts=counts,production_ids=ids,selection_sha256=pin,visual_review_sha256=vp,production_target=b.target(),verified_public_images=len(ids),verified_api_rows=len(ids),attribution='Exact locked null-primary preimages and audit transitions to this operation media; persisted source/selection/visual checksums and storage operation establish own delivery. All earlier catalogue additions and museum links excluded.'))
 print(json.dumps(counts))
