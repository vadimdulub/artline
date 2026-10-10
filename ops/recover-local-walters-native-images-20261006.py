#!/usr/bin/env python3
"""Selected local Walters images from exact inventory pages and CC0 downloads."""
import argparse,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlparse,parse_qs,unquote
from bs4 import BeautifulSoup

s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('recover-local-commons-images-20261005.py'))
base=importlib.util.module_from_spec(s);s.loader.exec_module(base);core=base.core
RUN=core.ROOT/'docs/research/local-walters-native-images-20261006';base.RUN=RUN
PROVIDER='walters-native';core.PROVIDERS[PROVIDER]='The Walters Art Museum'
core.HOSTS.add('art.thewalters.org');core.VERSION='local-walters-exact-native-cc0-v1'
CC0='https://creativecommons.org/publicdomain/zero/1.0/'
IID='d7fa70fa-a918-511f-8cc0-eeff020ceaea'
ICON='72649460-5d32-5515-be41-a29d0673e88c'
QUALIFICATION_NOTICE="The museum's creator line includes '(?)'; the attribution remains subject to editorial review."

def clean(text):return ' '.join(text.split())

def creator_matches(im,native_name):
 return base.m.norm(native_name)==base.m.norm(im['creators'][0]['name'])

def creator_role_matches(im,name,author_text):
 return author_text in (name+' (Painter)',name+' (Artist)')

def select_photo(im,images):return images[0]

def decorate_image(im):return im

def front_image_matches(im,filename):return '_Fnt_' in filename

def inventory_image_matches(im,filename):
 return bool(re.search(r'(?:^|_)'+re.escape(im['accession_number'])+r'(?:_|\.)',filename))

def parse_creation_date(im,date):
 m=re.fullmatch(r'(ca\.\s*)?(\d{4})(?:[-–](\d{4}))?',date)
 if not m:raise ValueError('Native date wording needs individual review')
 lo=int(m[2]);hi=int(m[3] or m[2]);precision=('circa' if lo==hi else 'circa_range') if m[1] else ('exact' if lo==hi else 'range')
 return lo,hi,precision

def select(limit):
 if (RUN/'candidates.json').exists():return
 with base.connect() as db:
  rows=db.execute('''SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end,a.date_display,a.date_precision,a.work_type,a.object_form,a.unlinked_creator_label,a.accession_number,to_jsonb(a) before_record,i.slug institution_slug,i.name museum,i.id::text institution_id,e.scheme,e.external_id,e.source_id::text,e.canonical_url page,
   ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) roles,
   COALESCE((SELECT jsonb_agg(jsonb_build_object('name',ar.display_name,'birth',ar.birth_year,'death',ar.death_year) ORDER BY ar.id) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') creators,
   COALESCE((SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') creator_links,
   (SELECT jsonb_agg(to_jsonb(ei) ORDER BY ei.id) FROM external_identifiers ei WHERE ei.entity_type='artwork' AND ei.entity_id=a.id) identifiers
   FROM artworks a JOIN institutions i ON i.id=a.current_institution_id JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='walters-object'
   WHERE a.current_institution_id=%s AND a.primary_media_id IS NULL AND a.status='review' AND e.source_id IS NOT NULL
   AND a.work_type IN ('painting','watercolor','fresco') AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' AND artline_has_selection_evidence(a.id)
   AND (a.id=%s OR a.creation_year_end-a.creation_year_start<=20)
   ORDER BY (a.id=%s) DESC,a.creation_year_start,a.id LIMIT %s''',(IID,ICON,ICON,limit)).fetchall()
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
 for c in rows:c.update(provider=PROVIDER,artist='; '.join(x['name'] for x in c['creators']) or c['unlinked_creator_label'],target_ids={'local':c['artwork_id']})
 core.save_new(RUN/'candidates.json',dict(at=core.now(),baseline=baseline,candidates=rows));print('Selected',len(rows),'existing inventory-matched candidates',flush=True)

