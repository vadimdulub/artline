#!/usr/bin/env python3
"""Reconcile Rijks loan record with exact Getty Stag Beetle; preserve audit and artwork identity."""
import sys,json,importlib.util,base64,hashlib
from pathlib import Path
import requests
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed
from psycopg.types.json import Jsonb
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
from historical_exhibitions_getty_ra1953_discovery_20261012 import OUT as RESEARCH
OP='historical-exhibitions-getty-stag-reconcile-20261012';OUT=RESEARCH/'stag-release';BACKUP=n.BACKUP.parent/'getty-stag';ACTOR='local-european-research';AID='515160f2-f13a-59a5-8a3f-7a53e72793fb';IID='62fb1e52-07ff-50bd-8eeb-95ea5bf4af1c';MID=c.uid(OP+'/image');SID=c.uid(OP+'/source');HID=c.uid(OP+'/holding');KEY='8a467f7a-c019-409c-9ee5-f41528562591'
def plan():
 obj=c.load(RESEARCH/'objects'/(KEY+'.json'));im=next(i for i in c.load(RESEARCH/'images/reviewed-batch.json')['images']if i['accession']=='83.GC.214');loan=c.load(RESEARCH/'stag-rijks-loan-evidence.json');page=c.load(RESEARCH/'stag-rijks-page.json');activity=c.load(RESEARCH/'activities/25c3a037-5eb1-548b-94fa-a5b3d13a20a9.json');assert 'Getty Museum' in loan['text']
 url=next(x['id']for x in obj['data']['subject_of']if '/art/collection/object/'in x['id'])
 with c.connect()as db:
  work=n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(AID,)).fetchone());locations=n.normal(db.execute('SELECT * FROM artwork_location_assertions WHERE artwork_id=%s',(AID,)).fetchall());ids=n.normal(db.execute("SELECT * FROM external_identifiers WHERE entity_type='artwork'AND entity_id=%s",(AID,)).fetchall());assert not work['primary_media_id']and work['accession_number']=='BC-0005016';assert len(locations)==1 and locations[0]['review_state']=='accepted'
  assert not db.execute("SELECT 1 FROM external_identifiers WHERE canonical_url=%s AND entity_id<>%s",(url,AID)).fetchone()
 p=dict(at=c.now(),work=work,locations=locations,identifiers=ids,object=obj,image=im,loan=loan,rijksPage=page,gettyLoan=activity,url=url,imagePath='/assets/artworks/imported/'+OP+'/'+im['sha256'][:16]+'.jpg',basis='Same title, creator,1505 date and14.1×11.4cm dimensions; Rijks nativeBC-0005016 explicitly lists Crawly Creatures; Rijks official exhibition credits Getty; Getty exact83.GC.214 records same Rijks loan. Existing native record represents borrowed Getty object, not separate Rijks holding.',confidence=.99)
 c.save(OUT/'plan.json.gz',p);c.save(BACKUP/'preimage.json.gz',p);print('Pinned existing work and holding; no duplicate work')
def upload():
 p=c.load(OUT/'plan.json.gz');im=p['image'];raw=Path(im['path']).read_bytes();assert c.sha(raw)==im['sha256']and len(raw)<=100000
 spec=importlib.util.spec_from_file_location('getty_stag_image_core',Path(__file__).with_name('enrich-artwork-images.py'));core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core);credentials=core.GcloudCredentials();credentials.refresh(None)
 blob=storage.Client(project='artline-508319',credentials=credentials).bucket('artline-508319-images').blob(p['imagePath'].lstrip('/'));blob.metadata=dict(sha256=im['sha256'],operation=OP);blob.cache_control='public,max-age=31536000,immutable'
 try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=45)
 except PreconditionFailed:blob.reload(timeout=30)
 assert blob.size==len(raw)and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode();r=requests.get('https://artlines.org'+p['imagePath'],timeout=40);r.raise_for_status();assert c.sha(r.content)==im['sha256']
 c.save(OUT/'uploaded.json',dict(at=c.now(),sha256=im['sha256'],generation=blob.generation));print('Uploaded image; public checksum verified')
