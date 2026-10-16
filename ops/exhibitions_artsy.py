#!/usr/bin/env python3
"""Public, closed, non-fair exhibition records from Artsy's documented GraphQL API.

No credentials or introspection. Provider IDs, original fields and bounded
artwork samples are retained; date anomalies and cancellations cannot count.
"""
import argparse
import base64
import datetime as dt
import json
import re
import time

import exhibitions_common as c
from exhibitions_collect import write_page

FIELDS = '''internalID slug name startAt endAt status isFairBooth isOnlineExclusive
isReference isStubShow city
partner { __typename ... on Partner { internalID slug name type } ... on ExternalPartner { internalID name } }
location { city country }
artists { internalID slug name }
artworksConnection(first: 5) { totalCount pageInfo { hasNextPage } edges { node { internalID slug title date artistNames } } }'''


def normalize(s, rc):
    r = c.event('artsy',s['internalID'],s['name'],'https://www.artsy.net/show/'+s['slug'],rc,
                s.get('startAt'),s.get('endAt'),source_payload=s,
                format='online' if s.get('isOnlineExclusive') else 'physical')
    issues=[]
    if s.get('isFairBooth'):
        issues.append('fair_booth_not_independent_exhibition')
    if s.get('isStubShow'):
        issues.append('local_discovery_stub_requires_primary_confirmation')
    if s.get('status') != 'closed':
        issues.append('source_not_closed')
    if not r['start_date'] or not r['end_date']:
        issues.append('missing_full_event_dates')
    elif r['start_date'] < '1600-01-01' or (dt.date.fromisoformat(r['end_date'])-dt.date.fromisoformat(r['start_date'])).days > 3653:
        issues.append('implausible_dates_for_this_modern_exhibition_platform')
    if r['date_conflict']:
        issues.append('reversed_date_range')
    if re.search(r'\b(cancelled|canceled|postponed)\b',s['name'],re.I):
        r['event_state']='cancelled'
        issues.append('source_title_reports_cancellation_or_postponement')
    if re.search(r'^(untitled|test|sample show|new show|coming soon|tbd|n/?a)\W*$',s['name'],re.I):
        issues.append('generic_or_test_title_requires_review')
    if issues:
        if r['event_state']!='cancelled':
            r['event_state']='uncertain'
        r['state_basis']='Source fields require review: '+', '.join(issues)
    else:
        r['state_basis']='Provider identifies a closed non-fair exhibition; explicit historical dates preserved. No independent attendance or installation verification asserted.'
    r['research_issues']=issues
    partner=s.get('partner') or {}
    location=s.get('location') or {}
    if partner.get('name'):
        r['participants'].append(dict(name_label=partner['name'],role='presenting_organization',source_person_id=partner.get('internalID'),evidence={'field':'partner','source':partner}))
        # A presenter's name is not a physical host for a source-labelled online show.
        if not s.get('isOnlineExclusive'):
            country=location.get('country')
            r['occurrences']=[dict(venue_label=partner['name'],source_venue_id=partner.get('internalID'),city_label=location.get('city') or s.get('city'),country_label=country,
                country_code=country if country and re.fullmatch('[A-Z]{2}',country) else None,
                start_date=r['start_date'],end_date=r['end_date'],evidence={'partner':partner,'location':location,'venue_basis':'Source exhibition presenter and reported show location; no museum identity inferred'})]
    for a in s.get('artists') or []:
        if not a.get('name'):
            continue
        r['participants'].append(dict(name_label=a['name'],role='artist',source_person_id=a['internalID'],source_scheme='artsy-artist',evidence=a))
    works=s.get('artworksConnection') or {}
    for edge in works.get('edges') or []:
        a=edge['node']
        r['entries'].append(dict(source_artwork_id=a['internalID'],title_label=a.get('title'),creator_label=a.get('artistNames'),date_label=a.get('date'),
            source_scheme='artsy-artwork',participation='catalogued',evidence={'source':'Artsy show artworksConnection','url':'https://www.artsy.net/artwork/'+a['slug'],'artwork':a,
                'interpretation':'Public artwork listed with this exhibition; no independent physical-installation claim.'}))
    # API completeness refers only to the public online list, never a certified final checklist.
    r['checklist_state']='partial' if r['entries'] else 'unknown'
    r['public_artwork_list']={'total':works.get('totalCount'),'retrieved':len(r['entries']),'has_more':(works.get('pageInfo') or {}).get('hasNextPage'),'scope':'public online listing'}
    return r


def collect(start_page=1, pages=1500, size=100):
    for page in range(start_page,start_page+pages):
        dest=c.DATA/'normalized/artsy'/f'{page:05d}.json.gz'
        if dest.exists():
            continue
        offset=(page-1)*size
        after='' if offset==0 else ', after: '+json.dumps(base64.b64encode(f'arrayconnection:{offset-1}'.encode()).decode())
        query='query ArtlineExhibitionResearch { showsConnection(first: '+str(size)+after+', status: CLOSED, atAFair: false, sort: START_AT_ASC) { totalCount pageInfo { hasNextPage endCursor } edges { node { '+FIELDS+' } } } }'
        started=time.monotonic()
        for attempt in range(3):
            retry_query=query if attempt==0 else query.replace('ArtlineExhibitionResearch','ArtlineExhibitionResearchRetry'+str(attempt),1)
            raw,rc=c.capture('https://metaphysics-cdn.artsy.net/v2',{'query':retry_query})
            doc=json.loads(raw)
            if (doc.get('data') or {}).get('showsConnection'):
                break
            if not doc.get('errors') or not all('TIME' in x.get('message','').upper() for x in doc['errors']):
                raise ValueError('GraphQL errors: '+json.dumps(doc.get('errors')))
            if attempt==2:
                raise ValueError('Repeated provider timeout: '+json.dumps(doc['errors']))
            time.sleep(5)
        data=doc['data']['showsConnection']
        for error in doc.get('errors') or []:
            path=error.get('path') or []
            if len(path)>=5 and path[:2]==['showsConnection','edges'] and path[-1]=='artworksConnection':
                data['edges'][path[2]]['node'].setdefault('artwork_query_errors',[]).append(error)
            else:
                raise ValueError('Unexpected partial GraphQL error: '+json.dumps(error))
        excluded=[x['node'] for x in data['edges'] if not (x.get('node') or {}).get('name','') or not x['node']['name'].strip()]
        if excluded:
            c.save(c.RUN/'artsy-exclusions'/f'{page:05d}.json',dict(reason='Missing source exhibition title; no invented title',records=excluded,receipt=rc))
        rows=[normalize(x['node'],rc) for x in data['edges'] if x['node'] not in excluded]
        if len({r['native_id'] for r in rows})!=len(rows):
            raise ValueError('Duplicate IDs within source page')
        write_page('artsy',page,rows)
        c.save(c.RUN/'artsy-pages'/f'{page:05d}.json',dict(page=page,size=size,source_total=data['totalCount'],page_info=data['pageInfo'],records=len(rows),held=sum(r['event_state']=='held' for r in rows),seconds=round(time.monotonic()-started,2),receipt=rc))
        if not data['pageInfo']['hasNextPage']:
            break
        time.sleep(.6)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--start-page',type=int,default=1);p.add_argument('--pages',type=int,default=1500);p.add_argument('--size',type=int,default=100)
    a=p.parse_args();collect(a.start_page,a.pages,a.size)
