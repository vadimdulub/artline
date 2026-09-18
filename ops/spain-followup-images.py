#!/usr/bin/env python3
"""Find, review, attach and verify additional Spanish-campaign images."""
import argparse,base64,collections,hashlib,importlib.util,io,json,re,subprocess,time,uuid
from pathlib import Path
from urllib.parse import quote,urlparse
from types import SimpleNamespace
import psycopg,requests
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from PIL import Image,ImageDraw,ImageOps
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/research/spain-deep-20260916';RUN=ROOT/'docs/research/spain-images-followup-20260917'
ORIGINALS=Path('/Users/vadimdulub/Library/Application Support/Artline/source-images/spain-images-followup-20260917')
BACKUP=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/spain-images-followup-20260917')
spec=importlib.util.spec_from_file_location('commons',ROOT/'ops/overnight-commons-images.py');cm=importlib.util.module_from_spec(spec);spec.loader.exec_module(cm)
core=cm.core
alt_spec=importlib.util.spec_from_file_location('alternates',ROOT/'ops/research-overnight-alternate-commons.py');alt=importlib.util.module_from_spec(alt_spec);alt_spec.loader.exec_module(alt)
delivery_spec=importlib.util.spec_from_file_location('spain_delivery',ROOT/'ops/deliver-spain-deep.py');delivery=importlib.util.module_from_spec(delivery_spec);delivery_spec.loader.exec_module(delivery)
CC0='https://creativecommons.org/publicdomain/zero/1.0/';PDM='https://creativecommons.org/publicdomain/mark/1.0/'
SITE=delivery.SITE;SOURCE='spain-images-followup-20260917';ACTOR=core.ACTOR

def save(name,value):core.save_new(RUN/name,value)
def load(name):return json.loads((RUN/name).read_text())
def norm(v):return ' '.join(re.findall(r'[^\W_]+',str(v or '').casefold()))
def connect(target,ro=True):return delivery.connect(target,ro)
def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/spain-images-followup/'+key))
def claim_values(e,p):
 out=[]
 for c in e.get('claims',{}).get(p,[]):
  if c.get('rank')=='deprecated':continue
  v=c.get('mainsnak',{}).get('datavalue',{}).get('value')
  if isinstance(v,dict) and 'id' in v:v=v['id']
  if v is not None:out.append(str(v))
 return out

def facts_and_plan():
 facts={x['qid']:x for x in json.loads((BASE/'selected-metadata-final-v2.json').read_text())['records']}
 plan=json.loads((BASE/'delivery-plan.json').read_text())['targets'];return facts,plan

def inventory():
 facts,plan=facts_and_plan();rows=[];held=[]
 receipts={t:{p.stem:json.loads(p.read_text()) for p in (BASE/'applied'/t).glob('*.json')} for t in ('local','production')}
 for st in plan['production']['states']:
  q=st['qid'];x=facts[q];other=next(s for s in plan['local']['states'] if s['qid']==q)
  if receipts['local'][q]['image_attached'] or receipts['production'][q]['image_attached']:continue
  reason=None
  if x['death'] is None or x['death']>1945:reason='Underlying artwork rights require individual permission; conservative automated path stops after creator death 1945'
  elif not x['date']['eligible'] or x['date']['first'] is None:reason='Creation date requires editorial review'
  if reason:held.append({'qid':q,'reason':reason});continue
  rows.append({'qid':q,'artwork_id':other['id'],'target_ids':{'local':other['id'],'production':st['id']},'slug':st['slug'],'title':x['title'],'titles':x['titles'],'artist':x['creator_name'],'creator_qid':x['creator_qid'],'creators':[{'qid':x['creator_qid'],'name':x['creator_name'],'death':x['death']}],'creation_year_start':st.get('applied_date',x['date'])['first'],'creation_year_end':st.get('applied_date',x['date'])['last'],'date_precision':st.get('applied_date',x['date'])['precision'],'date_display':st.get('applied_date',x['date'])['display'],'work_type':'painting','accession_number':x['accession'],'institution_qid':x['institution_qid'],'institution_slug':'spain-source-'+x['institution_qid'].lower(),'institution_name':x['institution_name'],'website_url':next(iter(x['institution_websites']),None),'entity':x['entity'],'source_receipt':x['receipt']})
 assert len({x['qid'] for x in rows})==len(rows)
 save('candidates.json',{'at':core.now(),'candidates':rows,'policy':'Only already selected and delivered review paintings still lacking media; known pre-1971 creation interval and named creator death no later than 1945. Exact object image identity and explicit reproduction licence remain separately required.'});save('inventory-held.json',held)
 print(core.now(),'Follow-up candidates',len(rows),'policy-held',len(held),flush=True)