def apply():
 p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz');im=p['image'];assert c.load(OUT/'uploaded.json')['sha256']==im['sha256'];ev=dict(operation=OP,basis=p['basis'],confidence=p['confidence'],loanReceipt=p['loan']['receipt'],gettyObjectReceipt=p['object']['receipt'],currentDisplayClaim=False)
 with c.connect(write=True)as db:
  db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
  assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s FOR UPDATE',(AID,)).fetchone())==p['work'];assert n.normal(db.execute('SELECT * FROM artwork_location_assertions WHERE artwork_id=%s',(AID,)).fetchall())==p['locations']
  db.execute("INSERT INTO sources(id,slug,name,source_type,base_url)VALUES(%s,%s,'Getty and Rijksmuseum — Stag Beetle identity and loan evidence','collection_page','https://www.getty.edu')",(SID,OP))
  db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)VALUES(%s,'artwork',%s,%s,'holding_and_image_identity','83.GC.214',%s,%s,%s,%s)",(c.uid(OP+'/citation'),AID,SID,p['url'],json.dumps(p,ensure_ascii=False),p['at'],ACTOR))
  db.execute("INSERT INTO external_identifiers(id,entity_type,entity_id,scheme,external_id,canonical_url,source_id)VALUES(%s,'artwork',%s,'getty-object',%s,%s,%s)",(c.uid(OP+'/identifier'),AID,p['url'].rsplit('/',1)[-1],p['url'],SID))
  db.execute("UPDATE artwork_location_assertions SET review_state='rejected' WHERE id=%s",(p['locations'][0]['id'],))
  db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(HID,AID,IID,SID,p['url'],json.dumps(ev),p['at']))
  db.execute("UPDATE artwork_location_assertions SET review_state='rejected',superseded_by=%s,evidence_note=evidence_note||%s WHERE id=%s",(HID,' Reconciled: this native Rijks record documents a Getty loan, not Rijks ownership. '+json.dumps(ev),p['locations'][0]['id']))
  db.execute("INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)VALUES(%s,'local',%s,%s,'J. Paul Getty Museum','image/jpeg',%s,%s,%s,%s,'Stag Beetle — Albrecht Dürer,1505','public_domain','CC0 1.0','https://creativecommons.org/publicdomain/zero/1.0/','The J. Paul Getty Museum, Los Angeles','The J. Paul Getty Museum, Los Angeles; full-frame reproduction resized and compressed.',%s,now(),%s)",(MID,p['imagePath'],p['url'],*im['derivativeSize'],im['bytes'],im['sha256'],im['imageReceipt']['retrieved_at'],ACTOR))
  db.execute("INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)VALUES(%s,%s,'83.GC.214',%s,%s,'https://creativecommons.org/publicdomain/zero/1.0/','Official Getty IIIF main-image CC0 statement.',%s,now(),%s)",(MID,SID,im['manifestReceipt']['sha256'],im['imageReceipt']['url'],OP,Jsonb(im)))
  db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label)VALUES(%s,%s,0,'Full drawing reproduction')",(AID,MID));db.execute('UPDATE artworks SET primary_media_id=%s WHERE id=%s',(MID,AID))
  after=n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(AID,)).fetchone());assert after['current_institution_id']==IID and after['primary_media_id']==MID
  for key in ['title','accession_number','creation_year_start','creation_year_end','date_precision','medium_text','status']:assert after[key]==p['work'][key]
 c.save(OUT/'delivered.json',dict(at=c.now(),artworkID=AID,newImages=1,newArtworks=0,holdingCorrected=True));print('Committed exact image and Getty holding; existing work and source accession retained')
def verify():
 p=c.load(OUT/'plan.json.gz');r=requests.get('https://artlines.org'+p['imagePath'],timeout=40);r.raise_for_status();assert c.sha(r.content)==p['image']['sha256']
 with c.connect()as db:
  w=n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(AID,)).fetchone());assert w['primary_media_id']==MID and w['current_institution_id']==IID and w['status']==p['work']['status']
  old=db.execute('SELECT review_state,superseded_by FROM artwork_location_assertions WHERE id=%s',(p['locations'][0]['id'],)).fetchone();assert old['review_state']=='rejected'and str(old['superseded_by'])==HID
 result=dict(at=c.now(),artworkID=AID,newImages=1,newArtworks=0,holdingCorrected=True,sourceAccessionPreserved=True,publicImageChecksumVerified=True,realLocalWrites=False,evidenceBasis=p['basis'])
 c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-stag-reconciliation-delivery.json',result);print(json.dumps(result))
if __name__=='__main__':assert sys.argv[1]in ['plan','upload','apply','verify'];globals()[sys.argv[1]]()
