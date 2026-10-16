#!/usr/bin/env python3
"""Selected WikiArt image gaps; exact native identity, preserved catalogue fields."""
import argparse,base64,collections,concurrent.futures,hashlib,importlib.util,io,json,re,time
from pathlib import Path
from urllib.parse import urlsplit
import psycopg,requests
from PIL import Image,ImageOps,ImageStat
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed

def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
m=module('million','million-catalogue-20261010.py');r=m.m
n=module('nga','million-nga-20261010.py');g=module('sheets','million-nga-images-20261010.py')
d=module('wiki_delivery','deliver-production-wikiart-images-20261006.py')
RUN=m.RUN/'wikiart/images-001';ORIG=Path.home()/'Library/Application Support/Artline/source-images'/m.OP/'wikiart-001'
POLICY='https://www.wikiart.org/en/terms-of-use';EXCLUDED=['008d3646-ed41-4691-9a37-25a9fff40e51']
IGNORE={'primary_media_id','updated_by','updated_at','revision'}

def selection():return m.load(RUN/'selection.json.gz')
def select():
 if (RUN/'selection.json.gz').exists():return
 discovery=m.load(m.RUN/'wikiart/images-001/discovery.json');artists={x['id']:x for x in discovery['artists']};ids=list(artists)
 date_leads={x['id'] for x in m.load(m.RUN/'wikiart/undated-date-hints-discovery.json')['rows']} if RUN.name=='images-004' else None
 prior={row['artwork_id'] for path in RUN.parent.glob('images-*/selection.json.gz') if path.parent!=RUN for row in m.load(path)['rows']}
 query="""SELECT DISTINCT a.id::text,aa.artist_id::text,to_jsonb(a) artwork,to_jsonb(e) external
 FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id
 JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikiart-artwork'
 WHERE aa.artist_id=ANY(%s::uuid[]) AND aa.attribution_role='primary' AND a.status<>'archived'
 AND a.primary_media_id IS NULL AND (a.creation_year_end<=1955 OR a.creation_year_end IS NULL)
 AND NOT coalesce(a.current_institution_id=ANY(%s::uuid[]),false)
 ORDER BY a.id::text,aa.artist_id::text"""
 with r.connect() as db:
  excluded=EXCLUDED+[x['id'] for x in db.execute("SELECT id::text FROM institutions WHERE lower(name) LIKE '%louvre%'")]
  plan=db.execute('EXPLAIN (FORMAT JSON) '+query,(ids,excluded)).fetchone()
  rows=db.execute(query,(ids,excluded)).fetchall()
  # Native artwork identifiers must point to one artwork and one creator profile.
  counts=collections.Counter(x['id'] for x in rows);seen=collections.Counter();chosen=[]
  rows.sort(key=lambda x:(x['artwork']['creation_year_end'] is None,artists[x['artist_id']]['display_name'],x['artwork']['title'],x['id']))
  for x in rows:
   if x['id'] in prior or (RUN.name not in ['images-001','images-004'] and x['artwork']['creation_year_end'] is None):continue
   if date_leads is not None and x['id'] not in date_leads:continue
   if counts[x['id']]!=1 or seen[x['artist_id']]>=20:continue
   if not (x['external']['canonical_url'] or '').startswith(artists[x['artist_id']]['canonical_url'].rstrip('/')+'/'):continue
   x.update(artwork_id=x['id'],title=x['artwork']['title'],creator_label=artists[x['artist_id']]['display_name'],artist=artists[x['artist_id']],source_url=x['external']['canonical_url'])
   chosen.append(x);seen[x['artist_id']]+=1
   if len(chosen)>=480:break
  snapshots=d.snapshots(db,[x['id'] for x in chosen])
  local_baseline=m.load(m.RUN/'baseline.json.gz')['local_readonly_counts']
 out=dict(at=m.now(),rows=chosen,query_plan=plan,discovered_gaps=len(rows),artists=len(seen),local_baseline=local_baseline,
  selection_basis='Up to 480 existing native WikiArt image gaps, at most 20 per verified creator; concurrent 500-painter campaign excluded. Known dates through 1955 first; unknown catalogue dates require an explicit eligible source date before preparation. Exact native object and artist profile checks precede downloads. No rights-label exclusion; actual labels remain evidence.')
 if date_leads is not None:out['date_research_basis']='Undated catalogue records whose existing source URLs contain a year, used only as research leads. Depicted-event years and URL numbers do not establish creation dates; explicit source creation metadata is still required before any download.'
 m.save(RUN/'selection.json.gz',out);m.save(RUN/'pin.json',dict(sha256=m.sha((RUN/'selection.json.gz').read_bytes())))
 m.save(m.BACKUP/'wikiart'/RUN.name/'selection-preimages.json.gz',snapshots)
 m.save(RUN/'authorization.json',dict(at=m.now(),user_instruction="nice, add more images use wikiart and don't think about rights!",source_approval='User approval 6 October reaffirmed 11 October 2026. No per-image rights-clearance hold. Actual source labels preserved separately.',production_images_authorized=True,local_readonly=True))
 print('Selected',len(chosen),'image gaps for',len(seen),'artists',flush=True)

