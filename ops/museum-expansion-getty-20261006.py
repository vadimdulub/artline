#!/usr/bin/env python3
"""Bounded Getty painting research; native object and ownership checks, no images."""
import argparse
import collections
import gzip
import hashlib
import importlib.util
import json
import re
import time
from pathlib import Path
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('museum-expansion-20261006.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
RUN=m.RUN/'getty'
API='https://data.getty.edu/museum/collection/'
SITE='https://www.getty.edu/art/collection'
LOCAL='https://data.getty.edu/local/thesaurus/'
AAT='http://vocab.getty.edu/aat/'
OWNER=API+'group/c496a7b4-6087-4deb-a1ac-0f21bd3fd87b'
KEEPER=API+'group/0453e4ea-4769-4b02-b590-9541ad174184'
SLUG='spain-research-museum-q731126'


def capture(url):
    assert url.startswith((API,SITE+'/object/',SITE+'/api/search?'))
    key=hashlib.sha256(url.encode()).hexdigest()
    for root in [RUN/'captures',m.RUN/'getty-probes']:
        path=root/(key+'.json')
        if path.exists():
            receipt=m.load(path);body=root/(key+'.body.gz')
            raw=gzip.decompress(body.read_bytes())
            assert hashlib.sha256(raw).hexdigest()==receipt['sha256']
            if receipt['status']!=200:raise requests.HTTPError('Retained source HTTP '+str(receipt['status']))
            return raw,dict(receipt=receipt,body_path=str(body.relative_to(m.ROOT)))
    time.sleep(0.35)
    with requests.get(url,timeout=(12,45),headers={'User-Agent':'ArtlineMuseumResearch/1.0 (bounded selected metadata; no images)'},stream=True) as response:
        raw=b''
        for chunk in response.iter_content(65536):
            raw+=chunk
            assert len(raw)<3_000_000,'Source response exceeds metadata bound'
        receipt=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        root=RUN/'captures';root.mkdir(parents=True,exist_ok=True);body=root/(key+'.body.gz')
        assert not body.exists();body.write_bytes(gzip.compress(raw,mtime=0));m.save(root/(key+'.json'),receipt)
        response.raise_for_status()
    return raw,dict(receipt=receipt,body_path=str(body.relative_to(m.ROOT)))


def types(row):
    return {r.get('id') for r in row.get('classified_as',[])}


def contents(rows,type_id):
    return list(dict.fromkeys(r['content'] for r in rows if type_id in types(r) and r.get('content')))


def html_fields(raw):
    soup=BeautifulSoup(raw,'html.parser')
    nodes=soup.select('script[type="application/ld+json"]');ids=soup.select('script#local_id_manager')
    assert len(nodes)==len(ids)==1,'Missing or multiple native object identity documents'
    return dict(object=json.loads(nodes[0].get_text()),identity=json.loads(ids[0].get_text()))


def period_date(value):
    # These are consistency envelopes for interpreting the literal period.
    # Stored bounds always come from the object's own production timespan.
    match=re.fullmatch(r'(?:(early|mid|late)[ -])?(\d{3,4})s',value or '')
    if match:
        first=int(match[2]);last=first+9
        if first%10 or not 100<=first<=last<=1970:return None
        return first,last,'range' if match[1] else 'decade'
    match=re.fullmatch(r'(?:(early|mid|late) )?(\d{1,2})(?:st|nd|rd|th) century',value or '')
    if match:
        first=(int(match[2])-1)*100;last=first+100
        if not 100<=first<last<=1970:return None
        return first,last,'range' if match[1] else 'century'
    match=re.fullmatch(r'(first|second|third|fourth) quarter of (\d{1,2})(?:st|nd|rd|th) century',value or '')
    if match:
        first=(int(match[2])-1)*100+['first','second','third','fourth'].index(match[1])*25;last=first+25
        if 100<=first<last<=1970:return first,last,'range'
    return None


def display_date(value):
    """Nominal years only; actual bounds must come from this production's API."""
    period=period_date(value)
    if period:return period[0],period[1],False
    match=re.fullmatch(r'(about )?(\d{3,4})(?:\s*[-–]\s*(\d{3,4}))?',value or '')
    if not match:return None
    first=int(match[2]);last=int(match[3] or match[2])
    if not 100<=first<=last<=1970:return None
    if match[1] and last==1970:return None
    return first,last,bool(match[1])


def source_dates(production,literal):
    parsed=display_date(literal);span=production.get('timespan') or {}
    if not parsed or contents(span.get('identified_by',[]),AAT+'300458798')!=[literal]:return None
    start=re.fullmatch(r'(\d{4})-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z)?',span.get('begin_of_the_begin',''))
    end=re.fullmatch(r'(\d{4})-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z)?',span.get('end_of_the_end',''))
    if not start or not end:return None
    first,last=int(start[1]),int(end[1]);lo,hi,circa=parsed
    period=period_date(literal)
    if period:
        if not 100<=lo<=first<=last<=hi<=1970:return None
        return first,last,period[2]
    if not 100<=first<=lo<=hi<=last<=1970:return None
    if not circa and (first,last)!=(lo,hi):return None
    if circa and last==1970:return None
    return first,last,('circa' if first==last else 'circa_range') if circa else ('exact' if first==last else 'range')


def facts(obj,index,html):
    native=html['object'];identity=html['identity'];key=index['id'];url=SITE+index['slug_with_path']
    if obj.get('id')!=API+key or obj.get('type')!='HumanMadeObject':return None,'api_object_identity_conflict'
    if identity!={'slug':index['id_manager_slug'],'indexedId':key}:return None,'native_api_identity_conflict'
    if native.get('url')!=url or native.get('@type')!='Painting':return None,'native_identity_or_type_requires_review'
    if url not in {v.get('id') for v in obj.get('subject_of',[])}:return None,'api_native_page_conflict'
    if {r.get('id') for r in obj.get('current_owner',[])}!={OWNER}:return None,'current_getty_ownership_not_confirmed'
    if {r.get('id') for r in obj.get('current_keeper',[])}!={KEEPER}:return None,'current_paintings_department_not_confirmed'
    if not {AAT+'300033618',LOCAL+'object-record-structure-whole'}<=types(obj):return None,'whole_painting_classification_requires_review'
    if obj.get('part_of') or obj.get('part') or not index.get('is_standalone') or index.get('is_parent') or index.get('is_root'):
        return None,'component_or_ensemble_requires_review'
    if any('deaccession' in str(v.get('_label','')).casefold() or 'deaccession' in str(v.get('id','')).casefold() for v in obj.get('classified_as',[])):
        return None,'deaccession_requires_review'
    title=contents(obj.get('identified_by',[]),LOCAL+'object-title-primary')
    if len(title)!=1 or title[0]!=native.get('name') or title[0]!=index.get('primary_name'):return None,'source_title_conflict'
    inventory=contents(obj.get('identified_by',[]),AAT+'300312355')
    if len(inventory)!=1 or native.get('identifier')!=inventory or index.get('accession_number')!=inventory[0]:return None,'source_inventory_conflict'
    production=obj.get('produced_by') or {}
    literal=native.get('temporal')
    if literal!=index.get('date_created'):return None,'native_index_creation_conflict'
    dates=source_dates(production,literal)
    if dates is None:return None,'production_date_requires_review'
    parts=production.get('part',[])
    if any(p.get('timespan') and p['timespan']!=production.get('timespan') for p in parts):return None,'multiple_production_phases_require_review'
    descriptions=[]
    for p in [production]+parts:descriptions+=contents(p.get('referred_to_by',[]),LOCAL+'producer-description')
    descriptions=list(dict.fromkeys(descriptions))
    if not descriptions or set(descriptions)!={v.get('description') for v in index.get('producers',[])}:
        return None,'current_attribution_descriptions_require_review'
    if {m.norm(v.get('name')) for v in native.get('creator',[])}!={m.norm(v.get('primary_name')) for v in index.get('producers',[])}:
        return None,'native_current_creator_conflict'
    medium=native.get('material') or None;dimensions=native.get('size') or None
    if medium and medium not in contents(obj.get('referred_to_by',[]),AAT+'300435429'):return None,'medium_conflict'
    if dimensions and dimensions not in contents(obj.get('referred_to_by',[]),AAT+'300435430'):return None,'dimensions_conflict'
    return dict(title=title[0],creator_label='; '.join(descriptions),first=dates[0],last=dates[1],date_precision=dates[2],date_display=literal,
        work_type='painting',medium=medium,dimensions=dimensions,accession=inventory[0],source_url=url,
        holding_basis='Getty native object page and Linked Art API agree on object identity and inventory. API records current J. Paul Getty Museum ownership and its Paintings department as keeper. Whole-object classification checked. Holding only; exhibition memberships and on-view facets are not used as display evidence.'),None


def read_capture(capture):
    raw=gzip.decompress((m.ROOT/capture['body_path']).read_bytes());rc=capture['receipt']
    assert rc['status']==200 and hashlib.sha256(raw).hexdigest()==rc['sha256']
    return raw


def validate_record(record,body):
    raw=record['raw_source_record'];obj=json.loads(read_capture(raw['api_capture']))
    assert raw['api_capture']['receipt']['url']==API+record['source_record_id']
    assert raw['index_capture']['receipt']['url'].startswith(SITE+'/api/search?')
    index_body=json.loads(read_capture(raw['index_capture']))
    rows=[r for r in index_body['data'] if r['id']==record['source_record_id']]
    assert len(rows)==1 and rows[0]==raw['index_record']
    assert obj==raw['api_object'] and html_fields(body)==raw['native_fields']
    assert record['museum']['slug']==SLUG and record['source_receipt']['url']==SITE+rows[0]['slug_with_path']
    result,reason=facts(obj,rows[0],raw['native_fields']);assert not reason,reason
    return result


def research(batch):
    assert re.fullmatch(r'getty-\d{3}',batch)
    destination=m.RUN/(batch+'-current-plan.json.gz');assert not destination.exists()
    museum=next(r for r in m.load(m.RUN/'after-wave-07.json')['institutions'] if r['slug']==SLUG)
    with m.connect() as db:
        known={r['source_url'].rstrip('/') for r in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url ILIKE '%getty.edu/%'")}
        known.update(r['canonical_url'].rstrip('/') for r in db.execute("SELECT canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url ILIKE '%getty.edu/%'"))
        # A global identity guard, not artwork enrichment: retain only title keys.
        titles={m.norm(r[k]) for r in db.execute('SELECT title,alternate_title FROM artworks') for k in ['title','alternate_title'] if r[k]}
        before=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(museum['id'],)).fetchone()
        existing=db.execute('''WITH selected AS MATERIALIZED (SELECT id FROM artworks WHERE current_institution_id=%s
          UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s AND superseded_by IS NULL)
          SELECT accession_number FROM artworks a JOIN selected s USING(id)''',(museum['id'],museum['id'])).fetchall()
        inventories=set().union(*(m.acc(r['accession_number']) for r in existing)) if existing else set()
    goal=max(0,200-before['eligible']);records=[];held=[];listings=[];seen=set();inspected=0;failures=0
    # At most 350 index records and 250 object inspections; stop at the gap.
    for offset in range(0,350,50):
        if len(records)>=goal or inspected>=250 or failures>=3:break
        url=SITE+'/api/search?'+urlencode(dict([('from',offset),('size',50),('department','Paintings'),('include_deaccessioned','false')]))
        try:raw,index_capture=capture(url);index=json.loads(raw)
        except requests.RequestException as exc:
            held.append(dict(url=url,reason='index_source_failure',error=str(exc)[:250]));break
        assert index['from']==offset and len(index['data'])<=50
        listings.append(dict(capture=index_capture,total=index['total'],from_offset=offset,returned=len(index['data'])))
        for item in index['data']:
            if len(records)>=goal or inspected>=250 or failures>=3:break
            key=item['id'];assert re.fullmatch(r'object/[0-9a-f-]{36}',key)
            assert re.fullmatch(r'/object/[A-Za-z0-9]+',item['slug_with_path'])
            if key in seen:continue
            seen.add(key);reason=None;native_url=SITE+item['slug_with_path']
            if API+key in known or native_url in known:reason='source_identity_already_catalogued'
            elif m.norm(item['primary_name']) in titles:reason='existing_or_selected_title_requires_identity_review'
            elif m.acc(item.get('accession_number'))&inventories:reason='existing_or_selected_inventory'
            elif not display_date(item.get('date_created')):reason='index_creation_date_requires_review'
            if reason:
                held.append(dict(source_record_id=key,index_record=item,reason=reason));continue
            inspected+=1
            try:
                body,api_capture=capture(API+key);obj=json.loads(body)
                body,native_capture=capture(native_url);html=html_fields(body)
                f,reason=facts(obj,item,html)
            except requests.RequestException as exc:
                failures+=1;held.append(dict(source_record_id=key,reason='object_source_failure',error=str(exc)[:250]));continue
            failures=0
            if reason:
                held.append(dict(source_record_id=key,reason=reason,index_record=item,api_capture=api_capture,native_capture=native_capture));continue
            records.append(dict(source_record_id=key,museum=museum,facts=f,
                raw_source_record=dict(api_object=obj,api_capture=api_capture,index_record=item,index_capture=index_capture,native_fields=html),
                source_receipt=native_capture['receipt'],body_path=native_capture['body_path']))
            titles.add(m.norm(f['title']));inventories.update(m.acc(f['accession']))
            if len(records)%10==0:print('Getty ready',len(records),'/',goal,'objects inspected',inspected,flush=True)
        m.save(RUN/(batch+f'-progress-{offset:03d}.json.gz'),dict(at=m.now(),before=before,records=records,held=held,listings=listings,inspected=inspected))
        if index['end']>=index['total']:break
    plan=dict(at=m.now(),records=records,held=held,listings=listings,before=before,inspected=inspected,
        museum= museum,policy='Bounded Getty painting metadata only. Exact native/API identity, current owner, keeper, whole-object structure and source production date required. Preserve literal current attribution descriptions and numeric source date bounds; obsolete attributions retained in raw evidence. All new works remain in review. No image downloads or display claims.')
    m.save(destination,plan)
    print(json.dumps(dict(batch=batch,ready=len(records),held=len(held),inspected=inspected,plan_sha256=hashlib.sha256(destination.read_bytes()).hexdigest())),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--batch',default='getty-001');args=p.parse_args();research(args.batch)
