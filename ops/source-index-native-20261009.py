#!/usr/bin/env python3
"""Refresh selected native object records and propose evidence-backed gap fills.

Only records bound by exact museum inventory/native IDs are fetched. No DB writes.
"""
import argparse
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlencode, urlsplit, unquote

spec=importlib.util.spec_from_file_location('fetch',Path(__file__).with_name('source-index-fetch-20261009.py'))
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
m=f.m;RUN=m.RUN


def norm(v):
    return re.sub(r'[^\w]+','',unicodedata.normalize('NFKD',str(v or '')).encode('ascii','ignore').decode().lower())


def native_fields(provider,o):
    if provider=='cleveland':
        return dict(native_id=str(o['id']),accession=o['accession_number'],titles=[o['title']]+(o.get('alternate_titles') or []),
            dates=dict(display=o.get('creation_date'),start=o.get('creation_date_earliest'),end=o.get('creation_date_latest')),
            medium=o.get('technique'),dimensions=o.get('measurements'),page=o['url'],
            creator_labels=[c.get('description') for c in o.get('creators',[])],
            qualified_creators=[c for c in o.get('creators',[]) if c.get('qualifier') or c.get('extent')],
            image=(o.get('images') or {}).get('web',{}).get('url'),image_rights=o.get('share_license_status'),
            image_open=o.get('share_license_status')=='CC0' and not o.get('copyright'),
            credit=o.get('creditline'),copyright=o.get('copyright'),legal_status=o.get('legal_status'),
            bibliographic_references=o.get('citations',[]))
    if provider=='chicago':
        return dict(native_id=str(o['id']),accession=o['main_reference_number'],titles=[o['title']]+(o.get('alt_titles') or []),
            dates=dict(display=o.get('date_display'),start=o.get('date_start'),end=o.get('date_end')),
            medium=o.get('medium_display'),dimensions=o.get('dimensions'),page='https://www.artic.edu/artworks/'+str(o['id']),
            creator_labels=[o.get('artist_display') or o.get('artist_title')],qualified_creators=[],
            image='https://www.artic.edu/iiif/2/'+o['image_id']+'/full/843,/0/default.jpg' if o.get('image_id') else None,
            image_rights='Public domain; Art Institute CC0 image' if o.get('is_public_domain') else o.get('copyright_notice') or 'Not marked public domain',
            image_open=o.get('is_public_domain') is True and not o.get('copyright_notice'),credit=o.get('credit_line'),copyright=o.get('copyright_notice'),
            bibliographic_references=o.get('publication_history'))
    if provider=='smk':
        dates=o.get('production_date') or []
        def year(value):
            v=(value or '').split('-',1)[0]
            return int(v) if re.fullmatch(r'\d{1,4}',v) else None
        dim='; '.join(' '.join(str(d.get(k) or '') for k in ['part','type','value','unit']).strip() for d in o.get('dimensions',[]))
        makers=o.get('production',[])
        return dict(native_id=o['object_number'],accession=o['object_number'],titles=[t['title'] for t in o.get('titles',[])],
            dates=dict(display='; '.join(d.get('period','') for d in dates),start=year(dates[0].get('start')) if len(dates)==1 else None,end=year(dates[0].get('end')) if len(dates)==1 else None),
            medium='; '.join(o.get('techniques') or []),dimensions=dim or None,page=o.get('frontend_url') or 'https://open.smk.dk/artwork/image/'+o['object_number'],
            creator_labels=[c.get('creator') for c in makers],qualified_creators=[c for c in makers if c.get('creator_role') or c.get('creator_qualifier')],
            image=(o.get('image_iiif_id')+'/full/1200,/0/default.jpg') if o.get('image_iiif_id') else None,
            image_rights=o.get('rights'),image_open=o.get('public_domain') is True and o.get('rights')=='https://creativecommons.org/publicdomain/mark/1.0/',
            credit='Statens Museum for Kunst, Copenhagen',copyright=None,bibliographic_references=o.get('documentation',[]))
    raise ValueError(provider)


