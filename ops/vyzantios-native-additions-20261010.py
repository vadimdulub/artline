#!/usr/bin/env python3
"""Seven source-backed Vyzantios museum records; unknown dates remain review."""
import importlib.util, json, re, uuid, io, sys, hashlib, base64
from pathlib import Path
from PIL import Image
from psycopg.types.json import Jsonb
spec=importlib.util.spec_from_file_location('batch','ops/vyzantios-random-ten-delivery-20261010.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
b=d.b;r=d.r;ROOT=b.ROOT;RUN=b.RUN/'native-additions';BACKUP=b.BACKUP/'native-additions';AID=b.cohort()[0]['artist']['id'];ACTOR=b.m.ACTOR
NG='052007aa-11f7-4d57-90e6-d3b62bb0bf4b';NH='5d1bc5d4-0e01-5e7b-8669-1411c393a158'
def uid(x):return str(uuid.uuid5(uuid.NAMESPACE_URL,b.OP+'/native/'+x))
def prepare():
 data=r.load(b.RUN/'vyzantios-native-sources.json.gz');selected=[]
 wanted={'hydra-1583':('Hydra',1970,'painting','Oil on canvas','81 x 116 cm','Π.8479'), 'landscape-32':('Landscape',None,'painting','Oil on canvas','79 x 100 cm','Π.4242'), 'landscape-8':('Landscape',None,'painting','Oil on canvas','80 x 115.5 cm','Π.4112'), 'portrait-of-the-artists-wife-frosso-skoumpourdi-4048':('Portrait of the Artist’s Wife Frosso Skoumpourdi',1928,'painting','Oil on canvas','98 x 72 cm','Π.8478'), 'wedding-in-hydra':('Wedding in Hydra',None,'drawing','Pencil, tempera on paper','18 x 25 cm','Κ.979')}
 for p in data['objects']:
  key=p['url'].rstrip('/').rsplit('/',1)[1]
  if key not in wanted:continue
  title,year,kind,medium,size,accession=wanted[key];img=next(x['src'] for x in p['images'] if 'Vyzantios' in (x['alt'] or ''))
  selected.append(dict(url=p['url'],title=title,year_start=year,year_end=year,work_type=kind,medium=medium,dimensions=size,accession=accession,institution_id=NG,provider='National Gallery of Greece',evidence=p,source_image_url=img,rights_label='No object-level reuse licence displayed; National Gallery copyright footer',rights_status='unknown',license_url='https://www.nationalgallery.gr/en/terms-of-use/',attach_image=year==1928))
 p=next(x for x in data['indexes'] if '221219' in x['url'])
 selected.append(dict(url=p['url'],title='Female Nude',alternate_title='Γυναικείο γυμνό',year_start=None,year_end=None,work_type='drawing',medium='Pencil on paper',dimensions='42.5 x 31 cm',accession='2001.411',institution_id=None,provider='Teloglion Foundation of Art',evidence=p,source_image_url=next(x['src'] for x in p['images'] if x['src'].endswith('1114526_187179.jpg')),rights_label='No object-level reuse licence captured',rights_status='unknown',license_url=None,attach_image=False,institution_review='Official collection identified; no verified matching Artline institution. Source retained without inventing an authority.'))
 p=r.load(b.RUN/'hammam-source.json')
 selected.append(dict(url=p['url'],title='Hammam',alternate_title='Χαμάμ',year_start=1921,year_end=1922,work_type='painting',medium='Oil on wood',dimensions=None,accession=None,institution_id=NH,provider='National Historical Museum / SearchCulture',evidence=p,source_image_url='https://www.searchculture.gr/aggregator/digital-files-from-preservator/file/6895ca3b713a6d501c21ac7e',rights_label='SearchCulture file panel: CC BY 4.0; legacy record rights: CC BY-NC-ND 4.0 (conflict preserved)',rights_status='restricted',license_url='https://creativecommons.org/licenses/by-nc-nd/4.0/',attach_image=True,date_review='2009-11-09 is a repository record timestamp; object description and semantic chronology explicitly identify 1921/1922.'))
 assert len(selected)==7
 for x in selected:
  x['id']=uid(x['url']);x['slug']='vyzantios-museum-'+r.sha(x['url'].encode())[:16]
  x['identity_basis']='Exact official object page and explicit Periklis Vyzantios creator; complete reproduction visually distinguished from all 33 in-scope WikiArt entries. Inventory numbers distinguish the two landscapes. Museum holdings do not assert current display.'
 with r.connect('production') as db:
  urls=[x['url'] for x in selected]
  conflicts=db.execute("SELECT entity_id::text,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(urls,)).fetchall()
  conflicts+=db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,)).fetchall()
  assert not conflicts,conflicts
  scoped=db.execute("SELECT to_jsonb(a) a FROM artworks a WHERE current_institution_id=ANY(%s::uuid[]) AND (accession_number=ANY(%s) OR title ILIKE ANY(%s))",([NG,NH],[x['accession'] for x in selected if x['accession']],['%Χαμάμ%','%Hammam%','%Σκουμπ%','%Skoump%'])).fetchall()
  assert not scoped,scoped
  before=b.s.snapshots(db,[x['id'] for x in selected]);assert not before
 if not (RUN/'plan.json.gz').exists():r.save_gz(RUN/'plan.json.gz',dict(at=r.now(),rows=selected,authorization_sha256=r.sha((b.RUN/'authorization.json').read_bytes()),museum_image_policy='User-approved Greek museum/artist workflow, 20 September and 8 October 2026; selected images dated by 1955. Actual rights retained, no independent clearance claimed.'))
 r.save_gz(BACKUP/'preflight.json.gz',dict(existing=before,source_url_conflicts=conflicts,scoped_inventory_conflicts=scoped))
 images=[]
 for x in selected:
  if not x['attach_image']:continue
  assert b.m.urlsplit(x['source_image_url']).hostname in {'www.nationalgallery.gr','www.searchculture.gr'}
  response=d.requests.get(x['source_image_url'],timeout=(15,90));response.raise_for_status();original=response.content;assert len(original)<=250000000
  origin=b.ORIGINALS/'native-originals'/(x['id']+'.original');r.save(origin,original)
  receipt=dict(url=x['source_image_url'],final_url=response.url,at=r.now(),sha256=r.sha(original),bytes=len(original),original_path=str(origin))
  raw,w,h,quality=d.d.core.compress(original)
  assert len(raw)<=100000
  path='/assets/artworks/imported/'+b.OP+'/'+x['id']+'-'+r.sha(raw)[:16]+'.jpg';file=ROOT/'apps/web/public'/path.lstrip('/');r.save(file,raw)
  images.append(dict(artwork_id=x['id'],media_id=uid('media/'+r.sha(raw)),path=path,visual_path=str(file),sha256=r.sha(raw),bytes=len(raw),width=w,height=h,original_receipt=receipt,source_image_url=x['source_image_url']))
 r.save(RUN/'images.json',images);print('Prepared native additions',len(selected),'pictures',len(images),[x['visual_path'] for x in images],flush=True)

