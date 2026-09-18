#!/usr/bin/env python3
"""Bounded, identity-checked image attachments for existing DK/RU works."""
import argparse,collections,hashlib,importlib.util,json,re,time
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode,urlparse
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb

spec=importlib.util.spec_from_file_location('research',Path(__file__).with_name('resolve-danish-russian-images.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
core=r.core;ROOT=r.ROOT;RUN=r.RUN;IMAGES=RUN/'images'
COMMONS='dk-ru-commons';SMK='dk-smk-gap';SYNC='dk-local-sync'
core.PROVIDERS.update({COMMONS:'Wikimedia Commons',SMK:'Statens Museum for Kunst',SYNC:'Statens Museum for Kunst'})
core.VERSION='danish-russian-exact-image-gaps-v1'
core.HOSTS.add('thumb.wikimedia.org')

def plain(s):return BeautifulSoup(s,'html.parser').get_text(' ',strip=True)
def candidate(image):return {k:image[k] for k in ('artwork_id','slug','title','provider','scheme','external_id','artist')}
def targets():
 d,works=r.gaps();authors={a['id']:a for a in d['artists']}
 return d,works,authors,{(e['scheme'],e['id']):w for w in works for e in w['identifiers'] or []}
def write_selection(provider,images):
 for image in images:core.save_new(IMAGES/'selected'/provider/(image['artwork_id']+'.json'),image)
 core.save_new(IMAGES/(provider+'-candidates.json'),{'limit':1200,'candidates':[candidate(i) for i in images]})
 print(provider,'selected',len(images),flush=True)

def smk_select():
 spec=importlib.util.spec_from_file_location('danish',ROOT/'ops/apply-danish-images.py');dk=importlib.util.module_from_spec(spec);spec.loader.exec_module(dk)
 d,works,authors,index=targets();out=[]
 for c in dk.eligible():
  w=c['work'];target=index.get((dk.SCHEME,w['source_object_id']))
  if not target or not c['source_image_url']:continue
  out.append({'artwork_id':target['id'],'slug':target['slug'],'title':target['title'],'provider':SMK,'scheme':dk.SCHEME,'external_id':w['source_object_id'],'artist':authors[target['creators'][0]['id']]['display_name'],'countries':target['countries'],'page':w['url'],'source_image_url':c['source_image_url'],'policy_url':dk.POLICY,'rights_status':'public_domain','license_label':'Public Domain Mark 1.0','checked_at':core.now(),'raw':w['raw'],'identity_basis':'Exact SMK object number and named Danish creator from pinned official museum record; public_domain=true and explicit Public Domain Mark.'})
 out.sort(key=lambda i:(index[(i['scheme'],i['external_id'])]['work_type']!='painting',i['artist'],i['external_id']))
 write_selection(SMK,out[:960])

def commons_select():
 d,works,authors,index=targets();matched=[]
 for c in json.loads((ROOT/'docs/research/russian-painters-20260913/image-rights-cleared.json').read_bytes()):
  w=index.get(('european-russian-session-museum-object',c['work']['source_object_id']))
  if w:matched.append({'target':w,'commons_title':c['commons_title'],'work_qid':c['wikidata_artwork'],'identity':c})
 extra=RUN/'commons-new-matches.json'
 if extra.exists():
  seen={c['target']['id'] for c in matched}
  matched.extend(c for c in json.loads(extra.read_bytes()) if c['target']['id'] not in seen)
 smk_selected={c['artwork_id'] for c in json.loads((IMAGES/(SMK+'-candidates.json')).read_bytes())['candidates']}
 matched=[c for c in matched if c['target']['id'] not in smk_selected]
 matched=matched[:500]
 pages={}
 for start in range(0,len(matched),20):
  titles=list(dict.fromkeys(c['commons_title'] for c in matched[start:start+20]))
  data=r.fetch('https://commons.wikimedia.org/w/api.php?'+urlencode({'action':'query','format':'json','titles':'|'.join(titles),'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':1280,'rvprop':'ids|content','rvslots':'main','maxlag':5}))
  for p in data['query']['pages'].values():pages[p['title'].replace('_',' ')]=p
  print('Commons rights metadata',min(start+20,len(matched)),'/',len(matched),flush=True)
 out=[];deferred=[]
 for c in matched:
  try:
   w=c['target'];p=pages[c['commons_title'].replace('_',' ')];info=p['imageinfo'][0];meta=info['extmetadata'];field=lambda k:meta.get(k,{}).get('value','')
   licenses={'Public domain':'public_domain','CC0':'cc0','CC BY 2.0':'cc_by','CC BY 3.0':'cc_by','CC BY 4.0':'cc_by','CC BY-SA 2.0':'cc_by_sa','CC BY-SA 2.5':'cc_by_sa','CC BY-SA 3.0':'cc_by_sa','CC BY-SA 4.0':'cc_by_sa'}
   label=field('LicenseShortName');assert label in licenses and not field('Restrictions'),'Unresolved per-file rights'
   if label=='Public domain':assert field('Copyrighted')=='False','Conflicting copyright status'
   assert not re.search(r'\b(?:rusmuseumvrm\.ru|(?:en\.)?rusmuseum\.ru)\b',field('Credit'),re.I),'Russian Museum source permission conflict'
   policy='https://creativecommons.org/publicdomain/mark/1.0/' if label=='Public domain' else field('LicenseUrl').replace('http://','https://')
   assert policy.startswith('https://creativecommons.org/'),'Missing explicit license URL'
   credit=plain(field('Artist'));assert credit,'Missing image creator credit'
   assert not re.search(r'\b(detail|detailled|collage|montage)\b',p['title'],re.I),'Detail or composite needs review'
   text=p['revisions'][0]['slots']['main']['*']
   identity=c['identity']
   if identity.get('verified'):
    assert identity['commons_page']['imageinfo'][0]['sha1']==info['sha1'],'File contents changed since museum identity review'
   else:
    assert re.search(r'\b'+re.escape(c['work_qid'])+r'\b',text) or (w.get('accession_number') and w['accession_number'] in text) or r.norm(plain(field('ObjectName'))) in {r.norm(t) for t in identity.get('titles',[])},'Commons file identity needs review'
   url=info.get('thumburl') or info['url'];assert urlparse(url).hostname in {'upload.wikimedia.org','thumb.wikimedia.org'}
   e=next((e for e in w['identifiers'] if e['scheme']=='wikidata'),w['identifiers'][0]);artist=authors[w['creators'][0]['id']]['display_name']
   image={'artwork_id':w['id'],'slug':w['slug'],'title':w['title'],'artist':artist,'countries':w['countries'],'provider':COMMONS,'scheme':e['scheme'],'external_id':e['id'],'page':info['descriptionurl'],'source_image_url':url,'policy_url':policy,'rights_status':licenses[label],'license_label':label,'checked_at':core.now(),'creator_credit':credit,'attribution_text':f"{artist}. {w['title']}. Image credit: {credit}. {plain(field('Attribution'))} {info['descriptionurl']}. {label} ({policy}). Full-frame proportional resize and JPEG compression.",'raw':{'identity_chain':c,'commons_page':p},'identity_basis':identity.get('identity_basis') or identity.get('basis'),'wikidata_artwork':c['work_qid'],'source_variant':'commons_thumbnail' if info.get('thumburl') else 'commons_original'}
   if not info.get('thumburl'):image['commons_original_sha1']=info['sha1']
   out.append(image)
  except (AssertionError,KeyError,ValueError) as error:deferred.append({'work':c['target']['id'],'file':c['commons_title'],'reason':str(error)})
 core.save_new(RUN/'commons-deferred.json',deferred);write_selection(COMMONS,out)
 print('Commons deferred',len(deferred),flush=True)

def sync_select():
 local=json.loads((RUN/'local-before.json').read_bytes());remote=json.loads((RUN/'production-before.json').read_bytes())
 ri={(e['scheme'],e['id']):w for w in remote['works'] for e in w['identifiers'] or []};out=[]
 with r.psycopg.connect('postgres://127.0.0.1/artline',row_factory=r.dict_row) as db:
  db.execute('SET TRANSACTION READ ONLY')
  for w in local['works']:
   if not w['primary_media_id'] or w['date_scope']!='eligible' or not w['selected']:continue
   e=next((e for e in w['identifiers'] or [] if (e['scheme'],e['id']) in ri and not ri[(e['scheme'],e['id'])]['primary_media_id']),None)
   if not e:continue
   row=db.execute('SELECT to_jsonb(m) media,to_jsonb(r) evidence FROM media_assets m JOIN media_rights_evidence r ON r.media_id=m.id WHERE m.id=%s',(w['primary_media_id'],)).fetchone();assert row
   m=row['media'];ev=row['evidence'];raw=ev['evidence_json']['object']
   assert raw['object_number']==e['id'] and raw['public_domain'] is True and raw['rights']=='https://creativecommons.org/publicdomain/mark/1.0/'
   data=(ROOT/'apps/web/public'/m['storage_path'].lstrip('/')).read_bytes();assert core.sha(data)==m['checksum_sha256'] and len(data)==m['byte_size']<=100000
   image={'artwork_id':w['id'],'slug':w['slug'],'title':w['title'],'artist':m['creator_credit'],'countries':w['countries'],'provider':SYNC,'scheme':e['scheme'],'external_id':e['id'],'page':m['source_page_url'],'source_image_url':ev['source_image_url'],'policy_url':m['license_url'],'rights_status':m['rights_status'],'license_label':m['license_label'],'checked_at':ev['checked_at'],'raw':raw,'identity_basis':'Existing verified local SMK image, exact object number and Public Domain Mark; production-only missing attachment repair.','path':m['storage_path'],'sha256':m['checksum_sha256'],'bytes':m['byte_size'],'width':m['width'],'height':m['height'],'media_id':m['id'],'downloaded_at':m['retrieved_at'],'original_local_media':m,'original_local_evidence':ev}
   core.save_new(IMAGES/'images'/SYNC/(w['id']+'.json'),image);out.append(image)
 write_selection(SYNC,out)

def older_danish_select():
 works=json.loads((RUN/'older-danish-painting-search-targets.json').read_bytes());pages=json.loads((RUN/'older-danish-painting-search-files.json').read_bytes())
 authors={a['id']:a for a in json.loads((RUN/'local-before.json').read_bytes())['artists']};out=[];deferred=[]
 for w in works:
  artist=authors[w['creators'][0]['id']]['display_name'];options=[]
  for page in pages.values():
   info=page['imageinfo'][0];meta=info['extmetadata'];field=lambda k:meta.get(k,{}).get('value','');credit=plain(field('Artist'))
   # Accession must occur in an official SMK source URL, not as a substring
   # of another inventory (e.g. KMS455 must never match KMSst455).
   if not re.search(r'(?:collection|open)\.smk\.dk/[^\s<>\"\']*[/=]'+re.escape(w['accession_number'])+r'(?![A-Za-z0-9])',field('Credit'),re.I):continue
   if r.norm(credit)!=r.norm(artist):continue
   if re.search(r'\b(detail|collage|montage)\b',page['title'],re.I):continue
   label=field('LicenseShortName')
   if label not in ('Public domain','CC0') or field('Restrictions') or label=='Public domain' and field('Copyrighted')!='False':continue
   text=page['revisions'][0]['slots']['main']['*'];q=re.search(r'\|\s*wikidata\s*=\s*(Q\d+)',text,re.I)
   options.append((page,info,credit,label,q[1] if q else None))
  if not options:deferred.append({'artwork_id':w['id'],'accession':w['accession_number'],'reason':'No matching official source URL, exact creator and explicit reusable Commons file'});continue
  # Prefer the standardized museum reproduction over duplicate upload variants.
  options.sort(key=lambda x:(' - '+w['accession_number']+' - ' not in x[0]['title'],x[0]['title'].lower().endswith('.tif'),x[0]['title']))
  page,info,credit,label,q=options[0];policy='https://creativecommons.org/publicdomain/mark/1.0/' if label=='Public domain' else info['extmetadata']['LicenseUrl']['value'].replace('http://','https://');assert policy.startswith('https://creativecommons.org/')
  e=next(e for e in w['identifiers'] if e['scheme']=='european-smk-statens-museum-for-kunst-object')
  image={'artwork_id':w['id'],'slug':w['slug'],'title':w['title'],'artist':artist,'countries':['DK'],'provider':COMMONS,'scheme':e['scheme'],'external_id':e['id'],'page':info['descriptionurl'],'source_image_url':info.get('thumburl') or info['url'],'policy_url':policy,'rights_status':'public_domain' if label=='Public domain' else 'cc0','license_label':label,'checked_at':core.now(),'creator_credit':credit,'attribution_text':f"{artist}. {w['title']}. Image credit: {credit}. Statens Museum for Kunst / Wikimedia Commons. {info['descriptionurl']}. {label} ({policy}). Full-frame proportional resize and JPEG compression.",'raw':{'target':w,'commons_page':page,'artist':authors[w['creators'][0]['id']],'search_scope':'46 older Danish painting gaps; exact official SMK accession URL and creator, not title-only search'},'identity_basis':'Exact accession in official SMK collection URL cited by Commons and exact creator label; explicit reusable file rights.','wikidata_artwork':q,'source_variant':'commons_thumbnail' if info.get('thumburl') else 'commons_original'}
  if not info.get('thumburl'):image['commons_original_sha1']=info['sha1']
  core.save_new(IMAGES/'selected'/COMMONS/(w['id']+'.json'),image);out.append(image)
 core.save_new(IMAGES/'commons-danish-accession-candidates.json',{'candidates':[candidate(i) for i in out]});core.save_new(RUN/'older-danish-painting-search-deferred.json',deferred);print('Additional Danish Commons paintings selected',len(out),flush=True)

def record_evidence():
 assert (RUN/'backups.json').exists()
 excluded={e['artwork_id'] for e in json.loads((RUN/'nationality-exclusions.json').read_bytes())};inputs=[]
 for p in (IMAGES/'selected'/COMMONS).glob('*.json'):
  s=json.loads(p.read_bytes())
  if s['artwork_id'] in excluded:continue
  inputs.append({'scheme':s['scheme'],'oid':s['external_id'],'url':s['page'],'note':json.dumps({'state':'Rights-reviewed image candidate; successful attachment is recorded separately in media rights evidence and application receipts.','identity_basis':s['identity_basis'],'source_image_url':s['source_image_url'],'license':s['license_label'],'license_url':s['policy_url'],'creator_credit':s['creator_credit'],'wikidata_artwork':s['wikidata_artwork'],'research_evidence_sha256':core.sha(core.encode(s['raw'])),'checked_at':s['checked_at']},ensure_ascii=False)})
 results={}
 for target,dsn in [('local','postgres://127.0.0.1/artline'),('production',core.cloud_dsn())]:
  with r.psycopg.connect(dsn,row_factory=r.dict_row) as db:
   db.execute('SELECT pg_advisory_xact_lock(2026091320)');db.execute("SET LOCAL statement_timeout='30s'")
   db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES('danish-russian-commons-gap-research','Danish and Russian artwork image gap research — Wikimedia Commons','authority_data','https://commons.wikimedia.org','https://commons.wikimedia.org/wiki/Commons:Licensing') ON CONFLICT DO NOTHING")
   sid=db.execute("SELECT id FROM sources WHERE slug='danish-russian-commons-gap-research'").fetchone()['id']
   n=db.execute("WITH input AS(SELECT * FROM jsonb_to_recordset(%s::jsonb) AS x(scheme text,oid text,url text,note text)) SELECT count(*) n FROM input i JOIN external_identifiers e ON e.entity_type='artwork' AND e.scheme=i.scheme AND e.external_id=i.oid",(Jsonb(inputs),)).fetchone()['n'];assert n==len(inputs)
   cursor=db.execute("""WITH input AS(SELECT * FROM jsonb_to_recordset(%s::jsonb) AS x(scheme text,oid text,url text,note text))
    INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
    SELECT 'artwork',e.entity_id,'image_candidate',%s,i.scheme||':'||i.oid,i.url,i.note,now(),%s FROM input i JOIN external_identifiers e ON e.entity_type='artwork' AND e.scheme=i.scheme AND e.external_id=i.oid
    WHERE NOT EXISTS(SELECT 1 FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=e.entity_id AND c.field_name='image_candidate' AND c.source_id=%s AND c.source_url=i.url)""",(Jsonb(inputs),sid,core.ACTOR,sid))
   results[target]={'rights_reviewed_candidates':n,'inserted_citations':cursor.rowcount}
 core.save_new(RUN/'commons-research-database-receipt.json',results);print(results,flush=True)

class ProviderPaused(BaseException):pass
class SelectedFetcher(core.Fetcher):
 def get(self,url,limit=8_000_000):
  host=urlparse(url).hostname
  if urlparse(url).scheme!='https' or host not in {'iip.smk.dk','api.smk.dk','upload.wikimedia.org','thumb.wikimedia.org'}:raise ValueError('Unapproved source host')
  logs=IMAGES/'events.jsonl'
  if logs.exists():
   for line in logs.read_text().splitlines():
    e=json.loads(line)
    paused_host=urlparse(e.get('source_url','')).hostname or ''
    same_provider=paused_host==host or paused_host.endswith('wikimedia.org') and host.endswith('wikimedia.org')
    if e.get('outcome')!='provider_paused_http' or not same_provider:continue
    retry=e.get('retry_after') or '600';delay=int(retry) if retry.isdigit() else 600
    if datetime.fromisoformat(e['at'].replace('Z','+00:00')).timestamp()+delay>time.time():raise ProviderPaused('Source cooldown active; no image request sent')
  interval=8 if host.endswith('wikimedia.org') else 1.3
  time.sleep(max(0,interval-(time.monotonic()-self.last)));self.last=time.monotonic()
  with self.session.get(url,timeout=(15,45),stream=True,allow_redirects=False) as response:
   if response.status_code in (429,502,503,504):
    core.event(IMAGES,{'provider':COMMONS if host.endswith('wikimedia.org') else SMK,'outcome':'provider_paused_http','status':response.status_code,'retry_after':response.headers.get('Retry-After'),'source_url':url})
    raise ProviderPaused('Source paused; Retry-After recorded without automatic retry')
   response.raise_for_status();assert response.status_code==200
   raw=bytearray()
   for chunk in response.iter_content(65536):
    raw.extend(chunk)
    if len(raw)>limit:raise ValueError('Source image exceeds selected byte budget')
   return bytes(raw),{k:response.headers.get(k) for k in ('Content-Type','ETag','Last-Modified')}
core.Fetcher=SelectedFetcher
original_attach=core.attach
def attach(db,image,target):
 with db.transaction():
  result=original_attach(db,image,target)
  if result=='attached' and image.get('creator_credit'):
   db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(image['creator_credit'],image['attribution_text'],image['media_id']))
   db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',(image['identity_basis']+'; explicit per-file Commons reuse license with required image credit.',image['media_id']))
  return result
core.attach=attach
old_event=core.event
def event(run,value):
 old_event(run,value)
 if sum(core.COUNTS.values())%10==0 or value['outcome'] not in ('prepared','complete'):print(core.now(),dict(core.COUNTS),value.get('error',''),flush=True)
core.event=event

def run_images(phase,provider):
 candidates=json.loads((IMAGES/(provider+'-candidates.json')).read_bytes())['candidates']
 alternatives=IMAGES/'commons-alternative-candidates.json'
 if provider==COMMONS and alternatives.exists():candidates+=json.loads(alternatives.read_bytes())['candidates']
 danish=IMAGES/'commons-danish-accession-candidates.json'
 if provider==COMMONS and danish.exists():candidates+=json.loads(danish.read_bytes())['candidates']
 exclusions=RUN/'nationality-exclusions.json'
 excluded={e['artwork_id'] for e in json.loads(exclusions.read_bytes())} if exclusions.exists() else set()
 candidates=[c for c in candidates if c['artwork_id'] not in excluded]
 if provider==COMMONS:
  popular={c['target']['id'] for c in json.loads((RUN/'commons-new-matches.json').read_bytes()) if c['identity']['wikipedia_articles']}
  highlighted=['Q478271','Q3205872','Q4404599','Q13381307','Q12135183','Q4812449','Q4110167','Q4110459']
  selected={c['artwork_id']:json.loads((IMAGES/'selected'/provider/(c['artwork_id']+'.json')).read_bytes()) for c in candidates}
  candidates.sort(key=lambda c:('DK' not in selected[c['artwork_id']]['countries'],highlighted.index(selected[c['artwork_id']]['wikidata_artwork']) if selected[c['artwork_id']]['wikidata_artwork'] in highlighted else 100,c['artwork_id'] not in popular,c['artist']!='Ilya Repin',c['external_id']))
 latest={}
 if (IMAGES/'events.jsonl').exists():
  for line in (IMAGES/'events.jsonl').read_text().splitlines():
   e=json.loads(line)
   if e.get('artwork_id'):latest[(e['provider'],e['artwork_id'])]=e
 if phase=='prepare':candidates=[c for c in candidates if not (IMAGES/'images'/provider/(c['artwork_id']+'.json')).exists()]
 else:
  assert (RUN/'backups.json').exists(),'Recovery backups required'
  candidates=[c for c in candidates if (IMAGES/'images'/provider/(c['artwork_id']+'.json')).exists() and not (latest.get((provider,c['artwork_id']),{}).get('outcome')=='complete' and latest[(provider,c['artwork_id'])].get('local')=='attached' and latest[(provider,c['artwork_id'])].get('cloud')=='attached')]
 print(phase,provider,len(candidates),flush=True)
 try:core.worker(provider,candidates,SimpleNamespace(run=IMAGES,prepare_only=phase=='prepare',upload_prepared_only=phase=='apply'),'' if phase=='prepare' else core.cloud_dsn())
 except ProviderPaused as error:print(str(error),flush=True)
 print('Finished current pass',dict(core.COUNTS),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['smk-select','commons-select','sync-select','older-danish-select','record-evidence','prepare','apply']);p.add_argument('--provider',choices=[COMMONS,SMK,SYNC]);a=p.parse_args()
 if a.phase=='smk-select':smk_select()
 elif a.phase=='commons-select':commons_select()
 elif a.phase=='sync-select':sync_select()
 elif a.phase=='older-danish-select':older_danish_select()
 elif a.phase=='record-evidence':record_evidence()
 else:run_images(a.phase,a.provider)
