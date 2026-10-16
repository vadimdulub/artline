#!/usr/bin/env python3
"""Resumable official exhibition datasets; metadata and native object links only."""
import argparse
import collections
import csv
import datetime as dt
import io
import json
import time

import exhibitions_common as c


def write_page(provider, page, rows):
    c.save(c.DATA / 'normalized' / provider / f'{page:05d}.json.gz', rows)
    print(json.dumps(dict(provider=provider, page=page, records=len(rows),
                         entries=sum(len(r['entries']) for r in rows))), flush=True)


def moma():
    url = 'https://raw.githubusercontent.com/MuseumofModernArt/exhibitions/master/MoMAExhibitions1929to1989.csv'
    raw, rc = c.capture(url)
    groups = collections.defaultdict(list)
    try:
        text = raw.decode('utf-8-sig')
        encoding = 'utf-8-sig'
    except UnicodeDecodeError:
        text = raw.decode('cp1252')
        encoding = 'cp1252'
    for r in csv.DictReader(io.StringIO(text)):
        # ExhibitionID is absent for 61 events; "No#" is also reused.
        # The museum's documented sort-order identifier is complete and unique.
        groups[r['ExhibitionSortOrder']].append(r)
    rows = []
    def date(s):
        if not s:
            return None
        try:
            return dt.datetime.strptime(s, '%m/%d/%Y').date().isoformat()
        except ValueError:
            return None
    for key, source in groups.items():
        first = source[0]
        url = first['ExhibitionURL'] or 'https://github.com/MuseumofModernArt/exhibitions/blob/master/MoMAExhibitions1929to1989.csv'
        if not url.startswith('http'):
            url = 'https://' + url
        r = c.event('moma', 'sort-'+key, first['ExhibitionTitle'], url, rc,
                    date(first['ExhibitionBeginDate']), date(first['ExhibitionEndDate']), format='physical')
        for field in ['ExhibitionTitle', 'ExhibitionBeginDate', 'ExhibitionEndDate']:
            if len({s[field] for s in source}) > 1:
                raise ValueError(f'Inconsistent MoMA event {key}: {field}')
        r['source_payload'] = dict(exhibition={k:v for k,v in first.items() if k.startswith('Exhibition') and 'Role' not in k}, constituents=source, encoding=encoding)
        r['occurrences'] = [dict(venue_label='The Museum of Modern Art', city_label='New York', country_code='US', institution_source='moma', start_date=r['start_date'], end_date=r['end_date'])]
        seen = set()
        for p in source:
            personkey = (p['ConstituentID'], p['ExhibitionRole'], p['DisplayName'])
            if personkey in seen or not p['DisplayName']:
                continue
            seen.add(personkey)
            r['participants'].append(dict(name_label=p['DisplayName'], role=p['ExhibitionRole'] or 'participant', source_person_id=p['ConstituentID'], source_scheme='moma-artist', evidence=p))
        rows.append(r)
    write_page('moma', 1, rows)


def aic():
    page = 1
    seen = set()
    while True:
        url = 'https://api.artic.edu/api/v1/exhibitions'
        raw, rc = c.capture(url, dict(limit=100, page=page, fields='id,api_link,title,web_url,status,aic_start_at,aic_end_at,gallery_id,gallery_title,artwork_ids,artwork_titles,artist_ids,document_ids'))
        doc = json.loads(raw)
        rows = []
        for s in doc['data']:
            if s['id'] in seen:
                raise ValueError(f"Repeated AIC ID {s['id']}")
            seen.add(s['id'])
            r = c.event('aic', s['id'], s['title'], s.get('web_url') or s['api_link'], rc,
                        s.get('aic_start_at'), s.get('aic_end_at'), source_payload=s)
            if r['start_date'] or r['end_date']:
                r['format'] = 'physical'
                r['occurrences'] = [dict(venue_label='Art Institute of Chicago', city_label='Chicago', country_code='US', institution_source='aic', start_date=r['start_date'], end_date=r['end_date'], evidence={'gallery_id':s.get('gallery_id'),'gallery_title':s.get('gallery_title')})]
            for aid, title in zip(s.get('artwork_ids') or [], s.get('artwork_titles') or []):
                r['entries'].append(dict(source_artwork_id=str(aid), title_label=title, source_scheme='aic-object', participation='exhibited', evidence={'field':'artwork_ids','exhibition_id':s['id']}))
            # Preserve IDs even where the title array is shorter or absent.
            done = {x['source_artwork_id'] for x in r['entries']}
            for aid in s.get('artwork_ids') or []:
                if str(aid) not in done:
                    r['entries'].append(dict(source_artwork_id=str(aid), source_scheme='aic-object', participation='exhibited', evidence={'field':'artwork_ids','exhibition_id':s['id']}))
            if r['entries']:
                r['checklist_state'] = 'partial'
            for docid in s.get('document_ids') or []:
                r['publications'].append(dict(publication_type='other', source_identifier=str(docid), url=f'https://api.artic.edu/api/v1/assets/{docid}', evidence={'field':'document_ids','type_unverified':True}))
            rows.append(r)
        write_page('aic', page, rows)
        if page >= doc['pagination']['total_pages']:
            break
        page += 1
        time.sleep(.4)
    c.save(c.RUN / 'aic-collection-summary.json', dict(records=len(seen), pages=page, source_total=doc['pagination']['total']))


