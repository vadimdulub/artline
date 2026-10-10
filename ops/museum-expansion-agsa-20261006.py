#!/usr/bin/env python3
"""Bounded AGSA painting research from native catalogue pages; no media requests."""
import argparse
import importlib.util
import re
from pathlib import Path
from urllib.parse import urljoin,urlparse,parse_qs
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('ireland',Path(__file__).with_name('museum-expansion-ireland-20261006.py'))
i=importlib.util.module_from_spec(spec);spec.loader.exec_module(i)
m=i.m;n=i.n
SITE='https://www.agsa.sa.gov.au'
n.SITES['agsa']=SITE
RUN=n.RUN/'agsa'
SLUG='wikimedia-museum-q705557'
INDEX=SITE+'/collection-publications/collection/?has-images=no&medium=Painting&on-display=no&creation-date-end=1970&page=1&type=work&work-sort=alphabetic'
captured_body=i.captured_body
title_collisions=i.title_collisions


def clean(value):return ' '.join((value or '').split())


def source_id(url):
    p=urlparse(url or '')
    match=re.fullmatch(r'/collection-publications/collection/works/[^/]+/(\d+)/?',p.path)
    return match[1] if p.hostname in ['www.agsa.sa.gov.au','agsa.sa.gov.au','www.artgallery.sa.gov.au'] and match else None


def inventory_keys(value):return m.acc(value)


