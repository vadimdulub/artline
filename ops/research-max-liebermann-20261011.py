#!/usr/bin/env python3
"""Creator-scoped, resumable metadata discovery. No DB writes or image downloads."""
import argparse, collections, concurrent.futures, csv, datetime, gzip, hashlib
import importlib.util, json, re, threading, time, unicodedata, html
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/max-liebermann-20261011'
DATA = Path.home() / 'Library/Application Support/Artline/source-metadata/million-catalogue-20261010'
_sessions = threading.local()

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def save(name, data):
    p = RUN / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def capture(url):
    key = hashlib.sha256(url.encode()).hexdigest()
    dest = RUN / 'captures' / (key + '.json')
    body = dest.with_suffix('.body.gz')
    if dest.exists():
        rc = json.loads(dest.read_text())
        raw = gzip.decompress(body.read_bytes())
        assert hashlib.sha256(raw).hexdigest() == rc['sha256']
    else:
        host = urlsplit(url).hostname
        hold = RUN / 'access-holds' / (host + '.json')
        if hold.exists():
            raise RuntimeError('Source access hold: ' + host)
        if not hasattr(_sessions, 'session'):
            _sessions.session = requests.Session()
        r = _sessions.session.get(url, headers={'User-Agent': 'Artline research: Max Liebermann metadata inventory'}, timeout=(20, 60))
        raw = r.content
        rc = dict(url=url, final_url=r.url, status=r.status_code, retrieved_at=now(),
                  sha256=hashlib.sha256(raw).hexdigest(), content_type=r.headers.get('Content-Type'),
                  body_path=str(body.relative_to(ROOT)))
        save(str(dest.relative_to(RUN)), rc)
        body.write_bytes(gzip.compress(raw, mtime=0))
        if r.status_code in (401, 403, 429):
            save(str(hold.relative_to(RUN)), rc)
    if rc['status'] != 200:
        raise RuntimeError(str(rc['status']) + ': ' + url)
    return raw, rc

def getjson(url):
    raw, rc = capture(url)
    return json.loads(raw), rc

def norm(value):
    return ' '.join(re.sub(r'[^\w]+', ' ', unicodedata.normalize('NFKD', html.unescape(value or '')).casefold()).split())

def wikiart():
    spec = importlib.util.spec_from_file_location('wikiart_parser', ROOT / 'ops/research-production-wikiart-images-20261006.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    base = 'https://www.wikiart.org/en/max-liebermann'
    raw, rc = capture(base + '/all-works/text-list')
    soup = BeautifulSoup(raw, 'html.parser')
    links = {urljoin(base, a['href']): a.get_text(' ', strip=True) for a in soup.select('li a[href]') if a['href'].startswith('/en/max-liebermann/')}
    meta, mrc = getjson('https://www.wikiart.org/en/App/Painting/PaintingsByArtist?artistUrl=max-liebermann&json=2')
    save('wikiart-index.json', dict(links=links, metadata=meta, receipt=rc, metadata_receipt=mrc))
    def one(pair):
        url, title = pair
        try:
            raw, receipt = capture(url)
            p = module.page_metadata(raw, receipt)
            assert p['metadata']['artistUrl'] == '/en/max-liebermann'
            assert norm(title) == norm(p['metadata']['title'])
            time.sleep(.25)
            return dict(source='WikiArt', source_id=p['metadata']['_id'], source_url=url, title=html.unescape(p['metadata']['title']),
                        date=p['metadata'].get('year'), medium=p['fields'].get('Media'), dimensions=p['fields'].get('Dimensions'),
                        collection_label=p['fields'].get('Location'), image_url=p['image_url'], rights_label=p['rights_label'],
                        creator='Max Liebermann', page=p, receipt=receipt)
        except Exception as e:
            return dict(source='WikiArt', source_url=url, title=title, error=str(e))
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        for x in ex.map(one, links.items()):
            rows.append(x)
            if len(rows)%10==0: print('WikiArt', len(rows), '/',len(links),flush=True)
    save('wikiart-records.json',rows)
    print('WikiArt records',len(rows),'errors',sum('error'in r for r in rows),flush=True)

def local_museums():
    # Reuse previously captured official open-data files; never query the local DB.
    out=[]
    met=DATA/'met/MetObjects.csv'
    with met.open(newline='',encoding='utf-8-sig')as f:
        for r in csv.DictReader(f):
            if 'Max Liebermann' not in r['Artist Display Name'].split('|'): continue
            out.append(dict(source='The Metropolitan Museum of Art', source_id=r['Object ID'],
                source_url='https://www.metmuseum.org/art/collection/search/'+r['Object ID'],
                title=r['Title'],date=r['Object Date'],medium=r['Medium'],dimensions=r['Dimensions'],accession=r['Object Number'],
                work_type=r['Classification'],object_name=r['Object Name'],creator=r['Artist Display Name'],raw=r))
    with (DATA/'nga/constituents.csv').open(newline='',encoding='utf-8-sig')as f:
        people={r['constituentid']:r for r in csv.DictReader(f)if r['forwarddisplayname']=='Max Liebermann'}
    assert len(people)==1
    links=collections.defaultdict(list)
    with (DATA/'nga/objects_constituents.csv').open(newline='',encoding='utf-8-sig')as f:
        for r in csv.DictReader(f):
            if r['constituentid']in people: links[r['objectid']].append(r)
    with (DATA/'nga/objects.csv').open(newline='',encoding='utf-8-sig')as f:
        for r in csv.DictReader(f):
            if r['objectid']not in links:continue
            out.append(dict(source='National Gallery of Art',source_id=r['objectid'],source_url='https://www.nga.gov/collection/art-object-page.'+r['objectid']+'.html',
                title=r['title'],date=r['displaydate'],medium=r['medium'],dimensions=r['dimensions'],accession=r['accessionnum'],
                work_type=r['classification'],creator='Max Liebermann',creator_roles=links[r['objectid']],raw=r))
    save('us-open-data-records.json',out)
    save('us-open-data-evidence.json',{'checked_at':now(),'files':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'receipt_path':str(ROOT/'docs/research/million-catalogue-20261010/sources'/str(p.relative_to(DATA)))+'.receipt.json'}for p in [met,DATA/'nga/objects.csv',DATA/'nga/objects_constituents.csv',DATA/'nga/constituents.csv']]})
    print('US open data',dict(collections.Counter(r['source']for r in out)),flush=True)