def selection():
    d=m.load(RUN/'catalogue-export.json.gz')
    institutions={i['id']:i for i in d['institutions']}
    urls=defaultdict(list)
    for v in d['citations']+d['identifiers']:
        u=v.get('source_url') or v.get('canonical_url')
        if u:urls[v['entity_id']].append(u)
    out=[];held=[]
    for w in d['artworks']:
        name=institutions[w['current_institution_id']]['name']
        provider=('cleveland' if re.search('Cleveland Museum of Art',name,re.I) else
                  'chicago' if re.search('Art Institute of Chicago',name,re.I) else
                  'smk' if re.search('Statens Museum|National Gallery of Denmark',name,re.I) else None)
        if not provider:continue
        native_ids=set()
        for url in urls[w['id']]:
            h=m.host(url);p=unquote(urlsplit(url).path)
            if provider=='chicago' and h in ['artic.edu','api.artic.edu']:
                match=re.search(r'/artworks/(\d+)',p)
                if match:native_ids.add(match.group(1))
            if provider=='cleveland' and h=='openaccess-api.clevelandart.org':
                match=re.search(r'/artworks/(\d+)',p)
                if match:native_ids.add(match.group(1))
        target=dict(artwork=w,provider=provider,institution=institutions[w['current_institution_id']],existing_source_urls=sorted(set(urls[w['id']])),native_ids=sorted(native_ids))
        if len(native_ids)>1 or (provider=='chicago' and len(native_ids)!=1) or (provider!='chicago' and not w.get('accession_number')):
            held.append(dict(target,reason='Missing or conflicting exact native binding'));continue
        out.append(target)
    m.save(RUN/'native-targets.json.gz',dict(selected=out,held=held))
    print('Native selection',dict(Counter(r['provider'] for r in out)),'held',len(held),flush=True)


def fetch_one(t):
    w=t['artwork'];p=t['provider'];dest=RUN/'native-objects'/(w['id']+'.json')
    if dest.exists():return m.load(dest)
    r=dict(artwork_id=w['id'],provider=p,target=t)
    try:
        if p=='cleveland':
            url='https://openaccess-api.clevelandart.org/api/artworks/?'+urlencode({'accession_number':w['accession_number'],'limit':5})
        elif p=='chicago':
            url='https://api.artic.edu/api/v1/artworks/'+t['native_ids'][0]
        else:
            url='https://api.smk.dk/api/v1/art?'+urlencode({'object_number':w['accession_number']})
        data,rc=f.get(url,True)
        rows=data['items'] if p=='smk' else data['data'] if p=='cleveland' else [data['data']]
        if len(rows)!=1:raise ValueError('Exact lookup must return one object')
        o=rows[0];facts=native_fields(p,o)
        if p=='chicago' and facts['native_id']!=t['native_ids'][0]:raise ValueError('Native ID differs')
        if p!='chicago' and facts['accession']!=w['accession_number']:raise ValueError('Exact inventory differs')
        r.update(state='captured',facts=facts,receipt=rc)
    except Exception as exc:
        r.update(state='held',reason=type(exc).__name__+': '+str(exc)[:400])
    m.save(dest,r)
    return r


def objects():
    if not (RUN/'native-targets.json.gz').exists():selection()
    targets=m.load(RUN/'native-targets.json.gz')['selected']
    with ThreadPoolExecutor(max_workers=3) as pool:
        for n,r in enumerate(pool.map(fetch_one,targets),1):
            if n%25==0:print('Native object metadata',n,'/',len(targets),flush=True)
    fresh=[]
    for t in targets:
        r=m.load(RUN/'native-objects'/(t['artwork']['id']+'.json'))
        if r['state']!='captured':continue
        facts=r['facts'];w=t['artwork']
        fresh.append(dict(url=facts['page'],title=facts['titles'][0],entity_type='artwork',entity_id=w['id'],
            kind='museum_or_collection_object',verified=r['receipt']['retrieved_at'],evidence=f.evidence(r['receipt'],facts['native_id']),facts=facts))
    m.save(RUN/'fresh-resources/native-objects.json',fresh)
    print('Fresh exact object records',len(fresh),flush=True)


