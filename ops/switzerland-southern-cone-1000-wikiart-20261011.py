#!/usr/bin/env python3
"""Independent approved WikiArt matches for the newly selected museum works."""
import collections,importlib.util,json,re,sys
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('switzerland-southern-cone-1000-20261011.py'))
c=importlib.util.module_from_spec(s);s.loader.exec_module(c);d=c.d
PHASES=['CH-wave1','CH-wave2','AR-wave1','UY-wave1','PY-wave1']

def main(extra=False):
    rows=[dict(r,catalogue_phase=p) for p in PHASES for r in d.pinned(p)[0]['records']]
    groups=collections.defaultdict(list);held=[];matches={}
    for r in rows:
        if r.get('artist_id') and r.get('year_end') and r['year_end']<=1955 and r['source_type'] in ['painting','drawing','watercolor']:
            groups[r['artist_id']].append(r)
    with d.connect() as db:
        profiles={x['entity_id']:x['canonical_url'] for x in db.execute("SELECT entity_id::text,canonical_url FROM external_identifiers WHERE entity_type='artist' AND scheme='wikiart-artist' AND entity_id=ANY(%s::uuid[])",(list(groups),))}
    if extra:profiles=d.load(c.RUN/'wikiart/extra-citation-profiles.json.gz')
    suffix='-extra' if extra else ''
    d.save(c.RUN/('wikiart/selected-creator-scope'+suffix+'.json.gz'),dict(groups=groups,profiles=profiles))
    for n,(aid,works) in enumerate(groups.items(),1):
        profile=profiles.get(aid)
        if not profile:continue
        path=c.RUN/'wikiart/creator-results'/(aid+'.json.gz')
        if path.exists():
            result=d.load(path);matches.update(result['matches']);held.extend(result['held']);continue
        accepted={};gaps=[]
        try:
            raw,rc=c.capture(profile.rstrip('/')+'/all-works/text-list');p=BeautifulSoup(raw,'html.parser');index=collections.defaultdict(dict)
            for li in p.select('li'):
                for a in li.select('a[href]'):
                    url=urljoin(profile,a['href'])
                    if url.startswith(profile.rstrip('/')+'/') and 'all-works' not in url:index[d.norm(a.get_text(' ',strip=True))][url]=li.get_text(' ',strip=True)
            for r in works:
                titles={d.norm(r['title'])}
                native=r['raw'].get('native',{})
                for labels in native.get('ObjSearchTitleTxt',[]):titles.update(d.norm(v) for k,v in labels.items() if k.startswith('LabelTxt'))
                candidates={url:caption for title in titles for url,caption in index[title].items()}
                candidates={url:cap for url,cap in candidates.items() if (years:=re.findall(r'\b[12]\d{3}\b',cap)) and (min(map(int,years)),max(map(int,years)))==(r['year_start'],r['year_end'])}
                if len(candidates)!=1:continue
                url=next(iter(candidates));raw2,rc2=c.capture(url);sp=BeautifulSoup(raw2,'html.parser');tag=sp.select_one('.wiki-layout-painting-info-bottom[ng-init]')
                if not tag:continue
                md=json.loads(tag['ng-init'].split('=',1)[1].strip());years=re.findall(r'\b[12]\d{3}\b',str(md.get('year') or ''))
                if not years or (min(map(int,years)),max(map(int,years)))!=(r['year_start'],r['year_end']):continue
                if md['artistUrl'].rstrip('/')!=urlsplit(profile).path.rstrip('/') or d.norm(md['title']) not in titles:continue
                if d.norm(md['title']) in {'portrait','self portrait','landscape','still life','untitled','nude','composition','study','sketch','pieta'}:
                    gaps.append(dict(key=r['key'],reason='Generic title requires additional object/version evidence',url=url));continue
                loc=sp.find(string=re.compile(r'^\s*Location:\s*$'));location=loc.parent.parent.get_text(' ',strip=True) if loc else ''
                if r['provider']=='swiss-basel' and location and 'basel' not in location.lower():
                    gaps.append(dict(key=r['key'],reason='Explicit WikiArt collection differs',location=location,url=url));continue
                im=sp.select_one('img[itemprop=image]');copyright=sp.select_one('.copyright-wrapper .copyright')
                if not im or not im.get('src'):continue
                with d.connect() as db:
                    prior=list(db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND ((scheme='wikiart-native-id' AND external_id=%s) OR canonical_url=%s)",(str(md['_id']),url)))
                if any(x['entity_id']!=r['artwork_id'] for x in prior):
                    gaps.append(dict(key=r['key'],artwork_id=r['artwork_id'],reason='Image source belongs to another existing catalogue identity; requires reconciliation',matches=prior,url=url,native_title=r['title'],wikiart=md));continue
                pd=bool(copyright and copyright.select_one('.copyright-icon-public-domain'))
                accepted[r['key']]=dict(image_url=im['src'],image_license_url='https://www.wikiart.org/en/terms-of-use',image_rights_status='public_domain' if pd else 'restricted' if copyright else 'unknown',image_rights_label=copyright.get_text(' ',strip=True) if copyright else 'Rights not specified',image_source_provider='WikiArt',image_source_page_url=url,image_source_record_id=str(md['_id']),image_identifier_scheme='wikiart-native-id',image_evidence=rc2,image_identity_confidence=.94,image_identity_basis='Exact verified creator, unique source title/explicit native translation and identical creation bounds; generic titles, print impressions, casts and conflicting holdings excluded.',image_rights_basis='User-approved WikiArt source policy of 6 October 2026; actual per-image rights label retained separately.',wikiart_metadata=md,wikiart_location=location,catalogue_phase=r['catalogue_phase'])
        except Exception as error:gaps.append(dict(profile=profile,reason=str(error)[:300]))
        result=dict(artist_id=aid,profile=profile,matches=accepted,held=gaps);d.save(path,result);matches.update(accepted);held.extend(gaps)
        if n%10==0:print('WikiArt creator scopes',n,'/',len(groups),'matched',len(matches),flush=True)
    d.save(c.RUN/('wikiart/matches'+suffix+'.json.gz'),dict(matches=matches,held=held));print('WikiArt matched',len(matches),'held',len(held),flush=True)

if __name__=='__main__':main(extra='--extra-citation-profiles' in sys.argv)