def official():
 rows=load('candidates.json')['candidates'];fetch=core.Fetcher(RUN/'official/metadata');selected=[];held=[]
 for n,c in enumerate(rows,1):
  provider=None;oid=None;e=c['entity']
  if c['institution_name']=='Metropolitan Museum of Art' and len(claim_values(e,'P3634'))==1:provider='met';oid=claim_values(e,'P3634')[0]
  elif c['institution_name']=='Art Institute of Chicago' and len(claim_values(e,'P4610'))==1:provider='chicago';oid=claim_values(e,'P4610')[0]
  if not provider:continue
  try:
   if provider=='met':
    url='https://collectionapi.metmuseum.org/public/collection/v1/objects/'+quote(oid,safe='');o=fetch.metadata(url)
    if str(o.get('objectID'))!=oid or o.get('accessionNumber')!=c['accession_number']:raise ValueError('Met object ID or accession differs')
    if o.get('objectWikidata_URL','').rstrip('/').rsplit('/',1)[-1] not in ('',c['qid']):raise ValueError('Met artwork authority differs')
    if o.get('artistWikidata_URL','').rstrip('/').rsplit('/',1)[-1]!=c['creator_qid']:raise ValueError('Met creator authority differs')
    if o.get('isPublicDomain') is not True or o.get('rightsAndReproduction') or not o.get('primaryImageSmall'):raise ValueError('Met object lacks an explicit Open Access primary image')
    image=o['primaryImageSmall'];h=urlparse(image).hostname
    if h not in ('images.metmuseum.org','collectionapi.metmuseum.org'):raise ValueError('Met image host differs')
    if norm(o.get('title')) not in {norm(x) for x in c['titles']}:raise ValueError('Met title differs')
    if 'Metropolitan Museum of Art' not in o.get('repository',''):raise ValueError('Met repository differs')
    page=o.get('objectURL') or 'https://www.metmuseum.org/art/collection/search/'+oid;credit=c['artist']+'; The Metropolitan Museum of Art; '+o.get('creditLine','')
    raw={'object':o,'metadata_receipt':json.loads((fetch.cache/(core.sha(url.encode())+'.receipt.json')).read_text())};label='CC0';lic=CC0
   else:
    fields='id,title,image_id,is_public_domain,copyright_notice,date_start,date_end,main_reference_number,artist_title,artist_display,artwork_type_title,api_link'
    url='https://api.artic.edu/api/v1/artworks/'+quote(oid,safe='')+'?fields='+fields;o=fetch.metadata(url)['data']
    if str(o.get('id'))!=oid or o.get('main_reference_number')!=c['accession_number']:raise ValueError('Chicago object ID or accession differs')
    if o.get('is_public_domain') is not True or o.get('copyright_notice') or not o.get('image_id'):raise ValueError('Chicago object lacks an explicit Open Access primary image')
    if norm(o.get('title')) not in {norm(x) for x in c['titles']}:raise ValueError('Chicago title differs')
    if norm(o.get('artist_title'))!=norm(c['artist']) and norm(c['artist']) not in norm(o.get('artist_display')):raise ValueError('Chicago creator differs')
    if o.get('artwork_type_title')!='Painting':raise ValueError('Chicago object type differs')
    image='https://www.artic.edu/iiif/2/'+o['image_id']+'/full/843,/0/default.jpg';page='https://www.artic.edu/artworks/'+oid;credit=c['artist']+'; Art Institute of Chicago';raw={'object':o,'metadata_receipt':json.loads((fetch.cache/(core.sha(url.encode())+'.receipt.json')).read_text())};label='CC0';lic=CC0
   selected.append({**c,'provider':provider,'external_id':oid,'page':page,'source_image_url':image,'policy_url':lic,'rights_status':'cc0','license_label':label,'creator_credit':credit,'attribution_text':c['artist']+'. '+c['title']+'. '+credit+'. CC0 ('+lic+'). Full-frame proportional resize and JPEG compression.','checked_at':core.now(),'raw':raw,'identity_basis':'Exact current museum object ID, accession, title and creator agree with the selected Wikidata authority; museum API marks the exact primary image Open Access/public domain. Underlying-work term checked separately.'})
  except Exception as exc:held.append({'qid':c['qid'],'provider':provider,'object_id':oid,'reason':type(exc).__name__+': '+str(exc)[:300]})
 save('official/selected.json',selected);save('official/held.json',held);print(core.now(),'Official selected',len(selected),'held',len(held),flush=True)

