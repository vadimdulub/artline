#!/usr/bin/env python3
"""Selected local Rijksmuseum image recovery; no catalogue or holding writes."""
import argparse,importlib.util,json,re,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup

def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=module('base','recover-local-commons-images-20261005.py');rijks=module('rijks','overnight-rijks-images.py');core=base.core
RUN=core.ROOT/'docs/research/local-rijks-native-images-20261006';base.RUN=RUN
EXCLUDE_RUNS=[];LIMIT=40
PROVIDER='rijks-native';core.PROVIDERS[PROVIDER]='Rijksmuseum';core.VERSION='local-rijks-exact-image-only-v1'

def page_object(c,html):
 soup=BeautifulSoup(html,'html.parser');script=soup.find('script',id='__NUXT_DATA__')
 if script is None:raise ValueError('Native collection page has no structured object')
 nodes=json.loads(script.get_text())
 def resolve(index,seen=()):
  if not isinstance(index,int) or isinstance(index,bool):return index
  if index<0:return None
  if index>=len(nodes) or index in seen:raise ValueError('Invalid native page reference')
  value=nodes[index];trail=seen+(index,)
  if isinstance(value,dict):return {k:resolve(v,trail) for k,v in value.items()}
  if isinstance(value,list):return [resolve(v,trail) for v in value]
  return value
 objects=[resolve(n) for n,v in enumerate(nodes) if isinstance(v,dict) and 'objectNodeUri' in v and resolve(v['objectNodeUri'])=='https://id.rijksmuseum.nl/'+c['external_id']]
 if len(objects)!=1:raise ValueError('Native page object is not exact and unique')
 return objects[0]

def page_facts(c,html,obj,service=None):
 o=page_object(c,html);titles={rijks.norm(x.get('content')) for x in obj.get('identified_by',[]) if x.get('type')=='Name'}
 if o.get('objectNumber')!=c['accession_number'] or rijks.norm(o.get('title')) not in titles:raise ValueError('Native page inventory or translated title differs')
 def walk(v):
  if isinstance(v,dict):
   yield v
   for x in v.values():yield from walk(x)
  elif isinstance(v,list):
   for x in v:yield from walk(x)
 rights=[n.get('values') for n in walk(o.get('dataTab')) if n.get('name')=='Copyright']
 if len(rights)!=1 or len(rights[0])!=1:raise ValueError('Native page image permission is absent or ambiguous')
 links=BeautifulSoup(rights[0][0],'html.parser').find_all('a')
 if len(links)!=1 or links[0].get('href') not in (rijks.PDM,rijks.PDM+'deed.nl',rijks.PDM+'deed.en') or links[0].get_text(' ',strip=True) not in ('Public domain','Publiek domein'):raise ValueError('Native page image lacks explicit Public Domain Mark')
 im=o.get('micrioImage') or {};ident=im.get('micrioId','')
 if im.get('type')!='MicrioImageApiModel' or not re.fullmatch('[A-Za-z0-9]+',ident) or im.get('isDownloadable') is not True or im.get('crop') is not None:raise ValueError('Native page image is not explicitly downloadable and uncropped')
 if rijks.norm(im.get('altText'))!=rijks.norm(o['title']):raise ValueError('Native photograph title differs')
 url='https://iiif.micr.io/'+ident
 if service is not None:
  if service.get('id')!=url or service.get('type')!='ImageService3' or service.get('organisation',{}).get('slug')!='rijks-collectie':raise ValueError('Native image service differs')
  if any(service.get(k)!=im.get(k) for k in ('width','height')) or min(service['width'],service['height'])<500:raise ValueError('Native image dimensions differ or are inadequate')
 return dict(service_url=url,source_image_url=url+'/full/!1000,1000/0/default.jpg',native_title=o['title'],catalogue_title=c['title'],title_basis='Both native page title and unchanged catalogue title occur in the exact Linked Art object.',native_object_number=o['objectNumber'],image=im,rights_link=links[0]['href'],rights_label=links[0].get_text(' ',strip=True))

