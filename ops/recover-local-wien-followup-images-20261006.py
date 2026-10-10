#!/usr/bin/env python3
"""Attach eight individually reviewed native Wien Museum photographs locally."""
import argparse
import importlib.util
import json
import re
import uuid
from pathlib import Path
from bs4 import BeautifulSoup

s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('recover-local-commons-images-20261005.py'))
base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
core=base.core
RUN=core.ROOT/'docs/research/local-wien-followup-images-20261006';base.RUN=RUN
LEADS=RUN.parent/'local-commons-wien-native-leads-20261006'
PROVIDER='wien-museum-native';core.PROVIDERS[PROVIDER]='Wien Museum'
core.HOSTS.add('sammlung.wienmuseum.at');core.VERSION='local-wien-reviewed-native-photographs-v1'
LICENCE='https://creativecommons.org/licenses/by/4.0/'
CREDIT='Birgit und Peter Kainz, Wien Museum'
SLUG='wien-native-image-recovery-20261006'
SID=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/sources/'+SLUG))
# Individual date discrepancies may be retained for an exact object identity.
# Empty for the original operation; later reviewed operations supply explicit
# stored/native bounds and wording, without modifying catalogue dates.
DATE_REVIEWS={}
REVIEWS={
 'Q110243338':('44693','Johann Matthias Ranftl (1804—1854)',
  'Exact stored inventory 44693, 1852 and authority-linked native page. Johann Matthias Ranftl is the fuller native form of the existing Matthias Ranftl identity. Children peddling matches is the specific native title of the existing begging-children work.'),
 'Q114983638':('139700','Heinrich Friedrich Füger (1751—1818)',
  'Exact stored inventory 139700, circa 1787–1788, authority-linked native page and Joseph II title. Heinrich Friedrich Füger is the fuller native name of the existing Heinrich Füger identity.'),
 'Q124288173':('117356','Friedrich von Amerling (1803—1887)',
  'Exact inventory 117356, German authority title Die drei köstlichsten Dinge, sole creator and 1838 date.'),
 'Q139377491':('10133','Ferdinand Georg Waldmüller (1793—1865)',
  'Exact inventory 10133, German authority title Kirchgang im Frühling, sole creator and 1863 date.'),
 'Q110197268':('117376','Max Kurzweil (1867—1916)',
  'Dame in Gelb and Dame im gelben Kleid / Woman in a yellow dress identify the same subject. Sole creator, 1899 date, Wien Museum and 171.5 cm height agree; authority width 171 cm is rounded from native 171.5 cm. The old Commons filename contains 1907, so it is not used as date evidence. Native signature Kurzweil 99 confirms 1899. Existing missing inventory remains missing.'),
 'Q127413996':('71100','Anton Romako (1832—1889)',
  'Salon Interieur is the short title of the native man-and-woman salon interior. Sole Romako authorship, 1887, museum and dimensions agree: native 48.5 × 62.5 cm rounds to authority 49 × 63 cm. Native restitution and reacquisition history remains source evidence only; no holding or provenance fields are rewritten. Existing missing inventory remains missing.'),
 'Q139590388':('16803','Hans Makart (1840—1884)',
  'Charlotte Wolter as Messalina, sole Makart authorship, 1875, museum and exact 142 × 223 cm dimensions agree. Native painting object 1471 is distinct from the historical photographic negative 30585. Existing missing inventory remains missing.'),
 'Q138306746':('61061','Gustav Klimt (1862—1918)',
  'Native unknown-woman portrait (Frau Heymann?) matches the authority alias Portrait of an unknown woman (Mrs. Heymann?), sole Klimt authorship and exact 30 × 23 cm dimensions. Both use 1894; native circa qualifier is retained in evidence and attribution without changing the existing exact-year field. Existing unknown sitter/title/inventory remain unchanged.'),
}

def parsed(path):
 soup=BeautifulSoup(path.read_bytes(),'html.parser')
 labels={x.get_text(' ',strip=True):x.find_next_sibling('dd') for x in soup.find_all('dt') if x.find_next_sibling('dd')}
 rows=labels['Artists/Producer'].select('tbody tr')
 creators=[[c.get_text(' ',strip=True) for c in r.find_all('td')] for r in rows]
 return soup,labels,creators

