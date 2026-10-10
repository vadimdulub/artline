#!/usr/bin/env python3
"""Bounded Tretyakov object HTML evidence, excluding the global app-state payload."""
import argparse
import collections
import gzip
import hashlib
import importlib.util
import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

spec=importlib.util.spec_from_file_location('native',Path(__file__).with_name('museum-expansion-native-20261006.py'))
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
m=n.m
BASE='https://my.tretyakov.ru'
SLUG='wikimedia-museum-q183334'
RUN=n.RUN/'tretyakov_collection'
MARKER=b'<script>window.__NUXT__='
CACHE={}


def source_id(url):
    parsed=urlparse(url or '')
    if parsed.hostname!='my.tretyakov.ru':return None
    match=re.fullmatch(r'/(?:app/)?masterpiece/(\d+)/?',parsed.path)
    return match[1] if match else None


def inventory_keys(value):
    cleaned=re.sub(r'^(?:инвентарный номер|инв\.?|гтг|gtg)\s*', '',value or '',flags=re.I)
    return m.acc(cleaned)


def capture(key):
    assert re.fullmatch(r'\d{1,8}',key)
    dest=RUN/'captures'/(key+'.json');body=dest.with_suffix('.body.gz')
    if dest.exists():
        receipt=m.load(dest);raw=gzip.decompress(body.read_bytes())
        assert hashlib.sha256(raw).hexdigest()==receipt['sha256']
        return raw,dict(receipt=receipt,body_path=str(body.relative_to(m.ROOT)))
    url=BASE+'/app/masterpiece/'+key
    # The server-rendered object and footer precede a very large global state
    # script. Capture the complete object HTML and avoid fetching that dataset.
    if key=='9337' and (RUN/'9337-head-discovery.json').exists():
        old=m.load(RUN/'9337-head-discovery.json');raw=gzip.decompress((m.ROOT/old['body_path']).read_bytes());status=old['status'];final=old['final_url'];at=old['retrieved_at']
    else:
        time.sleep(0.4)
        with n.requests.get(url,stream=True,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (bounded selected metadata; no images)'},timeout=(12,45)) as response:
            status=response.status_code;final=response.url;at=m.now();response.raise_for_status();raw=b''
            for chunk in response.iter_content(32768):
                raw+=chunk
                if MARKER in raw or len(raw)>1_500_000:break
    assert status==200 and source_id(final)==key and MARKER in raw,'Complete rendered object HTML not captured'
    raw=raw.split(MARKER,1)[0]
    assert b'</footer>' in raw and b'masterpiece-discription-block' in raw
    receipt=dict(url=url,final_url=final,status=status,retrieved_at=at,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),capture_mode='complete_server_rendered_object_html_before_global_app_state',complete_http_response=False,excluded_marker=MARKER.decode())
    body.parent.mkdir(parents=True,exist_ok=True);body.write_bytes(gzip.compress(raw,mtime=0));m.save(dest,receipt)
    return raw,dict(receipt=receipt,body_path=str(body.relative_to(m.ROOT)))


def fields(raw):
    soup=n.BeautifulSoup(raw,'html.parser');panels=[p for p in soup.select('.masterpiece-discription-block') if p.select_one('.discription-masterpiece-name')]
    assert len(panels)==1 and soup.select_one('footer') is not None,'Expected one complete object identity panel'
    panel=panels[0];names=list(panel.select_one('.discription-masterpiece-name').stripped_strings)
    assert len(names)==2
    creator=panel.select_one('.discription-author-name').get_text(' ',strip=True)
    values={}
    for div in panel.select('.masterpiece-discr'):
        label=div.select_one('.masterpiece-discr-name')
        if label:
            key=label.get_text(' ',strip=True).removesuffix('-').strip();value=div.get_text(' ',strip=True).removeprefix(label.get_text(' ',strip=True)).strip()
            assert key not in values;values[key]=value
    way=panel.select('.waydat');meta=soup.select('meta[property="og:title"],meta[name="og:title"]');related={}
    for a in soup.select('a[href]'):
        target=n.urljoin(BASE,a['href']);key=source_id(target);title=a.get_text(' ',strip=True)
        if key and title:related[key]=dict(source_id=key,title=title,url=target)
    return dict(title=names[0],date_display=names[1],creator=creator,fields=values,acquisition=way[0].get_text(' ',strip=True) if len(way)==1 else None,
        page_title=soup.title.get_text(' ',strip=True) if soup.title else None,og_title=meta[0].get('content') if len(meta)==1 else None,
        footer=soup.select_one('footer').get_text(' ',strip=True),related=list(related.values()))


def dates(literal):
    value=re.sub(r'^Около\s+','c. ',literal or '',flags=re.I)
    return n.creation_date(value)


