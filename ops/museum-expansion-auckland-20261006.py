#!/usr/bin/env python3
"""Bounded Auckland native catalogue research, with no media requests."""
import argparse
import functools
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import parse_qs,urlencode,urljoin,urlparse
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('agsa',Path(__file__).with_name('museum-expansion-agsa-20261006.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
m=a.m;n=a.n
SITE='https://www.aucklandartgallery.com'
n.SITES['auckland']=SITE
RUN=n.RUN/'auckland'
SLUG='wikimedia-museum-q4819492'
captured_body=a.captured_body
title_collisions=a.title_collisions


def clean(value):
    if isinstance(value,list):
        assert all(isinstance(part,str) for part in value),'Unsupported structured native field'
        value=' '.join(value)
    assert value is None or isinstance(value,str),'Unsupported native scalar field'
    return ' '.join((value or '').split())


def source_id(url):
    p=urlparse(url or '')
    match=re.fullmatch(r'/(?:explore-art-and-ideas|explore/art-and-artists)/artwork/(\d+)(?:/[^/?]+)?/?',p.path)
    return match[1] if p.hostname in ['www.aucklandartgallery.com','aucklandartgallery.com'] and match else None


def router_data(raw):
    """Read the public rendered page's JSON reference table, without executing JS."""
    soup=BeautifulSoup(raw,'html.parser')
    chunks=[s.get_text() for s in soup.select('script') if 'window.__reactRouterContext.streamController.enqueue(' in s.get_text()]
    assert len(chunks)==1,'Unexpected native state layout'
    encoded=chunks[0].split('.enqueue(',1)[1].rsplit(');',1)[0]
    table=json.loads(json.loads(encoded))
    @functools.lru_cache(maxsize=None)
    def ref(index):
        if index==-5:return None
        assert isinstance(index,int) and 0<=index<len(table),'Unexpected native state reference'
        node=table[index]
        if isinstance(node,dict):
            assert all(re.fullmatch(r'_\d+',key) for key in node)
            return {table[int(key[1:])]:ref(value) for key,value in node.items()}
        if isinstance(node,list):
            # Preserve tagged values as source data; never treat dates as object dates.
            if node and isinstance(node[0],str):return node
            return [ref(value) for value in node]
        return node
    return ref(0)['loaderData']


def index_url(page):
    return SITE+'/explore/art-and-artists?'+urlencode([('material[]','oil on canvas'),('from_date','1000-01-01'),('to_date','1970-12-31'),('limit',24),('page',page),('sort_by','title-asc')])


def creation_date(value):
    text=clean(value)
    text=re.sub(r'^circa\s+','c.',text)
    direct=a.creation_date(text)
    if direct:return direct
    century=re.fullmatch(r'(?:early|mid|late) (\d{1,2})(?:st|nd|rd|th) century',text)
    if century and 2<=int(century[1])<=19:
        c=int(century[1]);return (c-1)*100+1,c*100,'century'
    return None


def inventory_keys(value):return m.acc(value)


def index_rows(raw,url):
    p=urlparse(url);q=parse_qs(p.query)
    assert p.hostname=='www.aucklandartgallery.com' and p.path=='/explore/art-and-artists'
    assert q.get('material[]')==['oil on canvas'] and q.get('from_date')==['1000-01-01'] and q.get('to_date')==['1970-12-31']
    assert q.get('sort_by')==['title-asc'] and q.get('limit')==['24']
    data=router_data(raw)['routes/ArtAndArtistLandingPage']
    results=data['searchResults'];assert len(results)<=24
    rows=[]
    for item in results:
        assert item['type']=='vernon_object' and item['data']['type']=='artwork'
        native=item['data'];url=urljoin(SITE,native['url']);oid=source_id(url);assert oid
        rows.append(dict(source_id=oid,url=url,title=native['name'],date=native['production_date'],
            creators=native['artists'],index_native=native))
    assert len({r['source_id'] for r in rows})==len(rows)
    return rows,data['totalCount']


def fields(raw):
    soup=BeautifulSoup(raw,'html.parser');values={};repeated={}
    for dt in soup.select('dl dt'):
        dd=dt.find_next_sibling('dd');assert dd
        key=clean(dt.get_text(' ',strip=True));value=clean(dd.get_text(' ',strip=True))
        if key in values:repeated.setdefault(key,[values[key]]).append(value)
        else:values[key]=value
    data=router_data(raw)
    routes=[v for k,v in data.items() if k!='root'];assert len(routes)==1
    return dict(fields=values,repeated=repeated,native_route=routes[0],
        creator_names=[v['title'] for v in routes[0]['attributes']['artists']],
        headings=[clean(h.get_text(' ',strip=True)) for h in soup.select('h1,h2,h3')])


def facts(parsed,index):
    f=parsed['fields'];route=parsed['native_route'];native=route['attributes']
    if parsed['repeated']:return None,'repeated_fields_require_review'
    if str(route['id'])!=index['source_id'] or str(native['id'])!=index['source_id'] or source_id(urljoin(SITE,native['url']))!=index['source_id']:return None,'native_object_identity_conflict'
    if native['entity']!='artwork':return None,'native_object_classification_conflict'
    for column,key in [('Title','name'),('Production date','production_date'),('Medium','material_desc'),('Credit line','credit_line'),('Accession No','accession_no'),('Dimensions','dimensions'),('Copyright','copyright'),('Department','department')]:
        if clean(f.get(column))!=clean(native.get(key)):return None,'rendered_native_metadata_conflict'
    if f.get('Title')!=index['title'] or f.get('Production date')!=index['date']:return None,'index_native_title_or_date_conflict'
    creators=[{k:v.get(k) for k in ['title','url','role']} for v in native['artists']]
    if creators!=index['creators'] or len(creators)!=1 or not f.get('Artist'):return None,'creator_identity_or_multiple_roles_require_review'
    if creators[0]['title'] not in f['Artist'] or (creators[0]['role'] and str(creators[0]['role']).casefold() not in f['Artist'].casefold()):return None,'creator_role_label_requires_review'
    dates=creation_date(f.get('Production date'))
    if not dates:return None,'creation_date_requires_review'
    if f.get('Medium')!='oil on canvas':return None,'selected_painting_medium_conflict'
    inventory=f.get('Accession No') or ''
    if not re.fullmatch(r'(?:M?\d{4}/\d+(?:/\d+)*|M?U/\d+)',inventory):return None,'inventory_or_component_identity_requires_review'
    credit=f.get('Credit line') or ''
    if re.search(r'\b(?:loan|lent|deposit|deaccession|returned|restitu\w*|promised)\b',credit,re.I):return None,'custody_qualification_requires_review'
    trust=credit.startswith('Mackelvie Trust Collection, Auckland Art Gallery Toi o Tāmaki')
    if inventory.startswith('M')!=trust:return None,'trust_inventory_credit_conflict'
    explicit_collection=trust or credit=='Auckland Art Gallery Toi o Tāmaki'
    if 'Auckland Art Gallery' not in credit or not (explicit_collection or re.search(r'\b(?:purchased?|gift|bequest|bequeathed?|grant|presented|donated|fund|transferred)\b',credit,re.I)):return None,'acquisition_credit_requires_review'
    if re.search(r'\b(?:diptych|triptych|polyptych|pair of|recto|verso|reverse|part of)\b',f['Title'],re.I):return None,'compound_object_requires_review'
    return dict(title=f['Title'],creator_label=f['Artist'],first=dates[0],last=dates[1],date_precision=dates[2],date_display=f['Production date'],
        work_type='painting',medium=f['Medium'],dimensions=f.get('Dimensions') or None,accession=inventory,source_url=index['url'],
        holding_basis='Auckland Art Gallery official collection index and native object page agree on identity, title, creator and creation date. Rendered native fields agree with page state. Accession and acquisition credit: '+credit+'. Collection holding only; neither a current display claim nor an inference about legal ownership of trust collections.'+(' The museum collection policy identifies Mackelvie Trust works as permanent-loan holdings; trust ownership is retained.' if trust else '')),None


def existing_keys(db,iid):
    rows=db.execute('''WITH selected AS MATERIALIZED (
      SELECT id FROM artworks WHERE current_institution_id=%s
      UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s AND superseded_by IS NULL)
      SELECT a.id::text,a.title,a.alternate_title,a.accession_number FROM selected s JOIN artworks a ON a.id=s.id''',(iid,iid)).fetchall()
    urls={r['source_url'] for r in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE '%aucklandartgallery.com/%'")}
    urls.update(r['canonical_url'] for r in db.execute("SELECT canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url LIKE '%aucklandartgallery.com/%'"))
    return {source_id(u) for u in urls}-{None},{m.norm(r[k]) for r in rows for k in ['title','alternate_title'] if r[k]},set().union(*(inventory_keys(r['accession_number']) for r in rows))


VALIDATED_INDEXES={}


def validate_record(record,raw):
    original=record['raw_source_record'];index=original['index_record'];cap=original['index_capture']
    assert record['museum']['slug']==SLUG and record['source_record_id']==index['source_id']
    key=(cap['body_path'],cap['receipt']['sha256'])
    if key not in VALIDATED_INDEXES:VALIDATED_INDEXES[key]=index_rows(captured_body(cap),cap['receipt']['url'])[0]
    assert index in VALIDATED_INDEXES[key]
    assert source_id(record['source_receipt']['url'])==source_id(record['source_receipt']['final_url'])==record['source_record_id']
    parsed=fields(raw);assert parsed==original['native_fields']
    if parsed['fields']['Accession No'].startswith('M'):
        context=original['collection_context'];context_raw=captured_body(context['capture'])
        text=BeautifulSoup(context_raw,'html.parser').get_text(' ',strip=True)
        assert context['excerpt'] in text and 'permanent loans' in context['excerpt'] and 'Mackelvie Trust' in context['excerpt']
    result,reason=facts(parsed,index);assert not reason,reason
    return result


def research(batch):
    destination=RUN/(batch+'-research.json.gz')
    if destination.exists():print('Retained research',destination,flush=True);return
    museum=next(r for r in m.load(m.RUN/'after-wave-18.json')['institutions'] if r['slug']==SLUG)
    with m.connect() as db:
        known,titles,inventories=existing_keys(db,museum['id'])
        before=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(museum['id'],)).fetchone()
        old=db.execute('''WITH selected AS MATERIALIZED (SELECT id FROM artworks WHERE current_institution_id=%s
          UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s AND superseded_by IS NULL)
          SELECT to_jsonb(a) row FROM selected s JOIN artworks a ON a.id=s.id ORDER BY a.id''',(museum['id'],museum['id'])).fetchall()
    backup=m.BACKUP/(batch+'-existing-artwork-rows.json.gz')
    if backup.exists():assert m.load(backup)['artworks']==old,'Existing rows changed during research'
    else:m.save(backup,dict(at=m.now(),artworks=old))
    identity=RUN/(batch+'-identity-before.json')
    snapshot=dict(museum=museum,before=before,known_source_ids=sorted(known),existing_titles=sorted(titles),existing_inventories=sorted(inventories))
    if identity.exists():assert {k:v for k,v in m.load(identity).items() if k!='at'}==snapshot
    else:m.save(identity,dict(at=m.now(),**snapshot))
    context=m.load(RUN/'permanent-trust-holdings-context.json')
    goal=max(0,200-before['eligible']);target=min(goal+20,180);assert goal>0
    records=[];held=[];indexes=[];seen=set();failures=0;examined=0;remaining=[];page=1
    for page in range(1,21):
        url=index_url(page)
        try:raw,cap=n.capture('auckland',url);rows,total=index_rows(raw,url)
        except (a.i.requests.RequestException,AssertionError) as exc:
            held.append(dict(url=url,reason='index_source_failure',error=str(exc)[:250]));break
        indexes.append(dict(capture=cap,rows=rows,total_reported=total))
        with m.connect() as db:collisions=title_collisions(db,[dict(facts=dict(title=r['title'])) for r in rows])
        collision_keys={m.norm(r[k]) for r in collisions for k in ['title','alternate_title'] if r[k]}
        remaining=[]
        for pos,index in enumerate(rows):
            if len(records)>=target or failures>=3:remaining=rows[pos:];break
            oid=index['source_id'];examined+=1
            if oid in seen:held.append(dict(index=index,reason='repeated_index_identity'));continue
            seen.add(oid);key=m.norm(index['title'])
            if oid in known:held.append(dict(index=index,reason='existing_source_identity'));continue
            if key in titles:held.append(dict(index=index,reason='existing_or_selected_title'));continue
            if key in collision_keys:
                held.append(dict(index=index,reason='catalogue_title_identity_requires_review',existing=[r for r in collisions if any(r[k] and m.norm(r[k])==key for k in ['title','alternate_title'])]));continue
            if not creation_date(index['date']):held.append(dict(index=index,reason='index_creation_date_requires_review'));continue
            try:body,obj=n.capture('auckland',index['url']);parsed=fields(body);f,reason=facts(parsed,index)
            except (a.i.requests.RequestException,AssertionError) as exc:
                failures+=1;held.append(dict(index=index,reason='native_source_failure',error=str(exc)[:250]));continue
            if reason:held.append(dict(index=index,reason=reason,native_fields=parsed,capture=obj));continue
            if inventory_keys(f['accession'])&inventories:held.append(dict(index=index,reason='existing_or_selected_inventory',native_fields=parsed,capture=obj));continue
            records.append(dict(source_record_id=oid,museum=museum,facts=f,source_receipt=obj['receipt'],body_path=obj['body_path'],
                raw_source_record=dict(index_record=index,index_capture=cap,native_fields=parsed,
                    collection_context=context if f['accession'].startswith('M') else None)))
            titles.add(key);inventories.update(inventory_keys(f['accession']))
        print('Auckland page',page,'candidates',len(records),'held',len(held),'examined',examined,flush=True)
        m.save(RUN/'progress'/(batch+f'-{page:03d}.json.gz'),dict(records=records,held=held,indexes=indexes,before=before))
        if remaining or len(records)>=target or failures>=3 or page*24>=total:break
    m.save(destination,dict(at=m.now(),museum=museum,before=before,records=records,held=held,indexes=indexes,source_failures=failures,
        examined=examined,resume_page=page,unprocessed_captured_rows=remaining,next_page=page+1,
        policy='At most 480 bounded oil-on-canvas index entries in source search range 1000–1970, followed by selected object pages. Native creation dates are independently validated. Current/legacy source IDs, scoped inventories and catalogue title checks precede import. Every candidate requires individual narrative, chronology and version review. No images requested.'))
    print('Auckland research retained',len(records),len(held),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['research']);parser.add_argument('--batch',default='auckland-001')
    args=parser.parse_args();assert re.fullmatch(r'auckland-\d{3}',args.batch);research(args.batch)