def upload():
 plan=r.load(RUN/'plan.json.gz');pin=r.sha((RUN/'plan.json.gz').read_bytes());images=r.load(RUN/'images.json');review=r.load(RUN/'visual-review.json');assert review['plan_sha256']==pin and set(review['approved'])=={x['sha256'] for x in images}
 bucket=d.d.storage.Client(project='artline-508319',credentials=d.d.core.GcloudCredentials()).bucket(d.d.core.BUCKET)
 receipts=[]
 for im in images:
  raw=Path(im['visual_path']).read_bytes();assert r.sha(raw)==im['sha256'];blob=bucket.blob(im['path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],'operation':b.OP,'artwork-id':im['artwork_id']};blob.cache_control='public,max-age=31536000,immutable'
  try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
  except d.d.PreconditionFailed:blob.reload(timeout=30)
  assert blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
  response=d.requests.get('https://artlines.org'+im['path'],timeout=60);response.raise_for_status();assert r.sha(response.content)==im['sha256']
  receipts.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],generation=blob.generation,public_bytes_verified=True))
 r.save(RUN/'uploads.json',receipts);print('Uploaded native images',len(receipts),flush=True)

def apply():
 plan=r.load(RUN/'plan.json.gz');pin=r.sha((RUN/'plan.json.gz').read_bytes());images={x['artwork_id']:x for x in r.load(RUN/'images.json')};assert len(r.load(RUN/'uploads.json'))==len(images);assert r.load(b.BACKUP/'cloud-backup.json')['status']=='SUCCESSFUL'
 ids=[x['id'] for x in plan['rows']];marker=uid('applied');source=uid('source')
 with r.connect('production',readonly=False) as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='30s'");db.execute('SELECT pg_advisory_xact_lock(2026100607)')
  prev=db.execute('SELECT after_json FROM audit_log WHERE id=%s',(marker,)).fetchone()
  if prev:assert prev['after_json']['plan_sha256']==pin;print('Already applied');return
  assert not b.s.snapshots(db,ids)
  assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",([x['url'] for x in plan['rows']],)).fetchall()
  db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page','https://www.nationalgallery.gr/')",(source,b.OP+'-native','Vyzantios official museum object research, 10 October 2026'))
  db.execute('SELECT id FROM curated_collections WHERE id=%s FOR UPDATE',(b.m.COLLECTION,));pos=db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s',(b.m.COLLECTION,)).fetchone()['n']
  for x in plan['rows']:
   date=str(x['year_start']) if x['year_start']==x['year_end'] and x['year_start'] else f"{x['year_start']}–{x['year_end']}" if x['year_start'] else 'Unknown date';precision='unknown' if not x['year_start'] else 'exact' if x['year_start']==x['year_end'] else 'range'
   db.execute("INSERT INTO artworks(id,slug,title,alternate_title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)",(x['id'],x['slug'],x['title'],x.get('alternate_title'),b.q.norm(x['title']),date,x['year_start'],x['year_end'],precision,x['work_type'],x['medium'],x['dimensions'],x['accession'],ACTOR,ACTOR))
   db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",(x['id'],AID,x['identity_basis']))
   db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,'official-object-url',%s,%s,%s,%s)",(x['id'],x['url'],x['url'],source,x['evidence']['receipt']['retrieved_at']))
   note=json.dumps(dict(plan_sha256=pin,object=x,date_policy='Unknown dates remain explicit and unvalidated; no current-display claim.'),ensure_ascii=False)
   db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,%s,'native_object_identity',%s,%s,%s,%s,%s)",(uid('citation/'+x['id']),x['id'],source,x['accession'] or x['url'],x['url'],note,x['evidence']['receipt']['retrieved_at'],ACTOR))
   if x['institution_id']:
    db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(uid('holding/'+x['id']),x['id'],x['institution_id'],source,x['url'],x['identity_basis'],x['evidence']['receipt']['retrieved_at']))
   else:
    pos+=1;assert pos<=100000;db.execute('INSERT INTO curated_collection_items(id,collection_id,artwork_id,position,reason,source_id,source_url,checked_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(uid('selection/'+x['id']),b.m.COLLECTION,x['id'],pos,'User-requested Vyzantios research selection; official museum identity retained pending institution authority reconciliation.',source,x['url'],x['evidence']['receipt']['retrieved_at']))
   if x['id'] in images:
    im=images[x['id']];attribution='Periklis Vyzantios; '+x['provider']+'. '+x['rights_label']+'. Full source frame, proportional JPEG derivative. '+x['url']
    db.execute("INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at) VALUES(%s,'local',%s,%s,%s,'image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(im['media_id'],im['path'],x['url'],x['provider'],im['width'],im['height'],im['bytes'],im['sha256'],x['title']+' — Periklis Vyzantios',x['rights_status'],x['rights_label'],x['license_url'],'Periklis Vyzantios; '+x['provider'],attribution,r.now()))
    db.execute('INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(im['media_id'],source,x['accession'] or x['url'],x['evidence']['receipt']['sha256'],im['source_image_url'],x['license_url'],plan['museum_image_policy'],b.OP+'-native-v1',r.now(),Jsonb(dict(object=x,image=im,plan_sha256=pin))))
    db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,'Complete source reproduction')",(x['id'],im['media_id']))
    db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now() WHERE id=%s',(im['media_id'],x['id']))
  db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(b.m.COLLECTION,))
  after=b.s.snapshots(db,ids);assert len(after)==7
  for x in after.values():assert x['artwork']['status']=='review' and x['artwork']['published_at'] is None
  result=dict(at=r.now(),plan_sha256=pin,new_artworks=7,images=len(images),ids=ids,local_database_connected=False)
  db.execute("INSERT INTO audit_log(id,actor_user_id,action,entity_type,entity_id,after_json) VALUES(%s,%s,'vyzantios_native_additions','artist',%s,%s)",(marker,ACTOR,AID,Jsonb(result)))
  r.save_gz(BACKUP/'after.json.gz',after)
 r.save(RUN/'applied.json',result);print(result,flush=True)

def verify():
 result=r.load(RUN/'applied.json')
 with r.connect('production') as db:
  actual=b.s.snapshots(db,result['ids']);assert actual==r.load(BACKUP/'after.json.gz')
  assert all(x['ok'] for x in db.execute('SELECT artline_has_selection_evidence(id) ok FROM artworks WHERE id=ANY(%s::uuid[])',(result['ids'],)))
 r.save(RUN/'verification.json',dict(at=r.now(),records=7,images=2,errors=[]));print('Verified seven native works and two image attachments')

def link_rhodes():
 path=b.RUN/'rhodes-creator-link-plan.json';plan=r.load(path);pin=r.sha(path.read_bytes());ids=list(plan['before']);assert len(ids)==1
 aid=ids[0];marker=uid('rhodes-creator-link');citation=plan['citations'][0]['c'];assert plan['artist_id']==AID
 assert r.load(b.BACKUP/'cloud-backup.json')['status']=='SUCCESSFUL'
 r.save_gz(BACKUP/'rhodes-before.json.gz',plan)
 with r.connect('production',readonly=False) as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='120s'");db.execute('SELECT pg_advisory_xact_lock(2026100607)')
  previous=db.execute('SELECT after_json FROM audit_log WHERE id=%s',(marker,)).fetchone()
  if previous:
   assert previous['after_json']['plan_sha256']==pin
   result=previous['after_json']
  else:
   db.execute('SELECT id FROM artworks WHERE id=%s FOR UPDATE',(aid,))
   before=b.s.snapshots(db,ids);assert before==plan['before'] and not before[aid]['creators']
   db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",(aid,AID,plan['basis']))
   db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,%s,'creator_identity',%s,%s,%s,%s,%s)",(uid('rhodes-creator-citation'),aid,citation['source_id'],citation['source_record_id'],citation['source_url'],json.dumps(dict(basis=plan['basis'],original_label=before[aid]['artwork']['unlinked_creator_label'],plan_sha256=pin),ensure_ascii=False),citation['retrieved_at'],ACTOR))
   after=b.s.snapshots(db,ids);assert after[aid]['artwork']==before[aid]['artwork'] and after[aid]['locations']==before[aid]['locations'] and after[aid]['attachments']==before[aid]['attachments']
   assert len(after[aid]['creators'])==1 and after[aid]['creators'][0]['artist_id']==AID
   result=dict(at=r.now(),plan_sha256=pin,artwork_id=aid,artist_id=AID,linked=1,artwork_metadata_preserved=True)
   db.execute("INSERT INTO audit_log(id,actor_user_id,action,entity_type,entity_id,before_json,after_json) VALUES(%s,%s,'vyzantios_creator_link','artwork',%s,%s,%s)",(marker,ACTOR,aid,Jsonb(before),Jsonb(result)))
   r.save_gz(BACKUP/'rhodes-after.json.gz',after)
 with r.connect('production') as db:
  assert b.s.snapshots(db,ids)==r.load(BACKUP/'rhodes-after.json.gz')
 r.save(b.RUN/'rhodes-creator-link-applied.json',result);print(result,flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
