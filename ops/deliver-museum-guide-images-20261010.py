"""Deliver the 20 source-backed MuMa images reviewed for the museum guides.

Production only. No local catalogue writes. Preserves artwork fields and statuses.
Run stages separately: plan, upload, apply, verify. Recovery is under Library.
"""
import base64,concurrent.futures,datetime,gzip,hashlib,json,subprocess,sys,uuid
from pathlib import Path
import psycopg,requests
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from google.auth.credentials import Credentials
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/museum-guides-editorial-20261010';BACKUP=Path.home()/'Library/Application Support/Artline/backups/museum-guides-20261010';BACKUP.mkdir(parents=True,exist_ok=True)
OP='museum-guides-muma-images-20261010';ACTOR='local-european-research'
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+s))
def sha(b):return hashlib.sha256(b).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n')
def connect(write=False):
 raw=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319'],text=True).strip();f=psycopg.conninfo.conninfo_to_dict(raw);f.update(host='127.0.0.1',port='55448',sslmode='disable')
 return psycopg.connect(**f,options='-c default_transaction_read_only='+('off'if write else'on')+' -c statement_timeout=30000',row_factory=dict_row)
def snapshots(d,ids):
 return {x['artwork']['id']:x for x in d.execute("SELECT to_jsonb(a) artwork,coalesce((SELECT jsonb_agg(to_jsonb(aa) ORDER BY artist_id,attribution_role) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') creators,coalesce((SELECT jsonb_agg(to_jsonb(am) ORDER BY media_id) FROM artwork_media am WHERE am.artwork_id=a.id),'[]') attachments FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id",(ids,)).fetchall()}
def plan():
 ws=json.loads((RUN/'muma-image-selection.json').read_text());assert len(ws)==20 and len({w['id']for w in ws})==20
 for w in ws:
  m=w['media'];raw=(ROOT/'apps/web/public'/m['storage_path'].lstrip('/')).read_bytes();assert sha(raw)==m['checksum_sha256'] and len(raw)==m['byte_size']<=100000
  assert m['license_label']in ['Public domain','CC BY-SA 2.0','CC BY-SA 4.0'];assert (w['creation_year_end'] is not None and w['creation_year_end']<=1970) or (w['selectionIndex']==1 and w['date_display']=='ca. 1884-1886 / 1890 / 1900')
  m['id']=uid('media/'+m['checksum_sha256'])
 with connect()as d:
  before=snapshots(d,[w['id']for w in ws]);assert len(before)==20
  assert d.execute('SELECT 1 FROM editor_accounts WHERE user_id=%s',(ACTOR,)).fetchone()
  for w in ws:
   a=before[w['id']]['artwork'];assert a['primary_media_id']is None and a['status']!='archived'
   for k in ['title','creation_year_start','creation_year_end','date_display','accession_number']:assert a[k]==w[k],(w['id'],k)
   assert d.execute("SELECT 1 FROM institutions WHERE id=%s AND slug='muma-le-havre'",(a['current_institution_id'],)).fetchone()
 result={'at':now(),'source_id':uid('source'),'works':ws,'before':before,'review':{'confidence':0.96,'basis':'Editorial assessment, not calibrated probability. Matched museum, creator, exact work title and date/version; all 20 reproductions visually inspected against object evidence. Source photographs retained without cropping. Commons CC BY-SA/public-domain labels preserved; independent visitor photographs are not museum-supplied commercial photographs.'}}
 save(BACKUP/'plan.json',result);save(RUN/'image-plan-pin.json',{'sha256':sha((BACKUP/'plan.json').read_bytes()),'count':20,'at':now()});print('Pinned 20 reviewed images')
def pinned():
 raw=(BACKUP/'plan.json').read_bytes();assert sha(raw)==json.loads((RUN/'image-plan-pin.json').read_text())['sha256'];return json.loads(raw)
class GcloudCredentials(Credentials):
 def refresh(self,request):
  self.token=subprocess.check_output(['gcloud','auth','print-access-token'],text=True).strip();self.expiry=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)+datetime.timedelta(minutes=45)
