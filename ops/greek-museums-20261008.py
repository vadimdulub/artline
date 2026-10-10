#!/usr/bin/env python3
"""Source-backed Greek museum coverage and selected production delivery.

The local catalogue is read-only. Directory coverage is not artwork coverage.
Never treat digitisation dates, collection ranges or artist lives as work dates.
"""
import argparse, collections, concurrent.futures, gzip, hashlib, html, importlib.util, json, re, time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

spec = importlib.util.spec_from_file_location('delivery', Path(__file__).with_name('research-havre-rouen-cyprus-20261006.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
ROOT = m.ROOT
RUN = ROOT / 'docs/research/greek-museums-20261008'
BACKUP = Path.home() / 'Library/Application Support/Artline/backups' / RUN.name
ORIGINALS = Path.home() / 'Library/Application Support/Artline/source-images' / RUN.name
m.RUN, m.BACKUP = RUN, BACKUP
save, load, norm, uid, sha, now, connect = m.save, m.load, m.norm, m.uid, m.sha, m.now, m.connect
SC = 'https://www.searchculture.gr'
PORTAL = 'https://archaeologicalmuseums.culture.gov.gr'
NA = 'https://nationalarchive.culture.gr'


def clean(node):
    return ' '.join(node.get_text(' ', strip=True).split()) if node else ''


def page(url):
    raw, receipt = m.capture(url, timeout=30)
    if receipt['status'] != 200:
        raise ValueError('Source HTTP ' + str(receipt['status']) + ': ' + url)
    return BeautifulSoup(raw, 'html.parser'), receipt


def directory():
    s, receipt = page(PORTAL + '/en')
    regions = {o['value']:g['label'] for g in s.select('optgroup') for o in g.select('option[value]')}
    museums = []
    for line in str(s).splitlines():
        if '["' in line and PORTAL + '/en/museum/' in line:
            values = json.loads(line.strip().rstrip(','))
            name, lat, lon, url, key, region = values
            museums.append(dict(key=key, name=html.unescape(name), latitude=lat, longitude=lon,
                                source_url=url, region=regions[key], directory_receipt=receipt))
    assert len({x['key'] for x in museums}) == len(museums) >= 200
    save(RUN/'ministry-directory.json', museums)
    all_collections = {}
    for n in range(1, 7):
        url = SC + '/aggregator/portal/collections?language=en' + ('&page.page='+str(n) if n > 1 else '')
        soup, rc = page(url)
        for a in soup.select('a[href^="/aggregator/portal/collections/"]'):
            title = clean(a)
            if not title: continue
            key = a['href'].rsplit('/', 1)[-1]
            parent = a
            while parent.parent and len(clean(parent)) < len(title)+100:
                parent = parent.parent
            all_collections[key] = dict(key=key, title=title, description=clean(parent),
                url=SC+a['href']+'?language=en', directory_receipt=rc)
    save(RUN/'searchculture-directory.json', list(all_collections.values()))
    print('Directories:', len(museums), 'Ministry entries;', len(all_collections), 'digital collections', flush=True)


def collection(key, ordered=False):
    destination = RUN/('collections-ordered' if ordered else 'collections')/(key+'.json')
    if destination.exists(): return load(destination)
    url = SC+'/aggregator/portal/collections/'+key+('/search?language=en&sortResults=YEAR_ASC' if ordered else '?language=en')
    soup, rc = page(url)
    items = []
    for card in soup.select('.thumbnail'):
        a = card.select_one('h6 a[href*="/aggregator/edm/"]')
        if not a: continue
        fields = {}
        for dt in card.select('dt'):
            fields[clean(dt)] = clean(dt.find_next_sibling('dd'))
        items.append(dict(title=clean(a), source_url=SC+a['href']+'?language=en', fields=fields,
            image_url=urljoin(url, card.select_one('img.results')['src']) if card.select_one('img.results') else None))
    result = dict(key=key, receipt=rc, text=clean(soup), items=items,
        links=[dict(title=clean(a), url=urljoin(url, a['href'])) for a in soup.select('a[href]')])
    save(destination, result)
    return result


def collections_probe():
    keys=load(RUN/'collection-selection.json')['keys']
    def one(key):
        try:
            x=collection(key)
            print(key, len(x['items']), 'items', flush=True)
            return dict(key=key, items=len(x['items']))
        except Exception as e:
            return dict(key=key, error=str(e))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        rows=list(pool.map(one, keys))
    save(RUN/'collection-probe.json', rows)


def inspect_item(url):
    dest=RUN/'items'/(sha(url.encode())+'.json')
    if dest.exists(): return load(dest)
    soup,rc=page(url)
    result=dict(url=url,receipt=rc,text=clean(soup),
        headings=[clean(n) for n in soup.select('h1,h2,h3')],
        links=[dict(title=clean(a),url=urljoin(url,a['href']))for a in soup.select('a[href]')],
        images=[dict(src=urljoin(url,x['src']),alt=x.get('alt'))for x in soup.select('img[src]')])
    save(dest,result)
    return result


def na_search(label, limit=16):
    """The public, unauthenticated catalogue search used by the museum website."""
    path=RUN/'nationalarchive-search'/(sha(label.encode())+'.json')
    if path.exists(): return load(path)
    body=dict(language='en',sortOrder='asc',filters=dict(materials=[],types=[],creators=[],
        storeLocations=[label],providers=[],stolen=False,repatriated=False))
    url=NA+'/portal-api/exhibits/_search?limit='+str(limit)+'&offset=0'
    time.sleep(1.1)
    r=m.requests.post(url,json=body,timeout=(15,35),headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected collection metadata)'})
    r.raise_for_status()
    result=dict(url=url,request=body,status=r.status_code,response=r.json(),at=now(),sha256=sha(r.content))
    save(path,result)
    return result


def na_research():
    locations=load(RUN/'nationalarchive-search-probe.json')['response']['aggregations']['storeLocations']
    museums=[x for x in locations if x['docCount'] and any(k in x['key'] for k in ['Μουσ','Συλλογ','Μαγίστρου'])]
    output=[]
    for loc in museums:
        data=na_search(loc['key'])
        rows=data['response']['exhibits']
        for row in rows:
            assert norm(row['storeLocation']['name']['gr'])==norm(loc['key'])
        output.append(dict(location=loc,search_path=str((RUN/'nationalarchive-search'/(sha(loc['key'].encode())+'.json')).relative_to(ROOT)),items=len(rows)))
        print(loc['key'],len(rows),'source items',flush=True)
    save(RUN/'nationalarchive-museum-scope.json',output)


def sc_fields(soup):
    fields={}
    for group in soup.select('div.form-group'):
        label=group.select_one('label.control-label')
        values=group.select_one('div.col-sm-8')
        if not label or not values: continue
        # Keep the provider's statements separate from EKT semantic enrichments.
        fields[clean(label)]=[clean(v) for v in values.select('.item-control-static') if clean(v)]
    return fields


def sc_research(ordered=False):
    selected=[];held=[]
    accepted_types={'Painting','Engraving','Print','Lithography','Sketch','Drawing','Watercolour',
        'Sculpture','Relief','Ceramic ware','Vase','Figurine','Icon','Murals','Photo','Textile','Needlework','Medal','Shadow puppet'}
    prior_urls={x['index']['source_url'] for x in load(RUN/'searchculture-object-facts.json')['records']} if ordered else set()
    for path in sorted((RUN/'collections').glob('*.json')):
        col=collection(path.stem, True) if ordered else load(path);chosen=[]
        if col['key'] in ['mnam','DigLaskSeaScapes','volanakis','DigTelloglio','European_Delphi','Eforeia_Euboea','Digital_Pylia']:
            continue  # mixed custody/private collections/archive-only require separate identity review
        for item in col['items']:
            if item['source_url'] in prior_urls: continue
            types=set((item['fields'].get('Item type') or '').split(', '))
            if not types & accepted_types: continue
            if '3D model from scanning' in types: continue
            date=item['fields'].get('Date','')
            years=re.findall(r'(?<!\d)(\d{3,4})(?!\d)',date)
            if years and 'BC' not in date and max(map(int,years))>1970:
                held.append(dict(collection=col['key'],item=item,reason='after_or_crossing_cutoff'))
                continue
            if len(chosen)<(6 if ordered else 12): chosen.append(item)
        for item in chosen:
            try:
                x=inspect_item(item['source_url'])
                raw=gzip.decompress((ROOT/x['receipt']['body_path']).read_bytes())
                soup=BeautifulSoup(raw,'html.parser')
                selected.append(dict(collection=col['key'],index=item,receipt=x['receipt'],fields=sc_fields(soup),
                    original_urls=[l['url'] for l in x['links'] if l['title']=='see the original item page'],
                    download_urls=[l['url'] for l in x['links'] if l['title']=='see or download the digital file'],
                    license_links=[l for l in x['links'] if 'creativecommons.org/' in l['url'] and l['title']],
                    thumbnail=next((i['src'] for i in x['images'] if '/thumbnails/edm-record/' in i['src']),None)))
            except Exception as e:
                held.append(dict(collection=col['key'],item=item,reason='source_unavailable',error=str(e)))
        print('SC objects',col['key'],len(chosen),flush=True)
    save(RUN/('searchculture-ordered-object-facts.json' if ordered else 'searchculture-object-facts.json'),dict(records=selected,held=held))


NA_ALIASES={
 'Μουσείο Βυζαντινού Πολιτισμού Θεσσαλονίκης':'5df34af3deca5e2d79e8c154',
 'Μουσείο Βυζαντινού Πολιτισμού (Θεσσαλονίκη)':'5df34af3deca5e2d79e8c154',
 'Αρχαιολογικό Μουσείο Π.Ε. Καστοριάς,  Άργος Ορεστικό':'5df34af3deca5e2d79e8c1af',
 'Αρχαιολογικό Μουσείο Αιανής, Κοζάνη':'5df34af3deca5e2d79e8c1ac',
 'Συλλογή Εικόνων και Εκκλησιαστικών Κειμηλίων Αγίας Τριάδας, Πύργος, Θήρα':'5df34af3deca5e2d79e8c192',
 'Μουσείο Κάστρου Χλεμούτσι, Ηλεία':'5df34af3deca5e2d79e8c1ce',
 'Αρχαιολογικό Μουσείο Μεσσηνίας, Καλαμάτα':'5df34af3deca5e2d79e8c1d4',
 'Αρχαιολογική Συλλογή Απειράνθου':'5df34af3deca5e2d79e8c19e',
}


def na_kind(row):
    types='; '.join(x.get('en') or x.get('gr') or '' for x in row.get('types') or []).lower()
    materials='; '.join(x.get('en') or x.get('gr') or '' for x in row.get('materials') or []).lower()
    title=(row['title'].get('en') or row['title'].get('gr') or '').lower()
    if re.search(r'hoard|lot of|set of|group of|models|replica|reproduction',title): return None
    if re.search(r'icon|εικόνα',types): return 'painting'
    if re.search(r'painting|wall painting|τοιχογραφ',types): return 'fresco' if re.search('wall|τοιχογραφ',types) else 'painting'
    if re.search(r'engrav|etching|xylograph|lithograph|χαλκογραφ',types): return 'print'
    if re.search(r'shadow theater',types): return 'unknown'
    if re.search(r'embroider|textile|vestment|apron|shirt|scarf|towel|dress|sash|neck-opening',types): return 'textile'
    if re.search(r'statue|statuette|figurine|relief|stele|capital|panel|altar|sculpt|portrait|architrave|στήλη',types): return 'sculpture'
    if re.search(r'necklace|bracelet|earring|jewelry|pendant|currency|coin|cross|reliquary|ring|buckle|fibula|medal',types): return 'metalwork' if re.search('gold|silver|bronze|copper|iron|χρυσ|αργυρ|χαλκ|σιδηρ',materials) else 'unknown'
    if re.search(r'vase|amphora|alabastr|cup|kylix|pyxis|lekyth|oinocho|kanthar|aryball|pelik|krater|bowl|jug|pitcher|unguent|skyph|lagyna|kalath|container and vessel|kantharos|πυξ|αγγει',types):
        return 'ceramic' if re.search('clay|terracotta|ceramic|porcelain|stoneware|πηλ|πορσελ',materials) else 'unknown'
    return None


def na_details():
    names=load(RUN/'ministry-greek-names.json')['names']
    name_index={norm(v):k for k,v in names.items()}
    directory_index={x['key']:x for x in load(RUN/'ministry-directory.json')}
    facts=[];held=[];museums={}
    for scope in load(RUN/'nationalarchive-museum-scope.json'):
        loc=scope['location']['key'];key=NA_ALIASES.get(loc) or name_index.get(norm(loc))
        museum_key='ministry-'+key if key else 'na-location-'+sha(norm(loc).encode())[:12]
        museum=directory_index.get(key)
        if museum_key not in museums:
            museums[museum_key]=dict(key=museum_key,name=museum['name'] if museum else loc,
                original_name=loc,directory=museum,labels=[loc])
        else: museums[museum_key]['labels'].append(loc)
        rows=load(ROOT/scope['search_path'])['response']['exhibits']
        chosen=[r for r in rows if na_kind(r)][:6]
        for candidate in chosen:
            url=NA+'/portal-api/exhibits/'+str(candidate['recordId'])
            raw,rc=m.capture(url,timeout=30)
            if rc['status']!=200:
                held.append(dict(url=url,reason='source_unavailable'));continue
            row=json.loads(raw);assert row['recordId']==candidate['recordId']
            if norm(row['storeLocation']['name']['gr'])!=norm(loc):
                held.append(dict(url=url,reason='source_holding_changed'));continue
            first=re.match(r'^(-?\d+)-\d\d-\d\d$',row.get('start')or'')
            last=re.match(r'^(-?\d+)-\d\d-\d\d$',row.get('end')or'')
            first=int(first[1]) if first else None;last=int(last[1]) if last else None
            if first is None or last is None or first==0 or last==0:
                held.append(dict(url=url,reason='creation_date_not_explicit',record=row));continue
            if first>last or last>1970:
                held.append(dict(url=url,reason='creation_range_after_or_crossing_cutoff',record=row));continue
            if row.get('stolen') or row.get('lost'):
                held.append(dict(url=url,reason='stolen_or_lost_custody',record=row));continue
            label=lambda year:str(abs(year))+(' BCE' if year<0 else '')
            title=' '.join((row['title'].get('en')or row['title'].get('gr')or'').split())
            title_gr=' '.join((row['title'].get('gr')or'').split())
            facts.append(dict(source='nationalarchive',scheme='greek-national-archive-exhibit',source_id=str(row['recordId']),
                source_url=NA+'/exhibits/'+str(row['recordId']),receipt=rc,museum_key=museum_key,
                title=title,alternate_title=title_gr if title_gr!=title else None,
                creator_label='; '.join(x.get('en')or x.get('gr')or'' for x in row.get('creators')or[]) or None,
                first=first,last=last,precision='exact' if first==last else 'range',
                date_display=label(first) if first==last else label(first)+'–'+label(last),
                work_type=na_kind(row),medium='; '.join(x.get('en')or x.get('gr')or''for x in row.get('materials')or[])or None,
                dimensions=None,accession=None,raw=row,holding_confidence=0.98,
                holding_basis='The Greek Ministry of Culture public object catalogue explicitly identifies this museum in storeLocation. Recorded as collection holding only; storage position and display are not imported. Native inventory references retained without treating legacy registry numbers as new accessions.'))
        print('NA detail',loc,len([f for f in facts if f['museum_key']==museum_key]),flush=True)
    save(RUN/'nationalarchive-object-facts.json',dict(records=facts,held=held,museums=list(museums.values())))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['directory','collections','na-research','sc-research','sc-ordered','na-details'])
    args=p.parse_args()
    {'directory':directory,'collections':collections_probe,'na-research':na_research,'sc-research':sc_research,'sc-ordered':lambda:sc_research(True),'na-details':na_details}[args.action]()
