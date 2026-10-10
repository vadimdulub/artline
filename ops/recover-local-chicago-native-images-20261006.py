#!/usr/bin/env python3
"""Selected image-only Chicago recovery against current object/photo authorities."""
import argparse,collections,importlib.util,json,re
import requests
from pathlib import Path
from urllib.parse import urlencode,urlparse,parse_qs,urljoin
from bs4 import BeautifulSoup

def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=module('base','recover-local-commons-images-20261005.py');check=module('check','popular-chicago-verification.py');core=base.core
RUN=core.ROOT/'docs/research/local-chicago-native-images-20261006';base.RUN=RUN
AUDIT=RUN.parent/'local-chicago-native-audit-20261006'
PROVIDER='chicago-native';core.PROVIDERS[PROVIDER]='Art Institute of Chicago';core.VERSION='local-chicago-exact-image-only-v1'
FIELDS='id,title,alt_titles,artist_id,artist_ids,artist_title,artist_display,artist_pivots,date_display,date_start,date_end,main_reference_number,artwork_type_title,classification_title,classification_titles,medium_display,dimensions,credit_line,is_public_domain,copyright_notice,image_id,department_title,fiscal_year_deaccession'
ARTIST_FIELDS='id,title,alt_titles,is_artist,birth_date,death_date'
IMAGE_FIELDS='id,type,credit_line,iiif_url,artwork_ids,width,height'
SCHEMES=['aic-object',check.SCHEME]
LIMIT=40;EXCLUDE_RUNS=[]

