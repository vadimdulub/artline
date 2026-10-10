#!/usr/bin/env python3
"""Independent approved WikiArt matching for remaining named-creator image gaps."""
import importlib.util,json,re,hashlib
from pathlib import Path
from collections import defaultdict,Counter
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('secondary',Path(__file__).with_name('source-index-secondary-20261010.py'));sec=importlib.util.module_from_spec(s);s.loader.exec_module(sec);m=sec.m;n=sec.n;r=sec.r;RUN=r.RUN

def run():
    inv=m.load(RUN/'inventory.json.gz');works={w['id']:w for w in inv['artworks'] if not w['primary_media_id'] and w['status']!='archived'};profiles={e['entity_id']:e['canonical_url'] for e in inv['artist_identifiers'] if e['scheme']=='wikiart-artist'};groups=defaultdict(dict);seen=set()
    for p in (RUN/'prepared-images').glob('*.json'):
        x=m.load(p)
        if x['state']=='prepared':seen.add(x['artwork_id'])
    for c in inv['creators']:
        if c['artwork_id'] in works and c['artwork_id'] not in seen and c['artist_id'] in profiles and c['attribution_role']=='primary':groups[c['artist_id']][c['artwork_id']]=works[c['artwork_id']]
    resources=defaultdict(set)
    for source in m.resources():
        for b in source['artline_bindings']:
            if b['entity_type']=='artwork':resources[b['entity_id']].add(source['id'])
    accepted=[];held=[]
    for i,(artist_id,ww) in enumerate(sorted(groups.items()),1):
        profile=profiles[artist_id].rstrip('/');receipt=None
        try:
            raw,receipt=n.f.get(profile+'/all-works/text-list');sp=BeautifulSoup(raw,'html.parser');index=defaultdict(dict)
            for li in sp.select('li'):
                for a in li.select('a[href]'):
                    url=urljoin(profile,a['href'])
                    if url.startswith(profile+'/') and 'all-works' not in url:index[r.norm(a.get_text(' ',strip=True))][url]=li.get_text(' ',strip=True)
            for aid,w in ww.items():
                titles={r.norm(w['title'])}
                if w.get('alternate_title'):titles.add(r.norm(w['alternate_title']))
                if w['work_type'] in ('sculpture','print') or r.norm(w['title']) in {'portrait','self portrait','landscape','still life','untitled','nude','composition'}:held.append(dict(artwork_id=aid,reason='Generic title or edition/cast requires stronger independent identity evidence'));continue
                matches={url:caption for t in titles for url,caption in index[t].items()}
                matches={url:caption for url,caption in matches.items() if re.findall(r'\b[12]\d{3}\b',caption) and min(map(int,re.findall(r'\b[12]\d{3}\b',caption)))==w['creation_year_start'] and max(map(int,re.findall(r'\b[12]\d{3}\b',caption)))==w['creation_year_end']}
                if len(matches)!=1:held.append(dict(artwork_id=aid,reason='No unique exact title and creation date on approved creator profile',matches=len(matches)));continue
                url=next(iter(matches));raw2,rc=n.f.get(url);sp2=BeautifulSoup(raw2,'html.parser');tag=sp2.select_one('.wiki-layout-painting-info-bottom[ng-init]');assert tag;obj=json.loads(tag['ng-init'].split('=',1)[1].strip());lo,hi,precision=n.date_parse(str(obj.get('year') or ''))
                assert (lo,hi)==(w['creation_year_start'],w['creation_year_end']) and hi<=1970 and r.norm(obj['title']) in titles;assert urljoin('https://www.wikiart.org',obj['artistUrl']).rstrip('/')==profile
                location=sp2.find(string=re.compile(r'^\s*Location:\s*$'));location=location.parent.parent.get_text(' ',strip=True) if location else None
                # This secondary match must not override an explicit different collection or an ambiguous physical version.
                institution=next((x for x in inv['institutions'] if x['id']==w['current_institution_id']),None)
                if location and institution:
                    tokens={x for x in r.norm(institution['name']).split() if len(x)>=5 and x not in {'museum','gallery','national','collection','state','fine','arts','kunst'}}
                    if tokens and not any(x in r.norm(location) for x in tokens):held.append(dict(artwork_id=aid,reason='Explicit WikiArt holding not reconciled with existing museum',url=url,location=location));continue
                im=sp2.select_one('img[itemprop=image]');assert im and im.get('src');copyright=sp2.select_one('.copyright-wrapper .copyright');rights=copyright.get_text(' ',strip=True) if copyright else 'No per-image rights label stated';pd=bool(copyright and copyright.select_one('.copyright-icon-public-domain'))
                facts=dict(native_id=str(obj['_id']),scheme='wikiart-native-id',accession=None,titles=[obj['title']],dates=dict(display=str(obj.get('year') or ''),start=lo,end=hi),date_precision=precision,medium=None,dimensions=None,page=url,creator_labels=[obj.get('artistName')],creator_authorities=[],qualified_creators=[],raw_creator_data=obj['artistUrl'],image=im['src'],image_open=True,image_rights=rights,rights_status='public_domain' if pd else 'restricted',rights_basis='User-approved WikiArt source policy, 6 October 2026; actual rights label retained separately from user approval.',license_url='https://www.wikiart.org/en/terms-of-use',credit='WikiArt',institution_id=w['current_institution_id'],work_type=w['work_type'],holding_qualified=False)
                dest=RUN/'secondary-native/wikiart-independent'/(aid+'.json.gz');m.save(dest,dict(provider='wikiart',key=str(obj['_id']),state='captured',facts=facts,raw=obj,receipt=rc,creator_index_receipt=receipt,identity_confidence=.94,identity_basis='Exact existing linked creator and official WikiArt artist profile; unique supplied artwork title and exact creation bounds; generic titles, prints, casts and conflicting explicit holdings excluded.',source_index_ids=sorted(resources[aid])))
                accepted.append(dict(provider='wikiart',key=str(obj['_id']),native_file=str(dest.relative_to(m.ROOT)),artwork_id=aid,state='existing',title=w['title'],matched_ids=[aid],identity_basis=['Exact existing linked creator authority and WikiArt profile','Unique exact artwork title and source creation bounds','Explicit source holding checked when supplied; no catalogue holding changes'],creator_links=[],unlinked_creator_label=None,image_candidate=True,field_updates={},source_index_ids=sorted(resources[aid])))
        except Exception as e:held.append(dict(artist_id=artist_id,profile=profile,reason=type(e).__name__+': '+str(e)[:250]))
        if i%10==0:print('Independent WikiArt',i,'/',len(groups),'creators; supported matches',len(accepted),flush=True)
    m.save(RUN/'independent-wikiart-resolution.json.gz',dict(at=m.now(),creators=len(groups),works=sum(map(len,groups.values())),rows=accepted,held=held));print('Independent WikiArt selected',len(accepted),flush=True)

if __name__=='__main__':run()