def assess(r):
    if r['state']!='captured':return dict(artwork_id=r['artwork_id'],decision='hold',reasons=[r['reason']])
    w=r['target']['artwork'];facts=r['facts'];p=r['provider']
    reasons=[]
    target_titles={norm(w.get(k)) for k in ['title','alternate_title'] if w.get(k)}
    source_titles={norm(t) for t in facts['titles'] if isinstance(t,str) and norm(t)}
    title_match=bool(target_titles & source_titles)
    inventory_match=bool(w.get('accession_number')) and norm(w['accession_number'])==norm(facts['accession'])
    native_match=len(r['target']['native_ids'])==1 and r['target']['native_ids'][0]==facts['native_id']
    if not title_match:reasons.append('Title or translation needs individual review')
    if w.get('accession_number') and not inventory_match:reasons.append('Catalogue inventory conflicts')
    if not (inventory_match or native_match):reasons.append('No exact inventory or native ID identity')
    if facts.get('legal_status') and facts['legal_status']!='accessioned':reasons.append('Museum legal/holding state needs review')
    if facts['qualified_creators']:reasons.append('Qualified or multiple-role creator requires individual review')
    # This wave adds fields only to exact, consistent object identities.
    updates={}
    if not reasons:
        for field,key in [('medium_text','medium'),('dimensions_text','dimensions'),('accession_number','accession')]:
            value=facts.get(key)
            if (w.get(field) is None or not str(w[field]).strip()) and isinstance(value,str) and value.strip():
                updates[field]=value.strip()
    start,end=facts['dates']['start'],facts['dates']['end']
    image_reasons=[]
    if w.get('primary_media_id'):image_reasons.append('Existing primary image preserved')
    if not facts['image_open']:image_reasons.append('No explicit reusable source image rights')
    if not facts.get('image'):image_reasons.append('No source image')
    if start is None or end is None or end>1970 or start>end:image_reasons.append('Source creation date uncertain or beyond 1970')
    if w.get('creation_year_end') is None or w['creation_year_end']>1970 or w.get('date_precision') in ('unknown','after'):
        image_reasons.append('Catalogue creation scope requires editorial review')
    # Conflicting numeric bounds are preserved, but not automatically accepted for an image.
    if start is not None and end is not None and w.get('creation_year_start') is not None and w.get('creation_year_end') is not None:
        if end<w['creation_year_start'] or start>w['creation_year_end']:image_reasons.append('Source and catalogue date ranges do not overlap')
    return dict(artwork_id=w['id'],provider=p,title=w['title'],source_title=facts['titles'],decision='hold' if reasons else 'exact_identity',
        reasons=reasons,identity=dict(title_match=title_match,inventory_match=inventory_match,native_id_match=native_match,
            editorial_confidence=0.99 if not reasons else None,confidence_is_calibrated_probability=False),
        field_updates=updates,image_candidate=not reasons and not image_reasons,image_holds=image_reasons,
        source_dates=facts['dates'],catalogue_dates={k:w.get(k) for k in ['creation_year_start','creation_year_end','date_precision','date_display']},
        source_url=facts['page'],native_object_file=str((RUN/'native-objects'/(w['id']+'.json')).relative_to(m.ROOT)))


def review():
    rows=[assess(m.load(p)) for p in sorted((RUN/'native-objects').glob('*.json'))]
    m.save(RUN/'native-review.json',dict(at=m.now(),rows=rows,counts=dict(Counter(r['decision'] for r in rows)),
        metadata_candidates=sum(bool(r.get('field_updates')) for r in rows),image_candidates=sum(bool(r.get('image_candidate')) for r in rows)))
    print(json.dumps(dict(records=len(rows),decisions=dict(Counter(r['decision'] for r in rows)),metadata_candidates=sum(bool(r.get('field_updates')) for r in rows),image_candidates=sum(bool(r.get('image_candidate')) for r in rows)),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['select','objects','review']);args=p.parse_args()
    {'select':selection,'objects':objects,'review':review}[args.command]()
