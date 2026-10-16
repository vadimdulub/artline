#!/usr/bin/env python3
"""One selected Getty Poussin historical exhibition painting with its specific image rights label."""
import sys,json,re,importlib.util,base64,hashlib
from pathlib import Path
import requests
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed
from psycopg.types.json import Jsonb
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
from historical_exhibitions_getty_checklist_expansion_20261012 import DEST as RESEARCH
OP='historical-exhibitions-getty-poussin-work-20261012';OUT=RESEARCH/'poussin-release';BACKUP=n.BACKUP.parent/'getty-poussin-work';SID=c.uid(OP+'/source');IID='62fb1e52-07ff-50bd-8eeb-95ea5bf4af1c';ACTOR='local-european-research'
def conflicts(db,records):
 return n.normal(db.execute("SELECT id,title,accession_number FROM artworks WHERE (accession_number=ANY(%s) AND current_institution_id='62fb1e52-07ff-50bd-8eeb-95ea5bf4af1c') OR id IN(SELECT entity_id FROM external_identifiers WHERE canonical_url=ANY(%s))",([r['accession']for r in records],[r['url']for r in records])).fetchall())
def plan():
 scope=c.load(RESEARCH/'scope-review.json.gz');images=c.load(RESEARCH/'images/poussin-reviewed.json');audit=c.load(RESEARCH/'matching-review.json.gz');records=[]
 existing={x['accession_number']for x in scope['existingExactAccessionMatches']}
 for o in scope['eligibleObjects']:
  if o['accession']!='81.PA.43':continue
  key=o['id'].rsplit('/',1)[-1];src=c.load(RESEARCH/'objects'/(key+'.json'));d=src['data'];im=next(i for i in images['images']if i['objectID']==o['id']);assert im['visualReview'].startswith('Passed')
  candidates=next(x for x in audit['objects']if x['objectID']==o['id']);title=next(x['content']for x in d['identified_by']if x.get('_label')=='Preferred Title');url=next(x['id']for x in d['subject_of']if '/art/collection/object/'in x['id']);date='; '.join(o['dateLabel']);years=[int(y)for y in re.findall(r'\b\d{4}(?=\b|s\b)',date)];assert len(years)in [1,2]and max(years)<=1970
  if re.fullmatch(r'\d{4}s',date):years=[int(date[:4]),int(date[:4])+9]
  precision=('circa_range'if len(years)==2 else'circa')if date.startswith('about ')else('range'if len(years)==2 else'exact')
  medium=next(x['content']for x in d['referred_to_by']if x.get('_label')=='Materials Description');dims=[x['content']for x in d['referred_to_by']if x.get('_label')=='Dimensions Statement'];creator='; '.join(candidates['creatorLabels']);assert creator
  artist=candidates['creatorCandidates'][0]['id']if candidates['creatorState']=='single-name-candidate'else None
  kind='drawing'if 'Drawings'in o['types']else'painting';assert kind=='drawing'or 'Paintings'in o['types']
  records.append(dict(id=c.uid('artwork/getty/'+o['accession']),mid=c.uid(OP+'/media/'+key),slug='getty-'+kind+'-'+o['accession'].lower().replace('.','-'),objectID=o['id'],key=key,accession=o['accession'],title=title,url=url,date=date,first=min(years),last=max(years),precision=precision,medium=medium,dimensions='; '.join(dims)or None,creator=creator,artistID=artist,workType=kind,source=src,image=im,imagePath='/assets/artworks/imported/'+OP+'/'+im['sha256'][:16]+'.jpg',candidateAudit=candidates))
 assert len(records)==1
 with c.connect()as db:
  assert not conflicts(db,records);assert not db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone()
  artists=n.normal(db.execute('SELECT id,display_name,birth_year,death_year,revision FROM artists WHERE id=ANY(%s::uuid[])',([r['artistID']for r in records if r['artistID']],)).fetchall());institution=n.normal(db.execute('SELECT id,name,status FROM institutions WHERE id=%s',(IID,)).fetchone())
  candidateIDs=list({x['id']for r in records for x in r['candidateAudit']['artworkCandidates']});before=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(candidateIDs,)).fetchall())
 result=dict(at=c.now(),records=records,artists=artists,institution=institution,candidatesBefore=before,counts=dict(newArtworks=len(records),newImages=len(records),newPrimaryArtistLinks=sum(bool(r['artistID'])for r in records),newHoldings=len(records)),review='Exact Getty 81.PA.43 native painting with reciprocal pre-1990 exhibition history. Eight internal/WikiArt candidate reproductions inspected and found different compositions; other candidates are distinct subjects or drawings. Getty full-frame source image visually reviewed. Preserve its canvas-specific No Copyright - United States label and conflicting manifest-level CC0 as evidence, not a CC0 image claim. User-authorized selected historical image workflow. No current display claim.')
 c.save(OUT/'plan.json.gz',result);c.save(BACKUP/'preimage.json.gz',result);print(result['counts'])
def upload():
 p=c.load(OUT/'plan.json.gz');spec=importlib.util.spec_from_file_location('getty_ten_image_core',Path(__file__).with_name('enrich-artwork-images.py'));core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core);creds=core.GcloudCredentials();creds.refresh(None);bucket=storage.Client(project='artline-508319',credentials=creds).bucket('artline-508319-images');rows=[]
 for r in p['records']:
  im=r['image'];raw=Path(im['path']).read_bytes();assert c.sha(raw)==im['sha256']and len(raw)<=100000;blob=bucket.blob(r['imagePath'].lstrip('/'));blob.metadata=dict(sha256=im['sha256'],operation=OP);blob.cache_control='public,max-age=31536000,immutable'
  try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=45)
  except PreconditionFailed:blob.reload(timeout=30)
  assert blob.size==len(raw)and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode();response=requests.get('https://artlines.org'+r['imagePath'],timeout=40);response.raise_for_status();assert c.sha(response.content)==im['sha256'];rows.append(dict(id=r['id'],sha256=im['sha256'],generation=blob.generation));print('Uploaded',r['accession'],flush=True)
 c.save(OUT/'uploaded.json',dict(at=c.now(),images=rows))
