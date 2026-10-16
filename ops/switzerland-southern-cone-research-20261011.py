#!/usr/bin/env python3
"""Resumable official-directory research; no database writes or image downloads."""
import argparse
import collections
import concurrent.futures
import csv
import fcntl
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

spec = importlib.util.spec_from_file_location('source_base', Path(__file__).with_name('cesi-top100-20261010.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
OP = 'switzerland-southern-cone-museums-20261011'
RUN = b.ROOT / 'docs/research' / OP
b.RUN = RUN
SWISS = b.ROOT / 'docs/research/switzerland-india-museums-20261011'
UY = 'https://www.museos.gub.uy/index.php/component/k2/itemlist/category/1'
PY = 'https://agendarte.cultura.gov.py/categorias/museos'
_capture = b.capture


def locked_capture(url, params=None):
    """Serialize each URL across processes so receipt/body pairs stay consistent."""
    request_url=b.requests.Request('GET',url,params=params).prepare().url
    folder=Path('/tmp/artline-switzerland-southern-cone-capture-locks')
    folder.mkdir(parents=True,exist_ok=True)
    with (folder/b.sha(request_url.encode())).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        return _capture(url,params)


b.capture=locked_capture


def page(url):
    raw, receipt = b.capture(url)
    assert receipt['status'] == 200, f"HTTP {receipt['status']}: {url}"
    return BeautifulSoup(raw, 'html.parser'), receipt


def text(node):
    return node.get_text(' ', strip=True) if node else ''


def directory(country):
    if country == 'AR':
        return rmi(country)
    start = {'UY': UY, 'PY': PY}[country]
    pending, seen, rows = [start], set(), {}
    receipts = []
    while pending:
        url = pending.pop(0)
        if url in seen:
            continue
        seen.add(url)
        assert len(seen) < 100, 'Unexpected pagination; inspect before continuing'
        soup, receipt = page(url)
        receipts.append(receipt)
        selector = '.catItemView' if country == 'UY' else '.w-dyn-item'
        for item in soup.select(selector):
            a = item.select_one('.catItemTitle a' if country == 'UY' else 'a.events_item')
            if not a:
                continue
            detail = urljoin(url, a['href'])
            if country == 'UY':
                key = re.search(r'/item/(\d+)-', detail).group(1)
                fields = {}
                native = []
                for field in item.select('.catItemExtraFields li'):
                    label = text(field.select_one('.catItemExtraFieldsLabel'))
                    value = field.select_one('.catItemExtraFieldsValue')
                    fields[label] = text(value)
                    if label == 'Sitio Web' and value:
                        native = [urljoin(url, link['href']) for link in value.select('a[href]')]
                name = text(a)
                locality = text(item.select_one('.catItemCategory a'))
                classification = 'official museum-directory institution lead'
            else:
                key = detail.rsplit('/', 1)[-1]
                name = text(item.select_one('.heading-style-h4'))
                locality = text(item.select_one('.evento_item:not(.fecha)'))
                fields = {'description': text(item.select_one('.text-style-3lines')),
                          'dates': text(item.select_one('.fecha'))}
                native = []
                classification = ('dated cultural-event lead; institution identity needs separate reconciliation'
                                  if re.match(r'Homenaje|Visita |Taller|Exposici[oó]n|Celebraci[oó]n|Concierto|D[ií]a ', name, re.I)
                                  else 'official cultural-portal museum lead; individual identity review required')
            row = dict(directory_id=key, name=name, country=country, locality=locality,
                       directory_url=detail, native_websites=native, fields=fields,
                       classification=classification, evidence=receipt,
                       object_coverage='individual object evidence pending')
            if key in rows:
                assert rows[key]['name'] == name
            else:
                rows[key] = row
        for a in soup.select('a[href]'):
            href = urljoin(url, a['href']).split('#')[0]
            if ((country == 'UY' and href.startswith(UY + '?start=')) or
                    (country == 'PY' and href.startswith(PY + '?4f879e15_page='))):
                if href not in seen and href not in pending:
                    pending.append(href)
        print(json.dumps(dict(country=country, pages=len(seen), entries=len(rows))), flush=True)
    b.save(RUN/country/'directory.json.gz', dict(country=country, sources=receipts, records=list(rows.values()),
           scope='Exhausted linked pagination for this source; not proof that the source lists every museum'))
    ledger(country)


def rmi(country):
    """Read the public registry's own country filter and pagination endpoints."""
    country_name = {'AR': 'Argentina', 'UY': 'Uruguay', 'PY': 'Paraguay'}[country]
    raw, tree_receipt = b.capture('https://www.rmiberoamericanos.org/Busqueda/GetJsTree3Data')
    tree = json.loads(raw)
    country_id = next(x['id'] for x in tree if x['text'] == country_name)
    rows, receipts, expected = {}, [tree_receipt], None
    for number in range(1, 201):
        url = ('https://www.rmiberoamericanos.org/Busqueda/IndexFilterTree?'
               f'searchString=&searchStringTree={country_id}&page={number}')
        soup, receipt = page(url)
        total = int(soup.select_one('#hdNumRegistros')['value'])
        if expected is None:
            expected = total
        assert total == expected, 'Registry changed during pagination'
        receipts.append(receipt)
        for card in soup.select('.ficha'):
            key = card.select_one('.ficha__link[id]')['id'].split('_')[1]
            assert key not in rows, 'Repeated registry page'
            fields = {}
            for strong in card.select('strong'):
                label = text(strong.parent).removesuffix(text(strong)).strip().rstrip(':')
                fields[label] = text(strong)
            assert fields['País'] == country_name
            rows[key] = dict(directory_id=key, name=text(card.select_one('h2 a')),
                             country=country, locality=fields.get('Ciudad'), fields=fields,
                             directory_url='https://www.rmiberoamericanos.org/Busqueda/DetalleByID?id='+key,
                             native_websites=[], evidence=receipt,
                             classification='Ibermuseos institution lead; country-endorsed registry',
                             object_coverage='individual object evidence pending')
        print(json.dumps(dict(country=country, source='Ibermuseos', page=number,
                              entries=len(rows), source_total=expected)), flush=True)
        if len(rows) == expected:
            break
    assert len(rows) == expected
    dest = RUN/country/('directory.json.gz' if country == 'AR' else 'ibermuseos-directory.json.gz')
    b.save(dest, dict(country=country, sources=receipts, records=list(rows.values()),
                     scope='All records returned by this registry country filter; not proof of every museum nationwide'))
    if country == 'AR':
        ledger(country)


def icom(country):
    assert country == 'PY'
    url='https://www.icomparaguay.org/directorio-virtual-museos-del-paraguay-2024'
    soup,receipt=page(url)
    records=[]
    for a in soup.select('a[href]'):
        if '/directorio-virtual-museos-del-paraguay-2024/' not in a['href']:
            continue
        card=a.parent.parent
        title=card.select_one('.wixui-rich-text')
        assert title
        records.append(dict(directory_id='icom-'+b.sha(a['href'].encode())[:16],name=text(title),country='PY',locality=None,
                            directory_url=a['href'],native_websites=[],evidence=receipt,
                            classification='ICOM Paraguay cultural-institution directory lead; includes archives, libraries and cultural centres',
                            object_coverage='individual object evidence pending'))
    assert len({x['directory_url'] for x in records})==len(records)>100
    b.save(RUN/'PY/icom-directory.json.gz',dict(records=records,sources=[receipt],scope='All 108 linked entries in the 2024 ICOM directory; broader than museums, with institution reconciliation pending.'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for number,_ in enumerate(pool.map(detail,records),1):
            if number%20==0:print('ICOM Paraguay profiles',number,flush=True)


def detail(row):
    target = RUN/row['country']/'directory-details'/(row['directory_id']+'.json.gz')
    if target.exists():
        return b.load(target)
    try:
        soup, receipt = page(row['directory_url'])
        main = soup.select_one('.itemView') or soup.find('main') or soup
        for node in main.select('script,style,noscript,header,footer'):
            node.decompose()
        links = [dict(label=text(a), url=urljoin(receipt['final_url'], a['href'])) for a in main.select('a[href]')]
        external = [x for x in links if urlsplit(x['url']).scheme in ['http', 'https'] and
                    urlsplit(x['url']).hostname != urlsplit(row['directory_url']).hostname and
                    not re.search(r'facebook|twitter|instagram|whatsapp|youtube|gtranslate|linkedin|google', x['url'], re.I)]
        result = dict(directory_id=row['directory_id'], name=row['name'], evidence=receipt,
                      source_text=text(main), external_links=external,
                      result='directory description checked; individual object evidence pending')
    except Exception as error:
        result = dict(directory_id=row['directory_id'], name=row['name'], result='directory source gap',
                      error=type(error).__name__ + ': ' + str(error)[:400])
    b.save(target, result)
    return result


def details(country):
    rows = b.load(RUN/country/'directory.json.gz')['records']
    counts = collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for n, result in enumerate(pool.map(detail, rows), 1):
            counts[result['result']] += 1
            if n % 20 == 0:
                print(json.dumps(dict(country=country, checked=n, results=dict(counts))), flush=True)
    print(json.dumps(dict(country=country, checked=len(rows), results=dict(counts))), flush=True)
    ledger(country)


def native(country, supplemental=False, reviewed=False):
    """Check directory-linked sites once; retain unavailable and ambiguous leads."""
    rows = b.load(RUN/country/'directory.json.gz')['records'] if not supplemental else []
    if supplemental:
        for filename in ['ibermuseos-directory.json.gz','icom-directory.json.gz']:
            path=RUN/country/filename
            if path.exists():
                rows.extend(dict(x,directory_id=('rmi-'+x['directory_id']) if filename.startswith('ibermuseos') else x['directory_id']) for x in b.load(path)['records'])
    def one(row):
        dest = RUN/country/('native-reviewed' if reviewed else 'native-sites')/(row['directory_id']+'.json.gz')
        if dest.exists():
            return b.load(dest)
        profile = b.load(RUN/country/'directory-details'/(row['directory_id']+'.json.gz'))
        candidates = list(dict.fromkeys(u.strip() for u in row.get('native_websites', []) +
                          [x['url'] for x in profile.get('external_links', [])]))
        candidates = [u for u in candidates if urlsplit(u).scheme in ['http','https'] and
                      not re.search(r'facebook|twitter|instagram|youtube|pinterest|linkedin|whatsapp|google|gobiernoelectronico|innova|localhost|127\.0\.0|fondec\.gov\.py', u, re.I)]
        out = dict(directory_id=row['directory_id'], name=row['name'], candidates=candidates,
                   result='No individual native website supplied; object-source research gap')
        if len(candidates)>3:
            out['result']='Multiple external destinations; native website identity needs review'
        elif candidates:
            try:
                soup, receipt = page(candidates[0])
                links = [dict(label=text(a), url=urljoin(receipt['final_url'],a['href'])) for a in soup.select('a[href]')
                         if re.search(r'colec|acervo|patrimonio|collection|obras|catalog|muse',text(a)+' '+a['href'],re.I)]
                for node in soup.select('script,style,noscript,nav,header,footer'):
                    node.decompose()
                out.update(result='Directory-linked native site checked; individual collection-object review pending',
                           evidence=receipt, source_text=text(soup)[:22000], collection_links=links[:80])
            except Exception as error:
                out.update(result='Native-site access or availability gap', error=type(error).__name__+': '+str(error)[:400])
        b.save(dest,out)
        return out
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for number, out in enumerate(pool.map(one,rows),1):
            counts[out['result']]+=1
            if number%25==0:
                print(json.dumps(dict(country=country,native_checked=number,results=dict(counts))),flush=True)
    b.save(RUN/country/('native-reviewed-summary.json' if reviewed else 'native-supplement-summary.json' if supplemental else 'native-summary.json'),dict(entries=len(rows),results=dict(counts)))
    if not supplemental:ledger(country)


def native_supplements(country):
    native(country,True)


def native_reviewed(country):
    native(country,True,True)


def collection_discovery(country):
    """Bounded metadata discovery; collection links alone never become objects."""
    sites={p.name:b.load(p) for p in sorted((RUN/country/'native-sites').glob('*.json.gz'))}
    reviews={p.name:b.load(p) for p in sorted((RUN/country/'native-reviewed').glob('*.json.gz'))}
    sites.update(reviews)
    sites=list(sites.values())
    def one(site):
        dest=RUN/country/('collection-reviewed' if reviews else 'collection-discovery')/(site['directory_id']+'.json.gz')
        if dest.exists():return b.load(dest)
        candidates=[]
        host=urlsplit(site.get('evidence',{}).get('final_url','')).netloc
        for link in site.get('collection_links',[]):
            url=link['url'].split('#')[0]
            if urlsplit(url).netloc!=host or not re.search(r'colecci|acervo|collection|obras|catalog',link['label']+' '+url,re.I):continue
            if re.search(r'\.pdf(?:\?|$)|mailto:',url,re.I):continue
            if url not in candidates:candidates.append(url)
        checked=[]
        for url in candidates[:2]:
            try:
                soup,receipt=page(url)
                for node in soup.select('script,style,noscript,nav,header,footer'):node.decompose()
                checked.append(dict(url=url,evidence=receipt,text=text(soup)[:32000],
                                    links=[dict(label=text(a),url=urljoin(url,a['href'])) for a in soup.select('a[href]')][:160],
                                    status='Collection metadata checked; object identity/date/holding and image clearance remain required'))
            except Exception as error:
                checked.append(dict(url=url,status='Collection source access/availability gap',error=str(error)[:300]))
        out=dict(directory_id=site['directory_id'],name=site['name'],pages=checked,candidate_links=candidates,
                 result='collection pages checked' if checked else 'No usable native collection link; object-source gap')
        b.save(dest,out);return out
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for number,out in enumerate(pool.map(one,sites),1):
            counts[out['result']]+=1
            if number%50==0:print(country,'collection discovery',number,dict(counts),flush=True)
    b.save(RUN/country/('collection-reviewed-summary.json' if reviews else 'collection-discovery-summary.json'),dict(sites=len(sites),results=dict(counts)))


def ledger(country):
    source = SWISS if country == 'CH' else RUN
    rows = b.load(source/country/'directory.json.gz')['records']
    institutions = b.load(RUN/'production-institutions-baseline.json.gz')
    output = []
    for row in rows:
        f = source/country/'directory-details'/(row['directory_id']+'.json.gz')
        detail = b.load(f) if f.exists() else {}
        n = source/country/'native-sites'/(row['directory_id']+'.json.gz')
        native = b.load(n) if n.exists() else {}
        websites = row.get('native_websites', [])
        candidates = [i for i in institutions if b.norm(i['name']) == b.norm(row['name']) or
                      (i.get('website_url') and i['website_url'].rstrip('/') in [u.rstrip('/') for u in websites])]
        output.append(dict(directory_id=row['directory_id'], name=row['name'], locality=row.get('locality'),
                           source_country_scope=country, directory_url=row['directory_url'],
                           classification=row.get('classification', row.get('primary_category')),
                           directory_status=detail.get('result', 'indexed; directory detail pending'),
                           native_status=native.get('result', 'native-site collection review pending'),
                           native_websites=' | '.join(websites),
                           catalogue_identity_candidates=' | '.join(i['id'] for i in candidates),
                           object_coverage='reconcile delivery receipts; unresolved objects remain research gaps'))
    dest = RUN/country/'directory-coverage.csv'
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    print(json.dumps(dict(country=country, ledger_entries=len(output))), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['directory', 'details', 'ledger', 'rmi', 'native', 'native_supplements', 'native_reviewed', 'collection_discovery', 'icom'])
    parser.add_argument('country', choices=['CH', 'AR', 'UY', 'PY'])
    args = parser.parse_args()
    globals()[args.action](args.country)