def us_apis():
    rows=[]
    # Creator restriction is checked on returned records; a name in a title is insufficient.
    d,rc=getjson('https://api.artic.edu/api/v1/artworks/search?q=Max%20Liebermann&limit=100&fields=id,title,artist_title,artist_id,date_display,date_start,date_end,medium_display,dimensions,main_reference_number,image_id,is_public_domain,artwork_type_title,api_link')
    for r in d['data']:
        if r.get('artist_title')!='Max Liebermann':continue
        rows.append(dict(source='Art Institute of Chicago',source_id=str(r['id']),source_url='https://www.artic.edu/artworks/'+str(r['id']),title=r['title'],date=r['date_display'],medium=r['medium_display'],dimensions=r['dimensions'],accession=r['main_reference_number'],work_type=r['artwork_type_title'],creator=r['artist_title'],raw=r,receipt=rc))
    save('aic-search.json',dict(data=d,receipt=rc))
    d,rc=getjson('https://openaccess-api.clevelandart.org/api/artworks/?artists=Max%20Liebermann&limit=1000')
    for r in d['data']:
        if not any(c.get('description','').startswith('Max Liebermann (')for c in r.get('creators',[])):continue
        rows.append(dict(source='The Cleveland Museum of Art',source_id=str(r['id']),source_url=r['url'],title=r['title'],date=r['creation_date'],medium=r['technique'],dimensions=r.get('measurements'),accession=r['accession_number'],work_type=r['type'],creator='Max Liebermann',raw=r,receipt=rc))
    save('cleveland-search.json',dict(data=d,receipt=rc));save('us-api-records.json',rows)
    print('US APIs',dict(collections.Counter(r['source']for r in rows)),flush=True)

