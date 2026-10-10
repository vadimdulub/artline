#!/usr/bin/env python3
"""Bounded National Gallery of Ireland metadata review; no media requests."""
import argparse
import collections
import gzip
import hashlib
import importlib.util
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup
import requests

spec=importlib.util.spec_from_file_location('native',Path(__file__).with_name('museum-expansion-native-20261006.py'))
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
m=n.m
SITE='https://onlinecollection.nationalgallery.ie'
n.SITES['ireland']=SITE
RUN=n.RUN/'ireland'
SLUG='national-gallery-ireland'
INDEX=SITE+'/objects/images?filter=classification%3APaintings'


def source_id(url):
    parsed=urlparse(url or '')
    match=re.match(r'/objects/(\d+)(?:/|$)',parsed.path)
    return match[1] if parsed.hostname=='onlinecollection.nationalgallery.ie' and match else None


def inventory_keys(value):
    return {re.sub(r'^ngi','',key) for key in m.acc(value)}


def creation_date(raw):
    raw=' '.join((raw or '').split())
    direct=n.creation_date(raw)
    if direct:return direct
    decade=re.fullmatch(r'(\d{3})0s',raw)
    if decade and not raw.endswith('00s'):
        first=int(decade[1])*10
        return (first,first+9,'range') if 100<=first<=1960 else None
    period=re.fullmatch(r'(?:(first|second|third|fourth) (half|quarter) of the )?(\d{1,2})(?:st|nd|rd|th) century',raw)
    if period:
        part,unit,century=period.groups();century=int(century)
        if not 2<=century<=19:return None
        first=(century-1)*100+1;last=century*100
        if part:
            ordinal={'first':0,'second':1,'third':2,'fourth':3}[part]
            if unit=='half' and ordinal>1:return None
            width=50 if unit=='half' else 25
            first+=ordinal*width;last=first+width-1
        return first,last,'range' if part else 'century'
    return None


def index_rows(raw,url):
    assert urlparse(url).netloc==urlparse(SITE).netloc
    assert parse_qs(urlparse(url).query).get('filter')==['classification:Paintings']
    soup=BeautifulSoup(raw,'html.parser');rows=[]
    for item in soup.select('.grid-item-inner'):
        title=item.select_one('.title a[href]');creator=item.select_one('.primaryMaker');date=item.select_one('.displayDate')
        assert title
        target=urljoin(SITE,title['href']).split('?',1)[0]
        assert source_id(target)
        rows.append(dict(source_id=source_id(target),url=target,title=title.get_text(' ',strip=True),
            creator=creator.get_text(' ',strip=True) if creator else None,date=date.get_text(' ',strip=True) if date else None))
    assert 0<len(rows)<=48 and len({r['source_id'] for r in rows})==len(rows)
    links={urljoin(SITE,a['href']) for a in soup.select('a[rel=next][href]')}
    assert len(links)<=1
    return rows,next(iter(links),None)


def fields(raw):
    soup=BeautifulSoup(raw,'html.parser');detail=soup.select_one('#detailView')
    assert detail and 'VisualArtwork' in detail.get('itemtype','')
    result={};repeated={}
    for row in detail.select('.detailField'):
        label=row.select_one('.detailFieldLabel');value=row.select_one('.detailFieldValue,.toggleContent')
        if not label or not value:continue
        key=label.get_text(' ',strip=True);text=value.get_text(' ',strip=True)
        if key in result:repeated.setdefault(key,[result[key]]).append(text)
        else:result[key]=text
    return dict(fields=result,repeated=repeated,
        creators=[v.get_text(' ',strip=True) for v in detail.select('.peopleField .detailFieldValue')],
        creator_names=[v.get_text(' ',strip=True) for v in detail.select('.peopleField [itemprop=name]')])


def facts(parsed,index):
    f=parsed['fields']
    if parsed['repeated']:return None,'repeated_fields_require_review'
    if f.get('Title')!=index['title']:return None,'index_title_conflict'
    if f.get('Date')!=index['date']:return None,'index_creation_date_conflict'
    if index['creator'] not in parsed['creator_names'] or len(parsed['creators'])!=1:return None,'creator_identity_or_multiple_roles_require_review'
    dates=creation_date(f.get('Date'))
    if not dates:return None,'creation_date_requires_review'
    inv=f.get('Object number') or ''
    if not re.fullmatch(r'NGI\.\d+(?:\.\d+)*',inv):return None,'inventory_or_loan_identity_requires_review'
    credit=f.get('Credit Line') or ''
    if not re.search(r'\b(?:purchased?|presented|bequeathed?|bequest|gift|donated|transferred)\b',credit,re.I):return None,'acquisition_credit_requires_review'
    if re.search(r'\b(?:loan|lent|deposit|deaccession|returned|restitu\w*|promised)\b',credit,re.I):return None,'custody_qualification_requires_review'
    if re.search(r'\b(?:diptych|triptych|polyptych|fragment|part of|verso|reverse|recto|pair of)\b',f['Title'],re.I):return None,'compound_object_requires_review'
    medium=f.get('Medium') or ''
    if not re.search(r'\b(?:oil|tempera|gouache|acrylic|watercolou?r|pastel|encaustic)\b',medium,re.I):return None,'painting_medium_requires_review'
    return dict(title=f['Title'],creator_label=parsed['creators'][0],first=dates[0],last=dates[1],date_precision=dates[2],date_display=f['Date'],
        work_type='painting',medium=medium,dimensions=f.get('Dimensions') or None,accession=inv,source_url=index['url'],
        holding_basis='National Gallery of Ireland official painting index and native object page agree on identity, title, date and creator. Unique NGI inventory and acquisition credit: '+credit+'. Collection holding only; no current display or physical-presence claim.'),None