def creation_date(value):
    raw=clean(value)
    direct=i.creation_date(raw)
    if direct:return direct
    shortened=re.fullmatch(r'(c\.?\s*)?(\d{4})[-–](\d{2})',raw)
    if shortened:
        first=int(shortened[2]);last=(first//100)*100+int(shortened[3])
        if last<first:last+=100
        return i.creation_date(('c.' if shortened[1] else '')+str(first)+'-'+str(last))
    return None


def index_rows(raw,url):
    p=urlparse(url);q=parse_qs(p.query)
    assert p.hostname=='www.agsa.sa.gov.au' and p.path=='/collection-publications/collection/'
    assert q.get('medium')==['Painting'] and q.get('type')==['work'] and q.get('creation-date-end')==['1970']
    soup=BeautifulSoup(raw,'html.parser');rows=[]
    for item in soup.select('.collection-work-item'):
        a=item.select_one('.collection-work-item__title a[href]');assert a
        target=urljoin(SITE,a['href']);assert source_id(target)
        def value(selector):
            node=item.select_one(selector);return clean(node.get_text(' ',strip=True)) if node else None
        rows.append(dict(source_id=source_id(target),url=target,title=clean(a.get_text(' ',strip=True)),
            creator_names=[clean(c.get_text(' ',strip=True)) for c in item.select('.collection-work-item__creator-names')],
            creator_lifespans=[clean(c.get_text(' ',strip=True)) for c in item.select('.collection-work-item__creator-dates')],
            date=value('.collection-work-item__creation-date'),medium=value('.collection-work-item__medium'),
            accession=value('.collection-work-item__accession .collection-work-item__data > span')))
    assert 0<len(rows)<=24 and len({r['source_id'] for r in rows})==len(rows)
    links={urljoin(url,a['href']) for a in soup.select('a[href]') if a.get_text(' ',strip=True)=='Next page'}
    assert len(links)<=1
    return rows,next(iter(links),None)


def fields(raw):
    soup=BeautifulSoup(raw,'html.parser');detail=soup.select_one('.collection-detail-work-details')
    heading=soup.select_one('h1.page-header__title');assert detail and heading
    title=clean(heading.get_text(' ',strip=True));parts=[clean(s) for s in detail.stripped_strings]
    assert parts.count(title)==1
    split=parts.index(title);prefix=parts[:split];tail=parts[split+1:]
    values={};repeated={}
    for dt in soup.select('dl.collection-detail-data dt'):
        dd=dt.find_next_sibling('dd');assert dd
        key=clean(dt.get_text(' ',strip=True));value=clean(dd.get_text(' ',strip=True))
        if key in values:repeated.setdefault(key,[values[key]]).append(value)
        else:values[key]=value
    return dict(title=title,header_parts=parts,creator_label=clean(' '.join(prefix)),
        creator_names=[clean(a.get_text(' ',strip=True)) for a in detail.select('.collection-detail-work-details__creator-link')],
        creation_and_medium=tail,fields=values,repeated=repeated,
        narratives=[dict(id=p.get('id'),text=clean(p.get_text(' ',strip=True))) for p in soup.select('.collection-detail-body [role=tabpanel]') if p.get('id')!='details'],
        image_captions=[clean(BeautifulSoup(a['data-caption'],'html.parser').get_text(' ',strip=True)) for a in soup.select('.collection-image-gallery a[data-caption]')])


def facts(parsed,index):
    f=parsed['fields'];tail=parsed['creation_and_medium']
    if parsed['repeated']:return None,'repeated_fields_require_review'
    if parsed['title']!=index['title']:return None,'index_title_conflict'
    if len(tail)!=2 or tail[0]!=index['date']:return None,'native_creation_layout_or_index_conflict'
    if parsed['creator_names']!=index['creator_names'] or len(parsed['creator_names'])!=1:return None,'creator_identity_or_multiple_roles_require_review'
    dates=creation_date(tail[0])
    if not dates:return None,'creation_date_requires_review'
    inventory=f.get('Accession number') or ''
    if inventory!=index['accession'] or not re.fullmatch(r'[0-9][0-9A-Za-z.]*',inventory):return None,'inventory_or_component_identity_requires_review'
    if f.get('Media category')!='Painting' or f.get('Medium')!=index['medium'] or tail[1]!=f.get('Medium'):return None,'painting_or_medium_identity_requires_review'
    credit=f.get('Credit line') or ''
    if not re.search(r'\b(?:purchased?|gift|bequest|bequeathed?|grant|presented|donated|fund)\b',credit,re.I):return None,'acquisition_credit_requires_review'
    if re.search(r'\b(?:loan|lent|deposit|deaccession|returned|restitu\w*|promised)\b',credit,re.I):return None,'custody_qualification_requires_review'
    if re.search(r'\b(?:diptych|triptych|polyptych|pair of|recto|verso|reverse)\b',parsed['title'],re.I):return None,'compound_object_requires_review'
    return dict(title=parsed['title'],creator_label=parsed['creator_label'],first=dates[0],last=dates[1],date_precision=dates[2],date_display=tail[0],
        work_type='painting',medium=f['Medium'],dimensions=f.get('Dimensions') or None,accession=inventory,source_url=index['url'],
        holding_basis='Art Gallery of South Australia official painting index and native object page agree on title, creator, creation date, medium and individual accession. Acquisition credit: '+credit+'. Collection holding only; no current display claim.'),None


def existing_keys(db,iid):
    rows=db.execute('''WITH selected AS MATERIALIZED (
      SELECT id FROM artworks WHERE current_institution_id=%s
      UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s AND superseded_by IS NULL)
      SELECT a.id::text,a.title,a.alternate_title,a.accession_number FROM selected s JOIN artworks a ON a.id=s.id''',(iid,iid)).fetchall()
    urls={r['source_url'] for r in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND (source_url LIKE '%agsa.sa.gov.au/%' OR source_url LIKE '%artgallery.sa.gov.au/%')")}
    urls.update(r['canonical_url'] for r in db.execute("SELECT canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url LIKE '%agsa.sa.gov.au/%' OR canonical_url LIKE '%artgallery.sa.gov.au/%')"))
    return {source_id(u) for u in urls}-{None},{m.norm(r[k]) for r in rows for k in ['title','alternate_title'] if r[k]},set().union(*(inventory_keys(r['accession_number']) for r in rows))


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
    museum=next(r for r in m.load(m.RUN/'after-wave-17.json')['institutions'] if r['slug']==SLUG)
    with m.connect() as db:
        known,titles,inventories=existing_keys(db,museum['id'])
        before=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(museum['id'],)).fetchone()
        old=db.execute('''WITH selected AS MATERIALIZED (SELECT id FROM artworks WHERE current_institution_id=%s
          UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s AND superseded_by IS NULL)
          SELECT to_jsonb(a) row FROM selected s JOIN artworks a ON a.id=s.id ORDER BY a.id''',(museum['id'],museum['id'])).fetchall()
    m.save(m.BACKUP/(batch+'-existing-artwork-rows.json.gz'),dict(at=m.now(),artworks=old))
    m.save(RUN/(batch+'-identity-before.json'),dict(at=m.now(),museum=museum,before=before,known_source_ids=sorted(known),existing_titles=sorted(titles),existing_inventories=sorted(inventories)))
    goal=max(0,200-before['eligible']);target=min(goal+20,160);assert goal>0
    records=[];held=[];indexes=[];seen=set();url=INDEX;failures=0;examined=0;remaining=[]
    for page in range(1,16):
        if not url or len(records)>=target or failures>=3:break
        try:raw,cap=n.capture('agsa',url);rows,next_url=index_rows(raw,url)
        except (i.requests.RequestException,AssertionError) as exc:
            held.append(dict(url=url,reason='index_source_failure',error=str(exc)[:250]));break
        indexes.append(dict(capture=cap,rows=rows,next_url=next_url))
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
            if inventory_keys(index['accession'])&inventories:held.append(dict(index=index,reason='existing_or_selected_inventory'));continue
            if not creation_date(index['date']):held.append(dict(index=index,reason='index_creation_date_requires_review'));continue
            try:body,obj=n.capture('agsa',index['url']);parsed=fields(body);f,reason=facts(parsed,index)
            except (i.requests.RequestException,AssertionError) as exc:
                failures+=1;held.append(dict(index=index,reason='native_source_failure',error=str(exc)[:250]));continue
            if reason:held.append(dict(index=index,reason=reason,native_fields=parsed,capture=obj));continue
            records.append(dict(source_record_id=oid,museum=museum,facts=f,source_receipt=obj['receipt'],body_path=obj['body_path'],
                raw_source_record=dict(index_record=index,index_capture=cap,native_fields=parsed)))
            titles.add(key);inventories.update(inventory_keys(f['accession']))
        print('AGSA page',page,'candidates',len(records),'held',len(held),'examined',examined,flush=True)
        m.save(RUN/'progress'/(batch+f'-{page:03d}.json.gz'),dict(records=records,held=held,indexes=indexes,before=before))
        if remaining:break
        url=next_url
    m.save(destination,dict(at=m.now(),museum=museum,before=before,records=records,held=held,indexes=indexes,source_failures=failures,
        examined=examined,resume_index=url,unprocessed_captured_rows=remaining,next_index=indexes[-1]['next_url'] if indexes else url,
        policy='At most 360 painting-index entries, native pages only for selected eligible candidates. Fresh source ID, inventory and title checks. Individual narrative, date/creator chronology and version review required before import. No images downloaded.'))
    print('AGSA research retained',len(records),len(held),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['research']);parser.add_argument('--batch',default='agsa-001')
    args=parser.parse_args();assert re.fullmatch(r'agsa-\d{3}',args.batch);research(args.batch)