def wikidata():
    query='''SELECT ?item ?itemLabel ?date ?collection ?collectionLabel ?inventory ?image ?url WHERE {
      ?item wdt:P170 wd:Q158062. OPTIONAL {?item wdt:P571 ?date.} OPTIONAL {?item wdt:P195 ?collection.}
      OPTIONAL {?item wdt:P217 ?inventory.} OPTIONAL {?item wdt:P18 ?image.} OPTIONAL {?item wdt:P973 ?url.}
      SERVICE wikibase:label {bd:serviceParam wikibase:language "en,de".}}
      ORDER BY ?item LIMIT 10000'''
    url=requests.Request('GET','https://query.wikidata.org/sparql',params={'query':query,'format':'json'}).prepare().url
    d,rc=getjson(url);bindings=d['results']['bindings'];assert len(bindings)<10000
    grouped=collections.defaultdict(list)
    for x in bindings:grouped[x['item']['value']].append({k:v['value']for k,v in x.items()})
    rows=[]
    for url,vs in grouped.items():
        vals=lambda k:sorted({v[k]for v in vs if k in v})
        rows.append(dict(source='Wikidata',source_id=url.rsplit('/',1)[-1],source_url=url,title=vals('itemLabel')[0],dates=vals('date'),collections=vals('collectionLabel'),collection_ids=vals('collection'),collection_map={v['collection']:v.get('collectionLabel')for v in vs if'collection'in v},accessions=vals('inventory'),image_urls=vals('image'),described_at=vals('url'),creator='Max Liebermann',receipt=rc))
    save('wikidata-records.json',rows);print('Wikidata objects',len(rows),flush=True)

def wikidata_details():
    rows=json.loads((RUN/'wikidata-records.json').read_text())
    entities={};receipts=[]
    for start in range(0,len(rows),50):
        ids='|'.join(r['source_id']for r in rows[start:start+50])
        url=requests.Request('GET','https://www.wikidata.org/w/api.php',params={'action':'wbgetentities','ids':ids,'props':'claims|labels|aliases','languages':'en|de|fr|ru','format':'json'}).prepare().url
        data,rc=getjson(url);entities.update(data['entities']);receipts.append(rc)
        print('Wikidata detailed objects',len(entities),flush=True)
    save('wikidata-details.json',dict(entities=entities,receipts=receipts))

def rijks():
    import xml.etree.ElementTree as ET
    sp=importlib.util.spec_from_file_location('rijks_parser',ROOT/'ops/million-rijks-20261010.py');a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
    files=Path('/tmp/artline-liebermann-20261011/rijks-matching-files.txt').read_text().splitlines()
    rows=[];other=[];seen=set();receipts=[]
    for file in files:
        p=Path(file);rcpath=ROOT/'docs/research/million-catalogue-20261010/sources'/(str(p.relative_to(DATA))+'.receipt.json')
        rc=json.loads(rcpath.read_text());assert hashlib.sha256(p.read_bytes()).hexdigest()==rc['sha256'];receipts.append(rc)
        for node in ET.parse(p).findall('.//o:record',a.NS):
            cho=node.find('.//e:ProvidedCHO',a.NS)
            if cho is None:continue
            agents={c.get(a.ABOUT):a.literal(c,'s:prefLabel')for c in node.findall('.//e:Agent',a.NS)}
            creators=[agents.get(c.get(a.RESOURCE),'')for c in cho.findall('d:creator',a.NS)]
            if 'Max Liebermann'not in creators:continue
            oid=a.literal(node,'o:header/o:identifier').rsplit('/',1)[-1]
            if oid in seen:continue
            seen.add(oid)
            concepts={c.get(a.ABOUT):a.literal(c,'s:prefLabel')for c in node.findall('.//s:Concept',a.NS)}
            types=[concepts.get(c.get(a.RESOURCE),'')for c in cho.findall('d:type',a.NS)]
            agg=node.find('.//ore:Aggregation',a.NS);shown=agg.find('e:isShownAt',a.NS)if agg is not None else None
            url=shown.get(a.RESOURCE)if shown is not None else cho.get(a.ABOUT)
            parents=[c.get(a.RESOURCE)for c in cho.findall('t:isPartOf',a.NS)]
            row=dict(source='Rijksmuseum',source_id=oid,source_url=url,title=a.literal(cho,'d:title'),date=a.literal(cho,'t:created'),accession=a.literal(cho,'d:identifier'),dimensions=a.literal(cho,'t:extent'),medium='; '.join(concepts.get(c.get(a.RESOURCE),'')for c in cho.findall('t:medium',a.NS)),types=types,creator='; '.join(creators),parents=parents,receipt=rc,source_xml=ET.tostring(node,encoding='unicode'))
            if any(t in a.TYPE for t in types):rows.append(row)
            else:other.append(row)
    save('rijks-records.json',rows);save('rijks-non-art-and-unit-review.json',other)
    save('rijks-coverage.json',dict(researched_files=len(files),receipts=receipts,art_records=len(rows),other_records=len(other),scope='Creator-scoped search of all locally captured Rijksmuseum OAI pages; this is a source snapshot, not a claim that the entire museum feed was harvested.'))
    print('Rijks artwork records',len(rows),'other material',len(other),flush=True)