def facts(im,path):
 soup=BeautifulSoup(path.read_bytes(),'html.parser')
 def one(selector):
  xs=soup.select(selector)
  if len(xs)!=1:raise ValueError('Native field not unique: '+selector)
  return xs[0]
 title=clean(one('h1.artwork--title').get_text(' ',strip=True));date=clean(one('.section__date').get_text(' ',strip=True))
 accession=clean(one('.stat--accession-number .stat > p').get_text(' ',strip=True))
 if title!=clean(im['title']) or accession!=im['accession_number'] or date!=clean(im['date_display']):raise ValueError('Native title, date or inventory differs')
 author=one('.section__author');links=author.find_all('a',href=True);author_text=clean(author.get_text(' ',strip=True))
 if im['artwork_id']==ICON:
  if im['creators'] or im['creator_links'] or im['roles'] or im['unlinked_creator_label']!='Russian (Artist)' or author_text!='Russian (Artist)':raise ValueError('Anonymous icon attribution differs')
  if (im['creation_year_start'],im['creation_year_end'],im['date_precision'],date,im['object_form'])!=(1501,1600,'century','16th century (early Modern)','icon'):raise ValueError('Individual icon date/form differs')
 else:
  if len(im['creators'])!=1 or im['roles']!=['primary'] or len(links)!=1:raise ValueError('Native named authorship needs review')
  name=clean(links[0].get_text(' ',strip=True));plain_name=name.split(' (')[0]
  if not creator_matches(im,plain_name):raise ValueError('Native creator name differs')
  if not creator_role_matches(im,name,author_text):raise ValueError('Native attribution wording or creator role requires review')
  native_life=re.search(r'\([^()]*,\s*([0-9]{4})\s*[-–]\s*([0-9]{4})\)',name)
  local_death=im['creators'][0].get('death')
  native_activity=re.search(r'\(act\.\s*([0-9]{4})[-–]([0-9]{4})\)',name)
  if native_activity and local_death==int(native_activity[2]):local_death=None
  known_deaths=[year for year in (local_death,int(native_life[2]) if native_life else None) if year is not None]
  if known_deaths and max(known_deaths)+70>=int(core.now()[:4]):raise ValueError('Walters policy excludes artists copyright; recent creator death requires separate underlying-work clearance')
  lo,hi,precision=parse_creation_date(im,date)
  if (lo,hi,precision)!=(im['creation_year_start'],im['creation_year_end'],im['date_precision']):raise ValueError('Native date bounds/precision differ')
  life=re.search(r'(?<!\d)(\d{4})[-–](\d{4})(?!\d)',name)
  if life and lo!=hi and (lo,hi)==(int(life[1]),int(life[2])):raise ValueError('Object range repeats native creator lifespan; editorial review required')
 images=soup.select('a.item__image');
 if not images:raise ValueError('No native primary image')
 primary=select_photo(im,images);item=primary.find_parent(class_='item');photo=primary.find('img',src=True)
 if not item or not photo:raise ValueError('Native photograph container absent')
 grants=item.select('.item__actions .tooltip__inner a[href]');downloads=item.select('a.btn--download__image[href]')
 if len(grants)!=1 or grants[0].get('href')!=CC0 or grants[0].get_text(' ',strip=True)!='Creative Commons Zero':raise ValueError('Exact photograph CC0 licence missing')
 if len(downloads)!=1:raise ValueError('Exact photograph download not unique')
 filename=parse_qs(urlparse(downloads[0]['href']).query).get('download',[])
 if len(filename)!=1 or unquote(Path(urlparse(photo['src']).path).name)!=filename[0]:raise ValueError('Displayed and downloadable photograph differ')
 if not re.fullmatch(r'https://art\.thewalters\.org/images/art/[A-Za-z0-9_. -]+\.(?:jpg|JPG)',photo['src']):raise ValueError('Native image host/path unapproved')
 if not inventory_image_matches(im,filename[0]):raise ValueError('Photo inventory differs')
 if im['artwork_id']==ICON:
  if filename[0]!='PL2_37.568_VwA_BW_H56.jpg':raise ValueError('Reviewed icon source photograph differs')
 elif not front_image_matches(im,filename[0]):raise ValueError('Native primary is not a labelled front image')
 credit_nodes=[h.find_next_sibling('p') for h in soup.select('.stat h3') if h.get_text(' ',strip=True)=='Credit Line']
 if len(credit_nodes)!=1 or credit_nodes[0] is None:raise ValueError('Native credit line absent')
 credit='The Walters Art Museum; '+clean(credit_nodes[0].get_text(' ',strip=True))
 result=dict(title=title,date=date,inventory=accession,author=author_text,creator_links=[x['href'] for x in links],image_url=photo['src'],download_url='https://art.thewalters.org/object/'+accession+'/'+downloads[0]['href'],credit=credit,monochrome=bool(re.search(r'_BW(?:_|\.)',filename[0])),image_scope='Single Virgin panel of three-panel group; held after visual review' if im['artwork_id']==ICON else 'Front photograph; visual review required')
 if re.search(r'\(\s*\?\s*\)',author_text):result['creator_qualification']=QUALIFICATION_NOTICE
 return result

