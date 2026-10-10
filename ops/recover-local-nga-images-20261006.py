#!/usr/bin/env python3
"""Selected local NGA recovery using current object-page primary downloads."""
import argparse,csv,functools,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup

s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('recover-local-commons-images-20261005.py'))
base=importlib.util.module_from_spec(s);s.loader.exec_module(base);core=base.core
RUN=core.ROOT/'docs/research/local-nga-native-images-20261006';base.RUN=RUN
AUDIT=RUN.parent/'local-nga-open-image-audit-20261006';PROVIDER='nga'
CC0='https://creativecommons.org/publicdomain/zero/1.0/'
POLICY='https://www.nga.gov/terms-and-notices'
core.HOSTS.add('www.nga.gov');core.VERSION='local-nga-current-primary-download-cc0-v1'

def capture(path,receipt):
 data=path.read_bytes()
 if core.sha(data)!=receipt['sha256']:raise ValueError('Pinned source capture changed')
 return data

@functools.lru_cache(maxsize=1)
def published():
 audit=json.loads((AUDIT/'discovery.json').read_bytes())
 if not audit['source_revision_current'] or audit['current_revision']!=audit['source_receipt']['revision']:raise ValueError('Source revision unverified')
 data=capture(core.ROOT/audit['source_csv_path'],audit['source_receipt'])
 ids={x['artwork']['external_id'] for x in audit['selected']}
 return {r['uuid']:r for r in csv.DictReader(data.decode('utf-8-sig').splitlines()) if r['depictstmsobjectid'] in ids}

def page_facts(soup):
 def one(selector):
  xs=soup.select(selector)
  if len(xs)!=1:raise ValueError('Native field is not unique: '+selector)
  return xs[0]
 labels={x.find('h3').get_text(' ',strip=True):x.find('p').get_text(' ',strip=True) for x in soup.select('.c-tombstone__detail') if x.find('h3') and x.find('p')}
 graph=json.loads(one('script[type="application/ld+json"]').string)['@graph']
 if len(graph)!=1 or graph[0]['@type']!='CreativeWork':raise ValueError('Native artwork schema is not unique')
 artists=soup.select('.c-artwork-header__artist-item')
 return dict(title=one('.c-artwork-header__title').get_text(' ',strip=True),date=one('.c-artwork-header__date').get_text(' ',strip=True),attribution=one('.c-artwork-header__attribution').get_text(' ',strip=True),labels=labels,schema=graph[0],artists=artists)