def html_object(source,url):
    raw,rc=capture(url);s=BeautifulSoup(raw,'html.parser');fields={}
    def txt(css):
        el=s.select_one(css);return el.get_text(' ',strip=True)if el else None
    row=dict(source=source,source_url=url,receipt=rc)
    if source=='Hamburger Kunsthalle':
        for el in s.select('p.hkos-object__sidebar-content > span'):
            value=el.get_text(' ',strip=True)
            fields.setdefault('sidebar',[]).append(value)
        title=txt('.hkos-object__title');assert title
        accession=next((v.removeprefix('Inv. Nr.:').strip()for v in fields.get('sidebar',[])if v.startswith('Inv. Nr.:')),None)
        row.update(source_id=urlsplit(url).path.split('/')[3],title=title,creator=txt('.hkos-object__artists'),
                   accession=accession,medium=(fields.get('sidebar')or[None])[0],title_includes_source_date=True,
                   image_urls=[urljoin(url,x['src'])for x in s.select('.hkos-object--preview-image-container img[src]')],
                   verso_title=txt('.hkos-object__title-verso'))
    elif source=='Städel Museum':
        for dl in s.select('dl.dsProperty'):
            k=dl.select_one('dt');v=dl.select_one('dd')
            if k and v:fields[k.get_text(' ',strip=True)]=v.get_text(' ',strip=True)
        row.update(source_id=fields.get('Inventory Number'),title=txt('.dsArtwork__titleCaption'),
                   date=(txt('.dsArtwork__titleYear')or'').lstrip(', '),creator=fields.get('Painter')or fields.get('Draughtsman')or fields.get('Etcher')or fields.get('Lithographer'),
                   accession=fields.get('Inventory Number'),medium=fields.get('Physical Description'),dimensions=fields.get('Dimensions'),work_type=fields.get('Object Type'))
        if not row['creator']:
            row['creator']='Max Liebermann' if s.select_one('a[href$="/person/liebermann-max"]')else None
    elif source=='ALBERTINA':
        for el in s.select('.detailField'):
            k=el.select_one('.detailFieldLabel');v=el.select_one('.detailFieldValue')
            if k and v:fields[k.get_text(' ',strip=True)]=v.get_text(' ',strip=True)
        row.update(source_id=urlsplit(url).path.split('/')[2],title=txt('#shortinfo h1'),creator=txt('#shortinfo h2'),date=txt('#shortinfo h3'),accession=fields.get('Object number'),medium=fields.get('Materials / Techniques'),dimensions=fields.get('Dimensions'),work_type=fields.get('Object type'),image_urls=[urljoin(url,x['src'])for x in s.select('#mediaZone img[src]')])
    elif source=='Buchheim Museum':
        row.update(source_id=urlsplit(url).path.rsplit('/',1)[-1],title=txt('h1'),creator='Max Liebermann'if s.select_one('a[href$="/kuenstler/liebermann-max"]')else None)
    row['fields']=fields
    # Capture original prose as research evidence, never republish it as Artline copy.
    row['page_text']=s.get_text(' ',strip=True)
    assert row.get('title')and row.get('creator'),('Missing object identity',url)
    return row