def prepare():
 select();d.RUN=RUN;d.ORIGINALS=ORIG;ORIG.mkdir(parents=True,exist_ok=True)
 def one(row):
  aid=row['artwork_id'];dest=RUN/'prepared'/(aid+'.json')
  if dest.exists():return m.load(dest)['state']
  out=dict(artwork_id=aid,title=row['title'],artist=row['creator_label'],source_url=row['source_url'])
  try:
   p=r.wiki_fields(row['source_url']);out['page']=p
   assert str(p['source_id'])==row['external']['external_id'],'Native artwork ID differs'
   assert p['artist_url'].rstrip('/')==row['artist']['canonical_url'].rstrip('/'),'Native creator profile differs'
   assert p['date'] and p['date']['last']<=1955,'Source creation date unknown or outside selected image scope'
   assert r.norm(p['title']) in {r.norm(row['title']),r.norm(row['artwork']['alternate_title'])},'Native artwork title changed; review translation/version'
   url=p['metadata']['image'];display=p['image_url']
   if d.q.image_key(url)!=d.q.image_key(display):
    assert display=='https://uploads.wikiart.org/Content/images/FRAME-600x480.jpg','Source display and metadata images differ'
    out['source_display_placeholder']=dict(display_url=display,explicit_metadata_url=url,basis='Fetch only the public image URL explicitly supplied in this exact artwork metadata; no URL guessing or access workaround.')
   host=urlsplit(url).hostname;hold=RUN/'access-holds'/(host+'.json');assert not hold.exists(),'Image source access held'
   d.core.provider_rate_slot(host)
   try:original,receipt=d.download(url)
   except requests.HTTPError as error:
    if error.response is not None and error.response.status_code in [401,403,429]:m.save(hold,dict(at=m.now(),url=url,status=error.response.status_code))
    raise
   raw,width,height,quality=d.core.compress(original)
   assert 0<len(raw)<=100000 and min(width,height)>=50 and max(width,height)>=200
   with Image.open(io.BytesIO(original)) as source:original_size=ImageOps.exif_transpose(source).size
   assert abs(width/height-original_size[0]/original_size[1])<.025
   with Image.open(io.BytesIO(raw)) as im:
    im.verify()
   with Image.open(io.BytesIO(raw)) as im:
    assert ImageStat.Stat(im.convert('L')).stddev[0]>1,'Uniform error image'
    pixels=list(im.convert('L').resize((17,16)).getdata());bits=''.join('1' if pixels[y*17+x]>pixels[y*17+x+1] else '0' for y in range(16) for x in range(16));dhash=hex(int(bits,2))[2:].zfill(64)
   digest=m.sha(raw);storage_path='/assets/artworks/imported/'+m.OP+'/'+aid+'-'+digest[:16]+'.jpg';local=m.ROOT/'apps/web/public'/storage_path.lstrip('/');local.parent.mkdir(parents=True,exist_ok=True)
   if local.exists():assert local.read_bytes()==raw
   else:local.write_bytes(raw)
   out.update(state='prepared',path=str(local),storage_path=storage_path,sha256=digest,bytes=len(raw),width=width,height=height,quality=quality,media_id=m.uid('media/wikiart/'+aid+'/'+digest),download=receipt,source_image_url=url,original_dimensions=list(original_size),dhash=dhash,identity_confidence=.99,identity_basis='Exact previously catalogued WikiArt native artwork ID, source page, unchanged title, verified artist profile; source date retained as evidence without catalogue rewriting.')
  except Exception as error:out.update(state='held',reason=type(error).__name__+': '+str(error)[:500])
  m.save(dest,out);return out['state']
 counts=collections.Counter()
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for i,state in enumerate(pool.map(one,selection()['rows']),1):
   counts[state]+=1
   if i%20==0:print('WikiArt preparation',i,dict(counts),flush=True)
 print('WikiArt preparation complete',dict(counts),flush=True)

def sheets():
 g.RUN=RUN;g.ORIG=ORIG;g.select=selection;g.sheets()
 ready=[m.load(p) for p in (RUN/'prepared').glob('*.json') if m.load(p)['state']=='prepared'];groups=collections.defaultdict(list)
 for x in ready:groups[x['artist']].append(x)
 duplicates=[]
 for group in groups.values():
  for i,a in enumerate(group):
   for b in group[i+1:]:
    distance=(int(a['dhash'],16)^int(b['dhash'],16)).bit_count()
    if a['sha256']==b['sha256'] or distance<=3:duplicates.append(dict(ids=[a['artwork_id'],b['artwork_id']],distance=distance,titles=[a['title'],b['title']]))
 m.save(RUN/'duplicate-image-check.json',dict(checked=len(ready),candidates=duplicates))

