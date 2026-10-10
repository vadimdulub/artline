#!/usr/bin/env python3
"""Bounded Städel native painting metadata research; no media downloads."""
import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import parse_qs,urlencode,urlparse
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('agsa',Path(__file__).with_name('museum-expansion-agsa-20261006.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
m=a.m;n=a.n
SITE='https://sammlung.staedelmuseum.de'
n.SITES['staedel']=SITE
RUN=n.RUN/'staedel'
SLUG='staedel-museum'
captured_body=a.captured_body
title_collisions=a.title_collisions
clean=a.clean
inventory_keys=a.inventory_keys


def object_url(url):
    p=urlparse(url or '')
    return p.hostname=='sammlung.staedelmuseum.de' and bool(re.fullmatch(r'/(?:en/work|de/werk)/[a-z0-9-]+/?',p.path))


def creation_date(value):
    raw=clean(value)
    return a.creation_date(raw)


def index_url(page):
    return SITE+'/en/search?'+urlencode({'f':'+object:term(48)','production':'+1000,1970','p':page})


def index_rows(raw,url):
    p=urlparse(url);q=parse_qs(p.query)
    assert p.hostname=='sammlung.staedelmuseum.de' and p.path=='/en/search'
    assert q.get('f')==['+object:term(48)'] and q.get('production')==['+1000,1970']
    soup=BeautifulSoup(raw,'html.parser')
    data=[json.loads(s.get_text()) for s in soup.select('script[type="application/json"]') if '"result"' in s.get_text()]
    assert len(data)==1
    result=data[0]['result'];query=result['query']
    assert query['page']==int(q['p'][0]) and query['pageStep']==120
    assert query['filters']==[dict(field='object',id=48,operator='+',title='painting (artwork)',type='term')]
    assert query['production']==dict(operator='+',range=[1000,1970]) and not query['flags'] and not query['fullText']
    assert query['sort']=='title' and query['sortDir']=='asc'
    documents=result['documents'];assert len(documents)<=130
    rows=[]
    for doc in documents[:120]:
        assert object_url(doc['url']) and doc['number'] and doc['title'] and doc['creator']
        keys=inventory_keys(doc['number'])
        rows.append(dict(source_id=next(iter(keys)) if len(keys)==1 else None,url=doc['url'],title=clean(doc['title']),creator=clean(doc['creator']),
            accession=clean(doc['number']),date=clean(doc['production']),native_index=doc))
    assert len({r['native_index']['id'] for r in rows})==len(rows)
    return rows,result['numDocuments'],documents[120:]


def fields(raw):
    soup=BeautifulSoup(raw,'html.parser');values={};repeated={};unlabelled=[]
    for dl in soup.select('dl.dsProperty'):
        dt=dl.find('dt');dd=dl.find('dd');assert dd
        if dt is None:
            unlabelled.append(clean(dd.get_text(' ',strip=True)));continue
        key=clean(dt.get_text(' ',strip=True));value=clean(dd.get_text(' ',strip=True))
        if key in values:
            repeated.setdefault(key,[values[key]]).append(value)
        else:values[key]=value
    def one(selector):
        nodes=soup.select(selector);return clean(nodes[0].get_text(' ',strip=True)) if len(nodes)==1 else None
    canonical=soup.select('meta[property="og:url"]')
    narratives=[]
    for node in soup.select('.dsUiExpandable__content'):
        if node.select_one('h3') and node.select_one('h3').get_text(' ',strip=True)=='About the Work':
            narratives.append(clean(node.get_text(' ',strip=True)))
    return dict(fields=values,repeated=repeated,unlabelled_properties=unlabelled,title=one('h1 .dsArtwork__titleCaption'),
        date=(one('h1 .dsArtwork__titleYear') or '').lstrip(', '),creator=one('.dsArtwork__titleCreators'),
        canonical=canonical[0].get('content') if len(canonical)==1 else None,
        permalinks=sorted({link['href'] for link in soup.select('a[href]') if '/go/ds/' in link['href']}),
        narratives=narratives,
        source_update=[clean(p.get_text(' ',strip=True)) for el in soup.select('.dsArtworkFooter__caption') if el.get_text(' ',strip=True)=='Last update' for p in [el.find_next_sibling()] if p])


def facts(parsed,index):
    f=parsed['fields']
    if any(len(set(values))>1 for key,values in parsed['repeated'].items() if key in ['Title','Painter','Inventory Number','Institution','Acquisition','Collection','Object Type','Physical Description','Dimensions']):return None,'repeated_identity_fields_require_review'
    if parsed['canonical']!=index['url'] or not object_url(parsed['canonical']):return None,'native_source_identity_conflict'
    if parsed['title']!=index['title'] or f.get('Title') not in [index['title'],index['title']+' (Original Title)']:return None,'native_title_conflict'
    if parsed['creator']!=index['creator'] or f.get('Painter')!=index['creator']:return None,'native_creator_role_requires_review'
    if parsed['date']!=index['date']:return None,'index_native_creation_conflict'
    dates=creation_date(parsed['date'])
    if not dates:return None,'creation_date_requires_review'
    if f.get('Object Type')!='painting (artwork)':return None,'native_object_type_requires_review'
    inventory=f.get('Inventory Number') or ''
    if inventory_keys(inventory)!=inventory_keys(index['accession']):return None,'native_inventory_conflict'
    if len(parsed['permalinks'])!=1 or inventory_keys(urlparse(parsed['permalinks'][0]).path.split('/')[-1])!=inventory_keys(inventory):return None,'native_permalink_identity_conflict'
    if f.get('Institution')!='Städel Museum':return None,'native_holding_institution_conflict'
    credit=f.get('Creditline') or '';acquisition=f.get('Acquisition') or '';collection=f.get('Collection') or ''
    if not credit.startswith('Städel Museum, Frankfurt am Main'):return None,'native_collection_credit_requires_review'
    if collection not in ['Städelsches Kunstinstitut','Städtische Galerie']:return None,'loan_or_other_collection_requires_review'
    if not re.match(r'(?:Acquired|Purchased|Gift|Donated|Bequeathed|Bequest)\b',acquisition,re.I):return None,'acquisition_evidence_requires_review'
    if re.search(r'\b(?:loan|lent|deposit|returned|restitut\w*|promised|lost|missing)\b',acquisition,re.I):return None,'qualified_acquisition_requires_review'
    if not f.get('Physical Description'):return None,'physical_description_requires_review'
    if re.search(r'\b(?:triptych|diptych|polyptych|altarpiece|altar retable|verso|reverse|both sides|fragment|left wing|right wing|predella|panel of|part of)\b',index['title'],re.I):return None,'component_or_compound_identity_requires_review'
    return dict(title=index['title'],creator_label=f['Painter'],first=dates[0],last=dates[1],date_precision=dates[2],date_display=parsed['date'],
        work_type='painting',medium=f['Physical Description'],dimensions=f.get('Dimensions') or None,accession=inventory,source_url=index['url'],
        holding_basis='Official Städel painting index and object page agree on title, creator, creation date and inventory. Native Institution: Städel Museum; Collection: '+collection+'. Acquisition: '+acquisition+'. Creditline: '+credit+'. Collection holding only; separately named ownership remains qualified. Display status is retained as source evidence without creating a current-display assertion.'),None


def existing_keys(db,iid):
    rows=db.execute('''WITH selected AS MATERIALIZED (SELECT id FROM artworks WHERE current_institution_id=%s
      UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s AND superseded_by IS NULL)
      SELECT a.id::text,a.title,a.alternate_title,a.accession_number FROM selected s JOIN artworks a ON a.id=s.id''',(iid,iid)).fetchall()
    urls={r['source_url'].rstrip('/') for r in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE '%staedelmuseum.de/%'")}
    ext=db.execute("SELECT scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (scheme ILIKE '%staedel%' OR canonical_url LIKE '%staedelmuseum.de/%')").fetchall()
    urls.update(r['canonical_url'].rstrip('/') for r in ext if r['canonical_url'])
    inventories=set().union(*(inventory_keys(r['accession_number']) for r in rows))
    for r in ext:
        if 'staedel' in r['scheme'].lower():inventories.update(inventory_keys(r['external_id']))
    for url in urls:
        if '/go/ds/' in url:inventories.update(inventory_keys(urlparse(url).path.split('/')[-1]))
    return urls,{m.norm(r[k]) for r in rows for k in ['title','alternate_title'] if r[k]},inventories


VALIDATED_INDEXES={}


def validate_record(record,raw):
    original=record['raw_source_record'];index=original['index_record'];cap=original['index_capture']
    assert record['museum']['slug']==SLUG and record['source_record_id']==index['source_id']
    key=(cap['body_path'],cap['receipt']['sha256'])
    if key not in VALIDATED_INDEXES:VALIDATED_INDEXES[key]=index_rows(captured_body(cap),cap['receipt']['url'])[0]
    assert index in VALIDATED_INDEXES[key]
    assert record['source_receipt']['url']==record['source_receipt']['final_url']==index['url']
    parsed=fields(raw);assert parsed==original['native_fields']
    result,reason=facts(parsed,index);assert not reason,reason
    return result


def research(batch):
    destination=RUN/(batch+'-research.json.gz')
    if destination.exists():print('Retained research',destination,flush=True);return
    baseline=m.load(RUN/(batch+'-before.json'));museum=baseline['museum'];before=baseline['before']
    with m.connect() as db:
        known,titles,inventories=existing_keys(db,museum['id'])
        current=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(museum['id'],)).fetchone()
        assert current==before
    snapshot=dict(museum=museum,before=before,known_source_urls=sorted(known),existing_titles=sorted(titles),existing_inventories=sorted(inventories))
    identity=RUN/(batch+'-identity-before.json')
    if identity.exists():assert {k:v for k,v in m.load(identity).items() if k!='at'}==snapshot
    else:m.save(identity,dict(at=m.now(),**snapshot))
    target=min(200-before['eligible']+40,200);assert target>0
    records=[];held=[];indexes=[];seen=set();failures=0;examined=0;remaining=[];page=1
    for page in range(1,6):
        url=index_url(page)
        try:raw,cap=n.capture('staedel',url);rows,total,preview=index_rows(raw,url)
        except (a.i.requests.RequestException,AssertionError) as exc:
            held.append(dict(url=url,reason='index_source_failure',error=str(exc)[:250]));break
        indexes.append(dict(capture=cap,rows=rows,total_reported=total,preview_rows_outside_page=preview))
        with m.connect() as db:collisions=title_collisions(db,[dict(facts=dict(title=r['title'])) for r in rows])
        collision_keys={m.norm(r[k]) for r in collisions for k in ['title','alternate_title'] if r[k]}
        for pos,index in enumerate(rows):
            if len(records)>=target or failures>=3:remaining=rows[pos:];break
            oid=index['source_id'];examined+=1;key=m.norm(index['title'])
            if oid is None:held.append(dict(index=index,reason='compound_index_inventory_requires_review'));continue
            if oid in seen:held.append(dict(index=index,reason='repeated_index_identity'));continue
            seen.add(oid)
            if index['url'].rstrip('/') in known or inventory_keys(index['accession'])&inventories:held.append(dict(index=index,reason='existing_source_or_inventory'));continue
            if key in titles:held.append(dict(index=index,reason='existing_or_selected_title'));continue
            if key in collision_keys:
                held.append(dict(index=index,reason='catalogue_title_identity_requires_review',existing=[r for r in collisions if any(r[k] and m.norm(r[k])==key for k in ['title','alternate_title'])]));continue
            if not creation_date(index['date']):held.append(dict(index=index,reason='index_creation_date_requires_review'));continue
            try:body,obj=n.capture('staedel',index['url']);parsed=fields(body);f,reason=facts(parsed,index)
            except (a.i.requests.RequestException,AssertionError) as exc:
                failures+=1;held.append(dict(index=index,reason='native_source_failure',error=str(exc)[:250]));continue
            if reason:held.append(dict(index=index,reason=reason,native_fields=parsed,capture=obj));continue
            records.append(dict(source_record_id=oid,museum=museum,facts=f,source_receipt=obj['receipt'],body_path=obj['body_path'],
                raw_source_record=dict(index_record=index,index_capture=cap,native_fields=parsed)))
            titles.add(key);inventories.update(inventory_keys(f['accession']))
            if len(records)%10==0:print('Städel candidates',len(records),'examined',examined,flush=True)
        print('Städel page',page,'candidates',len(records),'held',len(held),'examined',examined,flush=True)
        m.save(RUN/'progress'/(batch+f'-{page:03d}.json.gz'),dict(records=records,held=held,indexes=indexes,before=before))
        if remaining or len(records)>=target or failures>=3 or page*120>=total:break
    m.save(destination,dict(at=m.now(),museum=museum,before=before,records=records,held=held,indexes=indexes,source_failures=failures,
        examined=examined,resume_page=page,unprocessed_captured_rows=remaining,next_page=page+1,
        policy='At most 600 painting-index entries within source search range 1000–1970. Source returns ten preview rows beyond each 120-row page; those are retained but not processed twice. Native creation statements independently checked. Selected individual object pages only; every candidate requires narrative and version review. No media requested.'))
    print('Städel research retained',len(records),len(held),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['research']);parser.add_argument('--batch',default='staedel-001')
    args=parser.parse_args();assert re.fullmatch(r'staedel-\d{3}',args.batch);research(args.batch)