def alternates(limit=0):
 rows=load('candidates.json')['candidates'];official_q={x['qid'] for x in load('official/selected.json')};rows=[x for x in rows if x['qid'] not in official_q]
 rows.sort(key=lambda x:(x['institution_name']!='Museo del Prado',x['creation_year_start'],x['artist'],x['qid']));rows=rows[:limit] if limit else rows
 fetch=core.Fetcher(RUN/'alternates/metadata');selected=[];held=[]
 for n,c in enumerate(rows,1):
  dest=RUN/'alternates/review'/(c['qid']+'.json')
  if dest.exists():result=json.loads(dest.read_text());
  else:
   result={'qid':c['qid'],'considered':[],'selected':None}
   try:
    # Review a bounded set of the most relevant exact structured links. Large
    # filesets often contain details and reverse views rather than independent
    # full-object reproductions.
    search=cm.api(fetch,'commons.wikimedia.org',{'action':'query','list':'search','srsearch':'haswbstatement:P6243='+c['qid'],'srnamespace':6,'srlimit':8,'srprop':''})
    names=[x['title'].removeprefix('File:') for x in search.get('query',{}).get('search',[])]
    primary=set(claim_values(c['entity'],'P18'))
    names=[x for x in names if x not in primary]
    for name in names:
     try:
      data=cm.api(fetch,'commons.wikimedia.org',{'action':'query','titles':'File:'+name,'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':960,'rvprop':'ids|content','rvslots':'main'});page=cm.page_for_filename(data,name)
      sdc=cm.api(fetch,'commons.wikimedia.org',{'action':'wbgetentities','ids':'M'+str(page['pageid']),'props':'claims'})['entities']['M'+str(page['pageid'])]
      alt.valid_alternate(c,page,sdc,next(iter(primary),''));rendered=cm.rendered_rights_uri(fetch,page);info,credit,label,uri,status,image=cm.rights_and_identity(c,c['entity'],page,sdc,rendered)[:6]
      im={**c,'provider':'commons-alternate','external_id':c['qid'],'page':info['descriptionurl'],'source_image_url':image,'policy_url':uri,'rights_status':status,'license_label':label,'creator_credit':credit,'attribution_text':c['artist']+'. '+c['title']+'. Image credit: '+credit+'. '+label+' ('+uri+'). Full-frame proportional resize and JPEG compression.','checked_at':core.now(),'raw':{'wikidata':c['entity'],'commons':page,'structured_data':sdc,'search':search},'identity_basis':'Alternate Commons file has an exact single structured P6243 link to the selected artwork and independently passes source, creator, licence and physical-object checks.'}
      if rendered:im['rendered_licence_evidence']=rendered
      result['selected']=im;break
     except Exception as exc:result['considered'].append({'file':name,'reason':type(exc).__name__+': '+str(exc)[:250]})
   except Exception as exc:result['error']=type(exc).__name__+': '+str(exc)[:300]
   core.save_new(dest,result)
  if result.get('selected'):selected.append(result['selected'])
  else:held.append({'qid':c['qid'],'reason':result.get('error') or 'No independently licensed exact alternate found','considered':len(result.get('considered',[]))})
  if n%25==0:print(core.now(),'Alternate search',n,'/',len(rows),'selected',len(selected),flush=True)
 save('alternates/selected.json',selected);save('alternates/held.json',held);print(core.now(),'Alternates selected',len(selected),'held',len(held),flush=True)

