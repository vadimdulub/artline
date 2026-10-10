#!/usr/bin/env python3
"""Bounded native museum metadata captures; no image downloads."""
import argparse
import collections
import gzip
import hashlib
import importlib.util
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin,urlparse,urlencode,parse_qs

import requests
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('museum-expansion-20261006.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
RUN=m.RUN/'native'
SITES={'seattle':'https://art.seattleartmuseum.org','mauritshuis':'https://www.mauritshuis.nl'}
SLUGS={'seattle':'museum-authority-q1816301','mauritshuis':'mauritshuis'}
VALIDATED_INDEXES={}


def capture(provider,url):
    assert url.startswith(SITES[provider]+'/')
    key=hashlib.sha256(url.encode()).hexdigest();root=RUN/provider/'captures';dest=root/(key+'.json')
    if dest.exists():
        rc=m.load(dest);body=root/(key+'.body.gz');raw=gzip.decompress(body.read_bytes())
        assert hashlib.sha256(raw).hexdigest()==rc['sha256']
        if rc['status']!=200:raise requests.HTTPError('Retained source HTTP '+str(rc['status']))
        return raw,dict(receipt=rc,body_path=str(body.relative_to(m.ROOT)))
    time.sleep(0.4)
    with requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (bounded selected metadata; no images)'},timeout=(12,45),stream=True) as response:
        raw=b''
        for chunk in response.iter_content(65536):
            raw+=chunk
            assert len(raw)<4_000_000,'Response exceeds metadata bound'
        rc=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        root.mkdir(parents=True,exist_ok=True);body=root/(key+'.body.gz');assert not body.exists()
        body.write_bytes(gzip.compress(raw,mtime=0));m.save(dest,rc);response.raise_for_status()
        assert response.url.startswith(SITES[provider]+'/')
    return raw,dict(receipt=rc,body_path=str(body.relative_to(m.ROOT)))


def probe(provider):
    url=SITES[provider]+('/objects/images' if provider=='seattle' else '/en/our-collection')
    raw,c=capture(provider,url);soup=BeautifulSoup(raw,'html.parser');selected=[]
    for a in soup.select('a[href]'):
        if (provider=='seattle' and a.get_text(' ',strip=True).startswith('Paintings')) or (provider=='mauritshuis' and '/en/our-collection/artworks/' in a['href']):
            selected.append(dict(title=a.get_text(' ',strip=True),url=urljoin(url,a['href'])))
    print(json.dumps(dict(provider=provider,source=c,links=selected[:4]),ensure_ascii=False),flush=True)
    if provider=='mauritshuis':
        print('scripts',[s.get('src') for s in soup.select('script[src]')],flush=True)
        print('data attributes',[(v.name,{k:str(x)[:180] for k,x in v.attrs.items() if k.startswith('data-')}) for v in soup.select('[data-api],[data-component],[data-collection]')][:10],flush=True)
    if selected:
        body,cap=capture(provider,selected[0]['url']);ss=BeautifulSoup(body,'html.parser')
        for a in ss.select('a[href]'):
            if provider=='seattle' and re.search(r'/objects/\d+/',a['href']):
                print('sample object',urljoin(selected[0]['url'],a['href']),flush=True);break
        print('sample tables',str(ss.select('table'))[:2500],flush=True)


def mauritshuis_index(raw,url):
    soup=BeautifulSoup(raw,'html.parser');grid=soup.select_one('[js-hook-collection-grid]')
    assert grid is not None
    rows=[]
    for a in grid.select('a.collection-grid__item[href]'):
        title=a.select_one('.collection-tile__name');creator=a.select_one('.collection-tile__artist')
        target=urljoin(url,a['href']);match=re.fullmatch(r'https://www\.mauritshuis\.nl/en/our-collection/artworks/([A-Za-z0-9.]+)-[^/?]+/?',target)
        assert title and target.startswith(SITES['mauritshuis']+'/en/our-collection/')
        rows.append(dict(source_id=match[1].casefold() if match else None,url=target,title=title.get_text(' ',strip=True),creator=creator.get_text(' ',strip=True) if creator else None))
    assert len(rows)<=40
    return rows,grid.get('data-next-page-url') or None


def mauritshuis_fields(raw):
    soup=BeautifulSoup(raw,'html.parser');fields={};repeated={}
    for tr in soup.select('table.table-accordion__content tr'):
        cells=tr.find_all(['td','th'],recursive=False)
        if len(cells)!=2:continue
        key,value=(c.get_text(' ',strip=True) for c in cells)
        if key in fields:repeated.setdefault(key,[fields[key]]).append(value)
        else:fields[key]=value
    provenance=[h.parent.get_text(' ',strip=True).removeprefix('Provenance').strip() for h in soup.select('h2') if h.get_text(' ',strip=True)=='Provenance']
    canonical=soup.select('link[rel="canonical"]')
    return dict(fields=fields,repeated=repeated,provenance=provenance,
        heading=soup.h1.get_text(' ',strip=True) if soup.h1 else None,
        canonical=canonical[0].get('href') if len(canonical)==1 else None)


def creation_date(raw):
    before=re.fullmatch(r'before (\d{3,4})',raw or '')
    if before:
        upper=int(before[1])
        # "Before 1971" explicitly entails the artwork cutoff. Preserve the
        # unknown lower bound and the exclusive source endpoint unchanged.
        return (None,upper,'before') if 100<upper<=1971 else None
    match=re.fullmatch(r'(?:(c\.|ca\.)\s*)?(\d{3,4})(?:\s*[-–]\s*(\d{3,4}))?',raw or '')
    if not match:return None
    first,last=int(match[2]),int(match[3] or match[2])
    if not 100<=first<=last<=1970 or (match[1] and last==1970):return None
    return first,last,('circa' if first==last else 'circa_range') if match[1] else ('exact' if first==last else 'range')


def mauritshuis_facts(parsed,index):
    f=parsed['fields'];important={'Title','Dated','Inventory number','Object name'}
    if important&set(parsed['repeated']):return None,'repeated_identity_fields_require_review'
    if f.get('Title')!=index['title'] or parsed['heading']!=f.get('Title'):return None,'native_title_conflict'
    if (parsed['canonical'] or '').rstrip('/')!=index['url'].rstrip('/'):return None,'native_canonical_identity_conflict'
    if not index['source_id'] or (f.get('Inventory number') or '').casefold()!=index['source_id']:return None,'native_inventory_identity_conflict'
    if f.get('Object name') not in ['painting','sculpture','drawing','print']:return None,'object_type_requires_review'
    if not f.get('Artist'):return None,'creator_label_not_stated'
    # The object field retains dates, locations, anonymous labels and qualifiers.
    # Only compare the index name after removing source lifespan parentheses.
    creators=parsed['repeated'].get('Artist',[f['Artist']])
    bare=' and '.join(re.sub(r'\([^)]*\d{3,4}[^)]*\)','',v).strip() for v in creators)
    def name_key(value):return m.norm((value or '').replace('&',' and '))
    anonymous=index['creator']=='Anonymous' and all(re.fullmatch(r'Anonymous(?:\s*\([^)]*\))*',v) for v in creators)
    if not anonymous and name_key(bare)!=name_key(index['creator']):return None,'index_native_attribution_conflict'
    dates=creation_date(f.get('Dated'))
    if not dates:return None,'creation_date_requires_review'
    if len(parsed['provenance'])!=1 or not parsed['provenance'][0]:return None,'provenance_requires_review'
    provenance=parsed['provenance'][0];tail=provenance.rsplit(';',1)[-1].strip()
    acquisition=r'\b(?:purchased?|acquired|acquisition|bequest|gift|donat(?:ed|ion)|transferred|transfer|Mauritshuis)\b'
    outward_loan=False;ownership_event=tail
    if re.search(r'\b(?:loan|lent|deposit|restitution|restituted|returned|promised|missing|lost|private collection)\b',tail,re.I):
        # An explicit outward loan does not transfer collection ownership.
        # Incoming loans and ownership/restitution ambiguities still stay held.
        earlier=provenance.rsplit(';',1)[0].rsplit(';',1)[-1].strip() if ';' in provenance else ''
        outward_loan=bool(re.match(r'on (?:long-term )?loan to\b',tail,re.I) and 'mauritshuis' not in tail.casefold()
            and not re.search(r'\b(?:from|restitution|restituted|returned|promised|missing|lost)\b',tail,re.I)
            and re.search(acquisition,earlier,re.I) and not re.search(r'\b(?:loan|lent|deposit|restitution|restituted|returned|promised)\b',earlier,re.I))
        if not outward_loan:return None,'latest_custody_or_ownership_event_requires_review'
        ownership_event=earlier
    if not re.search(acquisition,ownership_event,re.I):return None,'latest_provenance_event_not_confirmed'
    if re.search(r'\b(?:pair|diptych|triptych|polyptych|verso|reverse|fragment|part of|pendant)\b',f['Title'],re.I):return None,'component_or_version_requires_review'
    basis='Mauritshuis official collection index and native object agree on title, inventory and creator. Latest provenance event retained: '+tail+'. Collection holding only; catalogue room and on-view labels are not used as display evidence.'
    if outward_loan:basis+=' The source records an outward loan after this collection acquisition: '+ownership_event+'. The holding identifies the owning collection and does not claim physical custody at the Mauritshuis.'
    return dict(title=f['Title'],creator_label='; '.join(creators),first=dates[0],last=dates[1],date_precision=dates[2],date_display=f['Dated'],
        work_type=f['Object name'],medium=' on '.join(v for v in [f.get('Technique'),f.get('Material')] if v) or None,
        dimensions=f.get('Dimensions') or None,accession=f['Inventory number'],source_url=index['url'],
        holding_basis=basis),None


def source_id(url):
    if 'mauritshuis.nl/' not in (url or ''):return None
    match=re.search(r'/artworks/([A-Za-z0-9.]+)(?:-|/|$)',url)
    if not match:match=re.search(r'/kunstwerken/[^/?]*-([A-Za-z]*\d+[A-Za-z0-9.]*)/?(?:\?.*)?$',url)
    return match[1].casefold() if match else None


def foreign_inventory_references(parsed):
    # Rijksmuseum painting, sculpture and works-on-paper inventories occur in
    # outward-loan provenance. Titles can differ across the two catalogues.
    return sorted(set(re.findall(r'\b(?:SK|BK|RP)-(?:[A-Z]+-)*\d+(?:[.-]\d+)*(?:-[A-Z])?\b',' '.join(parsed['provenance']))))


def foreign_inventory_records(db):
    return db.execute("SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE accession_number ~ '(SK|BK|RP)-'").fetchall()


def filter_cross_references(source_batch,target_batch):
    assert re.fullmatch(r'mauritshuis-\d{3}',source_batch) and re.fullmatch(r'mauritshuis-\d{3}',target_batch)
    assert not (m.RUN/(source_batch+'-applied.json')).exists()
    plan=m.load(m.RUN/(source_batch+'-current-plan.json.gz'));ready=[];held=list(plan['held'])
    with m.connect() as db:
        existing=collections.defaultdict(list)
        for row in foreign_inventory_records(db):
            for key in m.acc(row['accession_number']):existing[key].append(row)
    for r in plan['records']:
        matches=[v for key in foreign_inventory_references(r['raw_source_record']['native_fields']) for v in existing.get(next(iter(m.acc(key))),[])]
        if matches:held.append(dict(source_record_id=r['source_record_id'],reason='foreign_inventory_already_catalogued',foreign_references=foreign_inventory_references(r['raw_source_record']['native_fields']),existing_records=matches))
        else:ready.append(r)
    filtered=dict(plan,at=m.now(),records=ready,held=held,derived_from=source_batch+'-current-plan.json.gz',cross_reference_exclusions=len(plan['records'])-len(ready))
    dest=m.RUN/(target_batch+'-current-plan.json.gz');m.save(dest,filtered)
    print(json.dumps(dict(batch=target_batch,ready=len(ready),cross_reference_exclusions=filtered['cross_reference_exclusions'],plan_sha256=hashlib.sha256(dest.read_bytes()).hexdigest())),flush=True)


def validate_record(record,body):
    original=record['raw_source_record'];capture=original['index_capture'];cache_key=(capture['body_path'],capture['receipt']['sha256'])
    if cache_key not in VALIDATED_INDEXES:
        raw=gzip.decompress((m.ROOT/capture['body_path']).read_bytes())
        assert capture['receipt']['status']==200 and hashlib.sha256(raw).hexdigest()==capture['receipt']['sha256']
        VALIDATED_INDEXES[cache_key]=mauritshuis_index(raw,capture['receipt']['url'])[0]
    rows=VALIDATED_INDEXES[cache_key]
    assert original['index_record'] in rows and record['source_record_id']==original['index_record']['source_id']
    assert record['museum']['slug']==SLUGS['mauritshuis'] and record['source_receipt']['url']==original['index_record']['url']
    fields=mauritshuis_fields(body);assert fields==original['native_fields']
    facts,reason=mauritshuis_facts(fields,original['index_record']);assert not reason,reason
    return facts


def research(batch,start_page=1):
    assert re.fullmatch(r'mauritshuis-\d{3}',batch)
    assert 1<=start_page<=30
    destination=m.RUN/(batch+'-current-plan.json.gz');assert not destination.exists()
    museum=next(v for v in m.load(m.RUN/'after-wave-08.json')['institutions'] if v['slug']==SLUGS['mauritshuis'])
    with m.connect() as db:
        urls={v['source_url'] for v in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url ILIKE '%mauritshuis.nl/%'")}
        urls.update(v['canonical_url'] for v in db.execute("SELECT canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url ILIKE '%mauritshuis.nl/%'"))
        known={source_id(u) for u in urls};titles={m.norm(r[k]) for r in db.execute('SELECT title,alternate_title FROM artworks') for k in ['title','alternate_title'] if r[k]}
        before=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(museum['id'],)).fetchone()
        scoped=db.execute('''WITH selected AS MATERIALIZED (SELECT id FROM artworks WHERE current_institution_id=%s
          UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s AND superseded_by IS NULL)
          SELECT accession_number FROM artworks JOIN selected USING(id)''',(museum['id'],museum['id'])).fetchall()
        inventories=set().union(*(m.acc(v['accession_number']) for v in scoped)) if scoped else set()
        foreign_inventories=set().union(*(m.acc(r['accession_number']) for r in foreign_inventory_records(db)))
    goal=max(0,200-before['eligible']);ready=[];held=[];seen=set();listings=[];inspected=0;failures=0
    url=SITES['mauritshuis']+'/en/our-collection'+('' if start_page==1 else '?p='+str(start_page))
    for page in range(start_page,start_page+14):
        if not url or len(ready)>=goal or inspected>=300 or failures>=3:break
        try:raw,index_capture=capture('mauritshuis',url);rows,next_url=mauritshuis_index(raw,url)
        except requests.RequestException as exc:
            held.append(dict(url=url,reason='index_source_failure',error=str(exc)[:250]));break
        listings.append(dict(capture=index_capture,rows=len(rows)))
        for item in rows:
            if len(ready)>=goal or inspected>=300 or failures>=3:break
            key=item['source_id']
            if key is None:
                held.append(dict(index_record=item,reason='non_object_collection_feature_requires_review'));continue
            if key in seen:continue
            seen.add(key);reason=None
            if key in known:reason='source_identity_already_catalogued'
            elif m.acc(key)&inventories:reason='existing_or_selected_inventory'
            elif m.norm(item['title']) in titles:reason='existing_or_selected_title_requires_identity_review'
            if reason:held.append(dict(index_record=item,reason=reason));continue
            inspected+=1
            try:
                body,object_capture=capture('mauritshuis',item['url']);parsed=mauritshuis_fields(body);f,reason=mauritshuis_facts(parsed,item)
            except requests.RequestException as exc:
                failures+=1;held.append(dict(index_record=item,reason='object_source_failure',error=str(exc)[:250]));continue
            failures=0
            if not reason and any(m.acc(inv)&foreign_inventories for inv in foreign_inventory_references(parsed)):
                reason='foreign_inventory_already_catalogued'
            if reason:
                held.append(dict(index_record=item,reason=reason,native_fields=parsed,object_capture=object_capture));continue
            ready.append(dict(source_record_id=key,museum=museum,facts=f,
                raw_source_record=dict(index_record=item,index_capture=index_capture,native_fields=parsed),
                source_receipt=object_capture['receipt'],body_path=object_capture['body_path']))
            titles.add(m.norm(f['title']));inventories.update(m.acc(f['accession']))
            if len(ready)%10==0:print('Mauritshuis ready',len(ready),'/',goal,'inspected',inspected,flush=True)
        m.save(RUN/'mauritshuis'/(batch+f'-progress-{page:02d}.json.gz'),dict(at=m.now(),before=before,records=ready,held=held,listings=listings,inspected=inspected))
        url=next_url
    plan=dict(at=m.now(),records=ready,held=held,listings=listings,before=before,inspected=inspected,museum=museum,start_page=start_page,
        policy='At most 14 bounded index pages and 300 object checks, stopping at 200 eligible museum works. Native identity and latest provenance event required; loans, uncertain custody, components, duplicate identities and unresolved dates held. Literal creators and source fields preserved. No images or current-display assertions.')
    m.save(destination,plan)
    print(json.dumps(dict(batch=batch,ready=len(ready),held=len(held),inspected=inspected,plan_sha256=hashlib.sha256(destination.read_bytes()).hexdigest())),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('provider',choices=list(SITES));p.add_argument('--batch');p.add_argument('--start-page',type=int,default=1);p.add_argument('--filter-from');args=p.parse_args()
    if args.filter_from:assert args.provider=='mauritshuis' and args.batch;filter_cross_references(args.filter_from,args.batch)
    elif args.batch:assert args.provider=='mauritshuis';research(args.batch,args.start_page)
    else:probe(args.provider)
