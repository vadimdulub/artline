#!/usr/bin/env python3
"""Selected official works matched to approved WikiArt by exact creator/title/date."""
import importlib.util,collections,re,json,sys
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('import-random-country-collections-20261010.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-random-country-collections-20261010.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
code=sys.argv[1];r.phase(code);folder=m.RUN/code;rows=m.source_records(code);source=r.b.Source();groups=collections.defaultdict(list)
for w in rows:
 if w.get('verified_artist_id') and w.get('year_end') and w['year_end']<=1955 and w['date_decision'].startswith('within_cutoff') and not w.get('image_license_url') and 'print' not in w['source_type'].lower():groups[w['verified_artist_id']].append(w)
with m.connect() as db:
 profiles={x['entity_id']:x['canonical_url'] for x in db.execute("SELECT entity_id::text,canonical_url FROM external_identifiers WHERE entity_type='artist' AND scheme='wikiart-artist' AND entity_id=ANY(%s::uuid[])",(list(groups),))}
out={};held=[]
for n,(aid,works) in enumerate(groups.items(),1):
 u=profiles.get(aid)
 if not u:continue
 try:
  sp,rc=r.page(u.rstrip('/')+'/all-works/text-list',source);index=collections.defaultdict(list)
  for li in sp.select('li'):
   for a in li.select('a[href]'):
    href=urljoin(u,a['href']);path=u.split('wikiart.org')[-1].rstrip('/')+'/'
    if path not in href or 'all-works' in href:continue
    index[m.norm(a.get_text(' ',strip=True))].append(dict(url=href,caption=li.get_text(' ',strip=True)))
  for w in works:
   titles={m.norm(w['title'])}
   for t in (w.get('alternate_title') or '').splitlines():titles.add(m.norm(re.sub(r'\s*\[[^]]*\]\s*$','',t)))
   mt=re.fullmatch(r'(.+?) \(([^()]+)\)',w['title'])
   if mt:titles.update(m.norm(t) for t in mt.groups())
   found={x['url']:x for t in titles for x in index[t]};matches=[]
   for v in found.values():
    years=list(map(int,re.findall(r'\b[12]\d{3}\b',v['caption'])))
    if years and min(years)==w['year_start'] and max(years)==w['year_end']:matches.append(v)
   if len(matches)!=1:continue
   sp2,rc2=r.page(matches[0]['url'],source);tag=sp2.select_one('.wiki-layout-painting-info-bottom[ng-init]')
   if not tag:continue
   md=json.loads(tag['ng-init'].split('=',1)[1].strip());lo,hi=r.bounds(str(md.get('year') or ''))
   if m.norm(md['title']) not in titles or (lo,hi)!=(w['year_start'],w['year_end']) or md['artistUrl'].rstrip('/')!=u.split('wikiart.org')[-1].rstrip('/'):continue
   location_node=sp2.find(string=re.compile(r'^\s*Location:\s*$'))
   location=location_node.parent.parent.get_text(' ',strip=True) if location_node else None
   expected={'McMichael Canadian Art Collection':['mcmichael'],'National Gallery of Canada':['national gallery of canada'],'Montreal Museum of Fine Arts':['montreal museum','beaux-arts de montr'],'Kunsthaus Zürich':['kunsthaus zurich','kunsthaus zürich'],'Kunstmuseum Basel':['kunstmuseum basel'],'Cantonal Museum of Fine Arts':['cantonal','lausanne'],'Kunstmuseum Winterthur, Winterthur, Switzerland':['winterthur']}.get(w['museum'],[])
   if location and expected and not any(t in location.lower() for t in expected):held.append(dict(key=w['provider']+'/'+w['source_id'],reason='WikiArt explicit holding differs',location=location,url=rc2['final_url']));continue
   img=sp2.select_one('img[itemprop=image]');copyright=sp2.select_one('.copyright-wrapper .copyright')
   if not img:continue
   pd=bool(copyright and copyright.select_one('.copyright-icon-public-domain'))
   # Exact translated title and date cannot separate generic names or sculpture casts.
   generic=bool(re.fullmatch(r'portrait|self portrait|landscape|still life|untitled|nude|composition',m.norm(md['title'])))
   if generic or w['source_type'].lower()=='sculpture':held.append(dict(key=w['provider']+'/'+w['source_id'],reason='Generic title or physical cast requires further identity evidence',url=rc2['final_url']));continue
   out[w['provider']+'/'+w['source_id']]=dict(image_url=img['src'],image_license_url='https://www.wikiart.org/en/terms-of-use',image_rights_status='public_domain' if pd else 'restricted' if copyright else 'unknown',image_rights_label=copyright.get_text(' ',strip=True) if copyright else 'Rights not specified',image_source_provider='WikiArt',image_source_page_url=rc2['final_url'],image_source_record_id=md['_id'],image_evidence=rc2,image_identity_confidence=.94,image_identity_basis='Exact existing creator authority/WikiArt profile plus unique official title/explicit translation and exact creation bounds; generic titles, prints and sculpture casts excluded. Source metadata retained.',image_rights_basis='User approved WikiArt across Artline policies 6 October 2026; actual per-image rights retained separately.',wikiart_metadata=md)
 except Exception as e:
  held.append(dict(profile=u,error=str(e)[:220]))
  if source.blocked:break
 if n%10==0:print('WikiArt',code,n,'creators',len(out),'matches',flush=True)
m.save(folder/'image-enrichment.json.gz',out);m.save(folder/'image-enrichment-held.json.gz',held);print('WikiArt matched',code,len(out),flush=True)