def upload():
 p=pinned();bucket=storage.Client(project='artline-508319',credentials=GcloudCredentials()).bucket('artline-508319-images')
 def one(w):
  m=w['media'];raw=(ROOT/'apps/web/public'/m['storage_path'].lstrip('/')).read_bytes();assert sha(raw)==m['checksum_sha256'];b=bucket.blob(m['storage_path'].lstrip('/'));b.cache_control='public,max-age=31536000,immutable';b.metadata={'sha256':sha(raw),'artwork-id':w['id'],'operation':OP,'provider':'Wikimedia Commons'}
  try:b.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
  except PreconditionFailed:b.reload()
  assert b.size==len(raw) and b.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
  r=requests.get('https://artlines.org'+m['storage_path'],timeout=40);r.raise_for_status();assert sha(r.content)==sha(raw)
  return {'id':w['id'],'generation':str(b.generation),'sha256':sha(raw),'publicVerified':True}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as ex:rows=list(ex.map(one,p['works']))
 save(RUN/'image-uploads.json',{'at':now(),'items':rows});print('Uploaded and publicly verified',len(rows))
def apply():
 p=pinned();ids=[w['id']for w in p['works']];assert len(json.loads((RUN/'image-uploads.json').read_text())['items'])==20
 backups=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--filter=description='+OP,'--limit=1','--format=json'],text=True));assert backups and backups[0]['status']=='SUCCESSFUL';save(BACKUP/'cloud-sql-backup.json',backups[0])
 with connect(True)as d,d.transaction():
  d.execute("SET LOCAL lock_timeout='5s'");d.execute('SELECT pg_advisory_xact_lock(202610105)');d.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall();assert snapshots(d,ids)==p['before'],'Production changed since preflight'
  d.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page','https://commons.wikimedia.org/')",(p['source_id'],OP,'MuMa independently licensed images for Artline museum guides, 10 October 2026'))
  for w in p['works']:
   m=w['media'];page=w['guideImageEvidence'];info=page['imageinfo'][0];imageurl=info.get('thumburl',info['url']);policy=m['license_url']or m['source_page_url'];record=str(page['pageid'])
   d.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by) VALUES(%s,'local',%s,%s,'Wikimedia Commons','image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),%s)''',(m['id'],m['storage_path'],m['source_page_url'],m['width'],m['height'],m['byte_size'],m['checksum_sha256'],w['title'],m['rights_status'],m['license_label'],policy,m['creator_credit'],m['attribution_text'],ACTOR))
   d.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,now(),%s)''',(m['id'],p['source_id'],record,sha(json.dumps(page,sort_keys=True,ensure_ascii=False).encode()),imageurl,policy,'Commons per-file rights label and independent photograph/source evidence; preserved attribution, licence and proportional compression notice. No current display claim.',OP,Jsonb({'commons':page,'holding_sources':w['holdings'],'review':p['review'],'derivative':m})))
   d.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,'Full source photograph')",(w['id'],m['id']))
   cur=d.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(m['id'],ACTOR,w['id']));assert cur.rowcount==1
   d.execute("INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,'image_identity',%s,%s,%s,%s,now(),%s)",(uid('citation/'+w['id']),w['id'],p['source_id'],record,m['source_page_url'],json.dumps({'operation':OP,'review':p['review'],'museum_source':w['holdings'][0]['url'],'scope':'Image attachment only; metadata, holdings and editorial status preserved.'},ensure_ascii=False),ACTOR))
  after=snapshots(d,ids);allowed={'primary_media_id','revision','updated_at','updated_by'}
  for w in p['works']:
   old=p['before'][w['id']];new=after[w['id']];assert {k:v for k,v in old['artwork'].items()if k not in allowed}=={k:v for k,v in new['artwork'].items()if k not in allowed};assert old['creators']==new['creators'];assert len(new['attachments'])==len(old['attachments'])+1
 save(BACKUP/'after.json',after);save(RUN/'images-applied.json',{'at':now(),'images':20,'backupID':backups[0]['id'],'localDatabaseChanged':False,'metadataChanged':False,'publicationChanged':False});print('Attached 20 production images; other artwork fields preserved')
def verify():
 p=pinned()
 with connect()as d:
  for w in p['works']:
   m=w['media'];row=d.execute('SELECT a.primary_media_id::text id,m.checksum_sha256 sha,a.status FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=%s',(w['id'],)).fetchone();assert row['id']==m['id'] and row['sha']==m['checksum_sha256'] and row['status']==p['before'][w['id']]['artwork']['status']
 save(RUN/'images-verified.json',{'at':now(),'verified':20,'errors':[]});print('Verified 20 production image attachments')
if __name__=='__main__':{'plan':plan,'upload':upload,'apply':apply,'verify':verify}[sys.argv[1]]()