def unchanged(before,after):
 assert before['creators']==after['creators'],'Creator links changed'
 assert all(after['artwork'][k]==v for k,v in before['artwork'].items() if k not in IGNORE),'Catalogue metadata changed'
 assert all(x in after['attachments'] for x in before['attachments']),'Original attachment removed'

def deliver():
 p=selection();pin=m.load(RUN/'pin.json')['sha256'];assert m.sha((RUN/'selection.json.gz').read_bytes())==pin
 selected_before=m.load(m.BACKUP/'wikiart'/RUN.name/'selection-preimages.json.gz')
 reviews=m.load(RUN/'visual-review.json');rows=[x for x in p['rows'] if reviews.get(x['artwork_id'],{}).get('decision')=='accept']
 bucket=storage.Client(project='artline-508319',credentials=d.core.GcloudCredentials()).bucket(d.core.BUCKET)
 def upload(row):
  aid=row['artwork_id'];im=m.load(RUN/'prepared'/(aid+'.json'));assert im['state']=='prepared' and im['sha256']==reviews[aid]['sha256'];raw=Path(im['path']).read_bytes();assert m.sha(raw)==im['sha256'];dest=RUN/'uploads'/(aid+'.json')
  if dest.exists():assert m.load(dest)['sha256']==im['sha256'];return
  blob=bucket.blob(im['storage_path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],'operation':m.OP};blob.cache_control='public,max-age=31536000,immutable'
  try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0)
  except PreconditionFailed:pass
  blob.reload();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
  response=requests.get('https://artlines.org'+im['storage_path'],timeout=(15,60));response.raise_for_status();assert m.sha(response.content)==im['sha256']
  m.save(dest,dict(at=m.now(),sha256=im['sha256'],generation=blob.generation,public_verified=True))
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(upload,rows))
 for index,group in enumerate(m.chunks(rows,30)):
  dest=RUN/'applied'/(str(index).zfill(3)+'.json');backup=m.BACKUP/'wikiart'/RUN.name/('locked-'+str(index).zfill(3)+'.json.gz')
  if dest.exists():continue
  for attempt in range(12):
   try:
    ids=[x['artwork_id'] for x in group];attached=[];skipped=[];recovered=[]
    with r.connect(write=True) as db:
     db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
     db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall();before=d.snapshots(db,ids)
     if backup.exists():original=m.load(backup)
     else:m.save(backup,before);original=before
     for row in group:
      aid=row['artwork_id'];a=before[aid]['artwork'];im=m.load(RUN/'prepared'/(aid+'.json'));page=im['page']
      if a['primary_media_id']==im['media_id']:unchanged(original[aid],before[aid]);recovered.append(aid);continue
      if a['primary_media_id'] is not None:skipped.append(dict(artwork_id=aid,reason='Another authorized job supplied a primary image'));continue
      assert before[aid]['creators']==selected_before[aid]['creators'],'Creator attribution changed since image selection'
      assert a['status']!='archived';assert all(a[k]==row['artwork'][k] for k in ['title','alternate_title','creation_year_start','creation_year_end','current_institution_id','status'])
      assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND entity_id=%s AND scheme='wikiart-artwork' AND external_id=%s AND canonical_url=%s",(aid,page['source_id'],row['source_url'])).fetchone()
      credit=page['creator']+'. WikiArt. '+page['rights_label']
      n.copy_rows(db,'media_assets',[dict(id=im['media_id'],storage_kind='local',storage_path=im['storage_path'],source_page_url=row['source_url'],provider_name='WikiArt',mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=row['title']+' — '+row['creator_label'],rights_status=page['rights_status'],license_label=page['rights_label'],license_url=POLICY,creator_credit=credit,attribution_text=credit+'. Full source frame preserved; proportionally resized and JPEG compressed.',retrieved_at=im['download']['at'],verified_at=m.now(),verified_by=m.ACTOR)])
      evidence=dict(selection_sha256=pin,page=page,download=im['download'],visual_review=reviews[aid],identity_basis=im['identity_basis'],identity_confidence=im['identity_confidence'],user_approval=m.load(RUN/'authorization.json'))
      n.copy_rows(db,'media_rights_evidence',[dict(media_id=im['media_id'],source_id=row['external']['source_id'],source_record_id=page['source_id'],source_checksum=page['receipt']['sha256'],source_image_url=im['source_image_url'],policy_url=POLICY,rights_basis=page['rights_basis']+' Reaffirmed by the user on 11 October 2026.',adapter_version='million-wikiart-images-20261011',checked_at=m.now(),evidence_json=json.dumps(evidence,ensure_ascii=False))])
      order=db.execute('SELECT coalesce(max(sort_order),-1)+1 n FROM artwork_media WHERE artwork_id=%s',(aid,)).fetchone()['n']
      n.copy_rows(db,'artwork_media',[dict(artwork_id=aid,media_id=im['media_id'],sort_order=order,view_label='WikiArt reproduction')]);db.execute('UPDATE artworks SET primary_media_id=%s,updated_by=%s,updated_at=now(),revision=revision+1 WHERE id=%s',(im['media_id'],m.ACTOR,aid));attached.append(aid)
     after=d.snapshots(db,ids)
     for aid in ids:unchanged(before[aid],after[aid])
     db.commit()
    m.save(dest,dict(at=m.now(),attached=attached,recovered=recovered,skipped=skipped,images=len(attached)+len(recovered)));print('Attached WikiArt batch',index,len(attached),'recovered',len(recovered),'skipped',len(skipped),flush=True);break
   except (psycopg.OperationalError,psycopg.errors.LockNotAvailable,psycopg.errors.DeadlockDetected):
    if attempt==11:raise
    time.sleep(5)

