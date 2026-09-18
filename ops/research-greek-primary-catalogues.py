#!/usr/bin/env python3
"""Twenty bounded, primary-museum painter scopes; facts, never image downloads.

Collect at most twelve previously uncatalogued object pages per painter, plus
already catalogued pages within the first twenty-four source-listed works.
Unknown dates and attribution conflicts remain editorial holds.
"""
import argparse,hashlib,importlib.util,json,re,time
from pathlib import Path
from urllib.parse import urlsplit
import requests
from bs4 import BeautifulSoup

s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
BASE=m.x.BASE/'greek-primary-catalogues'
ORIGIN='https://www.nationalgallery.gr'

def capture(url):
    parsed=urlsplit(url)
    assert parsed.scheme=='https' and parsed.netloc=='www.nationalgallery.gr' and not parsed.query
    key=hashlib.sha256(url.encode()).hexdigest();path=BASE/'captures'/(key+'.html');rp=path.with_suffix('.receipt.json')
    if path.exists() and rp.exists():
        raw=path.read_bytes();receipt=json.loads(rp.read_text());assert receipt['sha256']==m.m.core.sha(raw) and receipt['url']==url
        return BeautifulSoup(raw,'html.parser'),receipt
    # Retain exploratory captures; a fresh dated capture supplies the evidence.
    if path.exists():path.rename(path.with_suffix('.exploratory.html'))
    time.sleep(2)
    with requests.get(url,timeout=(15,45),stream=True,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected factual museum metadata; https://github.com/vadimdulub/artline)'}) as resp:
        resp.raise_for_status();chunks=[];size=0
        for chunk in resp.iter_content(65536):
            chunks.append(chunk);size+=len(chunk)
            if size>3_000_000:raise ValueError('Bounded museum page capture exceeded')
        raw=b''.join(chunks);receipt=dict(url=url,resolved_url=resp.url,retrieved_at=m.m.core.now(),sha256=m.m.core.sha(raw),bytes=len(raw),status=resp.status_code)
    m.m.core.save_new(path,raw);m.m.core.save_new(rp,receipt)
    return BeautifulSoup(raw,'html.parser'),receipt

def text(node):return node.get_text(' ',strip=True) if node else ''

def date(raw):
    clean=raw.strip().replace('–','-').replace('—','-')
    match=re.fullmatch(r'(?:c\.?|ca\.?|circa)?\s*(\d{4})(?:\s*-\s*(\d{4}))?',clean,re.I)
    if not match:return dict(display=raw,first=None,last=None,precision='unknown',eligible=False,review='Unknown/ambiguous source date retained for editorial review')
    first=int(match[1]);last=int(match[2] or match[1]);circa=bool(re.match(r'c',clean,re.I))
    return dict(display=raw,first=first,last=last,precision='circa_range' if circa and first!=last else 'circa' if circa else 'range' if first!=last else 'exact',eligible=first<=last<=1970,review='museum_creation_date')

def roster():
    path=BASE/'primary-roster.json'
    if path.exists():return json.loads(path.read_text())
    index,receipt=capture(ORIGIN+'/en/artists/')
    links={a['href'].rstrip('/').rsplit('/',1)[-1]:dict(url=a['href'],label=text(a)) for a in index.select('a[href]') if re.fullmatch(ORIGIN+r'/en/artist/[a-z0-9-]+/',a['href'])}
    rows=json.loads((BASE/'existing-museum-person-ids.json').read_text())
    extras={'altamouras-ioannis':'Q3154048','giallinas-angelos':'Q536988','tsokos-dionysios':'Q155272','vegias-dionysios':'Q16863174','zacharias-ioannis':'Q3154052','zairis-emmanuel':'Q18019560'}
    with m.m.r.base.connect(False) as db,db.transaction():
        db.execute('SET TRANSACTION READ ONLY')
        for key,qid in extras.items():
            a=db.execute("SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=%s AND a.status<>'archived'",(qid,)).fetchone()
            if a is None:raise ValueError('Existing exact painter identity missing: '+qid)
            rows.append({**a,'external_id':key,'wikidata':qid,'canonical_url':links[key]['url'],'identity_basis':'Exact existing Wikidata person, source full-name/lifespan still requires primary corroboration'})
    for n,row in enumerate(rows,1):
        assert row['external_id'] in links and links[row['external_id']]['url']==row['canonical_url']
        row.update(round=n,index_label=links[row['external_id']]['label'])
    assert len(rows)==20
    payload=dict(at=m.m.core.now(),index_receipt=receipt,painters=rows,scope='Twenty distinct named-painter primary catalogue reviews, at most twelve new metadata objects each; no museum image reuse permission inferred.')
    m.m.core.save_new(path,payload);return payload

def research(n):
    row=roster()['painters'][n-1];run=BASE/f'round-{n:02d}';dest=run/'research.json'
    if dest.exists():return
    soup,receipt=capture(row['canonical_url']);main=soup.find('main') or soup
    links=list(dict.fromkeys(a['href'] for a in main.select('a[href]') if re.fullmatch(ORIGIN+r'/en/artwork/[a-z0-9-]+/',a['href'])))[:24]
    artist_fact=dict(name=text(main.find('h1')),headings=[text(x) for x in main.find_all(['h1','h2'])][:5],receipt=receipt)
    # The primary person page may show disputed birth years; retain those facts,
    # never overwrite existing uncertain numeric biography dates here.
    with m.m.r.base.connect(False) as db,db.transaction():
        db.execute('SET TRANSACTION READ ONLY')
        keys=[u.rstrip('/').rsplit('/',1)[-1] for u in links]
        known={r['external_id'] for r in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='nationalgallery-gr-work' AND external_id=ANY(%s)",(keys,)).fetchall()}
        cited={r['source_url'] for r in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(links,)).fetchall()}
    selected=[];new_count=0;holds=[]
    for url in links:
        key=url.rstrip('/').rsplit('/',1)[-1];existing=key in known or url in cited
        if not existing and new_count>=12:continue
        if not existing:new_count+=1
        try:
            obj,oreceipt=capture(url);body=obj.find('main') or obj
            heading=body.select_one('h1.artwork');span=heading.find('span') if heading else None
            rawdate=text(span);title=text(heading)
            if rawdate:title=title.removesuffix(rawdate).rstrip(' ,')
            author=body.select_one('p.artist');makerlinks=[a['href'] for a in author.select('a[href]')] if author else []
            inv=text(body.select_one('.artwork-no')).removeprefix('Inv. Number').strip()
            medium=text(body.select_one('p.description'));collection=text(body.select_one('p.obtainment'))
            reason=None
            if not title or not inv:reason='Missing source title or museum inventory identifier'
            if makerlinks!=[row['canonical_url']]:reason='Object maker does not exactly match the scoped primary person page'
            d=date(rawdate)
            if d['first'] is not None and not d['eligible']:reason='Creation range beyond 1970 or invalid'
            work=dict(key=key,title=title,date=d,accession=inv,medium_dimensions=medium,collection_credit=collection,source_url=url,receipt=oreceipt,artist=row,source_artist_label=text(author),source_artist_links=makerlinks,listed_on_artist_page=True,existing_source_identity=existing,review_reason=reason,status='review',image_policy='Museum photograph not downloaded. Match a separate Commons reproduction and per-file licence before use. No current-display assertion imported.')
            selected.append(work)
        except Exception as e:holds.append(dict(url=url,error=type(e).__name__,reason=str(e)[:300]))
    result=dict(at=m.m.core.now(),round=n,artist=row,primary_artist=artist_fact,listed_object_urls=links,inspected=len(selected),new_source_objects=sum(not w['existing_source_identity'] for w in selected),records=selected,source_failures=holds,completed=not holds)
    m.m.core.save_new(dest,result);print('Greek primary',n,row['display_name'],'inspected',len(selected),'new source objects',result['new_source_objects'],'source failures',len(holds),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--round',type=int);a=p.parse_args()
    for n in ([a.round] if a.round else range(1,21)):research(n)