def verify_image(im):
 cap=im['raw']['native_capture'];p=core.ROOT/cap['path']
 if not p.resolve().is_relative_to((RUN/'metadata').resolve()) or core.sha(p.read_bytes())!=cap['sha256']:raise ValueError('Pinned native capture differs')
 page='https://art.thewalters.org/object/'+im['accession_number']+'/'
 if cap['url']!=page or im['page']!=page or im['institution_id']!=IID:raise ValueError('Native source identity differs')
 actual=facts(im,p)
 if actual!=im['raw']['native_facts']:raise ValueError('Reviewed native facts differ')
 if (im['source_image_url'],im['rights_status'],im['policy_url'],im['license_label'],im['creator_credit'])!=(actual['image_url'],'cc0',CC0,'CC0 1.0',actual['credit']):raise ValueError('Native image/licence/credit differs')
 if actual['credit'] not in im['attribution_text'] or CC0 not in im['attribution_text']:raise ValueError('Native credit missing')
 if actual['monochrome'] and 'monochrome' not in im['attribution_text']:raise ValueError('Monochrome source limitation missing')
 if actual.get('creator_qualification') and actual['creator_qualification'] not in im['attribution_text']:raise ValueError('Native creator qualification missing')

def research(limit,retry_held=False):
 select(limit);f=core.Fetcher(RUN/'metadata');done={} if retry_held else core.latest_events(RUN)
 for c in json.loads((RUN/'candidates.json').read_bytes())['candidates']:
  dest=RUN/'selected'/PROVIDER/(c['artwork_id']+'.json')
  if dest.exists():verify_image(json.loads(dest.read_bytes()));continue
  if c['artwork_id'] in done:continue
  try:
   if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)*(?:[A-Z])?',c['accession_number'] or ''):raise ValueError('Inventory requires individual URL review')
   url='https://art.thewalters.org/object/'+c['accession_number']+'/';p=f.cache/(c['accession_number']+'.html')
   if not p.exists():
    data,headers=f.get(url,3_000_000);core.save_new(p,data);core.save_new(p.with_suffix('.receipt.json'),dict(url=url,path=str(p.relative_to(core.ROOT)),sha256=core.sha(data),headers=headers,at=core.now()))
   cap=json.loads(p.with_suffix('.receipt.json').read_bytes());obj=facts(c,p)
   im=dict(c,page=url,source_image_url=obj['image_url'],rights_status='cc0',license_label='CC0 1.0',policy_url=CC0,creator_credit=obj['credit'],checked_at=core.now(),raw=dict(native_capture=cap,native_facts=obj),attribution_text=f"{c['artist']}. {c['title']}, {c['date_display']}. {obj['credit']}. Inventory {c['accession_number']}. CC0 ({CC0}). {url}. Full-frame proportional resize and JPEG compression.")
   if obj['monochrome']:im['attribution_text']+=' Source-provided archival monochrome reproduction; original painting colours are not represented.'
   if obj.get('creator_qualification'):im['attribution_text']+=' '+obj['creator_qualification']
   im=decorate_image(im)
   verify_image(im);core.save_new(dest,im);core.event(RUN,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='rights_selected'));print('Selected native CC0:',c['title'],flush=True)
  except Exception as error:core.event(RUN,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='manual_review',reason=str(error)[:350]));print('Held:',c['title'],str(error)[:150],flush=True)