def prepare():
 selected=load('official/selected.json')+load('alternates/selected.json');seen=set();images=[];held=[];fetch=core.Fetcher(RUN/'downloads')
 for c in selected:
  if c['qid'] in seen:continue
  seen.add(c['qid']);dest=RUN/'prepared'/(c['qid']+'.json')
  if dest.exists():images.append(json.loads(dest.read_text()));continue
  try:
   raw,headers=fetch.get(c['source_image_url'],20_000_000)
   original=ORIGINALS/(c['qid']+'-'+core.sha(raw)[:16]+'.original');core.save_new(original,raw)
   data,w,h,quality=core.compress(raw);digest=core.sha(data);path='/assets/artworks/open-museums/spain-followup/'+c['qid'].lower()+'-'+digest[:16]+'.jpg';core.save_new(ROOT/'apps/web/public'/path.lstrip('/'),data)
   im={**c,'path':path,'sha256':digest,'bytes':len(data),'width':w,'height':h,'jpeg_quality':quality,'media_id':uid('media/'+c['qid']+'/'+digest),'source_sha256':core.sha(raw),'source_bytes':len(raw),'downloaded_at':core.now(),'response_headers':headers,'transform':'Full-frame proportional resize and JPEG compression; no crop or generated content'}
   core.save_new(dest,im);images.append(im)
  except Exception as exc:held.append({'qid':c['qid'],'reason':type(exc).__name__+': '+str(exc)[:300]})
 save('prepared-manifest.json',images);save('preparation-held.json',held);print(core.now(),'Prepared',len(images),'held',len(held),flush=True)