def verify():
 rows={x['artwork_id']:x for x in selection()['rows']};ids=[aid for p in sorted((RUN/'applied').glob('*.json')) for aid in m.load(p)['attached']+m.load(p)['recovered']];assert len(ids)==len(set(ids))
 with r.connect() as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');actual=d.snapshots(db,ids);checks=collections.Counter()
  media_ids=[m.load(RUN/'prepared'/(aid+'.json'))['media_id'] for aid in ids]
  media={x['media']['id']:x for x in db.execute('SELECT to_jsonb(ma) media,to_jsonb(re) evidence FROM media_assets ma JOIN media_rights_evidence re ON re.media_id=ma.id WHERE ma.id=ANY(%s::uuid[])',(media_ids,))}
  for path in sorted((RUN/'applied').glob('*.json')):
   receipt=m.load(path);before=m.load(m.BACKUP/'wikiart'/RUN.name/('locked-'+path.stem+'.json.gz'))
   for aid in receipt['attached']+receipt['recovered']:
    im=m.load(RUN/'prepared'/(aid+'.json'));unchanged(before[aid],actual[aid]);assert actual[aid]['artwork']['primary_media_id']==im['media_id']
    got=media.get(im['media_id']);assert got
    assert got['media']['checksum_sha256']==im['sha256'] and got['media']['byte_size']==im['bytes']<=100000
    assert got['media']['rights_status']==im['page']['rights_status'] and got['media']['license_label']==im['page']['rights_label']
    assert got['evidence']['source_record_id']==im['page']['source_id'] and got['evidence']['source_image_url']==im['source_image_url']
    assert any(x['media_id']==im['media_id'] for x in actual[aid]['attachments']);assert m.load(RUN/'uploads'/(aid+'.json'))['public_verified'];checks['images']+=1
  checks['matching_search_documents']=db.execute('SELECT count(*) n FROM artworks a JOIN artwork_search_documents s ON s.id=a.id WHERE a.id=ANY(%s::uuid[]) AND s.primary_media_id=a.primary_media_id',(ids,)).fetchone()['n'];assert checks['matching_search_documents']==len(ids)
 with r.connect(local=True) as db:local={t:db.execute('SELECT count(*) n FROM '+t).fetchone()['n'] for t in selection()['local_baseline']}
 assert local==selection()['local_baseline']
 chosen=list({rows[aid]['artist_id']:aid for aid in ids}.values());public=[]
 def public_one(aid):
  row=rows[aid];im=m.load(RUN/'prepared'/(aid+'.json'));url='https://artlines.org/api/backend/v1/artists/'+row['artist']['slug']+'/works/'+aid;response=requests.get(url,timeout=(15,60));response.raise_for_status();assert im['storage_path'] in response.text;public.append(dict(artwork_id=aid,url=url,status=response.status_code))
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(public_one,chosen))
 public.sort(key=lambda x:x['artwork_id'])
 result=dict(at=m.now(),checks=dict(checks),artists=len(chosen),public_artwork_routes=public,local_readonly_counts=local,local_baseline_equal=True,metadata_creator_and_status_preserved=True)
 m.save(RUN/'verification.json',result);print(json.dumps(dict(images=len(ids),artists=len(chosen),public_routes=len(public),local_unchanged=True)),flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['select','prepare','sheets','deliver','verify']);ap.add_argument('--phase',choices=['001','002','003','004','005'],default='001');args=ap.parse_args();RUN=m.RUN/('wikiart/images-'+args.phase);ORIG=ORIG.parent/('wikiart-'+args.phase);globals()[args.action]()