def select():
 if (RUN/'candidates.json').exists():return
 discovery=json.loads((AUDIT/'discovery.json').read_bytes());leads=collections.defaultdict(set)
 for lead in discovery['open_image_leads']:
  aids={x['artwork_id'] for x in lead['local_matches']}
  if len(aids)==1:leads[next(iter(aids))].add(str(lead['native']['id']))
 ids=[aid for aid,oids in leads.items() if len(oids)==1]
 excluded=sorted({c['artwork_id'] for run in EXCLUDE_RUNS for c in json.loads((run/'candidates.json').read_bytes())['candidates']})
 with base.connect() as db:
  chosen=db.execute('''WITH eligible AS (
   SELECT a.id,aa.artist_id,a.creation_year_start,a.work_type,
    EXISTS(SELECT 1 FROM artist_countries ac WHERE ac.artist_id=aa.artist_id AND ac.country_code IN ('RU','GR','CY')) priority,
    EXISTS(SELECT 1 FROM artist_discovery_selection ds WHERE ds.artist_id=aa.artist_id AND ds.is_popular) popular,
    row_number() OVER(PARTITION BY aa.artist_id ORDER BY (a.work_type='drawing') DESC,a.creation_year_start,a.id) creator_rank
   FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id
   JOIN institutions i ON i.id=a.current_institution_id
   WHERE a.id=ANY(%s::uuid[]) AND NOT(a.id=ANY(%s::uuid[]))
    AND i.slug='art-institute-of-chicago' AND a.primary_media_id IS NULL AND a.status='review'
    AND aa.attribution_role='primary' AND NOT EXISTS(SELECT 1 FROM artwork_artists other WHERE other.artwork_id=a.id AND other.artist_id<>aa.artist_id)
    AND EXISTS(SELECT 1 FROM external_identifiers ei WHERE ei.entity_type='artist' AND ei.entity_id=aa.artist_id AND ei.scheme='wikidata')
    AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' AND artline_has_selection_evidence(a.id))
   SELECT id::text FROM eligible WHERE creator_rank<=3 ORDER BY priority DESC,creator_rank,popular DESC,creation_year_start,id LIMIT %s''',(ids,excluded,LIMIT)).fetchall()
  ids=[r['id'] for r in chosen]
  rows=db.execute('''SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,a.accession_number,to_jsonb(a) before_record,
   i.id::text institution_id,i.slug institution_slug,i.name museum,e.scheme,e.external_id,e.source_id::text,e.canonical_url page,
   ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) roles,
   (SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creator_links,
   (SELECT jsonb_agg(to_jsonb(ei) ORDER BY ei.id) FROM external_identifiers ei WHERE ei.entity_type='artwork' AND ei.entity_id=a.id) identifiers,
   COALESCE((SELECT jsonb_agg(to_jsonb(la) ORDER BY la.id) FROM artwork_location_assertions la WHERE la.artwork_id=a.id),'[]') holding_assertions
   FROM artworks a JOIN institutions i ON i.id=a.current_institution_id
   JOIN LATERAL(SELECT * FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme=ANY(%s) ORDER BY e.scheme LIMIT 1) e ON true
   WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',(SCHEMES,ids)).fetchall()
  artist_ids=sorted({c['creator_links'][0]['artist_id'] for c in rows})
  artists={r['record']['id']:r['record'] for r in db.execute('SELECT to_jsonb(ar) record FROM artists ar WHERE id=ANY(%s::uuid[])',(artist_ids,)).fetchall()}
  identifiers=collections.defaultdict(list);aliases=collections.defaultdict(list)
  for r in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(artist_ids,)).fetchall():identifiers[r['record']['entity_id']].append(r['record'])
  for r in db.execute('SELECT to_jsonb(al) record FROM artist_aliases al WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id,id',(artist_ids,)).fetchall():aliases[r['record']['artist_id']].append(r['record'])
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
  for c in rows:
   if len(c['creator_links'])!=1 or c['roles']!=['primary'] or not c['source_id'] or leads[c['artwork_id']]!={c['external_id']}:raise ValueError('Selected catalogue identity is not unique')
   aid=c['creator_links'][0]['artist_id'];proof=dict(artist_record=artists[aid],artist_identifiers=identifiers[aid],artist_aliases=aliases[aid])
   c.update(provider=PROVIDER,artist=artists[aid]['display_name'],creator_authorities=[proof],target_ids={'local':c['artwork_id']})
 if not 1<=len(rows)<=LIMIT:raise ValueError('No bounded native selection')
 core.save_new(RUN/'candidates.json',dict(at=core.now(),baseline=baseline,candidates=rows,discovery=str(AUDIT.relative_to(core.ROOT)),discovery_sha256=core.sha((AUDIT/'discovery.json').read_bytes()),excluded_runs=[str(p.relative_to(core.ROOT)) for p in EXCLUDE_RUNS],selection='Exact existing native IDs with potential open images; up to three per creator, priority countries first, then creator breadth/popularity. Full native and image validation follows.'))
 print('Selected existing gaps:',len(rows),'artists:',len(artist_ids),flush=True)

def batch(fetch,endpoint,ids,fields,include=None):
 if not ids:return {},{}
 if len(ids)>100:raise ValueError('Native request exceeds bounded ID batch')
 params=dict(ids=','.join(map(str,ids)),fields=fields,limit=100)
 if include:params['include']=include
 url='https://api.artic.edu/api/v1/'+endpoint+'?'+urlencode(params);data=fetch.metadata(url)
 receipt=json.loads((fetch.cache/(core.sha(url.encode())+'.receipt.json')).read_bytes());objects=data['data']
 if len({str(x['id']) for x in objects})!=len(objects) or any(str(x['id']) not in set(map(str,ids)) for x in objects):raise ValueError('Returned native IDs differ')
 return {str(x['id']):x for x in objects},{str(x['id']):receipt for x in objects}

def captured(receipt,endpoint,ident):
 url=receipt['url'];parsed=urlparse(url)
 if parsed.scheme!='https' or parsed.netloc!='api.artic.edu' or parsed.path!='/api/v1/'+endpoint or str(ident) not in parse_qs(parsed.query)['ids'][0].split(','):raise ValueError('Native capture endpoint/identity differs')
 path=RUN/'metadata'/(core.sha(url.encode())+'.json');data=path.read_bytes()
 if core.sha(data)!=receipt['sha256'] or len(data)!=receipt['bytes'] or json.loads(path.with_suffix('.receipt.json').read_bytes())!=receipt:raise ValueError('Pinned current native capture changed')
 rows=[x for x in json.loads(data)['data'] if str(x['id'])==str(ident)]
 if len(rows)!=1:raise ValueError('Exact source object is absent or ambiguous')
 return rows[0]

def current_page(c,fetch):
 path=RUN/'metadata/current-pages'/(c['external_id']+'.html');url='https://www.artic.edu/artworks/'+c['external_id']
 if path.exists():return path.read_bytes(),json.loads(path.with_suffix('.receipt.json').read_bytes())
 target=url;redirects=[]
 for _ in range(4):
  parsed=urlparse(target)
  if parsed.scheme!='https' or parsed.netloc!='www.artic.edu' or not re.fullmatch('/artworks/'+c['external_id']+'(?:/[^/?]+)?',parsed.path) or parsed.query:raise ValueError('Unexpected native collection redirect')
  core.provider_rate_slot('www.artic.edu');response=fetch.session.get(target,timeout=(15,45),allow_redirects=False)
  if response.status_code in (301,302,303,307,308):
   redirects.append(dict(url=target,status=response.status_code,location=response.headers['Location']));target=urljoin(target,response.headers['Location']);continue
  if response.status_code!=200:raise ValueError('Current native page HTTP '+str(response.status_code))
  data=response.content
  if len(data)>5_000_000:raise ValueError('Native page exceeds response budget')
  rc=dict(url=target,requested_url=url,redirects=redirects,at=core.now(),bytes=len(data),sha256=core.sha(data),path=str(path.relative_to(core.ROOT)))
  core.save_new(path,data);core.save_new(path.with_suffix('.receipt.json'),rc);return data,rc
 raise ValueError('Too many native redirects')

def page_image(o,resource,html):
 # Current /images responses omit credit_line. The exact gallery button on
 # the native artwork page still carries a photograph-specific CC0 grant.
 iid=o.get('image_id');service='https://www.artic.edu/iiif/2/'+str(iid)
 if o.get('is_public_domain') is not True or o.get('copyright_notice') or not isinstance(iid,str) or not re.fullmatch(r'[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}',iid):raise ValueError('No clear public-domain primary image')
 if resource.get('id')!=iid or resource.get('type')!='image' or resource.get('credit_line') not in (None,'CC0 Public Domain Designation') or resource.get('iiif_url') not in ('/'+iid,service) or resource.get('artwork_ids')!=[o['id']]:raise ValueError('Exact image association or resource credit conflicts')
 if not all(type(resource.get(k)) is int and resource[k]>0 for k in ('width','height')):raise ValueError('Native image dimensions missing')
 soup=BeautifulSoup(html,'html.parser');title=soup.find('h1')
 if title is None or check.norm(title.get_text(' ',strip=True))!=check.norm(o['title']):raise ValueError('Current artwork page title differs')
 canonical=soup.find('link',rel='canonical');pattern='https://www.artic.edu/artworks/'+str(o['id'])+'(?:/[^/?]+)?'
 if canonical is None or not re.fullmatch(pattern,canonical.get('href','')):raise ValueError('Current page canonical object differs')
 buttons=soup.select('button[data-gallery-img-iiifid]');matches=[b for b in buttons if b['data-gallery-img-iiifid']==service]
 if len(matches)!=1:raise ValueError('Exact current page photograph is absent or ambiguous')
 button=matches[0];grant=button.get('data-gallery-img-credit');licence=button.get('data-gallery-img-credit-url');download=button.get('data-gallery-img-download-url')
 if grant!='CC0 Public Domain Designation' or licence not in (None,'/image-licensing') or download!=service+'/full/!3000,3000/0/default.jpg':raise ValueError('Current exact photograph lacks explicit CC0 download grant')
 if licence is None:
  # Some native pages render the primary-photo CC0 credit as plain text.
  # Require both photo-specific labels and an explicit same-page policy link.
  credits=soup.select('[data-gallery-credit]');main=soup.find('main')
  if len(credits)!=1 or credits[0].get_text(' ',strip=True)!='CC0 Public Domain Designation' or main is None or main.find('a',href='/image-licensing') is None:raise ValueError('Unlinked gallery credit lacks corroborating primary-photo grant and policy reference')
 if not button.get('data-gallery-img-download-name','').startswith(o['main_reference_number']+' - '):raise ValueError('Native download inventory differs')
 if any(button.get('data-gallery-img-'+k)!=str(resource[k]) for k in ('width','height')):raise ValueError('Current page image dimensions differ')
 meta=soup.find('meta',property='og:image');url=service+'/full/843,/0/default.jpg'
 if meta is None or meta.get('content')!=url:raise ValueError('Native page primary image differs')
 result=dict(source_image_url=url,image_id=iid,grant=grant,licensing_path=licence,download_url=download,download_name=button['data-gallery-img-download-name'],canonical_url=canonical['href'])
 if licence is None:result['licensing_basis']='Matching photo-specific CC0 gallery and primary-image labels, plus an explicit same-page image-policy link and separately captured native policy.'
 return result

def policy_evidence():
 path=RUN/'metadata/current-pages/image-licensing.html';rc=json.loads(path.with_suffix('.receipt.json').read_bytes());data=path.read_bytes()
 if rc['url']!='https://www.artic.edu/image-licensing' or core.sha(data)!=rc['sha256']:raise ValueError('Pinned native image policy changed')
 soup=BeautifulSoup(data,'html.parser');text=soup.get_text(' ',strip=True)
 if not all(x in text for x in ('CC0 Public Domain Designation','for any purpose, including commercial and noncommercial uses','free of charge and without additional permission from the museum')):raise ValueError('Exact label-specific image policy absent')
 if not soup.find('a',href=check.CC0):raise ValueError('Native image policy lacks exact CC0 link')
 return rc

def facts(c,o,person):
 if len(c['creator_authorities'])!=1 or len(c['creator_links'])!=1 or c['roles']!=['primary']:raise ValueError('Single unqualified local creator required')
 proof=c['creator_authorities'][0];artist=proof['artist_record']
 if c['creator_links'][0]['artist_id']!=artist['id']:raise ValueError('Local creator authority differs')
 qids=[x['external_id'] for x in proof['artist_identifiers'] if x['scheme']=='wikidata']
 if len(qids)!=1 or not re.fullmatch('Q[1-9][0-9]*',qids[0]):raise ValueError('Existing independent creator authority missing or ambiguous')
 authority=dict(artist,aliases=[x['alias'] for x in proof['artist_aliases']],qid=qids[0])
 if str(o['id'])!=c['external_id'] or c['institution_slug']!=check.SLUG:raise ValueError('Exact native object/institution differs')
 if {x['external_id'] for x in c['identifiers'] if x['scheme'] in SCHEMES}!={c['external_id']}:raise ValueError('Local native identifiers conflict')
 result=check.metadata(o,authority,person)
 for key in ('accession_number','creation_year_start','creation_year_end','date_precision','work_type'):
  if c[key]!=result[key]:raise ValueError('Current native '+key+' differs; preserve catalogue for individual review')
 titles={check.norm(x) for x in [o['title'],*(o.get('alt_titles') or [])]}
 if check.norm(c['title']) not in titles:raise ValueError('Current native title differs; exact work needs review')
 if not check.same_date_wording(c['date_display'],result['date_display']):raise ValueError('Current native date wording differs; retain source and catalogue dates')
 for local,native in [('birth_year','birth_date'),('death_year','death_date')]:
  if artist[local] is not None and person.get(native) is not None and artist[local]!=person[native]:raise ValueError('Known artist life year differs')
 return result

def delivery_failure(im,delivery):
 failed=delivery['previous_failure'];receipt=delivery.get('previous_failure_capture')
 if receipt:
  path=core.ROOT/receipt['path']
  if not path.resolve().is_relative_to((RUN/'metadata/prior-delivery').resolve()):raise ValueError('Previous delivery evidence is outside the pinned operation')
  data=path.read_bytes()
  if core.sha(data)!=receipt['sha256'] or len(data)!=receipt['bytes']:raise ValueError('Archived previous delivery evidence differs')
  events=[json.loads(line) for line in data.decode().splitlines()]
 else:events=[json.loads(line) for line in (RUN/'events.jsonl').read_text().splitlines()]
 if failed not in events or failed.get('artwork_id')!=im['artwork_id'] or failed.get('outcome')!='download_deferred' or failed.get('reason')!='403 Client Error: Forbidden for url: '+delivery['original_source_image_url']:raise ValueError('Original image-delivery failure is not preserved')
 return failed

def verify_image(im):
 raw=im['raw'];o=captured(raw['object_capture'],'artworks',im['external_id']);person=captured(raw['artist_capture'],'artists',o['artist_id']);resource=captured(raw['image_capture'],'images',o['image_id'])
 if (o,person,resource)!=(raw['object'],raw['artist'],raw['image']):raise ValueError('Exact native object, creator or image evidence differs')
 if facts(im,o,person)!=raw['native_facts']:raise ValueError('Source metadata evidence differs')
 current=raw.get('current_collection_page')
 if current:
  rc=current['receipt'];path=RUN/'metadata/current-pages'/(im['external_id']+'.html');html=path.read_bytes()
  if rc!=json.loads(path.with_suffix('.receipt.json').read_bytes()) or core.sha(html)!=rc['sha256'] or len(html)!=rc['bytes'] or rc['requested_url']!='https://www.artic.edu/artworks/'+im['external_id']:raise ValueError('Pinned native page capture changed')
  image_facts=page_image(o,resource,html)
  if current['facts']!=image_facts or raw['native_image_policy']!=policy_evidence():raise ValueError('Exact current image grant or source policy changed')
  url=image_facts['source_image_url']
  delivery=raw.get('native_download_selection')
  if delivery:
   if delivery['original_source_image_url']!=url or delivery['source_image_url']!=image_facts['download_url'] or delivery['image_id']!=o['image_id']:raise ValueError('Native download is not the exact licensed gallery photograph')
   delivery_failure(im,delivery)
   url=image_facts['download_url']
 else:
  if raw.get('native_download_selection'):raise ValueError('Native gallery download requires a captured current artwork page')
  url=check.image(o,resource)
 page='https://www.artic.edu/artworks/'+str(o['id']);credit=im['artist']+'; Art Institute of Chicago'
 if (im['source_image_url'],im['page'],im['rights_status'],im['policy_url'],im['license_label'],im['creator_credit'])!=(url,page,'cc0',check.CC0,'CC0 1.0',credit):raise ValueError('Source image, exact CC0 grant or credit differs')
 if any(x not in im['attribution_text'] for x in [credit,check.CC0,page,o['credit_line']]):raise ValueError('Native collection credit or image attribution missing')

def research(use_pages=False):
 select();rows=json.loads((RUN/'candidates.json').read_bytes())['candidates'];fetch=core.Fetcher(RUN/'metadata');fetch.defer_long_cooldowns=True
 if use_pages and not (RUN/'metadata/current-pages/image-licensing.html').exists():
  url='https://www.artic.edu/image-licensing';data,headers=fetch.get(url,5_000_000);path=RUN/'metadata/current-pages/image-licensing.html'
  core.save_new(path,data);core.save_new(path.with_suffix('.receipt.json'),dict(url=url,at=core.now(),bytes=len(data),sha256=core.sha(data),headers=headers,path=str(path.relative_to(core.ROOT))))
 if use_pages:policy_evidence()
 objects,orc=batch(fetch,'artworks',[c['external_id'] for c in rows],FIELDS,'artist_pivots')
 people,prc=batch(fetch,'artists',sorted({o['artist_id'] for o in objects.values() if o.get('artist_id')}),ARTIST_FIELDS)
 image_ids=sorted({o['image_id'] for o in objects.values() if o.get('image_id')});images={};irc={}
 for start in range(0,len(image_ids),20):
  items,receipts=batch(fetch,'images',image_ids[start:start+20],IMAGE_FIELDS);images.update(items);irc.update(receipts)
 done=core.latest_events(RUN)
 for c in rows:
  path=RUN/'selected'/PROVIDER/(c['artwork_id']+'.json')
  if path.exists():verify_image(json.loads(path.read_bytes()));continue
  if c['artwork_id'] in done and not use_pages:continue
  try:
   o=objects[c['external_id']];person=people[str(o['artist_id'])];resource=images[o['image_id']];native=facts(c,o,person);extra={}
   if use_pages:
    html,page_rc=current_page(c,fetch);review=page_image(o,resource,html);url=review['source_image_url'];extra=dict(current_collection_page=dict(receipt=page_rc,facts=review),native_image_policy=policy_evidence())
   else:url=check.image(o,resource)
   page='https://www.artic.edu/artworks/'+c['external_id'];credit=c['artist']+'; Art Institute of Chicago'
   im=dict(c,page=page,source_image_url=url,rights_status='cc0',license_label='CC0 1.0',policy_url=check.CC0,creator_credit=credit,checked_at=extra['current_collection_page']['receipt']['at'] if use_pages else irc[o['image_id']]['retrieved_at'],raw=dict(object=o,artist=person,image=resource,object_capture=orc[c['external_id']],artist_capture=prc[str(o['artist_id'])],image_capture=irc[o['image_id']],native_facts=native,**extra),attribution_text=f"{c['artist']}. {c['title']}, {c['date_display']}. Inventory {c['accession_number']}. {credit}. Collection credit: {o['credit_line']}. CC0 1.0 ({check.CC0}). {page}. Full-frame proportional resize and JPEG compression.")
   if check.norm(c['date_display'])!=check.norm(native['date_display']):
    im['attribution_text']+=f" Source date wording {native['date_display']!r} and existing catalogue wording {c['date_display']!r} express the same interval; the catalogue wording is preserved."
   verify_image(im);core.save_new(path,im);core.event(RUN,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='rights_selected'));print('Selected CC0:',c['artist'],c['title'],flush=True)
  except (ValueError,KeyError,requests.RequestException) as error:
   core.event(RUN,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='manual_review',reason=str(error)));print('Held:',c['artist'],c['title'],str(error),flush=True)

def native_downloads():
 """Select the museum's explicitly published download for a failed preview URL."""
 events=core.latest_events(RUN);selected=0
 for path in sorted((RUN/'selected'/PROVIDER).glob('*.json')):
  im=json.loads(path.read_bytes())
  if (RUN/'images'/path.name).exists() or im['raw'].get('native_download_selection'):continue
  prior=im.get('previous_download_failure');failed=prior['event'] if prior else events.get(im['artwork_id'],{})
  if failed.get('outcome')!='download_deferred' or failed.get('reason')!='403 Client Error: Forbidden for url: '+im['source_image_url']:continue
  verify_image(im);current=im['raw'].get('current_collection_page')
  if not current:continue
  delivery=dict(original_source_image_url=im['source_image_url'],source_image_url=current['facts']['download_url'],image_id=im['raw']['object']['image_id'],previous_failure=failed)
  if prior:delivery['previous_failure_capture']=prior['capture']
  im['source_image_url']=delivery['source_image_url'];im['raw']['native_download_selection']=delivery;verify_image(im)
  core.save_new(RUN/'history/before-native-download'/path.name,path.read_bytes());path.write_bytes(core.encode(im));selected+=1
  core.event(RUN,dict(provider=PROVIDER,artwork_id=im['artwork_id'],outcome='native_gallery_download_selected',reason='Use the exact public download button already captured and explicitly licensed for the same photograph; original preview-URL failure retained.'))
 print('Exact native gallery download URLs selected:',selected,flush=True)

def authority_unchanged(db,c,lock=False):
 suffix=' FOR SHARE' if lock else ''
 for proof in c['creator_authorities']:
  aid=proof['artist_record']['id'];artist=db.execute('SELECT to_jsonb(ar) record FROM artists ar WHERE id=%s'+suffix,(aid,)).fetchone()['record']
  ids=[r['record'] for r in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=%s ORDER BY id"+suffix,(aid,)).fetchall()]
  aliases=[r['record'] for r in db.execute('SELECT to_jsonb(al) record FROM artist_aliases al WHERE artist_id=%s ORDER BY id'+suffix,(aid,)).fetchall()]
  if artist!=proof['artist_record'] or ids!=proof['artist_identifiers'] or aliases!=proof['artist_aliases']:raise ValueError('Creator authority changed')
 holding=[r['record'] for r in db.execute('SELECT to_jsonb(la) record FROM artwork_location_assertions la WHERE artwork_id=%s ORDER BY id'+suffix,(c['artwork_id'],)).fetchall()]
 if holding!=c['holding_assertions']:raise ValueError('Holding evidence changed')

def attach(db,im,target):
 if target!='local':raise ValueError('Only local image attachment authorized')
 verify_image(im);verify_view(im);verify_identity_review(im);authority_unchanged(db,im,True);result=base.m.original_attach(db,im,target)
 if result=='attached':
  db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
  if im.get('alt_text'):
   db.execute('UPDATE media_assets SET alt_text=%s WHERE id=%s',(im['alt_text'],im['media_id']))
  if im.get('view_label'):
   db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,%s) ON CONFLICT(artwork_id,media_id) DO NOTHING',(im['artwork_id'],im['media_id'],im['view_label']))
  db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',('Exact current Chicago object, inventory, title/type/date, unique unqualified native creator matched by existing name/aliases and life dates with unchanged independent authority. Exact primary image resource has a unique association to this object. Photograph-specific CC0 Public Domain Designation is verified on the image resource or exact current native gallery download button, corroborated by the captured native image policy. Metadata CC0 is separate from the verified image grant. Image-only attachment; catalogue, artist and holding assertions unchanged.',im['media_id']))
 return result
base.m.attach=attach

def verify_view(im):
 path=RUN/'view-scope-review.json';rows=json.loads(path.read_bytes())['images'] if path.exists() else []
 matched=[x for x in rows if x['artwork_id']==im['artwork_id']]
 # WikiArt also uses this view guard and has no Chicago object payload.
 paired_images=all(label in (im['raw'].get('object',{}).get('dimensions') or '') for label in ('Left image:','Right image:'))
 if (re.search(r'\b(?:recto|verso)\b',im['title'],re.I) or re.match(r'^(?:sketchbook|album)\b',im['title'],re.I) or re.match(r'^Page \d+ and Page \d+\b',im['title'],re.I) or paired_images) and len(matched)!=1:raise ValueError('Two-sided or compound artwork requires an explicit inspected image-view decision')
 if matched:
  if len(matched)!=1:raise ValueError('Ambiguous inspected image view')
  view=matched[0]
  if any(im[k]!=view[k] for k in ('source_image_url','source_sha256','sha256','view_label','alt_text')) or im['raw'].get('view_scope_review')!=view or view['note'] not in im['attribution_text']:raise ValueError('Inspected image view or qualification differs')
 elif im.get('view_label') or im['raw'].get('view_scope_review'):raise ValueError('Unexpected image view qualification')

def verify_identity_review(im):
 if im['artwork_id']!='cf250aa7-8470-574a-b966-73e0e450b2b3':
  if im['raw'].get('source_identity_review'):raise ValueError('Unreviewed native title concordance')
  return
 review=json.loads((RUN/'rousseau-title-review.json').read_bytes())
 if (im['external_id'],im['title'],im['accession_number'],im['raw']['object']['image_id'])!=('186406','Oak Branch','2013.1019','a72c7248-28af-7527-b067-70f2db93b1f1'):raise ValueError('Individual Rousseau title case differs')
 if any(im[k]!=review[k] for k in ('artwork_id','source_image_url','source_sha256','sha256','alt_text')) or im['raw'].get('source_identity_review')!=review or review['note'] not in im['attribution_text']:raise ValueError('Rousseau photograph or title qualification differs')
 page=im['raw']['current_collection_page']['receipt'];html=(RUN/'metadata/current-pages/186406.html').read_bytes()
 if core.sha(html)!=review['native_page_sha256'] or page['sha256']!=review['native_page_sha256']:raise ValueError('Rousseau native caption capture differs')
 text=BeautifulSoup(html,'html.parser').find('main').get_text(' ',strip=True)
 if not all(x in text for x in ('this rare drawing was a gift from the artist','Mademoiselle Herminie','daisies','Pour Mlle. Herminie/Sincère amitié H. Rousseau')):raise ValueError('Native description and inscribed dedication do not corroborate the flower image')

def verify():
 for im in base.prepared():verify_image(im);verify_view(im);verify_identity_review(im)
 base.verify();approved={r['artwork_id'] for r in json.loads((RUN/'apply-receipt.json').read_bytes())['receipts'] if r['result']=='attached'};checks=[];held=[]
 with base.connect() as db:
  for c in json.loads((RUN/'candidates.json').read_bytes())['candidates']:
   authority_unchanged(db,c)
   if c['artwork_id'] not in approved:
    if db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(c['artwork_id'],)).fetchone()['record']!=c['before_record']:raise ValueError('Held artwork changed')
    held.append(c['artwork_id']);continue
   im=json.loads((RUN/'images'/(c['artwork_id']+'.json')).read_bytes());row=db.execute('SELECT m.creator_credit,m.attribution_text,m.rights_status,e.evidence_json,e.source_checksum FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=%s',(im['media_id'],)).fetchone()
   if any(row[k]!=im[k] for k in ['creator_credit','attribution_text','rights_status']) or row['source_checksum']!=core.sha(core.encode(im['raw'])) or row['evidence_json']!={k:v for k,v in im.items() if k not in ('artist','title')}:raise ValueError('Complete stored image evidence differs')
   if im.get('view_label'):
    view=db.execute('SELECT m.alt_text,am.view_label FROM media_assets m JOIN artwork_media am ON am.media_id=m.id WHERE m.id=%s AND am.artwork_id=%s',(im['media_id'],im['artwork_id'])).fetchone()
    if view!=dict(alt_text=im['alt_text'],view_label=im['view_label']):raise ValueError('Explicit image view not preserved in database')
   elif im.get('alt_text'):
    if db.execute('SELECT alt_text FROM media_assets WHERE id=%s',(im['media_id'],)).fetchone()['alt_text']!=im['alt_text']:raise ValueError('Source identity qualification omitted from accessible image text')
   checks.append(c['artwork_id'])
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
 core.save_new(RUN/'source-rights-verification.json',dict(at=core.now(),passed=True,verified=len(checks),artwork_ids=checks,creator_aliases_authorities_and_holding_evidence_unchanged=True,complete_stored_evidence_verified=True,unchanged_held_artworks=held))
 core.save_new(RUN/'report.json',dict(at=core.now(),local_only=True,reviewed=len(checks)+len(held),attached=len(checks),still_unattached=len(held),cc0_attached=len(checks),baseline_after=baseline,all_catalogue_metadata_and_holdings_preserved=True,production_changed=False,remaining_catalogue_work=True,http_verification='No new delivery receipt following earlier server timeouts'))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','current_pages','native_downloads','prepare','apply','verify']);p.add_argument('--run-name',default=RUN.name);p.add_argument('--exclude-run',type=Path,action='append',default=[]);p.add_argument('--limit',type=int,default=40);a=p.parse_args()
 if not re.fullmatch('local-chicago-[a-z0-9-]+',a.run_name) or not 1<=a.limit<=60:p.error('Use a local-chicago operation and 1–60 selected records')
 RUN=core.ROOT/'docs/research'/a.run_name;base.RUN=RUN;LIMIT=a.limit;EXCLUDE_RUNS=[x.resolve() for x in a.exclude_run]
 if a.phase=='research':research()
 elif a.phase=='current_pages':research(True)
 elif a.phase=='native_downloads':native_downloads()
 elif a.phase=='prepare':
  for path in (RUN/'selected'/PROVIDER).glob('*.json'):verify_image(json.loads(path.read_bytes()))
  base.prepare(PROVIDER)
 elif a.phase=='apply':base.apply()
 else:verify()