def capture_page(c,url,fetch):
 path=RUN/'metadata/current-pages'/(c['artwork_id']+'.html')
 if path.exists():
  data=path.read_bytes();rc=json.loads(path.with_suffix('.receipt.json').read_bytes())
  if rc['requested_url']!=url or rc['sha256']!=core.sha(data):raise ValueError('Pinned current page changed')
  return data,rc
 redirects=[];target=url
 for attempt in range(4):
  if urlparse(target).netloc!='www.rijksmuseum.nl' or not re.match(r'^/(?:nl/collectie|en/collection)/object/',urlparse(target).path):raise ValueError('Unexpected native collection redirect')
  core.provider_rate_slot('www.rijksmuseum.nl');response=fetch.session.get(target,timeout=(15,45),allow_redirects=False)
  if response.status_code in (301,302,303,307,308):
   redirects.append(dict(url=target,status=response.status_code,location=response.headers.get('Location'),at=core.now()));target=urljoin(target,response.headers['Location']);continue
  if response.status_code!=200:raise ValueError('Current native page HTTP '+str(response.status_code))
  data=response.content
  if len(data)>5_000_000:raise ValueError('Native page exceeds response budget')
  rc=dict(at=core.now(),requested_url=url,url=target,redirects=redirects,bytes=len(data),sha256=core.sha(data),path=str(path.relative_to(core.ROOT)),headers={k:response.headers.get(k) for k in ('Content-Type','ETag','Last-Modified')})
  core.save_new(path,data);core.save_new(path.with_suffix('.receipt.json'),rc);return data,rc
 raise ValueError('Too many native collection redirects')

