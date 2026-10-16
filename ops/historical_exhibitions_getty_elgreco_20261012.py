#!/usr/bin/env python3
"""Selected Getty drawing and five verified historical exhibition connections."""
import sys,json,importlib.util,base64,hashlib
from pathlib import Path
import requests
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed
from psycopg.types.json import Jsonb
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
OP='historical-exhibitions-getty-elgreco-20261012';OUT=c.DATA/'getty-elgreco-release';BACKUP=n.BACKUP.parent/'getty-elgreco'
AID=c.uid('artwork/getty/82.GA.166');MID=c.uid(OP+'/image');SID=c.uid(OP+'/source');ARTIST='1e0af779-3de1-4811-adab-6e7dcaaabf29';IID='62fb1e52-07ff-50bd-8eeb-95ea5bf4af1c';ACTOR='local-european-research'
URL='https://www.getty.edu/art/collection/object/103QV5'
def conflicts(db):
 return n.normal(db.execute("SELECT a.id,a.title FROM artworks a WHERE a.accession_number='82.GA.166' OR a.id IN (SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=%s)",(URL,)).fetchall())
def plan():
 lead=c.load(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-elgreco-reviewed-leads.json');image=c.load(c.DATA/'getty-elgreco-image/reviewed.json');obj=c.load(c.DATA/'getty-elgreco-object.json');manifest=c.load(c.DATA/'getty-elgreco-manifest.json')
 assert manifest['data']['rights'].endswith('/zero/1.0/')
 assert obj['data']['produced_by']['timespan']['identified_by'][0]['content']=='about 1600'
 assert c.sha(Path(image['path']).read_bytes())==image['derivativeSHA256']
 with c.connect()as db:
  assert not conflicts(db)
  assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
  artist=n.normal(db.execute('SELECT id,display_name,birth_year,death_year,revision FROM artists WHERE id=%s',(ARTIST,)).fetchone());institution=n.normal(db.execute('SELECT id,name,status FROM institutions WHERE id=%s',(IID,)).fetchone())
  nearby=n.normal(db.execute("SELECT e.id,e.title,e.start_year,(SELECT jsonb_agg(o) FROM exhibition_occurrences o WHERE o.exhibition_id=e.id) venues FROM exhibitions e WHERE e.status<>'archived' AND e.start_year=ANY(%s) AND (e.normalized_title LIKE '%%greco%%' OR e.normalized_title LIKE '%%greek%%' OR e.normalized_title LIKE '%%drawing%%')",([1929,1937,1946,1953,1955],)).fetchall())
  assert not any(c.norm(x['title'])==c.norm(e['title'])for x in nearby for e in lead['events'])
  before=db.execute("SELECT count(*)n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
 events=[]
 for e in lead['events']:
  key=str(e['year']);events.append(e|dict(id=c.uid(OP+'/'+key),oid=c.uid(OP+'/venue/'+key),sid=c.uid(OP+'/source/'+key),entryID=c.uid(OP+'/entry/'+key)))
 result=dict(at=c.now(),lead=lead,image=image,object=obj,manifest=manifest,events=events,artist=artist,institution=institution,nearby=nearby,before=before,imagePath='/assets/artworks/imported/'+OP+'/'+image['derivativeSHA256'][:16]+'.jpg',counts=dict(newExhibitions=5,newArtworks=1,newImages=1,illustratedConnections=5,newArtistParticipants=5))
 c.save(OUT/'plan.json.gz',result);c.save(BACKUP/'preimage.json.gz',result);print(result['counts'])
def upload():
 p=c.load(OUT/'plan.json.gz');im=p['image'];raw=Path(im['path']).read_bytes();assert c.sha(raw)==im['derivativeSHA256'] and len(raw)<=100000
 spec=importlib.util.spec_from_file_location('getty_image_core',Path(__file__).with_name('enrich-artwork-images.py'));core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
 credentials=core.GcloudCredentials();credentials.refresh(None);blob=storage.Client(project='artline-508319',credentials=credentials).bucket('artline-508319-images').blob(p['imagePath'].lstrip('/'))
 blob.metadata=dict(sha256=im['derivativeSHA256'],operation=OP);blob.cache_control='public,max-age=31536000,immutable'
 try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=45)
 except PreconditionFailed:blob.reload(timeout=30)
 assert blob.size==len(raw)and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
 r=requests.get('https://artlines.org'+p['imagePath'],timeout=45);r.raise_for_status();assert c.sha(r.content)==im['derivativeSHA256']
 c.save(OUT/'uploaded.json',dict(at=c.now(),sha256=im['derivativeSHA256'],generation=blob.generation));print('Image uploaded and public bytes verified')
def apply():
 p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz');im=p['image'];assert c.load(OUT/'uploaded.json')['sha256']==im['derivativeSHA256'];lead=p['lead']
 evidence=dict(operation=OP,originalCatalogue=lead,objectReceipt=p['object']['receipt'],identity='Exact Getty accession82.GA.166 and original catalogue145; image visually verified.',currentDisplayClaim=False,checklistComplete=False)
 with c.connect(write=True)as db:
  db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
  assert not conflicts(db)
  assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
  assert n.normal(db.execute('SELECT id,display_name,birth_year,death_year,revision FROM artists WHERE id=%s',(ARTIST,)).fetchone())==p['artist']
  assert n.normal(db.execute('SELECT id,name,status FROM institutions WHERE id=%s',(IID,)).fetchone())==p['institution']
  db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,'Getty — exact historical exhibition drawing evidence','collection_page','https://www.getty.edu')",(SID,OP))
  db.execute("INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,created_by,updated_by) VALUES(%s,%s,%s,%s,'about 1600',1600,1600,'circa','drawing',%s,'33.7 × 21 cm','82.GA.166','review',true,%s,%s)",(AID,'getty-saint-john-evangelist-and-angel-82-ga-166',lead['title'],c.norm(lead['title']),lead['medium'],ACTOR,ACTOR))
  db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary','Explicit Getty creator attribution and original catalogue145.')",(AID,ARTIST))
  db.execute("INSERT INTO external_identifiers(id,entity_type,entity_id,scheme,external_id,canonical_url,source_id) VALUES(%s,'artwork',%s,'getty-object','103QV5',%s,%s)",(c.uid(OP+'/identifier'),AID,URL,SID))
  db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,%s,'historical_exhibition_object_identity','82.GA.166',%s,%s,%s,%s)",(c.uid(OP+'/citation'),AID,SID,URL,json.dumps(p,ensure_ascii=False),p['at'],ACTOR))
  db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(c.uid(OP+'/holding'),AID,IID,SID,URL,json.dumps(evidence),p['at']))
  db.execute("INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by) VALUES(%s,'local',%s,%s,'J. Paul Getty Museum','image/jpeg',%s,%s,%s,%s,%s,'public_domain','CC0 1.0',%s,%s,%s,%s,now(),%s)",(MID,p['imagePath'],URL,*im['derivativeSize'],im['bytes'],im['derivativeSHA256'],lead['title']+' — El Greco, about 1600',im['rights'].replace('http://','https://'),im['credit'],im['credit']+'; full-frame reproduction, resized and compressed.',im['source']['retrieved_at'],ACTOR))
  db.execute("INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES(%s,%s,'82.GA.166',%s,%s,%s,'Official Getty object IIIF manifest explicitly identifies main image as CC0.',%s,now(),%s)",(MID,SID,p['manifest']['receipt']['sha256'],im['source']['url'],im['rights'].replace('http://','https://'),OP,Jsonb(dict(manifest=p['manifest'],image=im))))
  db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,'Full drawing reproduction')",(AID,MID));db.execute('UPDATE artworks SET primary_media_id=%s WHERE id=%s',(MID,AID))
  for e in p['events']:
   db.execute("INSERT INTO exhibitions(id,title,normalized_title,start_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch) VALUES(%s,%s,%s,%s,%s,'year','held','Getty1988 catalogue145 explicit object exhibition history.','physical','partial','review',%s)",(e['id'],e['title'],c.norm(e['title']),e['year'],str(e['year']),OP))
   rc=lead['source'];db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['sid'],e['id'],OP,str(e['year']),rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(e),Jsonb(evidence)))
   country={'London':('United Kingdom','GB'),'Paris':('France','FR'),'Bordeaux':('France','FR'),'New York':('United States','US')}[e['city']]
   db.execute('INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,venue_label,city_label,country_label,country_code,date_display,evidence) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(e['oid'],e['id'],e['sid'],e['venue'],e['city'],*country,str(e['year']),Jsonb(evidence)))
   db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,'getty/82.GA.166',%s,%s,'El Greco','about 1600',%s,'exhibited',%s,'Exact Getty accession82.GA.166; original catalogue145 exhibition history.')",(e['entryID'],e['id'],e['sid'],e['oid'],AID,e['catalogueNumber'],lead['title'],lead['medium'],Jsonb(evidence)))
   db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) VALUES(%s,%s,%s,%s,'El Greco','artist',%s)",(c.uid(OP+'/artist/'+str(e['year'])),e['id'],e['sid'],ARTIST,Jsonb(evidence)))
  row=db.execute('SELECT status,current_institution_id,artline_has_selection_evidence(id) eligible FROM artworks WHERE id=%s',(AID,)).fetchone();assert row['status']=='review'and str(row['current_institution_id'])==IID and row['eligible']
 c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts']));print('Committed',p['counts'])