def apply():
 p=c.load(OUT/'plan.json.gz');assert p==c.load(BACKUP/'preimage.json.gz');assert len(c.load(OUT/'uploaded.json')['images'])==len(p['records'])
 with c.connect(write=True)as db:
  db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)');assert not conflicts(db,p['records']);assert not db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone()
  for a in p['artists']:assert n.normal(db.execute('SELECT id,display_name,birth_year,death_year,revision FROM artists WHERE id=%s',(a['id'],)).fetchone())==a
  for a in p['candidatesBefore']:assert n.normal(db.execute('SELECT * FROM artworks WHERE id=%s',(a['id'],)).fetchone())==a
  assert n.normal(db.execute('SELECT id,name,status FROM institutions WHERE id=%s',(IID,)).fetchone())==p['institution']
  db.execute("INSERT INTO sources(id,slug,name,source_type,base_url)VALUES(%s,%s,'Getty selected historical exhibition paintings and drawings','collection_page','https://www.getty.edu')",(SID,OP))
  for r in p['records']:
   im=r['image'];rc=r['source']['receipt'];ev=dict(operation=OP,sourceReceipt=rc,sourceObject=r['source']['data'],basis=p['review'],creator=r['creator'],currentDisplayClaim=False);note=json.dumps(ev,ensure_ascii=False)
   db.execute("INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,created_by,updated_by)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s)",(r['id'],r['slug'],r['title'],c.norm(r['title']),r['date'],r['first'],r['last'],r['precision'],r['workType'],r['medium'],r['dimensions'],r['accession'],None if r['artistID']else r['creator'],ACTOR,ACTOR))
   if r['artistID']:db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note)VALUES(%s,%s,'primary',%s)",(r['id'],r['artistID'],'Getty creator: '+r['creator']))
   db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)VALUES('artwork',%s,'getty-object',%s,%s,%s,%s)",(r['id'],r['url'].rsplit('/',1)[-1],r['url'],SID,rc['retrieved_at']))
   db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)VALUES('artwork',%s,'historical_exhibition_native_artwork',%s,%s,%s,%s,%s,%s)",(r['id'],SID,r['accession'],r['url'],note,rc['retrieved_at'],ACTOR))
   db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(r['id'],IID,SID,r['url'],note,rc['retrieved_at']))
   db.execute("INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)VALUES(%s,'local',%s,%s,'J. Paul Getty Museum','image/jpeg',%s,%s,%s,%s,%s,'public_domain','No Copyright - United States','https://rightsstatements.org/vocab/NoC-US/1.0/','The J. Paul Getty Museum, Los Angeles','The J. Paul Getty Museum, Los Angeles; full-frame primary reproduction resized and compressed.',%s,now(),%s)",(r['mid'],r['imagePath'],r['url'],*im['derivativeSize'],im['bytes'],im['sha256'],r['title']+' — '+r['creator'],im['imageReceipt']['retrieved_at'],ACTOR))
   db.execute("INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)VALUES(%s,%s,%s,%s,%s,'https://rightsstatements.org/vocab/NoC-US/1.0/','Official Getty canvas-specific No Copyright - United States statement; source label retained under selected historical image authorization.',%s,now(),%s)",(r['mid'],SID,r['accession'],im['manifestReceipt']['sha256'],im['imageReceipt']['url'],OP,Jsonb(im)))
   db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label)VALUES(%s,%s,0,'Primary full-frame artwork view')",(r['id'],r['mid']));db.execute('UPDATE artworks SET primary_media_id=%s WHERE id=%s',(r['mid'],r['id']))
 c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts']));print('Committed',p['counts'])
def verify():
 p=c.load(OUT/'plan.json.gz');ids=[r['id']for r in p['records']]
 with c.connect()as db:
  rows=n.normal(db.execute('SELECT a.*,artline_has_selection_evidence(a.id)eligible FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,)).fetchall());assert len(rows)==len(p['records'])
  for r in p['records']:
   a=next(x for x in rows if x['id']==r['id']);assert a['primary_media_id']==r['mid']and a['current_institution_id']==IID and a['status']=='review'and a['eligible'];assert a['date_precision']==r['precision']and a['creation_year_start']==r['first']and a['creation_year_end']==r['last']
  assert db.execute('SELECT count(*)n FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==p['counts']['newPrimaryArtistLinks']
 for r in p['records']:
  response=requests.get('https://artlines.org'+r['imagePath'],timeout=40);response.raise_for_status();assert c.sha(response.content)==r['image']['sha256']
 result=dict(at=c.now(),counts=p['counts'],artworks=[dict(id=r['id'],accession=r['accession'],title=r['title'])for r in p['records']],publicImageChecksumsVerified=len(p['records']),sourceDatePrecisionVerified=True,realLocalWrites=False,exhibitionConnectionsPending=True)
 c.save(OUT/'verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-poussin-work-delivery.json',result);print(json.dumps(result))
if __name__=='__main__':assert sys.argv[1]in ['plan','upload','apply','verify'];globals()[sys.argv[1]]()