def select():
 if (RUN/'candidates.json').exists():return
 excluded=sorted({c['artwork_id'] for run in EXCLUDE_RUNS for c in json.loads((run/'candidates.json').read_bytes())['candidates']})
 with base.connect() as db:
  rows=db.execute("""SELECT a.id::text artwork_id,a.slug,a.title,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,a.accession_number,to_jsonb(a) before_record,
   i.id::text institution_id,i.slug institution_slug,i.name museum,e.scheme,e.external_id,e.source_id::text,e.canonical_url page,
   ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) roles,
   COALESCE((SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') creator_links,
   (SELECT jsonb_agg(to_jsonb(ei) ORDER BY ei.id) FROM external_identifiers ei WHERE ei.entity_type='artwork' AND ei.entity_id=a.id) identifiers,
   COALESCE((SELECT jsonb_agg(to_jsonb(la) ORDER BY la.id) FROM artwork_location_assertions la WHERE la.artwork_id=a.id),'[]') holding_assertions
   FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id JOIN institutions i ON i.id=a.current_institution_id
   WHERE e.entity_type='artwork' AND e.scheme='rijks-object' AND e.source_id IS NOT NULL AND i.slug='rijksmuseum'
   AND a.primary_media_id IS NULL AND a.status='review' AND a.work_type='painting' AND a.creation_year_start>=1000
   AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' AND artline_has_selection_evidence(a.id)
   AND NOT(a.id=ANY(%s::uuid[])) ORDER BY a.creation_year_start,a.id LIMIT %s""",(excluded,LIMIT)).fetchall()
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
  for c in rows:
   proofs=[];people=[]
   for link in c['creator_links']:
    aid=link['artist_id'];artist=db.execute('SELECT to_jsonb(ar) record FROM artists ar WHERE id=%s',(aid,)).fetchone()['record']
    identifiers=[r['record'] for r in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=%s ORDER BY id",(aid,)).fetchall()]
    proofs.append(dict(artist_record=artist,artist_identifiers=identifiers));people.extend(x['external_id'] for x in identifiers if x['scheme']=='rijks-person')
   c.update(provider=PROVIDER,artist='; '.join(p['artist_record']['display_name'] for p in proofs),rijks_people=sorted(set(people)),creator_authorities=proofs,target_ids={'local':c['artwork_id']})
 core.save_new(RUN/'candidates.json',dict(at=core.now(),baseline=baseline,candidates=rows,excluded_runs=[str(p.relative_to(core.ROOT)) for p in EXCLUDE_RUNS]))

def capture(url,suffix):
 p=RUN/'metadata'/(core.sha(url.encode())+suffix);rc=json.loads(p.with_suffix('.receipt.json').read_bytes());data=p.read_bytes()
 if rc['url']!=url or core.sha(data)!=rc['sha256'] or len(data)!=rc['bytes']:raise ValueError('Pinned native source capture differs')
 return data,rc

def verify_image(im):
 if im['source_image_url'].startswith('https://iiif.micr.io/eudFF/'):raise ValueError('Reviewed native resource is a blank 71 by 85 pixel thumbnail; no identifiable artwork depiction')
 url='https://data.rijksmuseum.nl/'+im['external_id'];data,rc=capture(url+'?_profile=la-framed','.json');obj=json.loads(data)
 keys=('id','type','identified_by','classified_as','produced_by','subject_of')
 if im['raw']['object']!={k:obj.get(k) for k in keys} or im['raw']['metadata_capture']!=rc:raise ValueError('Exact native object evidence differs')
 facts=rijks.source_match(im,obj)
 if im['scope_evidence']!=facts:raise ValueError('Source date evidence differs')
 # The source bounds alone must not erase an approximate-date qualification.
 labels=facts['source_date_text'];supported=[x for x in labels if re.fullmatch(r'(?:(?:c\.|ca\.|circa|about)\s*)?\d{4}(?:\s*[-–—/]\s*\d{4})?',x,re.I)]
 source_approx={bool(re.match(r'^(?:c\.|ca\.|circa|about)\s*',x,re.I)) for x in supported}
 if len(source_approx)!=1 or next(iter(source_approx))!=(im['date_precision'] in ('circa','circa_range')):raise ValueError('Approximate date wording needs individual review')
 if len(im['creator_authorities'])!=1 or im['creator_links'][0]['artist_id']!=im['creator_authorities'][0]['artist_record']['id']:raise ValueError('Linked artist is not unique')
 native=sorted(set(x['external_id'] for p in im['creator_authorities'] for x in p['artist_identifiers'] if x['scheme']=='rijks-person'))
 if native!=im['rijks_people']:raise ValueError('Existing native creator authority differs')
 data,rc=capture(url+'?_profile=edm','.xml');document=data.decode('utf-8')
 if im['raw']['edm_capture']!=rc or (im['raw'].get('edm_document') or im['raw']['edm']['edm_document'])!=document:raise ValueError('Exact native image-rights capture differs')
 edm=core.rijks_edm(document,im['external_id'],im['accession_number'])
 current=im['raw'].get('current_collection_page')
 if current:
  page_rc=current['receipt'];html=(core.ROOT/page_rc['path']).read_bytes()
  if core.sha(html)!=page_rc['sha256'] or not (core.ROOT/page_rc['path']).resolve().is_relative_to((RUN/'metadata/current-pages').resolve()):raise ValueError('Current page capture differs')
  source=current['image_service'];service_url=current['facts']['service_url']+'/info.json';data,service_rc=capture(service_url,'.json')
  if json.loads(data)!=source or current['service_capture']!=service_rc:raise ValueError('Pinned image service differs')
  facts=page_facts(im,html,obj,source)
  if facts!=current['facts'] or im['source_image_url']!=facts['source_image_url'] or im['raw']['edm']!=edm:raise ValueError('Current page photograph or image permission differs')
 elif edm is None or im['raw']['edm']!=edm or im['source_image_url']!=edm['source_image_url']:raise ValueError('Native primary photograph or permission differs')
 root=ET.fromstring(document);rdf='{http://www.w3.org/1999/02/22-rdf-syntax-ns#}';ns={'edm':'http://www.europeana.eu/schemas/edm/','ore':'http://www.openarchives.org/ore/terms/'};agg=root.find('ore:Aggregation',ns)
 if agg.find('edm:dataProvider',ns).get(rdf+'resource')!='https://id.rijksmuseum.nl/2109266' or agg.find('edm:isShownAt',ns).get(rdf+'resource')!=im['page']:raise ValueError('Native provider or artwork page differs')
 rights=[x.get(rdf+'resource') for x in agg.findall('edm:rights',ns)]
 if not rights or any(x not in (rijks.PDM,rijks.PDM.replace('https:','http:')) for x in rights):raise ValueError('Native EDM permission conflicts')
 if current and current['receipt']['requested_url']!=im['page']:raise ValueError('Current page is not the published native artwork page')
 if (im['rights_status'],im['license_label'],im['policy_url'],im['creator_credit'])!=('public_domain','Public Domain Mark 1.0',rijks.PDM,im['artist']+'; Rijksmuseum'):raise ValueError('Image licence or credit differs')
 if any(x not in im['attribution_text'] for x in [im['creator_credit'],rijks.PDM,im['page']]):raise ValueError('Complete source attribution missing')

def research():
 select();fetch=core.Fetcher(RUN/'metadata');fetch.defer_long_cooldowns=True;done=core.latest_events(RUN)
 for n,c in enumerate(json.loads((RUN/'candidates.json').read_bytes())['candidates'],1):
  path=RUN/'selected'/PROVIDER/(c['artwork_id']+'.json')
  if path.exists():verify_image(json.loads(path.read_bytes()));continue
  if c['artwork_id'] in done:continue
  try:
   im=rijks.image_record(c,fetch,{},{});url='https://data.rijksmuseum.nl/'+c['external_id']
   if im is None:
    document,rc=capture(url+'?_profile=edm','.xml');root=ET.fromstring(document);ns={'edm':'http://www.europeana.eu/schemas/edm/','ore':'http://www.openarchives.org/ore/terms/'}
    agg=root.find('ore:Aggregation',ns);image=agg.find('edm:isShownBy',ns) if agg is not None else None
    raise ValueError('Current EDM has no primary image resource' if image is None else 'Current EDM lacks an exact unrestricted primary image grant')
   im['provider']=PROVIDER;im['raw']['metadata_capture']=capture(url+'?_profile=la-framed','.json')[1];im['raw']['edm_capture']=capture(url+'?_profile=edm','.xml')[1]
   im['attribution_text']=f"{c['artist']}. {c['title']}, {c['date_display']}. Inventory {c['accession_number']}. {im['creator_credit']}. Public Domain Mark ({rijks.PDM}). {im['page']}. Full-frame proportional resize and JPEG compression."
   verify_image(im);core.save_new(path,im);core.event(RUN,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='rights_selected'));print(n,'Selected:',c['title'],flush=True)
  except Exception as e:
   core.event(RUN,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='manual_review',reason=str(e)[:400]));print(n,'Held:',c['title'],str(e)[:140],flush=True)

