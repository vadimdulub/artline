#!/usr/bin/env python3
"""Publisher's public catalogue-download query, including explicit touring IDs."""
import json
import re
import time

import exhibitions_common as c
from exhibitions_collect import write_page


def label(value):
    value=value or {}
    return value.get('ja') or value.get('en')


def parse_period(period):
    """Recognize explicit full ranges, retaining all original display text.

    Do not complete abbreviated ranges, uncertain years or missing days.
    """
    def day(value):
        m=re.fullmatch(r'(\d{4})[.-](\d{1,2})[.-](\d{1,2})',value.strip())
        return c.exact_date(f'{int(m[1]):04d}-{int(m[2]):02d}-{int(m[3]):02d}') if m else None
    text=(period or '').strip()
    m=re.fullmatch(r'(\d{4}\.\d{1,2}\.\d{1,2})\s*-\s*(\d{4}\.\d{1,2}\.\d{1,2})',text)
    if not m:m=re.fullmatch(r'(\d{4}-\d{1,2}-\d{1,2})/(\d{4}-\d{1,2}-\d{1,2})(?:［[^］]*］)?',text)
    if m:return day(m[1]),day(m[2])
    return day(text),None


def collect():
    raw,_=c.capture('https://artplatform.go.jp/_nuxt/OHWRKyxP.js')
    query=re.search(r'SearchExhibitionsDownloadData:.*?e\.request\(`(.*?)`,i,',raw.decode(),re.S).group(1)
    # These are public fields also selected by the provider's single-event page.
    query=query.replace('artists {\n          label','artists {\n          artistID\n          label')
    offset=0;page=1;seen=set()
    while True:
        raw,rc=c.capture('https://api.artplatform.go.jp/graphql',{'query':query,'variables':json.dumps({'limit':500,'from':offset,'sort':{'field':'id','direction':'asc'}})})
        doc=json.loads(raw)
        if doc.get('errors'):raise ValueError(json.dumps(doc['errors']))
        data=doc['data']['searchExhibitions'];rows=[]
        for s in data['items']:
            if s['id'] in seen:raise ValueError('Repeated APJ record '+s['id'])
            seen.add(s['id']);period=label(s.get('period')) or '';start,end=parse_period(period)
            title=label(s['title'])
            r=c.event('apj_full',s['id'],title,'https://artplatform.go.jp/exhibitions/'+s['id'],rc,
                start,end,
                source_payload=s,alternate_titles=[v for k,v in s['title'].items() if k in ['ja','en'] and v and v!=title],date_display=period)
            r['canonical_source_id']=s.get('tourStartExhibitionID') or s['id']
            r['identity_basis']='Publisher tourStartExhibitionID groups venue occurrences into one exhibition'
            if label(s.get('venue')) or label(s.get('venueLocale')):
                r['occurrences']=[dict(venue_label=label(s.get('venue')),city_label=label(s.get('venueLocale')),start_date=r['start_date'],end_date=r['end_date'],date_display=period,
                    evidence={'venue':s.get('venue'),'venueLocale':s.get('venueLocale'),'tourIndex':s.get('tourIndex'),'tourStartExhibitionID':s.get('tourStartExhibitionID'),'locale_note':'Original source locality retained; may name a city, region or country'})]
            for field,role in [('organizers','organizer'),('curators','curator')]:
                for person in s.get(field) or []:
                    name=label(person.get('agent'))
                    if name:r['participants'].append(dict(name_label=name,role=role,evidence=person))
            people=set()
            for group in s.get('artistClassification') or []:
                for a in group.get('artists') or []:
                    name=label(a.get('label'));key=(a.get('artistID'),name)
                    if name and key not in people:
                        people.add(key);r['participants'].append(dict(name_label=name,role='artist',source_person_id=a.get('artistID'),source_scheme='apj-artist',evidence=a))
            for b in (s.get('bibliographies') or {}).get('items') or []:
                entry=b.get('bibliography') or {}
                r['publications'].append(dict(publication_type='other',source_identifier=b.get('bibliographyID') or entry.get('id'),title_label=label(entry.get('title')),evidence=b))
            r['source_bibliography']=s.get('source')
            rows.append(r)
        write_page('apj_full',page,rows)
        offset+=len(rows)
        if len(rows)<500:break
        page+=1;time.sleep(.5)
    c.save(c.RUN/'apj-full-summary.json',dict(records=len(seen),pages=page,source_total=c.load(c.RUN/'apj-collection-summary.json')['source_total'],identity='Explicit tourStartExhibitionID; touring stops are source records, not additional exhibitions'))


if __name__=='__main__':collect()
