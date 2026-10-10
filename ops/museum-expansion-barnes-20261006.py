#!/usr/bin/env python3
"""Bounded Barnes public catalogue research; metadata only, no images."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urlencode, urlparse

spec=importlib.util.spec_from_file_location('native',Path(__file__).with_name('museum-expansion-native-20261006.py'))
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
m=n.m
BASE='https://collection.barnesfoundation.org'
n.SITES['barnes']=BASE
SLUG='barnes-foundation'
INDEX_FIELDS=['id','title','people','culture','displayDate','beginDate','endDate','invno','classification','artistPrefix','artistSuffix','curatorialApproval']
INDEX_CACHE={}


def source_id(url):
    if urlparse(url or '').hostname!='collection.barnesfoundation.org':return None
    match=re.match(r'/(?:api/)?objects/(\d+)(?:/|$)',urlparse(url).path)
    return match[1] if match else None


def title_keys(title):
    # Translated subtitles must not hide a possible existing object identity.
    return {m.norm(v) for v in [title,(title or '').split('(',1)[0]] if m.norm(v)}


def existing_keys(db,museum_id):
    urls={v['source_url'] for v in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url ILIKE '%collection.barnesfoundation.org/%'")}
    urls.update(v['canonical_url'] for v in db.execute("SELECT canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url ILIKE '%collection.barnesfoundation.org/%'"))
    titles=set().union(*(title_keys(r[k]) for r in db.execute('SELECT title,alternate_title FROM artworks') for k in ['title','alternate_title'] if r[k]))
    inventories=db.execute('''WITH selected AS MATERIALIZED (
      SELECT id FROM artworks WHERE current_institution_id=%s
      UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s AND superseded_by IS NULL
      UNION SELECT id FROM artworks WHERE accession_number ~ '^BF[0-9]'
      ) SELECT accession_number FROM artworks JOIN selected USING(id)''',(museum_id,museum_id)).fetchall()
    return {source_id(u) for u in urls},titles,set().union(*(m.acc(v['accession_number']) for v in inventories))


def native_fields(raw):
    soup=n.BeautifulSoup(raw,'html.parser')
    result={}
    for key,selector,attribute in [('canonical','link[rel=canonical]','href'),('title','meta[property="og:title"]','content'),('description','meta[property="og:description"]','content'),('url','meta[property="og:url"]','content')]:
        values=soup.select(selector)
        result[key]=values[0].get(attribute) if len(values)==1 else None
    return result


def dates(api):
    literal=api.get('displayDate') or ''
    parsed=n.creation_date(literal)
    if not parsed or parsed[2]=='before':return None
    first,last,precision=parsed
    lower,upper=api.get('beginDate'),api.get('endDate')
    # Zero and blanks in the API are unknown, not creation dates. The displayed
    # object date supplies explicit dates even when the API end field is empty.
    bounds=[int(v) if re.fullmatch(r'\d{3,4}',str(v or '')) else None for v in [lower,upper]]
    if bounds[0] is not None and bounds[0]>first:return None
    if bounds[1] is not None and bounds[1]<last:return None
    if all(v is not None for v in bounds) and precision.startswith('circa'):
        if not 100<=bounds[0]<=first<=last<=bounds[1]<=1970:return None
        first,last=bounds;precision='circa' if first==last else 'circa_range'
    return first,last,precision


def facts(api,native):
    key=str(api.get('id') or '')
    if not key.isdigit() or source_id(native.get('canonical'))!=key or native.get('url')!=native.get('canonical'):return None,'native_object_identity_conflict'
    if api.get('classification')!='Paintings':return None,'object_type_requires_review'
    if not api.get('title') or not api.get('people') or not re.fullmatch(r'BF\d+[a-z]?',api.get('invno') or ''):return None,'missing_or_complex_identity'
    artist_or_culture=api.get('culture') or api['people']
    if native.get('title')!='Barnes Collection Online — '+artist_or_culture+': '+api['title']:return None,'native_title_or_creator_conflict'
    if not (native.get('description') or '').startswith('Barnes Foundation Collection: '+artist_or_culture+'. '+api['title']+' -- '):return None,'native_collection_membership_not_confirmed'
    dates_value=dates(api)
    if not dates_value:return None,'creation_date_requires_review'
    if re.search(r'\b(?:pair|diptych|triptych|polyptych|verso|reverse|fragment|part of|pendant)\b',api['title'],re.I):return None,'component_or_version_requires_review'
    if re.search(r'\b(?:loan|lent|deposit|promised|restitution|restituted|returned)\b',api.get('creditLine',''),re.I):return None,'credit_line_ownership_requires_review'
    location=api.get('locations') or ''
    if location and not location.startswith('Barnes Foundation (Philadelphia)'):return None,'native_location_requires_review'
    creator=' '.join(v.strip() for v in [api.get('artistPrefix'),api['people'],api.get('artistSuffix')] if v and v.strip())
    return dict(title=api['title'],creator_label=creator,first=dates_value[0],last=dates_value[1],date_precision=dates_value[2],date_display=api['displayDate'],work_type='painting',medium=api.get('medium') or None,dimensions=api.get('dimensions') or None,accession=api['invno'],cultural_context=api.get('culture') or None,source_url=native['canonical'],holding_basis='Barnes public collection object page and official API agree on object identity, title and creator or cultural label. The native page explicitly identifies the work as Barnes Foundation Collection. Literal catalogue provenance, curatorialApproval and date fields are retained without converting the source flag into Artline publication approval. Collection holding only; no gallery location or on-view field is used as a display claim.'),None


def read_capture(capture):
    raw=gzip.decompress((m.ROOT/capture['body_path']).read_bytes())
    assert capture['receipt']['status']==200 and hashlib.sha256(raw).hexdigest()==capture['receipt']['sha256']
    assert urlparse(capture['receipt']['url']).hostname==urlparse(BASE).hostname
    assert urlparse(capture['receipt']['final_url']).hostname==urlparse(BASE).hostname
    return raw


def validate_record(record,body):
    original=record['raw_source_record'];api=json.loads(body)
    assert api==original['api_record'] and str(api['id'])==record['source_record_id']
    assert record['source_receipt']['url']==BASE+'/api/objects/'+record['source_record_id']
    assert record['museum']['slug']==SLUG
    index=original['index_capture'];key=index['body_path']
    if key not in INDEX_CACHE:INDEX_CACHE[key]=json.loads(read_capture(index))['hits']['hits']
    hit=next(v for v in INDEX_CACHE[key] if v['_id']==record['source_record_id'])
    assert hit==original['index_record']
    assert all(hit['_source'].get(k)==api.get(k) for k in INDEX_FIELDS)
    native=native_fields(read_capture(original['native_capture']))
    assert native==original['native_fields']
    f,reason=facts(api,native);assert not reason,reason
    return f


def research(batch):
    assert re.fullmatch(r'barnes-\d{3}',batch)
    destination=m.RUN/(batch+'-current-plan.json.gz');assert not destination.exists()
    museum=next(r for r in m.load(m.RUN/'after-wave-09.json')['institutions'] if r['slug']==SLUG)
    with m.connect() as db:
        known,titles,inventories=existing_keys(db,museum['id'])
        before=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(museum['id'],)).fetchone()
    goal=max(0,200-before['eligible']);ready=[];held=[];seen=set();listings=[];inspected=0;failures=0
    for page in range(14):
        if len(ready)>=goal or inspected>=300 or failures>=3:break
        query={'from':page*50,'size':50,'query':{'bool':{'filter':[{'match_phrase':{'classification':'Paintings'}}]}}}
        url=BASE+'/api/search?'+urlencode({'body':json.dumps(query,separators=(',',':'))})
        try:body,index_capture=n.capture('barnes',url);data=json.loads(body)
        except n.requests.RequestException as exc:
            held.append(dict(reason='index_source_failure',url=url,error=str(exc)[:250]));break
        assert not data.get('timed_out') and data['_shards']['failed']==0
        hits=data['hits']['hits'];assert len(hits)<=50
        listings.append(dict(capture=index_capture,rows=len(hits),reported_total=data['hits']['total']))
        if not hits:break
        for hit in hits:
            if len(ready)>=goal or inspected>=300 or failures>=3:break
            item=hit['_source'];key=str(item['id']);assert key==hit['_id']
            if key in seen:continue
            seen.add(key);reason=None
            if key in known:reason='source_identity_already_catalogued'
            elif m.acc(item.get('invno'))&inventories:reason='existing_or_selected_inventory'
            elif title_keys(item.get('title'))&titles:reason='existing_or_selected_title_requires_identity_review'
            elif not dates(item):reason='creation_date_requires_review'
            if reason:held.append(dict(index_record=hit,reason=reason));continue
            inspected+=1
            try:
                raw,cap=n.capture('barnes',BASE+'/api/objects/'+key);api=json.loads(raw)
                native_raw,native_capture=n.capture('barnes',BASE+'/objects/'+key)
                native=native_fields(native_raw);f,reason=facts(api,native)
            except n.requests.RequestException as exc:
                failures+=1;held.append(dict(index_record=hit,reason='object_source_failure',error=str(exc)[:250]));continue
            failures=0
            if any(item.get(k)!=api.get(k) for k in INDEX_FIELDS):reason='index_object_fields_changed'
            original=dict(index_record=hit,index_capture=index_capture,api_record=api,native_fields=native,native_capture=native_capture)
            if reason:held.append(dict(source_record_id=key,reason=reason,raw_source_record=original));continue
            ready.append(dict(source_record_id=key,museum=museum,facts=f,raw_source_record=original,source_receipt=cap['receipt'],body_path=cap['body_path']))
            titles.update(title_keys(f['title']));inventories.update(m.acc(f['accession']))
            if len(ready)%20==0:print('Barnes ready',len(ready),'/',goal,'inspected',inspected,flush=True)
        m.save(n.RUN/'barnes'/(batch+f'-progress-{page:02d}.json.gz'),dict(at=m.now(),before=before,records=ready,held=held,listings=listings,inspected=inspected))
    plan=dict(at=m.now(),records=ready,held=held,listings=listings,before=before,inspected=inspected,museum=museum,policy='At most 700 painting index rows and 300 selected object checks, stopping at 200 eligible museum records. Public collection page identity and literal creation dates required; ambiguous components, holding and duplicate identities held. Preserve API curatorialApproval without interpreting it as Artline approval. No images or display assertions.')
    m.save(destination,plan)
    print(json.dumps(dict(batch=batch,ready=len(ready),held=len(held),inspected=inspected,plan_sha256=hashlib.sha256(destination.read_bytes()).hexdigest())),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--batch',required=True);args=p.parse_args();research(args.batch)