def native_check(im):
 review=REVIEWS.get(im['qid'])
 if not review:raise ValueError('Object lacks individual native identity review')
 base.original_entity_match(im,im['raw']['wikidata'],False)
 cap=im['raw']['native_capture'];p=core.ROOT/cap['path']
 if not p.resolve().is_relative_to((RUN/'metadata').resolve()) or core.sha(p.read_bytes())!=cap['sha256'] or cap['url']!=im['page']:
  raise ValueError('Pinned native page differs')
 soup,labels,creators=parsed(p);facts=im['native_identity_review']
 if creators!=[[review[1],'Artist']] or len(im['creators'])!=1 or im['roles']!=['primary']:
  raise ValueError('Native creator or role differs')
 death=int(re.search(r'—(\d{4})\)',review[1])[1])
 if im['creators'][0]['death']!=death or death>1955:raise ValueError('Creator date authority differs')
 inventory=labels['Inventory number'].get_text(strip=True)
 if inventory!=review[0] or (im['accession_number'] and im['accession_number']!=inventory):
  raise ValueError('Native inventory conflicts')
 headings=soup.find_all('h1')
 if len(headings)!=1 or headings[0].get_text(' ',strip=True)!=facts['native_title'] or facts['note']!=review[2]:
  raise ValueError('Individually reviewed title differs')
 date=' '.join(labels['Date'].get_text(' ',strip=True).split())
 match=re.fullmatch(r'(around )?(\d{4})(?:\s*–\s*(\d{4}))?',date)
 if not match:raise ValueError('Native creation interval is unparsed')
 native_bounds=(int(match[2]),int(match[3] or match[2]))
 stored_bounds=(im['creation_year_start'],im['creation_year_end'])
 if not (1000<=native_bounds[0]<=native_bounds[1]<=1970 and 1000<=stored_bounds[0]<=stored_bounds[1]<=1970):
  raise ValueError('Creation interval is outside approved scope')
 discrepancy=DATE_REVIEWS.get(im['qid'])
 actual=dict(stored_bounds=list(stored_bounds),native_bounds=list(native_bounds),native_text=date)
 if native_bounds!=stored_bounds:
  if discrepancy!=actual or facts.get('retained_date_discrepancy')!=actual:
   raise ValueError('Native creation interval conflicts without individual review')
 elif discrepancy or facts.get('retained_date_discrepancy'):
  raise ValueError('Spurious date-discrepancy review')
 if date!=facts['native_date'] or labels['Dimensions'].get_text(' ',strip=True)!=facts['native_dimensions']:
  raise ValueError('Reviewed native date/dimensions changed')
 if 'paintings' not in labels['Classification'].get_text(' ',strip=True) or im['work_type']!='painting':
  raise ValueError('Source object is not a painting')
 photos=soup.select('img.object-image')
 if not photos or photos[0].get('data-src')!=im['source_image_url']:raise ValueError('Source primary photograph differs')
 fig=photos[0].find_parent('figure');caps=fig.select('[data-caption]') if fig else []
 if len(caps)!=1 or caps[0].get_text(' ',strip=True)!='CC BY 4.0, Foto: '+CREDIT:
  raise ValueError('Photograph-specific credit/licence missing')
 if not soup.find('a',href=LICENCE+'deed.en') or not soup.find('a',href=im['source_image_url'],attrs={'download':True}):
  raise ValueError('Published licensed download missing')
 if (im['policy_url'],im['rights_status'],im['license_label'],im['creator_credit'])!=(LICENCE,'cc_by','CC BY 4.0',CREDIT):
  raise ValueError('Image credit/licence changed')
 if CREDIT not in im['attribution_text'] or LICENCE not in im['attribution_text'] or 'CC BY 4.0 Wien Museum' not in im['attribution_text']:
  raise ValueError('Required attribution missing')
 oid=re.search(r'/object/(\d+)',im['page'])[1]
 if not re.fullmatch(r'https://sammlung\.wienmuseum\.at/images/objects/'+oid+r'/\d+_full\.jpg',im['source_image_url']):
  raise ValueError('Photo belongs to a different native object')
 if im['institution_qid']!='Q505873':raise ValueError('Native holding differs')