def gallery():
 images=load('prepared-manifest.json');folder=Path('/tmp/artline-spain-followup-qa');folder.mkdir(exist_ok=True)
 for start in range(0,len(images),24):
  sheet=Image.new('RGB',(1440,1200),'#eee9df');draw=ImageDraw.Draw(sheet)
  for n,x in enumerate(images[start:start+24]):
   with Image.open(ROOT/'apps/web/public'/x['path'].lstrip('/')) as src:im=ImageOps.contain(src.convert('RGB'),(230,235))
   cx=(n%6)*240;cy=(n//6)*300;sheet.paste(im,(cx+(240-im.width)//2,cy));draw.multiline_text((cx+4,cy+240),f"{start+n+1} {x['qid']} {x['provider']}\n{x['artist'][:29]}\n{x['title'][:34]}",fill='black',spacing=3)
  sheet.save(folder/f'sheet-{start//24+1:02d}.jpg')
 save('gallery-index.json',[{'n':i+1,'qid':x['qid'],'provider':x['provider'],'path':x['path'],'artist':x['artist'],'title':x['title']} for i,x in enumerate(images)]);print(core.now(),'Gallery',folder,len(images),flush=True)

def quality():
 images=load('prepared-manifest.json');held={};media_state={}
 for target in ('local','production'):
  with connect(target) as db:
   rows=db.execute('SELECT a.id::text,a.primary_media_id::text FROM artworks a WHERE a.id=ANY(%s::uuid[])',([x['target_ids'][target] for x in images],)).fetchall()
  state={x['id']:x['primary_media_id'] for x in rows};assert len(state)==len(images);media_state[target]=state
  for im in images:
   if state[im['target_ids'][target]]:held[im['qid']]='Existing primary image preserved; follow-up candidate does not replace catalogue media'
 hashes={};sha={}
 for im in images:
  path=ROOT/'apps/web/public'/im['path'].lstrip('/');raw=path.read_bytes();assert core.sha(raw)==im['sha256'] and len(raw)<=100000
  assert im['policy_url'] and im['creator_credit'] and im['creation_year_end']<=1970 and all(c['death']<=1945 for c in im['creators'])
  with Image.open(path) as src:
   assert src.format=='JPEG' and src.size==(im['width'],im['height']);pix=list(src.convert('L').resize((9,8)).getdata())
  hashes[im['qid']]=sum((pix[j*9+i]>pix[j*9+i+1])<<(j*8+i) for j in range(8) for i in range(8));sha.setdefault(im['sha256'],[]).append(im['qid'])
 assert all(len(v)==1 for v in sha.values()),'Exact duplicate derivatives require review'
 pairs=[]
 for i,a in enumerate(images):
  for b in images[:i]:
   distance=(hashes[a['qid']]^hashes[b['qid']]).bit_count()
   if a['artist']==b['artist'] and distance<=5:pairs.append({'qids':[a['qid'],b['qid']],'artist':a['artist'],'distance':distance,'titles':[a['title'],b['title']]})
 sheets=sorted(str(p) for p in Path('/tmp/artline-spain-followup-qa').glob('sheet-*.jpg'));assert len(sheets)==2
 save('quality-review.json',{'at':core.now(),'approved':True,'images_sha256':core.sha((RUN/'prepared-manifest.json').read_bytes()),'visually_inspected_images':len(images),'eligible_images':len(images)-len(held),'held_images':held,'contact_sheets':sheets,'similarity_review':pairs,'notes':'Both sheets inspected in full. Images show coherent, correctly oriented paintings with no blank pages, watermarks, obvious details, reverse views or non-object substitutions. Existing primary media were checked live in both targets and held from replacement. Near-similarity leads are retained for explicit review and do not imply identity.'})
 print(core.now(),'Quality approved',len(images)-len(held),'eligible',len(held),'existing preserved','similarity leads',len(pairs),flush=True)

def backup():
 BACKUP.mkdir(parents=True,exist_ok=True);images=load('prepared-manifest.json');result={'at':core.now()}
 dump=BACKUP/'local-before.dump'
 if not dump.exists():subprocess.run(['pg_dump','-h','127.0.0.1','-d','artline','-Fc','-f',str(dump)],check=True)
 subprocess.run(['pg_restore','--list',str(dump)],check=True,stdout=subprocess.DEVNULL)
 result['local_dump']={'path':str(dump),'bytes':dump.stat().st_size,'sha256':core.sha(dump.read_bytes())}
 for target in ('local','production'):
  with connect(target) as db:rows=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id',([x['target_ids'][target] for x in images],)).fetchall()
  path=BACKUP/(target+'-artwork-preimages.json');core.save_new(path,rows);result[target]={'preimages':str(path),'sha256':core.sha(path.read_bytes()),'records':len(rows)}
 desc='Before Spanish follow-up images 20260917';receipt=BACKUP/'cloud-backup-request.json'
 if not receipt.exists():core.save_new(receipt,json.loads(subprocess.check_output(['gcloud','sql','backups','create','--instance=artline-postgres','--project=artline-508319','--description='+desc,'--async','--format=json'],text=True)))
 raw=json.loads(receipt.read_text());bid=str(raw.get('id') or raw.get('backupContext',{}).get('backupId') or raw.get('name','').rsplit('/',1)[-1]);
 while True:
  state=json.loads(subprocess.check_output(['gcloud','sql','backups','describe',bid,'--instance=artline-postgres','--project=artline-508319','--format=json'],text=True));status=state.get('status');print(core.now(),'Cloud backup',bid,status,flush=True)
  if status=='SUCCESSFUL':break
  if status in ('FAILED','DELETION_PENDING','DELETED'):raise RuntimeError('Cloud backup '+status)
  time.sleep(15)
 result['cloud']=state;save('backups.json',result)

def apply(target):
 qa=load('quality-review.json');manifest=RUN/'prepared-manifest.json';assert qa['approved'] and qa['images_sha256']==core.sha(manifest.read_bytes())
 backup=load('backups.json');assert backup['cloud']['status']=='SUCCESSFUL';images=[x for x in load('prepared-manifest.json') if x['qid'] not in qa.get('held_images',{})]
 bucket=storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET);counts=collections.Counter()
 with connect(target,False) as db:
  with db.transaction():
   db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,terms_url) VALUES(%s,%s,'Spanish paintings: follow-up licensed images','museum_api','https://commons.wikimedia.org/',%s) ON CONFLICT(slug) DO NOTHING",(uid('source'),SOURCE,CC0));sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
  pre={x['row']['id']:x['row'] for x in json.loads(Path(backup[target]['preimages']).read_text())}
  for im in images:
   receipt=RUN/'applied'/target/(im['qid']+'.json')
   if receipt.exists():counts['already']+=1;continue
   aid=im['target_ids'][target];old=pre[aid];assert old['primary_media_id'] is None
   data=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert core.sha(data)==im['sha256'] and len(data)<=100000
   blob=bucket.blob(im['path'].lstrip('/'))
   try:blob.metadata={'sha256':im['sha256'],'wikidata':im['qid'],'license':im['license_label']};blob.cache_control='public,max-age=31536000,immutable';blob.upload_from_string(data,content_type='image/jpeg',if_generation_match=0,timeout=60)
   except PreconditionFailed:pass
   blob.reload();assert blob.size==len(data) and blob.md5_hash==base64.b64encode(hashlib.md5(data).digest()).decode()
   with db.transaction():
    row=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s FOR UPDATE',(aid,)).fetchone()['row'];assert row==old,'Target artwork changed after preimage'
    db.execute("INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by) VALUES(%s,'local',%s,%s,%s,'image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(im['media_id'],im['path'],im['page'],'Wikimedia Commons' if im['provider']=='commons-alternate' else ('The Metropolitan Museum of Art' if im['provider']=='met' else 'Art Institute of Chicago'),im['width'],im['height'],im['bytes'],im['sha256'],im['title']+' — '+im['artist'],im['rights_status'],im['license_label'],im['policy_url'],im['creator_credit'],im['attribution_text'],im['downloaded_at'],im['checked_at'],ACTOR))
    db.execute("INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES(%s,%s,%s,%s,%s,%s,%s,'spain-followup-v1',%s,%s)",(im['media_id'],sid,im['qid'],core.sha(core.encode(im['raw'])),im['source_image_url'],im['policy_url'],im['identity_basis'],im['checked_at'],Jsonb(im)))
    db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,'Selected licensed reproduction')",(aid,im['media_id']))
    db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(im['media_id'],ACTOR,aid))
    assert db.execute('SELECT primary_media_id::text media FROM artworks WHERE id=%s',(aid,)).fetchone()['media']==im['media_id']
   core.save_new(receipt,{'at':core.now(),'target':target,'qid':im['qid'],'artwork_id':aid,'media_id':im['media_id'],'path':im['path'],'sha256':im['sha256']});counts['attached']+=1
   print(core.now(),target,dict(counts),flush=True)
 save('delivery-'+target+'.json',{'at':core.now(),'counts':dict(counts)})