def existing_keys(db,iid):
    rows=db.execute('''WITH selected AS MATERIALIZED (
      SELECT id FROM artworks WHERE current_institution_id=%s
      UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s AND superseded_by IS NULL
      ) SELECT a.id::text,a.title,a.alternate_title,a.accession_number FROM selected s JOIN artworks a ON a.id=s.id''',(iid,iid)).fetchall()
    urls={r['source_url'] for r in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE '%onlinecollection.nationalgallery.ie/%'")}
    urls.update(r['canonical_url'] for r in db.execute("SELECT canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url LIKE '%onlinecollection.nationalgallery.ie/%'"))
    return {source_id(u) for u in urls}-{None},{m.norm(r[k]) for r in rows for k in ['title','alternate_title'] if r[k]},set().union(*(inventory_keys(r['accession_number']) for r in rows))


def captured_body(capture):
    raw=gzip.decompress((m.ROOT/capture['body_path']).read_bytes());rc=capture['receipt']
    assert rc['status']==200 and hashlib.sha256(raw).hexdigest()==rc['sha256']
    return raw


def title_collisions(db,records):
    if not records:return []
    normalized=list({m.norm(r['facts']['title']) for r in records})
    literal=list({r['facts']['title'].lower() for r in records})
    return db.execute('''SELECT id::text,title,alternate_title,accession_number,current_institution_id::text
      FROM artworks WHERE normalized_title=ANY(%s) OR lower(title)=ANY(%s) OR lower(alternate_title)=ANY(%s)
      ORDER BY id''',(normalized,literal,literal)).fetchall()


def validate_record(record,raw):
    original=record['raw_source_record'];index=original['index_record'];cap=original['index_capture']
    assert record['museum']['slug']==SLUG and record['source_record_id']==index['source_id']
    rows,_=index_rows(captured_body(cap),cap['receipt']['url']);assert index in rows
    assert source_id(record['source_receipt']['url'])==source_id(record['source_receipt']['final_url'])==record['source_record_id']
    parsed=fields(raw);assert parsed==original['native_fields']
    result,reason=facts(parsed,index);assert not reason,reason
    return result


def research(batch):
    destination=RUN/(batch+'-research.json.gz')
    if destination.exists():print('Retained research',destination,flush=True);return
    museum=next(r for r in m.load(m.RUN/'after-wave-15.json')['institutions'] if r['slug']==SLUG)
    with m.connect() as db:
        known,titles,inventories=existing_keys(db,museum['id'])
        counts=db.execute("SELECT count(*) n,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(museum['id'],)).fetchone()
    goal=max(0,200-counts['eligible']);records=[];held=[];indexes=[];seen=set();url=INDEX;failures=0
    # At most 600 index rows; selected native pages only, stop at 200 eligible.
    for page in range(1,51):
        if not url or len(records)>=goal or failures>=3:break
        try:
            raw,cap=n.capture('ireland',url);rows,next_url=index_rows(raw,url)
        except (requests.RequestException,AssertionError) as exc:
            held.append(dict(url=url,reason='index_source_failure',error=str(exc)[:250]));break
        indexes.append(dict(capture=cap,rows=rows,next_url=next_url))
        for index in rows:
            if len(records)>=goal or failures>=3:break
            oid=index['source_id']
            if oid in seen:continue
            seen.add(oid)
            if oid in known:held.append(dict(index=index,reason='existing_source_identity'));continue
            if m.norm(index['title']) in titles:held.append(dict(index=index,reason='existing_or_selected_title'));continue
            if not creation_date(index['date']):held.append(dict(index=index,reason='index_creation_date_requires_review'));continue
            try:
                body,obj=n.capture('ireland',index['url']);parsed=fields(body);f,reason=facts(parsed,index)
            except (requests.RequestException,AssertionError) as exc:
                failures+=1;held.append(dict(index=index,reason='native_source_failure',error=str(exc)[:250]));continue
            if not reason and inventory_keys(f['accession'])&inventories:reason='existing_or_selected_inventory'
            if reason:held.append(dict(index=index,reason=reason,native_fields=parsed,capture=obj));continue
            records.append(dict(source_record_id=oid,museum=museum,facts=f,source_receipt=obj['receipt'],body_path=obj['body_path'],
                raw_source_record=dict(index_record=index,index_capture=cap,native_fields=parsed)))
            titles.add(m.norm(f['title']));inventories.update(inventory_keys(f['accession']))
        print('Ireland index page',page,'new',len(records),'/',goal,'held',len(held),flush=True)
        m.save(RUN/'progress'/(batch+f'-{page:03d}.json.gz'),dict(records=records,held=held,indexes=indexes,before=counts))
        url=next_url
    out=dict(at=m.now(),museum=museum,before=counts,records=records,held=held,indexes=indexes,source_failures=failures,next_index=url,
        scope='At most 600 painting index entries, native object pages only for eligible selected candidates. Narrative and cross-catalogue identity review required before assembling import plan.')
    m.save(destination,out);print('Ireland research retained',len(records),len(held),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['research']);parser.add_argument('--batch',default='ireland-001')
    args=parser.parse_args();assert re.fullmatch(r'ireland-\d{3}',args.batch);research(args.batch)