def verify_image(im):
 raw=im['raw'];rc=raw['page_capture'];p=core.ROOT/rc['path']
 if not p.resolve().is_relative_to((RUN/'metadata').resolve()) or rc['final_url']!=im['page']:raise ValueError('Native page identity changed')
 soup=BeautifulSoup(capture(p,rc),'html.parser');f=page_facts(soup)
 norm=base.m.norm
 if f['title']!=im['title'] or f['schema']['name']!=im['title'] or f['date']!=im['date_display']:raise ValueError('Native title/date differs')
 if f['schema']['dateCreated']!=im['date_display']:
  # The public page retains 1886/1890 while JSON-LD gives only its first
  # year. Require the exact displayed interval and matching schema start;
  # neither the catalogue range nor the source display is shortened.
  if (im['date_display']!=str(im['creation_year_start'])+'/'+str(im['creation_year_end'])
      or f['schema']['dateCreated']!=str(im['creation_year_start'])):raise ValueError('Native date schema conflicts')
 if f['labels']['Accession Number']!=im['accession_number']:raise ValueError('Native inventory differs')
 if len(im['creators'])!=1 or im['roles']!=['primary'] or len(f['artists'])!=1 or len(f['schema']['creator'])!=1:raise ValueError('Native creator is not unique')
 person=im['creators'][0];artist=f['artists'][0];link=artist.find('a',href=True)
 if norm(f['attribution'])!=norm(im['artist']) or norm(link.get_text(' ',strip=True))!=norm(im['artist']):raise ValueError('Artist attribution differs')
 if not re.match(r'/artists/'+re.escape(person['nga_id'])+r'-',link['href']):raise ValueError('Native artist authority differs')
 if f['schema']['creator'][0]['url']!='https://www.nga.gov'+link['href']:raise ValueError('Creator schema disagrees')
 if not re.match(r'(?:Artist|Painter),',artist.find('p').get_text(' ',strip=True)):raise ValueError('Qualified native role requires review')
 if not person['death'] or person['death']>1955:raise ValueError('Underlying work rights need review')
 image=raw['published_image'];known=published().get(image['uuid'])
 if known!=image or image['depictstmsobjectid']!=im['external_id'] or image['openaccess']!='1' or image['viewtype']!='primary':raise ValueError('Exact source image not open primary')
 resource='https://api.nga.gov/iiif/'+image['uuid']
 if image['iiifurl']!=resource:raise ValueError('Published primary resource differs')
 links=[a for a in soup.find_all('a',href=True) if 'download' in a.get_text(' ',strip=True).lower() and a['href'].startswith(resource+'/full/full/0/default.jpg?attachment_filename=')]
 if len(links)!=1 or 'media is not available for download' in soup.get_text(' ',strip=True):raise ValueError('Current exact open download absent or conflicting')
 if links[0]['href']!=raw['published_download_link']:raise ValueError('Reviewed primary download changed')
 if not re.match(r'https://www\.nga\.gov/artworks/'+re.escape(im['external_id'])+r'-',im['page']):raise ValueError('Native object ID differs')
 requested=resource+'/full/!1000,1000/0/default.jpg'
 if im['source_image_url']!=requested:
  redirect=raw.get('rendition_redirect',{})
  if (redirect.get('requested_url')!=requested or redirect.get('status') not in [301,302,303,307,308]
      or redirect.get('location')!=im['source_image_url'] or not re.fullmatch(re.escape(resource)+r'__\d+/full/!1000,1000/0/default\.jpg',im['source_image_url'])):raise ValueError('Unverified source rendition redirect')
 policy=raw['policy_capture'];html=capture(core.ROOT/policy['path'],policy);policy_soup=BeautifulSoup(html,'html.parser')
 if policy['url']!=POLICY or not policy_soup.find('a',href=re.compile(r'^https?://creativecommons.org/publicdomain/zero/1.0/?$')):raise ValueError('Museum CC0 policy missing')
 if 'commercial or non-commercial, under Creative Commons Zero (CC0)' not in policy_soup.get_text(' ',strip=True):raise ValueError('Current open-image CC0 grant missing')
 if (im['rights_status'],im['license_label'],im['policy_url'])!=('cc0','CC0 1.0',CC0):raise ValueError('Image licence differs')
 if im['creator_credit']!=im['artist']+'; Courtesy National Gallery of Art, Washington; '+f['labels']['Credit Line']:raise ValueError('Museum credit differs')
 if im['creator_credit'] not in im['attribution_text'] or CC0 not in im['attribution_text']:raise ValueError('Attribution missing')