def facts(parsed,url):
    f=parsed['fields']
    if parsed['title']!=parsed['page_title'] or parsed['title']!=parsed['og_title']:return None,'native_titles_conflict'
    if 'Третьяковская галерея' not in parsed['footer']:return None,'institution_identity_requires_review'
    if not f.get('Инвентарный номер') or not parsed['creator']:return None,'missing_inventory_or_creator'
    date=dates(parsed['date_display'])
    if not date:return None,'creation_date_requires_review'
    technique=f.get('Техника') or '';material=f.get('Материал') or ''
    techniques={v.strip() for v in technique.split(',')}
    if technique in ['масло','темпера'] and material in ['холст','дерево','картон','бумага','фанера','холст на картоне','бумага на картоне']:kind='painting'
    elif 'акварель' in techniques and techniques<={'акварель','карандаш','уголь','графитный карандаш'} and material in ['бумага','бумага на картоне']:kind='watercolor'
    else:return None,'object_technique_requires_review'
    acq=parsed['acquisition'] or ''
    if not re.match(r'(?:Поступил[ао]?|Приобретен[ао]?|Приобретён[ао]?|Передан[ао]?|Дар)\b',acq):return None,'acquisition_statement_requires_review'
    if re.search(r'временн|реститу|возврат|депозит|выставк',acq,re.I):return None,'custody_qualification_requires_review'
    if re.search(r'фрагмент|оборот|триптих|диптих|копия',parsed['title'],re.I):return None,'component_or_version_requires_review'
    return dict(title=parsed['title'],creator_label=parsed['creator'],first=date[0],last=date[1],date_precision=date[2],date_display=parsed['date_display'],work_type=kind,medium=f['Техника']+'; '+f['Материал'],dimensions=f.get('Размер') or None,accession=f['Инвентарный номер'],source_url=url,holding_basis='Official Tretyakov collection object, reached from its own collection links, with native inventory and acquisition statement: '+acq+'. This identifies the Tretyakov institutional collection, including its departments, without claiming physical presence in a particular building or current display. Original Russian labels and unknown dimension units are retained.'),None


def home_items():
    url='https://www.tretyakovgallery.ru/';key=hashlib.sha256(url.encode()).hexdigest();root=n.RUN/'tretyakov/captures'
    rc=m.load(root/(key+'.json'));path=root/(key+'.body.gz');raw=gzip.decompress(path.read_bytes());assert hashlib.sha256(raw).hexdigest()==rc['sha256']
    soup=n.BeautifulSoup(raw,'html.parser');state=next(s.get_text() for s in soup.select('script:not([src])') if '__NUXT__' in s.get_text())
    block=re.search(r'collections:\[(.*?)\],',state)[1];items=[]
    for piece in re.findall(r'\{[^{}]+\}',block):
        v={k:json.loads(value) for k,value in re.findall(r'(\w+):("(?:\\.|[^"\\])*")',piece)}
        assert source_id(v['external_url'])
        items.append(dict(source_id=source_id(v['external_url']),title=v['name'],url=v['external_url'],home_record=v))
    return items,dict(receipt=rc,body_path=str(path.relative_to(m.ROOT)))


def read_fields(cap):
    rc=cap['receipt'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes())
    assert rc['status']==200 and rc['capture_mode']=='complete_server_rendered_object_html_before_global_app_state'
    assert hashlib.sha256(raw).hexdigest()==rc['sha256'] and MARKER not in raw and b'</footer>' in raw
    return fields(raw)


def validate_record(record,body):
    original=record['raw_source_record'];parsed=read_fields(dict(receipt=record['source_receipt'],body_path=record['body_path']))
    assert parsed==original['native_fields'] and source_id(record['source_receipt']['url'])==record['source_record_id']
    assert source_id(record['source_receipt']['final_url'])==record['source_record_id'] and record['museum']['slug']==SLUG
    discovery=original['discovery'];item=discovery['item']
    if discovery['kind']=='homepage':
        items,cap=home_items();assert item in items and cap==discovery['capture']
    else:
        assert discovery['kind']=='related_object';parent=read_fields(discovery['capture']);assert item in parent['related']
    assert item['title']==parsed['title'] and item['source_id']==record['source_record_id']
    review=original['identity_review']
    assert review['decision']=='new_distinct_work' and review['english_readings'] and review['comparison_evidence']
    for evidence in review['comparison_evidence']:
        assert hashlib.sha256((m.ROOT/evidence['path']).read_bytes()).hexdigest()==evidence['sha256']
    f,reason=facts(parsed,record['source_receipt']['final_url']);assert not reason,reason
    return f