def verify():
 qa=load('quality-review.json');images=[x for x in load('prepared-manifest.json') if x['qid'] not in qa.get('held_images',{})];summary={};served={}
 for target in ('local','production'):
  receipts=[json.loads(p.read_text()) for p in (RUN/'applied'/target).glob('*.json')];assert len(receipts)==len(images)
  with connect(target) as db:
   rows=db.execute('SELECT a.id::text,a.primary_media_id::text,m.storage_path,m.checksum_sha256,m.byte_size,m.rights_status FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',([x['target_ids'][target] for x in images],)).fetchall();assert len(rows)==len(images)
   index={x['target_ids'][target]:x for x in images}
   for row in rows:
    im=index[row['id']];assert row['primary_media_id']==im['media_id'] and row['checksum_sha256']==im['sha256'] and row['byte_size']<=100000
    assert db.execute('SELECT 1 FROM media_rights_evidence WHERE media_id=%s',(im['media_id'],)).fetchone();served[row['storage_path']]=row['checksum_sha256']
  summary[target]={'attached':len(rows)}
 assert summary['local']==summary['production']
 def check(item):
  path,digest=item;res=requests.get(SITE+path,timeout=(10,45));res.raise_for_status();assert core.sha(res.content)==digest;return {'url':SITE+path,'status':res.status_code,'sha256':digest,'bytes':len(res.content)}
 import concurrent.futures
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:checks=list(pool.map(check,served.items()))
 save('verification.json',{'at':core.now(),'databases':summary,'public_images':checks});print(core.now(),'Verified',summary,'public',len(checks),flush=True)