def research():
 f=core.Fetcher(RUN/'metadata');audit=json.loads((AUDIT/'page-findings.json').read_bytes())['objects']
 policy_path=RUN/'metadata/policy.html'
 if not policy_path.exists():
  data,headers=f.get(POLICY,3_000_000);core.save_new(policy_path,data);core.save_new(policy_path.with_suffix('.receipt.json'),dict(url=POLICY,path=str(policy_path.relative_to(core.ROOT)),sha256=core.sha(data),at=core.now(),headers=headers))
 policy=json.loads(policy_path.with_suffix('.receipt.json').read_bytes())
 with base.connect() as db:
  ids=[x['artwork']['artwork_id'] for x in audit]
  rows=db.execute('''SELECT a.id::text artwork_id,a.title,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.accession_number,to_jsonb(a) before_record,
   e.scheme,e.external_id,e.source_id::text,
   ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) roles,
   (SELECT jsonb_agg(jsonb_build_object('name',ar.display_name,'death',ar.death_year,'nga_id',(SELECT ei.external_id FROM external_identifiers ei WHERE ei.entity_type='artist' AND ei.entity_id=ar.id AND ei.scheme='nga-constituent')) ORDER BY ar.id) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id) creators,
   (SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creator_links,
   (SELECT jsonb_agg(to_jsonb(ei) ORDER BY ei.id) FROM external_identifiers ei WHERE ei.entity_type='artwork' AND ei.entity_id=a.id) identifiers
   FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='european-nga-object'
   WHERE a.id=ANY(%s::uuid[]) AND a.primary_media_id IS NULL AND a.status='review' AND a.current_institution_id='4a7cf367-a105-f2bf-dc1c-a2210974752e'
   AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' AND artline_has_selection_evidence(a.id)''',(ids,)).fetchall()
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
 for c in rows:c.update(artist='; '.join(x['name'] for x in c['creators']),target_ids={'local':c['artwork_id']})
 if not (RUN/'candidates.json').exists():core.save_new(RUN/'candidates.json',dict(at=core.now(),baseline=baseline,candidates=rows))
 else:rows=json.loads((RUN/'candidates.json').read_bytes())['candidates']
 byid={x['artwork']['artwork_id']:x for x in audit}
 for c in rows:
  dest=RUN/'selected'/PROVIDER/(c['artwork_id']+'.json')
  if dest.exists():verify_image(json.loads(dest.read_bytes()));continue
  lead=byid[c['artwork_id']];original=core.ROOT/lead['capture'];rc=json.loads(original.with_suffix('.receipt.json').read_bytes());copy=RUN/'metadata'/original.name
  core.save_new(copy,capture(original,rc));rc.update(path=str(copy.relative_to(core.ROOT)),copied_from=lead['capture']);core.save_new(copy.with_suffix('.receipt.json'),rc)
  if len(lead['index_primary_ids_present_on_page'])!=1:raise ValueError('Current native primary is not unique')
  image=published()[lead['index_primary_ids_present_on_page'][0]];url=image['iiifurl']+'/full/!1000,1000/0/default.jpg'
  facts=page_facts(BeautifulSoup(copy.read_bytes(),'html.parser'));credit=c['artist']+'; Courtesy National Gallery of Art, Washington; '+facts['labels']['Credit Line']
  raw=dict(page_capture=rc,policy_capture=policy,published_image=image,published_download_link=next(u for u in lead['published_download_links'] if u.startswith(image['iiifurl']+'/')))
  im=dict(c,provider=PROVIDER,page=rc['final_url'],source_image_url=url,raw=raw,creator_credit=credit,rights_status='cc0',license_label='CC0 1.0',policy_url=CC0,checked_at=core.now(),attribution_text=f"{c['artist']}. {c['title']}, {c['date_display']}. {c['accession_number']}. {credit}. CC0 ({CC0}). {rc['final_url']}. Full-frame proportional resize and JPEG compression.")
  verify_image(im)
  core.provider_rate_slot('api.nga.gov');head=f.session.head(url,timeout=(15,30),allow_redirects=False)
  if head.status_code in [301,302,303,307,308]:
   im['source_image_url']=head.headers['Location'];raw['rendition_redirect']=dict(requested_url=url,status=head.status_code,location=im['source_image_url'],retrieved_at=core.now())
  elif head.status_code!=200:raise ValueError('Image service response needs review: '+str(head.status_code))
  head.close();verify_image(im);core.save_new(dest,im);core.event(RUN,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='rights_selected'))
  print('Selected exact current NGA image:',c['title'],c['accession_number'],flush=True)

def attach(db,im,target):
 if target!='local':raise ValueError('Only local image attachment authorized')
 verify_image(im);result=base.m.original_attach(db,im,target)
 if result=='attached':
  db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
  db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',('Current exact object-page download resolves the multiple primary-image rows; published openaccess=1, museum CC0 policy, exact inventory, date and native creator ID.',im['media_id']))
 return result
base.m.attach=attach
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='research':research()
 elif a.phase=='prepare':
  for path in (RUN/'selected'/PROVIDER).glob('*.json'):verify_image(json.loads(path.read_bytes()))
  base.prepare(PROVIDER)
 elif a.phase=='apply':base.apply()
 else:
  for im in base.prepared():verify_image(im)
  base.verify()
