"""Use ordinary observed collection search after the separate facet service failed."""
import importlib.util
import json
from pathlib import Path
from urllib.parse import urlencode, urljoin
spec = importlib.util.spec_from_file_location('src', Path(__file__).with_name('museum-expansion-nhm-source-20261010.py'))
src = importlib.util.module_from_spec(spec)
spec.loader.exec_module(src)
c, m, RUN = src.c, src.m, src.RUN

def main():
    assert not (RUN / 'source-selection-discovery-001.json').exists()
    failed = m.load(RUN / 'captures/facets-001.json')
    assert failed['status'] == 500
    previous = next(x for x in m.load(c.DISCOVERY)['rows'] if x['institution_id'] == c.IID)
    form = previous['forms'][0]
    assert form['action'] == '/aggregator/portal/collections/EIM/search' and form['method'] == 'GET'
    native, nr = src.capture('native-collections-001', 'https://www.nhmuseum.gr/tmimata/sylloges')
    links = [dict(title=src.clean(a.get_text(' ',strip=True)), url=urljoin(nr['final_url'], a['href'])) for a in native.select('a[href]') if a.get_text(' ',strip=True)]
    doc, receipt = src.capture('date-index-001', src.BASE + form['action'] + '?' + urlencode(dict(resultsMode='GRID', sortResults='YEAR_ASC', language='en', **{'page.page':1})))
    cards = src.index(doc)
    assert len(cards) == 30
    inputs = [dict(name=x.get('name'), type=x.get('type'), value=x.get('value')) for x in doc.select('input[name]')]
    selects = [dict(name=x.get('name'), options=[dict(value=o.get('value'), label=src.clean(o.get_text(' ',strip=True))) for o in x.select('option')]) for x in doc.select('select[name]')]
    m.save(RUN / 'source-selection-discovery-001.json', dict(at=m.now(), collection_reference=previous['receipt'], form=form, facet_failure_reference=c.ref(RUN / 'captures/facets-001.json'), facets=[], first_date_page=dict(receipt=receipt, cards=cards), inputs=inputs, selects=selects, native_receipt=nr, native_text=src.clean(native.get_text(' ',strip=True)), native_links=links, source_total=4727, policy='Facet-only endpoint returned500 and was not retried. Separate ordinary public date-sort search and native collection descriptions used, not an alternate mechanism for the failed endpoint. No object/image capture.', script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(cards=cards, selects=selects, native_text=src.clean(native.get_text(' ',strip=True))[:18000], native_links=[x for x in links if '/sylloges/' in x['url']]),ensure_ascii=False),flush=True)

if __name__ == '__main__':
    main()