def cleveland():
    page = 1
    seen = set()
    while True:
        raw, rc = c.capture('https://openaccess-api.clevelandart.org/api/exhibitions/', dict(limit=100, skip=(page-1)*100, include_artworks=1))
        doc = json.loads(raw)
        rows = []
        for s in doc['data']:
            if s['id'] in seen:
                raise ValueError(f"Repeated Cleveland ID {s['id']}")
            seen.add(s['id'])
            r = c.event('cleveland', s['id'], s['title'], f"https://openaccess-api.clevelandart.org/api/exhibitions/{s['id']}", rc,
                        s.get('opening_date'), s.get('closing_date'), source_payload=s, format='physical')
            for venue in s.get('venues') or []:
                r['occurrences'].append(dict(venue_label=venue.get('name'), source_venue_id=str(venue.get('venue_id','')),
                    start_date=c.exact_date(venue.get('start_date')), end_date=c.exact_date(venue.get('end_date')), evidence=venue))
            if s.get('organizer'):
                r['participants'].append(dict(name_label=s['organizer'], role='organizer', evidence={'field':'organizer'}))
            for a in s.get('artworks') or []:
                if not isinstance(a, dict):
                    raise ValueError('Unexpected Cleveland artwork representation')
                r['entries'].append(dict(source_artwork_id=str(a['id']), title_label=a.get('title'), source_scheme='cleveland-object', participation='exhibited', evidence=a))
            if r['entries']:
                r['checklist_state']='partial'
            for field,kind in [('catalog_urls','catalogue'),('press_release_urls','press_release'),('gallery_views_urls','installation')]:
                for url in s.get(field) or []:
                    r['publications'].append(dict(publication_type=kind, url=url, evidence={'field':field}))
            rows.append(r)
        write_page('cleveland', page, rows)
        if page * 100 >= doc['info']['total'] or not doc['data']:
            break
        page += 1
        time.sleep(.5)
    c.save(c.RUN / 'cleveland-collection-summary.json', dict(records=len(seen), pages=page, source_total=doc['info']['total']))


def decode_nuxt(data):
    def decode(i):
        if i < 0:
            return None
        value = data[i]
        if isinstance(value, dict):
            return {k:decode(v) for k,v in value.items()}
        if isinstance(value, list):
            if value and isinstance(value[0], str):
                return decode(value[1]) if len(value)>1 else value
            return [decode(v) for v in value]
        return value
    return decode(0)


def apj():
    from bs4 import BeautifulSoup
    offset = 0
    page = 1
    seen = set()
    while True:
        raw,rc=c.capture('https://artplatform.go.jp/exhibitions/', {'from':offset, 'limit':500})
        soup=BeautifulSoup(raw,'html.parser')
        doc=decode_nuxt(json.loads(soup.select_one('#__NUXT_DATA__').text))['data']['exhibition-index-en']
        rows=[]
        for s in doc['items']:
            if s['id'] in seen:
                raise ValueError('Repeated APJ ID: '+s['id'])
            seen.add(s['id'])
            period=(s.get('period') or {}).get('ja') or (s.get('period') or {}).get('en') or ''
            dates=period.split('/')
            title=s['title'].get('ja') or s['title'].get('en')
            r=c.event('apj',s['id'],title,'https://artplatform.go.jp/exhibitions/'+s['id'],rc,
                      dates[0] if dates else None,dates[1] if len(dates)==2 else None,source_payload=s,
                      alternate_titles=[v for k,v in s['title'].items() if v and v != title],date_display=period)
            venue=(s.get('venue') or {}).get('ja') or (s.get('venue') or {}).get('en')
            if venue:
                r['occurrences']=[dict(venue_label=venue,start_date=r['start_date'],end_date=r['end_date'],date_display=period,evidence={'field':'venue','source_label':s['venue']})]
            for organizer in s.get('organizers') or []:
                name=organizer['agent'].get('ja') or organizer['agent'].get('en')
                if name:
                    r['participants'].append(dict(name_label=name,role='organizer',evidence=organizer))
            rows.append(r)
        write_page('apj',page,rows)
        offset += len(doc['items'])
        if offset >= doc['total'] or not doc['items']:
            break
        page += 1
        time.sleep(.5)
    c.save(c.RUN/'apj-collection-summary.json',dict(records=len(seen),pages=page,source_total=doc['total']))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('provider',choices=['moma','aic','cleveland','apj'])
    args=parser.parse_args()
    globals()[args.provider]()
