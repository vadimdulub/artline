#!/usr/bin/env python3
"""Two existing Greek museum image gaps, with a separate WikiArt identity review."""
import argparse
import importlib.util
import json
import copy
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup

spec = importlib.util.spec_from_file_location('wiki', Path(__file__).with_name('recover-local-wikiart-approved-images-20261006.py'))
wiki = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wiki)
base, core = wiki.base, wiki.core
RUN = core.ROOT / 'docs/research/local-wikiart-papaloukas-images-20261006'
wiki.RUN = base.RUN = wiki.chicago.RUN = RUN
core.VERSION = 'local-wikiart-papaloukas-image-review-v1'
ARTIST = '96c93b65-37db-4879-9bf7-3bf5a9d8178e'
PROFILE = 'https://www.wikiart.org/en/spyros-papaloukas'
MUSEUM_ARTIST = 'https://www.nationalgallery.gr/en/artist/papaloukas-spyros/'
DUPLICATE = '567037a5-2713-5b8d-8acc-9fd882990aee'
TARGETS = {
 '0dcc8b99-c8c5-4309-a8d0-c47016f7150a': dict(page=PROFILE+'/boy-wearing-suspenders-1925', title='Boy wearing suspenders', inventory='Π.3300', year=1925, wikiart_id='57727c86edc2cb3880e4bc1c'),
 'e49858f3-fd02-5b47-ac48-cb2f84ce796d': dict(page=PROFILE+'/vase-of-flowers-dark-colors-1956', title='Vase of Flowers (dark colors)', inventory='Π.3303', year=1956, wikiart_id='57727cc3edc2cb3880e5709b'),
}
original_facts, original_attach = wiki.page_facts, wiki.attach
BASIS = 'Existing exact National Gallery of Greece object URL/accession, title, date and native creator identity; separately reviewed WikiArt creator profile and exact object/photo, including individual visual comparison. User WikiArt approval and actual rights labels recorded separately. Image-only local attachment; catalogue records and duplicate records remain unchanged.'