def check_translated_title_identities(db,records):
    lookup=collections.defaultdict(list)
    for row in db.execute('SELECT id::text,title,alternate_title FROM artworks'):
        for title in {m.norm(row[k]) for k in ['title','alternate_title'] if row[k]}:lookup[title].append(row)
    expected={}
    for record in records:
        review=record['raw_source_record']['identity_review']
        actual={row['id']:row for title in review['english_readings'] for row in lookup.get(m.norm(title),[])}
        cleared={row['id']:row for row in review.get('cleared_title_collisions',[])}
        assert actual.keys()==cleared.keys(),'Unreviewed translated-title collision'
        for key,row in actual.items():
            assert row['title']==cleared[key]['title'] and cleared[key]['creators'],'Changed title or unknown creator in disambiguation'
            expected[key]=cleared[key]
    if expected:
        links=collections.defaultdict(list)
        for row in db.execute('''SELECT aa.artwork_id::text,ar.id::text,ar.display_name name,ar.slug,aa.attribution_role role
          FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY ar.id,aa.attribution_role''',(list(expected),)):
            key=row.pop('artwork_id');links[key].append(row)
        for key,row in expected.items():assert links[key]==sorted(row['creators'],key=lambda v:(v['id'],v['role'])),'Creator identity changed since alias review'


def existing_keys(db,iid):
    urls={r['source_url'] for r in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE '%tretyakov.ru/%'")}
    urls.update(r['canonical_url'] for r in db.execute("SELECT canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url LIKE '%tretyakov.ru/%'"))
    titles={m.norm(r[k]) for r in db.execute('SELECT title,alternate_title FROM artworks') for k in ['title','alternate_title'] if r[k]}
    rows=db.execute('''WITH selected AS MATERIALIZED (SELECT id FROM artworks WHERE current_institution_id=%s
      UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s AND superseded_by IS NULL)
      SELECT accession_number FROM artworks JOIN selected USING(id)''',(iid,iid)).fetchall()
    return {source_id(u) for u in urls},titles,set().union(*(inventory_keys(r['accession_number']) for r in rows))


def research(batch,skip_failures_from=None):
    assert re.fullmatch(r'\d{3}',batch)
    dest=n.RUN/'tretyakov'/('review-candidates-'+batch+'.json.gz');assert not dest.exists()
    museum=next(v for v in m.load(m.RUN/'after-wave-10.json')['institutions'] if v['slug']==SLUG)
    with m.connect() as db:known,titles,inventories=existing_keys(db,museum['id'])
    items,cap=home_items();queue=collections.deque(dict(kind='homepage',item=v,capture=cap) for v in items);seen=set();ready=[];held=[];checked=0;failures=0
    if skip_failures_from:
        assert re.fullmatch(r'\d{3}',skip_failures_from)
        previous=m.load(n.RUN/'tretyakov'/('review-candidates-'+skip_failures_from+'.json.gz'))
        for row in previous['held']:
            if row['reason']=='native_source_failure':
                seen.add(row['discovery']['item']['source_id']);held.append(dict(row,reason='prior_source_failure_retained_not_retried'))
    while queue and checked<40 and len(ready)<24 and failures<3:
        discovery=queue.popleft();item=discovery['item'];key=item['source_id']
        if key in seen:continue
        seen.add(key);checked+=1
        try:raw,cap=capture(key);parsed=fields(raw)
        except (n.requests.RequestException,AssertionError) as exc:
            failures+=1;held.append(dict(discovery=discovery,reason='native_source_failure',error=str(exc)[:250]));continue
        failures=0
        queue.extend(dict(kind='related_object',item=v,capture=cap) for v in parsed['related'])
        f,reason=facts(parsed,cap['receipt']['final_url'])
        if item['title']!=parsed['title']:reason='discovery_title_conflict'
        if key in known:reason='existing_source_identity'
        elif inventory_keys(parsed['fields'].get('Инвентарный номер'))&inventories:reason='existing_inventory'
        elif m.norm(parsed['title']) in titles:reason='existing_title_requires_review'
        original=dict(discovery=discovery,native_fields=parsed)
        record=dict(source_record_id=key,museum=museum,facts=f,raw_source_record=original,source_receipt=cap['receipt'],body_path=cap['body_path'])
        if reason:held.append(dict(reason=reason,record=record));continue
        ready.append(record);titles.add(m.norm(f['title']));inventories.update(inventory_keys(f['accession']))
        if len(ready)%5==0:print('Tretyakov candidates',len(ready),'checked',checked,flush=True)
    m.save(dest,dict(at=m.now(),records=ready,held=held,checked=checked,policy='Research candidates only. Existing foreign-language titles and missing-inventory records require an additional identity review before a subset is pinned for insertion. At most 40 object pages; global app state and images not downloaded.'))
    print(json.dumps(dict(candidates=len(ready),held=len(held),checked=checked)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True);p.add_argument('--skip-failures-from');args=p.parse_args();research(args.batch,args.skip_failures_from)