def current_pages():
 fetch=core.Fetcher(RUN/'metadata');fetch.defer_long_cooldowns=True
 for n,c in enumerate(json.loads((RUN/'candidates.json').read_bytes())['candidates'],1):
  path=RUN/'selected'/PROVIDER/(c['artwork_id']+'.json')
  if (RUN/'images'/(c['artwork_id']+'.json')).exists():continue
  if path.exists() and json.loads(path.read_bytes())['raw'].get('current_collection_page'):continue
  try:
   url='https://data.rijksmuseum.nl/'+c['external_id'];data,obj_rc=capture(url+'?_profile=la-framed','.json');obj=json.loads(data);facts=rijks.source_match(c,obj)
   data,edm_rc=capture(url+'?_profile=edm','.xml');document=data.decode();edm=core.rijks_edm(document,c['external_id'],c['accession_number'])
   root=ET.fromstring(document);agg=root.find('{http://www.openarchives.org/ore/terms/}Aggregation');page=agg.find('{http://www.europeana.eu/schemas/edm/}isShownAt').get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
   html,page_rc=capture_page(c,page,fetch);review=page_facts(c,html,obj);service_url=review['service_url']+'/info.json';service=fetch.metadata(service_url);service_rc=capture(service_url,'.json')[1];review=page_facts(c,html,obj,service)
   credit=c['artist']+'; Rijksmuseum'
   im=dict(c,page=page,source_image_url=review['source_image_url'],rights_status='public_domain',license_label='Public Domain Mark 1.0',policy_url=rijks.PDM,creator_credit=credit,checked_at=page_rc['at'],scope_evidence=facts,raw=dict(object={k:obj.get(k) for k in ('id','type','identified_by','classified_as','produced_by','subject_of')},metadata_capture=obj_rc,edm=edm,edm_document=document,edm_capture=edm_rc,current_collection_page=dict(receipt=page_rc,facts=review,image_service=service,service_capture=service_rc)),attribution_text=f"{c['artist']}. {c['title']}, {c['date_display']}. Inventory {c['accession_number']}. {credit}. Public Domain Mark ({rijks.PDM}). {page}. Full-frame proportional resize and JPEG compression.")
   verify_image(im)
   if path.exists():core.save_new(RUN/'history/before-current-page'/path.name,path.read_bytes());path.write_bytes(core.encode(im))
   else:core.save_new(path,im)
   core.event(RUN,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='current_page_rights_selected'));print(n,'Current page selected:',c['title'],flush=True)
  except Exception as e:
   core.event(RUN,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='current_page_review',reason=str(e)[:400]));print(n,'Current page held:',c['title'],str(e)[:140],flush=True)