def attach(db,im,target):
 if target!='local':raise ValueError('Only local attachment authorized')
 if im['artwork_id']==ICON:raise ValueError('Single-panel photograph cannot represent the complete three-panel group')
 verify_image(im);result=base.m.original_attach(db,im,target)
 if result=='attached':
  db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
  db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',('Current exact Walters accession page, matching title/date/creator or individually retained anonymous icon label; selected primary display and download use the same resource and its own CC0 grant. No holdings, creator or date metadata changed.',im['media_id']))
 return result
base.m.attach=attach

def verify_rights_and_holds():
 decisions={x['artwork_id']:x for x in json.loads((RUN/'visual-review.json').read_bytes())['images']};checks=[]
 with base.connect() as db:
  for im in base.prepared():
   if decisions[im['artwork_id']]['decision']!='approved':continue
   verify_image(im)
   row=db.execute('''SELECT m.attribution_text,m.rights_status,e.evidence_json,e.source_checksum,e.source_id::text,e.source_record_id
    FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=%s''',(im['media_id'],)).fetchone()
   if not row or row['attribution_text']!=im['attribution_text'] or row['rights_status']!='cc0':raise ValueError('Stored native attribution or rights differ')
   if row['evidence_json']!={k:v for k,v in im.items() if k not in ('artist','title')} or row['source_checksum']!=core.sha(core.encode(im['raw'])):raise ValueError('Stored complete evidence differs')
   if (row['source_id'],row['source_record_id'])!=(im['source_id'],im['external_id']):raise ValueError('Native source identifier changed')
   checks.append(dict(artwork_id=im['artwork_id'],source_url=im['page'],monochrome=im['raw']['native_facts']['monochrome'],exact_database_evidence_verified=True))
  candidates=json.loads((RUN/'candidates.json').read_bytes())['candidates'];approved={x['artwork_id'] for x in checks};held=[]
  for c in candidates:
   if c['artwork_id'] in approved:continue
   record=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(c['artwork_id'],)).fetchone()['record']
   if record!=c['before_record']:raise ValueError('Held catalogue record changed')
   held.append(c['artwork_id'])
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
 core.save_new(RUN/'source-rights-verification.json',dict(at=core.now(),passed=True,verified=len(checks),monochrome_sources=sum(x['monochrome'] for x in checks),held_artworks_unchanged=held,checks=checks))
 core.save_new(RUN/'report.json',dict(at=core.now(),local_only=True,reviewed=len(candidates),attached=len(checks),still_unattached=len(held),monochrome_attached=sum(x['monochrome'] for x in checks),cc0_attached=len(checks),baseline_after=baseline,all_catalogue_metadata_preserved=True,all_remain_in_review=True,production_changed=False,remaining_catalogue_work=True,http_verification=dict(status='not_completed',reason='Existing Next.js server timed out in the latest earlier check; no server restart or further HTTP attempt in this operation.',prior_check='docs/research/local-academy-verso-image-20261006/local-http-check.json')))
 print('Verified exact native evidence, CC0 credits and source IDs:',len(checks),'unchanged held records:',len(held),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','prepare','apply','verify']);p.add_argument('--limit',type=int,default=30);a=p.parse_args()
 if a.phase=='research':research(a.limit)
 elif a.phase=='prepare':
  for p in (RUN/'selected'/PROVIDER).glob('*.json'):verify_image(json.loads(p.read_bytes()))
  base.prepare(PROVIDER)
 elif a.phase=='apply':base.apply()
 else:
  for im in base.prepared():verify_image(im)
  base.verify()
  verify_rights_and_holds()