def research():
 manifest=json.loads((LEADS/'candidates.json').read_bytes())
 if not (RUN/'candidates.json').exists():core.save_new(RUN/'candidates.json',manifest)
 else:manifest=json.loads((RUN/'candidates.json').read_bytes())
 probes={p['artwork_id']:p for p in json.loads((LEADS/'native-probe.json').read_bytes())['objects']}
 probes.update({p['artwork_id']:p for p in json.loads((LEADS/'search-followup-probe.json').read_bytes())['objects']})
 for c in manifest['candidates']:
  dest=RUN/'selected'/PROVIDER/(c['artwork_id']+'.json')
  if dest.exists():native_check(json.loads(dest.read_bytes()));continue
  probe=probes[c['artwork_id']]
  if c['qid'] not in REVIEWS:
   reason=probe.get('hold','Native date/object classification conflicts or an additional identity/precision review is required')
   core.event(RUN,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='manual_review',reason=reason,native_findings=probe));continue
  original=core.ROOT/probe['html'];capture=json.loads(original.with_suffix('.receipt.json').read_bytes())
  if core.sha(original.read_bytes())!=capture['sha256']:raise ValueError('Source receipt differs')
  copy=RUN/'metadata'/original.name;core.save_new(copy,original.read_bytes())
  capture.update(path=str(copy.relative_to(core.ROOT)),copied_from=str(original.relative_to(core.ROOT)))
  core.save_new(copy.with_suffix('.receipt.json'),capture)
  e=json.loads((LEADS/'authorities'/(c['qid']+'.json')).read_bytes())['entity']
  native_date=' '.join(probe['labels']['Date'].split());note=REVIEWS[c['qid']][2]
  im=dict(c,provider=PROVIDER,page=probe['url'],source_image_url=probe['photos'][0]['url'],policy_url=LICENCE,rights_status='cc_by',license_label='CC BY 4.0',checked_at=core.now(),creator_credit=CREDIT,
   raw=dict(wikidata=e,native_capture=capture),native_identity_review=dict(native_title=probe['native_title'],native_date=native_date,native_dimensions=probe['labels']['Dimensions'],inventory=REVIEWS[c['qid']][0],note=note),
   attribution_text=f"{c['artist']}. {probe['native_title']}, {native_date}. Wien Museum, inventory {REVIEWS[c['qid']][0]}. Photo: {CREDIT}. CC BY 4.0 Wien Museum ({LICENCE}). {probe['url']}. Full-frame proportional resize and JPEG compression.")
  if c['qid'] in DATE_REVIEWS:im['native_identity_review']['retained_date_discrepancy']=DATE_REVIEWS[c['qid']]
  native_check(im);core.save_new(dest,im);core.event(RUN,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='rights_selected'))
 print('Selected native images',len(list((RUN/'selected'/PROVIDER).glob('*.json'))),flush=True)

def attach(db,im,target):
 if target!='local':raise ValueError('Only local attachment authorized')
 native_check(im);result=base.m.original_attach(db,im,target)
 if result=='attached':
  if db.execute('SELECT id::text FROM sources WHERE slug=%s',(SLUG,)).fetchone()['id']!=SID:raise ValueError('Native source identity changed')
  db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
  native_id='/'.join(re.search(r'/objects/(\d+)/(\d+)_full',im['source_image_url']).groups())
  db.execute('UPDATE media_rights_evidence SET source_id=%s,source_record_id=%s,rights_basis=%s WHERE media_id=%s',(SID,native_id,'Individually reviewed native painting identity; exact photograph licensed CC BY 4.0 with named photographer credit. Existing catalogue fields retained.',im['media_id']))
 return result

base.m.attach=attach
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='research':research()
 elif a.phase=='prepare':
  for f in (RUN/'selected'/PROVIDER).glob('*.json'):native_check(json.loads(f.read_bytes()))
  base.prepare(PROVIDER)
 elif a.phase=='apply':base.apply()
 else:
  for im in base.prepared():native_check(im)
  base.verify()