def snapshot():
 if (RUN/'candidates.json').exists(): return
 with base.connect() as db:
  rows=db.execute('''SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,a.accession_number,
   to_jsonb(a) before_record,i.id::text institution_id,i.slug institution_slug,i.name museum,
   ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) roles,
   (SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creator_links,
   (SELECT jsonb_agg(to_jsonb(e) ORDER BY e.id) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) identifiers,
   COALESCE((SELECT jsonb_agg(to_jsonb(la) ORDER BY la.id) FROM artwork_location_assertions la WHERE la.artwork_id=a.id),'[]') holding_assertions
   FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE a.id=ANY(%s::uuid[])
   AND a.primary_media_id IS NULL AND a.status='review' AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
   AND artline_has_selection_evidence(a.id) ORDER BY a.id''',(list(TARGETS),)).fetchall()
  if len(rows)!=2: raise ValueError('Selected gaps changed')
  artist=db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=%s',(ARTIST,)).fetchone()['record']
  aliases=[x['record'] for x in db.execute('SELECT to_jsonb(a) record FROM artist_aliases a WHERE artist_id=%s ORDER BY id',(ARTIST,))]
  identifiers=[x['record'] for x in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=%s ORDER BY id",(ARTIST,))]
  duplicate=db.execute('SELECT to_jsonb(a) artwork,to_jsonb(m) media FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=%s',(DUPLICATE,)).fetchone()
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
 for c in rows:
  if c['roles']!=['primary'] or len(c['creator_links'])!=1 or c['creator_links'][0]['artist_id']!=ARTIST: raise ValueError('Creator differs')
  ids=[e for e in c['identifiers'] if e['scheme']=='nationalgallery-gr-work']
  if len(ids)!=1: raise ValueError('Unique native object missing')
  e=ids[0]
  c.update(provider=wiki.PROVIDER,scheme=e['scheme'],external_id=e['external_id'],source_id=e['source_id'],museum_page=e['canonical_url'],page=TARGETS[c['artwork_id']]['page'],artist=artist['display_name'],target_ids={'local':c['artwork_id']},creator_authorities=[dict(artist_record=artist,artist_aliases=aliases,artist_identifiers=identifiers)])
 core.save_new(RUN/'candidates.json',dict(at=core.now(),baseline=baseline,candidates=rows,selection='Two existing eligible National Gallery of Greece records with specific WikiArt page leads; image-only, no catalogue records created or merged.'))
 core.save_new(RUN/'existing-duplicate-record.json',duplicate)
 docs=[]
 for source in ('AGENTS.md','docs/ARTLINE_IMAGE_USE.md'):
  data=(core.ROOT/source).read_bytes(); capture='metadata/authorization/'+Path(source).name
  core.save_new(RUN/capture,data);docs.append(dict(source_path=source,capture=capture,sha256=core.sha(data)))
 core.save_new(RUN/'source-authorization.json',dict(at=core.now(),source='WikiArt',target='local',record_actual_rights_separately=True,documents=docs,user_instruction='see new md file - wiki art is fully approved',scope='Two existing Greek museum artwork images; keep actual source rights labels and catalogue metadata.'))
 print('Snapshotted two existing Greek museum gaps',flush=True)

def capture(url,path):
 if path.exists():
  data=path.read_bytes();rc=json.loads(path.with_suffix('.receipt.json').read_bytes())
  if rc['url']!=url or core.sha(data)!=rc['sha256'] or len(data)!=rc['bytes']: raise ValueError('Capture changed')
  return data,rc
 fetch=core.Fetcher(RUN/'metadata')
 core.provider_rate_slot(urlparse(url).hostname)
 with fetch.session.get(url,timeout=(15,45),allow_redirects=False) as response:
  response.raise_for_status()
  if response.status_code!=200 or len(response.content)>5000000: raise ValueError('Unexpected source response')
  data=response.content
 rc=dict(url=url,at=core.now(),bytes=len(data),sha256=core.sha(data),path=str(path.relative_to(core.ROOT)))
 core.save_new(path,data);core.save_new(path.with_suffix('.receipt.json'),rc)
 return data,rc

def sources():
 snapshot()
 capture(PROFILE,RUN/'metadata/creator.html')
 capture(MUSEUM_ARTIST,RUN/'metadata/museum-creator.html')
 fetch=core.Fetcher(RUN/'metadata')
 for c in json.loads((RUN/'candidates.json').read_bytes())['candidates']:
  capture(c['museum_page'],RUN/'metadata/museum'/(c['artwork_id']+'.html'))
  wiki.capture_page(c,fetch)
  print('Captured source pair',c['title'],flush=True)

def pinned(path,url):
 data=path.read_bytes();rc=json.loads(path.with_suffix('.receipt.json').read_bytes())
 if rc['url']!=url or core.sha(data)!=rc['sha256'] or len(data)!=rc['bytes']: raise ValueError('Pinned source changed')
 return BeautifulSoup(data,'html.parser'),rc

def bridge(c):
 target=TARGETS[c['artwork_id']]
 if c['page']!=target['page'] or c['institution_slug']!='national-gallery-greece' or c['accession_number']!=target['inventory'] or (c['creation_year_start'],c['creation_year_end'])!=(target['year'],target['year']): raise ValueError('Pinned object identity differs')
 if c['roles']!=['primary'] or len(c['creator_links'])!=1 or c['creator_links'][0]['artist_id']!=ARTIST: raise ValueError('Unique creator identity differs')
 proof=c['creator_authorities'][0]; ar=proof['artist_record']
 if (ar['id'],ar['display_name'],ar['birth_year'],ar['death_year'])!=(ARTIST,'Spyros Papaloukas',1892,1957): raise ValueError('Local creator differs')
 ids=[x for x in proof['artist_identifiers'] if x['scheme']=='nationalgallery-gr-artist']
 if len(ids)!=1 or ids[0]['external_id']!='papaloukas-spyros' or ids[0]['canonical_url']!=MUSEUM_ARTIST: raise ValueError('Native creator authority differs')
 nativeids=[x for x in c['identifiers'] if x['scheme']=='nationalgallery-gr-work']
 if len(nativeids)!=1 or (nativeids[0]['external_id'],nativeids[0]['canonical_url'])!=(c['external_id'],c['museum_page']): raise ValueError('Native object authority differs')
 profile,pr=pinned(RUN/'metadata/creator.html',PROFILE)
 if profile.select_one('meta[itemprop="name"]')['content']!='Spyros Papaloukas' or profile.select_one('[itemprop="birthDate"]').get_text(strip=True)!='1892' or profile.select_one('[itemprop="deathDate"]').get_text(strip=True)!='1957': raise ValueError('WikiArt creator profile differs')
 museumartist,mar=pinned(RUN/'metadata/museum-creator.html',MUSEUM_ARTIST)
 text=' '.join(museumartist.get_text(' ',strip=True).split())
 if 'Papaloukas Spyros Desfina, Parnassida 1892 - Athens 1957' not in text: raise ValueError('Native creator life evidence differs')
 museum,mr=pinned(RUN/'metadata/museum'/(c['artwork_id']+'.html'),c['museum_page'])
 title=museum.select_one('h1.artwork').get_text(' ',strip=True)
 if title!=c['title']+', '+str(target['year']): raise ValueError('Native artwork title/date differs')
 text=museum.get_text(' ',strip=True)
 if 'Inv. Number '+target['inventory'] not in text: raise ValueError('Native inventory differs')
 links=museum.select('header p.artist a[href]')
 if len(links)!=1 or links[0]['href']!=MUSEUM_ARTIST or links[0].get_text(' ',strip=True)!='Papaloukas Spyros (1892 - 1957)': raise ValueError('Native object creator differs')
 medium=museum.select_one('header p.description').get_text(' ',strip=True)
 if medium!=c['before_record']['medium_text']+', '+c['before_record']['dimensions_text']: raise ValueError('Native medium/dimensions differs')
 image=museum.select_one('img')['src']
 if not image.startswith('https://www.nationalgallery.gr/wp-content/uploads/'): raise ValueError('Unexpected museum reference photograph')
 return dict(wikiart_creator_capture=pr,native_creator_capture=mar,native_object_capture=mr,source_title=target['title'],source_object_id=target['wikiart_id'],museum_title=title,museum_inventory=target['inventory'],museum_medium_dimensions=medium,reference_image_url=image,
  basis='Native object URL, accession, title, date and creator page identify the existing museum record. WikiArt profile name and explicit 1892–1957 dates match the existing native creator authority. Source titles and images receive individual visual review; no WikiArt identifier or alias is inserted into the catalogue.')

def page_facts(c,data,rc):
 evidence=bridge(c)
 adapted=copy.deepcopy(c)
 adapted['external_id']=evidence['source_object_id']
 adapted['alternate_title']=evidence['source_title']
 adapted['creator_authorities'][0]['artist_identifiers'].append(dict(scheme='wikiart-artist',external_id='spyros-papaloukas',canonical_url=PROFILE))
 facts=original_facts(adapted,data,rc)
 facts['individual_museum_to_wikiart_identity']=evidence
 return facts

wiki.page_facts=page_facts
wiki.select=lambda limit:snapshot()

def references():
 for c in json.loads((RUN/'candidates.json').read_bytes())['candidates']:
  facts=bridge(c);url=facts['reference_image_url'];path=base.ARCHIVE/'source-images'/RUN.name/'private-museum-reference'/(c['artwork_id']+'.image')
  receipt=RUN/'metadata/reference-images'/(c['artwork_id']+'.json')
  if receipt.exists(): continue
  fetch=core.Fetcher(RUN/'metadata');core.provider_rate_slot(urlparse(url).hostname)
  with fetch.session.get(url,timeout=(15,45),allow_redirects=False) as response:
   response.raise_for_status()
   if response.status_code!=200 or len(response.content)>5000000: raise ValueError('Unexpected reference response')
   data=response.content
  core.save_new(path,data)
  core.save_new(receipt,dict(url=url,at=core.now(),path=str(path),sha256=core.sha(data),bytes=len(data),usage='Private visual identity reference only; attached image is from separately approved WikiArt.'))
  print('Private visual reference',c['title'],flush=True)

def version(im):
 reviews=json.loads((RUN/'object-version-review.json').read_bytes())['images']
 matches=[r for r in reviews if r['artwork_id']==im['artwork_id']]
 if len(matches)!=1: raise ValueError('Individual version review missing')
 review=matches[0]
 if review['decision']!='approved' or any(review[k]!=im[k] for k in ('source_sha256','sha256','source_image_url','external_id','scheme')): raise ValueError('Reviewed version differs')
 if review!=im['raw'].get('object_version_review') or review['note'] not in im['attribution_text']: raise ValueError('Version evidence omitted')
 ref=json.loads((RUN/'metadata/reference-images'/(im['artwork_id']+'.json')).read_bytes())
 data=Path(ref['path']).read_bytes()
 if review['reference_capture']!=ref or core.sha(data)!=ref['sha256'] or len(data)!=ref['bytes'] or ref['url']!=bridge(im)['reference_image_url']: raise ValueError('Private reference differs')

def duplicate_unchanged(db):
 old=json.loads((RUN/'existing-duplicate-record.json').read_bytes())
 current=db.execute('SELECT to_jsonb(a) artwork,to_jsonb(m) media FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=%s',(DUPLICATE,)).fetchone()
 if old!=current: raise ValueError('Existing illustrated duplicate changed')
 data=(core.ROOT/'apps/web/public'/old['media']['storage_path'].lstrip('/')).read_bytes()
 if core.sha(data)!=old['media']['checksum_sha256']: raise ValueError('Existing duplicate image changed')

def attach(db,im,target):
 version(im);duplicate_unchanged(db)
 result=original_attach(db,im,target)
 if result=='attached': db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',(BASIS,im['media_id']))
 return result

base.m.attach=attach

def verify():
 for im in base.prepared(): wiki.verify_image(im);version(im)
 with base.connect() as db:
  duplicate_unchanged(db)
  for im in base.prepared():
   if db.execute('SELECT rights_basis FROM media_rights_evidence WHERE media_id=%s',(im['media_id'],)).fetchone()['rights_basis']!=BASIS: raise ValueError('Wrong identity basis')
 wiki.verify()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','references','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='research': wiki.research(2)
 elif a.phase=='prepare': wiki.prepare()
 elif a.phase=='apply': base.apply()
 else: globals()[a.phase]()