def authority_unchanged(db,im,lock=False):
 suffix=' FOR SHARE' if lock else ''
 for proof in im['creator_authorities']:
  aid=proof['artist_record']['id'];artist=db.execute('SELECT to_jsonb(ar) record FROM artists ar WHERE id=%s'+suffix,(aid,)).fetchone()['record']
  ids=[r['record'] for r in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=%s ORDER BY id"+suffix,(aid,)).fetchall()]
  if artist!=proof['artist_record'] or ids!=proof['artist_identifiers']:raise ValueError('Creator authority changed')
 holding=[r['record'] for r in db.execute('SELECT to_jsonb(la) record FROM artwork_location_assertions la WHERE artwork_id=%s ORDER BY id'+suffix,(im['artwork_id'],)).fetchall()]
 if holding!=im['holding_assertions']:raise ValueError('Holding evidence changed')

def attach(db,im,target):
 if target!='local':raise ValueError('Only local image attachment authorized')
 verify_image(im);authority_unchanged(db,im,True);result=base.m.original_attach(db,im,target)
 if result=='attached':
  db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
  db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',('Exact current Rijksmuseum Linked Art object, inventory, existing native creator authority and title/type/date. EDM Public Domain Mark plus either its exact primary resource or the current same-object collection page with explicit image Public Domain Mark, uncropped downloadable photograph and matching native IIIF service. Metadata CC0 is separate from image permission. Local image-only attachment; catalogue and holdings unchanged.',im['media_id']))
 return result
base.m.attach=attach

def verify():
 for im in base.prepared():verify_image(im)
 base.verify();approved={r['artwork_id'] for r in json.loads((RUN/'apply-receipt.json').read_bytes())['receipts'] if r['result']=='attached'};checks=[];held=[]
 with base.connect() as db:
  for c in json.loads((RUN/'candidates.json').read_bytes())['candidates']:
   authority_unchanged(db,c)
   if c['artwork_id'] not in approved:
    if db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(c['artwork_id'],)).fetchone()['record']!=c['before_record']:raise ValueError('Held artwork changed')
    held.append(c['artwork_id']);continue
   im=json.loads((RUN/'images'/(c['artwork_id']+'.json')).read_bytes());row=db.execute('SELECT m.creator_credit,m.attribution_text,m.rights_status,e.evidence_json,e.source_checksum FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=%s',(im['media_id'],)).fetchone()
   if any(row[k]!=im[k] for k in ['creator_credit','attribution_text','rights_status']) or row['source_checksum']!=core.sha(core.encode(im['raw'])) or row['evidence_json']!={k:v for k,v in im.items() if k not in ('artist','title')}:raise ValueError('Complete stored image evidence differs')
   checks.append(c['artwork_id'])
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
 core.save_new(RUN/'source-rights-verification.json',dict(at=core.now(),passed=True,verified=len(checks),artwork_ids=checks,creator_and_holding_evidence_unchanged=True,complete_stored_evidence_verified=True,unchanged_held_artworks=held))
 core.save_new(RUN/'report.json',dict(at=core.now(),local_only=True,reviewed=len(checks)+len(held),attached=len(checks),still_unattached=len(held),public_domain_attached=len(checks),baseline_after=baseline,all_catalogue_metadata_and_holdings_preserved=True,production_changed=False,remaining_catalogue_work=True,http_verification='No new delivery receipt following earlier server timeouts'))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','current_pages','prepare','apply','verify']);p.add_argument('--run-name',default=RUN.name);p.add_argument('--exclude-run',type=Path,action='append',default=[]);p.add_argument('--limit',type=int,default=40);a=p.parse_args()
 if not re.fullmatch(r'local-rijks-[a-z0-9-]+',a.run_name) or not 1<=a.limit<=80:p.error('Use a local-rijks operation and 1–80 selected records')
 RUN=core.ROOT/'docs/research'/a.run_name;base.RUN=RUN;EXCLUDE_RUNS=[x.resolve() for x in a.exclude_run];LIMIT=a.limit
 if a.phase=='research':research()
 elif a.phase=='current_pages':current_pages()
 elif a.phase=='prepare':
  for path in (RUN/'selected'/PROVIDER).glob('*.json'):verify_image(json.loads(path.read_bytes()))
  base.prepare(PROVIDER)
 elif a.phase=='apply':base.apply()
 else:verify()