def european_museums(provider):
    source={'hamburg':'Hamburger Kunsthalle','staedel':'Städel Museum','albertina':'ALBERTINA','buchheim':'Buchheim Museum'}[provider]
    links={};pages=[]
    if provider=='hamburg':
        url='https://online-sammlung.hamburger-kunsthalle.de/de/suche?filter%5Bfacet_obj_artistName%5D%5B0%5D=Max%20Liebermann'
        seen=set()
        while url and url not in seen:
            seen.add(url);raw,rc=capture(url);s=BeautifulSoup(raw,'html.parser');pages.append(rc)
            for el in s.select('.object-teaser'):
                a=el.select_one('a[href*="/objekt/"]');title=el.select_one('.object-teaser__subtitle');creator=el.select_one('.object-teaser__title')
                if a:
                    clean=urljoin(url,a['href']).split('?')[0];links[clean]=dict(title=title.get_text(' ',strip=True)if title else None,creator=creator.get_text(' ',strip=True)if creator else None)
            nxt=s.select_one('.pager__item--next a[href]');url=urljoin(url,nxt['href'])if nxt else None
            print('Hamburg index',len(pages),'pages',len(links),'records',flush=True)
            assert len(pages)<100
    elif provider=='albertina':
        for url in ['https://sammlungenonline.albertina.at/people/18384/max-liebermann/objects','https://sammlungenonline.albertina.at/people/18384/max-liebermann/objects/images?page=2']:
            raw,rc=capture(url);s=BeautifulSoup(raw,'html.parser');pages.append(rc)
            for a in s.select('a[href^="/objects/"]'):
                clean=urljoin(url,a['href']).split('?')[0];links[clean]={}
        assert len(links)==32
    elif provider=='staedel':
        url='https://sammlung.staedelmuseum.de/en/person/liebermann-max';raw,rc=capture(url);s=BeautifulSoup(raw,'html.parser');pages.append(rc)
        for a in s.select('a[href*="/en/work/"]'):
            im=a.select_one('img[alt]')
            if im and im['alt'].endswith(', Max Liebermann'):links[a['href']]={}
        assert len(links)==27
    else:
        url='https://sammlung.buchheimmuseum.de/kuenstler/liebermann-max';raw,rc=capture(url);s=BeautifulSoup(raw,'html.parser');pages.append(rc)
        for a in s.select('a[href*="/werk/"]'):
            clean=urljoin(url,a['href']).split('?')[0]
            if re.search(r'/werk/[^/]+$',clean)and 'Max Liebermann'in a.get_text(' ',strip=True):links[clean]={}
    save(provider+'-index.json',dict(source=source,links=links,receipts=pages))
    def one(url):
        try:
            x=html_object(source,url);time.sleep(.2);return x
        except Exception as e:return dict(source=source,source_url=url,index=links[url],error=str(e))
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2)as ex:
        for row in ex.map(one,links):
            rows.append(row)
            if len(rows)%25==0:print(provider,'objects',len(rows),'/',len(links),flush=True)
    save(provider+'-records.json',rows);print(provider,'objects',len(rows),'errors',sum('error'in x for x in rows),flush=True)

def nuxt_data(raw, predicate):
    s=BeautifulSoup(raw,'html.parser');data=json.loads(s.select_one('#__NUXT_DATA__').string)
    def resolve(i):
        if i<0:return None
        x=data[i]
        if isinstance(x,dict):return {k:resolve(v)for k,v in x.items()}
        if isinstance(x,list):
            if x and isinstance(x[0],str):return resolve(x[1])if len(x)>1 else []
            return [resolve(v)for v in x]
        return x
    found=[i for i,x in enumerate(data)if isinstance(x,dict)and predicate(x)]
    assert len(found)==1,found
    return resolve(found[0])

def berlin():
    rows=[];receipts=[]
    for page in range(1,4):
        url='https://search.smb.museum/?involved=Max+Liebermann&limit=100'+('&page='+str(page)if page>1 else'')
        raw,rc=capture(url);d=nuxt_data(raw,lambda x:'artworks'in x and'total'in x);assert d['total']==279 and d['limit']==100
        rows.extend(d['artworks']);receipts.append(rc)
    assert len(rows)==len({r['id']for r in rows})==279
    save('berlin-index.json',dict(rows=rows,receipts=receipts))
    def one(r):
        url='https://search.smb.museum/object/'+r['id']
        try:
            raw,rc=capture(url);d=nuxt_data(raw,lambda x:'ident'in x and'actors'in x);assert d['id']==r['id']
            time.sleep(.2)
            return dict(source='Staatliche Museen zu Berlin',source_id=d['id'],source_url=url,permalink=d['permalink'],title=d['title'],date='; '.join(x['nameLine']for x in d.get('dating',[])),accession=d['ident'],creator='; '.join(x['nameLine']+'; '+x.get('role','')for x in d.get('actors',[])),creator_roles=d.get('actors',[]),medium=d.get('material_desc'),dimensions='; '.join(x['nameLine']for x in d.get('dimensions',[])),work_type=d.get('term'),collection=d['org_unit'],raw={k:v for k,v in d.items()if k!='additionalItems'},receipt=rc)
        except Exception as e:return dict(source='Staatliche Museen zu Berlin',source_url=url,index=r,error=str(e))
    result=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2)as ex:
        for row in ex.map(one,rows):
            result.append(row)
            if len(result)%25==0:print('Berlin objects',len(result),flush=True)
    save('berlin-records.json',result);print('Berlin total',len(result),'errors',sum('error'in x for x in result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['wikiart','local_museums','us_apis','wikidata','wikidata_details','rijks','hamburg','staedel','albertina','buchheim','berlin']);a=p.parse_args()
    european_museums(a.action)if a.action in ['hamburg','staedel','albertina','buchheim']else globals()[a.action]()