def verify():
 p=c.load(OUT/'plan.json.gz');events=[]
 for e in p['events']:
  url='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+e['id'];r=requests.get(url,timeout=40);r.raise_for_status();d=r.json();assert d['startYear']==e['year']and any(x['artist_id']==ARTIST for x in d['participants'])
  r=requests.get(url+'/entries',timeout=40);r.raise_for_status();items=r.json()['items'];assert len(items)==1 and items[0]['artworkId']==AID and items[0].get('image');events.append(dict(id=e['id'],title=e['title'],illustrated=True))
 r=requests.get('https://artlines.org'+p['imagePath'],timeout=40);r.raise_for_status();assert c.sha(r.content)==p['image']['derivativeSHA256']
 with c.connect()as db:
  totals=n.normal(db.execute("SELECT count(*)active,count(*)FILTER(WHERE event_state='held')held,count(*)FILTER(WHERE start_year IS NULL)undated FROM exhibitions WHERE status<>'archived'").fetchone());assert totals['active']>=p['before']+5
 result=dict(at=c.now(),counts=p['counts'],artworkID=AID,events=events,totals=totals,APIImagesVerified=True,publicImageChecksumVerified=True,realLocalWrites=False)
 c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-elgreco-delivery.json',result);print(json.dumps(result))
if __name__=='__main__':assert len(sys.argv)==2 and sys.argv[1]in ['plan','upload','apply','verify'];globals()[sys.argv[1]]()