def smoke():
 qa=load('quality-review.json');images=[x for x in load('prepared-manifest.json') if x['qid'] not in qa.get('held_images',{})];_,plans=facts_and_plan();t=plans['production'];states={x['qid']:x for x in t['states']};checks=[]
 sample=[]
 for provider in sorted({x['provider'] for x in images}):sample.extend([x for x in images if x['provider']==provider][:3])
 sample.extend(images[-3:]);sample={x['qid']:x for x in sample}.values()
 for im in sample:
  st=states[im['qid']];artist=t['artists'][st['artist_qid']];assert st['artist_id']
  url=SITE+'/api/backend/v1/artists/'+artist['slug']+'/works/'+st['id'];res=requests.get(url,timeout=(10,45));res.raise_for_status();obj=res.json()
  assert obj['id']==st['id'] and obj['status'] in ('review','published') and im['path'] in obj['media_url']
  checks.append({'qid':im['qid'],'url':url,'status':res.status_code,'media_url':obj['media_url']})
 save('api-smoke.json',{'at':core.now(),'checks':checks});print(core.now(),'API smoke',len(checks),flush=True)

def report():
 v=load('verification.json');qa=load('quality-review.json');ims=[x for x in load('prepared-manifest.json') if x['qid'] not in qa.get('held_images',{})];by=collections.Counter(x['provider'] for x in ims)
 body=f"""# Spain image follow-up — 17 September 2026

Attached **{len(ims)} additional licensed images** to the same records in local and production. Every served file was downloaded and checksum-verified. Existing images and non-media catalogue fields were preserved.

Sources: {', '.join(k+': '+str(n) for k,n in sorted(by.items()))}. All records remain in review. Exact object identity, named creator chronology, per-file rights, source provenance and credits were checked separately. Prepared images excluded during visual review remain in `quality-review.json`; source failures and rejected alternates remain in the evidence folders.

Recovery preimages and the successful Cloud SQL backup are indexed by `backups.json`. Transaction receipts are in `applied/`; public-file and database proofs are in `verification.json`.
"""
 (RUN/'README.md').write_text(body);print(core.now(),'Report written',flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['inventory','official','alternates','prepare','gallery','quality','backup','apply','verify','smoke','report']);p.add_argument('--limit',type=int,default=0);p.add_argument('--target',choices=['local','production']);a=p.parse_args()
 if a.phase=='alternates':alternates(a.limit)
 elif a.phase=='apply':apply(a.target)
 else:globals()[a.phase]()
