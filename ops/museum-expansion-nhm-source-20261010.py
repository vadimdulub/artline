"""Observe NHM public collection facets and native collection description."""
import gzip
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
spec = importlib.util.spec_from_file_location('c', Path(__file__).with_name('museum-expansion-nhm-common-20261010.py'))
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
m, RUN = c.m, c.RUN
CAP = RUN / 'captures'
BASE = 'https://www.searchculture.gr'
q = c.module('q', 'museum-expansion-kazantzakis-selection-20261009.py')
clean = q.clean

def capture(key, url):
    CAP.mkdir(parents=True, exist_ok=True)
    rp, bp = CAP / (key + '.json'), CAP / (key + '.body.gz')
    if rp.exists():
        rc = m.load(rp)
        raw = gzip.decompress(bp.read_bytes())
        assert rc['url'] == url and hashlib.sha256(raw).hexdigest() == rc['sha256'] and rc['status'] == 200
    else:
        response = requests.get(url, timeout=(15, 45))
        raw = response.content
        bp.write_bytes(gzip.compress(raw))
        rc = dict(url=url, final_url=response.url, status=response.status_code, retrieved_at=m.now(), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), content_type=response.headers.get('Content-Type'), body_path=str(bp.relative_to(m.ROOT)))
        m.save(rp, rc)
        response.raise_for_status()
    return BeautifulSoup(raw.decode('utf-8'), 'html.parser'), rc

def index(doc):
    out = []
    for el in doc.select('.edm-entity-result'):
        pairs = [(a, urljoin(BASE, a['href'])) for a in el.select('a[href]') if '/aggregator/edm/' in a['href'] and a.get_text(' ', strip=True)]
        if not pairs:
            continue
        a, url = pairs[0]
        text = clean(el.get_text(' ', strip=True))
        date = re.search(r' Date (.*?) Item type ', text)
        kind = re.search(r' Item type (.*?) (?:Creator|Institution|Place) ', text)
        out.append(dict(url=url, source_id=url.split('/aggregator/edm/')[1], title=clean(a.get_text(' ', strip=True)), text=text, index_date=date[1] if date else None, index_type=kind[1] if kind else None))
    assert len({x['source_id'] for x in out}) == len(out)
    return out

def main():
    assert not (RUN / 'source-selection-discovery-001.json').exists()
    src = next(x for x in m.load(c.DISCOVERY)['rows'] if x['institution_id'] == c.IID)
    raw = gzip.decompress((m.ROOT / src['receipt']['body_path']).read_bytes()).decode('utf-8')
    assert hashlib.sha256(raw.encode()).hexdigest() == src['receipt']['sha256']
    form = src['forms'][0]
    assert form['action'] == '/aggregator/portal/collections/EIM/search' and form['method'] == 'GET'
    assert "var collectionShortName = 'EIM'" in raw and "+ '/onlyFacetPanel?language=' + lang" in raw
    facets, fr = capture('facets-001', BASE + '/aggregator/portal/collections/EIM/onlyFacetPanel?language=en')
    controls = []
    for span in facets.select('span.labels'):
        node = span.parent.parent
        check = node.select_one('input[type=checkbox]')
        if check:
            value = facets.find('input', attrs={'name':check['name'].replace('.checked', '.value')})
            controls.append(dict(label=clean(span.get_text(' ',strip=True)), text=clean(node.get_text(' ',strip=True)), control=check['name'], value=value.get('value') if value else None))
    native, nr = capture('native-collections-001', 'https://www.nhmuseum.gr/tmimata/sylloges')
    native_links = [dict(title=clean(a.get_text(' ',strip=True)), url=urljoin(nr['final_url'], a['href'])) for a in native.select('a[href]') if a.get_text(' ',strip=True)]
    m.save(RUN / 'source-selection-discovery-001.json', dict(at=m.now(), collection_reference=src['receipt'], form=form, facet_receipt=fr, facets=controls, native_receipt=nr, native_text=clean(native.get_text(' ',strip=True)), native_links=native_links, source_total=4727, policy='Observed public type/date filters and native collection descriptions only. Mixed historical collection count is not eligible artwork count. No object or image capture.', script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(facets=controls, native_text=clean(native.get_text(' ',strip=True))[:18000]),ensure_ascii=False),flush=True)

if __name__ == '__main__':
    main()
