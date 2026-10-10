"""Bounded Papaloukas collection discovery, without database access."""
import csv
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urljoin

spec = importlib.util.spec_from_file_location('q', Path(__file__).with_name('museum-expansion-kazantzakis-selection-20261009.py'))
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)
m = q.m
RUN = m.RUN / 'native/theocharakis-20261010'
q.q.RUN = RUN
q.q.CAP = RUN / 'captures'
q.q.CAP.mkdir(parents=True, exist_ok=True)
IID = '71238d8f-08c1-5637-9f68-b89d17dd9c62'
BASE = 'https://www.searchculture.gr'


def index(soup):
    rows = []
    seen = set()
    for a in soup.select('a[href]'):
        url = urljoin(BASE, a['href'])
        if not re.fullmatch(BASE + r'/aggregator/edm/theocharakis/000163-\d+', url):
            continue
        title = q.clean(a.get_text(' ', strip=True))
        if not title or url in seen:
            continue
        seen.add(url)
        parent = a
        while parent and 'edm-entity-result' not in parent.get('class', []):
            parent = parent.parent
        assert parent is not None
        rows.append(dict(url=url, source_id=url.split('/aggregator/edm/')[1], title=title,
                         text=q.clean(parent.get_text(' ', strip=True))))
    return rows


def main():
    with (m.ROOT / 'docs/research/greek-museums-20261008/delivery.csv').open(encoding='utf-8-sig') as stream:
        historical = [r for r in csv.DictReader(stream) if r['museum_id'] == IID]
    assert len(historical) == 18
    known = {r['source_id'] for r in historical}
    rows = []
    for key, url in [('foundation-profile-001', 'https://thf.gr/en/the-foundation/'),
                     ('searchculture-collection-001', BASE + '/aggregator/portal/collections/theocharakis?language=en')]:
        soup, receipt = q.q.capture(key, url)
        rows.append(dict(key=key, receipt=receipt, text=q.clean(soup.get_text(' ', strip=True)),
                         links=[dict(title=q.clean(a.get_text(' ', strip=True)), url=urljoin(url, a['href'])) for a in soup.select('a[href]')]))
        if key.startswith('searchculture'):
            first_soup, first_receipt = soup, receipt
    m.save(RUN / 'source-discovery-001.json.gz', dict(at=m.now(), institution_id=IID, rows=rows,
        historical_records=historical, script_reference=q.s.ref(Path(__file__).resolve()),
        state='Research only. Google Cloud token refresh failed for the third consecutive continuation; independent research can proceed. Last register count 18/12 from 9 October, not refreshed. No DB reads or writes.'))
    pages = []
    allrows = []
    for page in range(1, 7):
        if page == 1:
            soup, receipt = first_soup, first_receipt
        else:
            soup, receipt = q.q.capture('index-page-' + str(page) + '-001', BASE + '/aggregator/portal/collections/theocharakis/search?page.page=' + str(page) + '&resultsMode=GRID&language=en')
        cards = index(soup)
        assert len(cards) == 30, (page, len(cards))
        assert not ({v['source_id'] for v in cards} & {v['source_id'] for v in allrows}), page
        for card in cards:
            card['historical_source_match'] = card['source_id'] in known
        pages.append(dict(page=page, receipt=receipt, cards=cards))
        allrows.extend(cards)
        print(json.dumps(dict(page=page, cards=len(cards), historical_matches=sum(c['historical_source_match'] for c in cards))), flush=True)
    m.save(RUN / 'bounded-index-001.json.gz', dict(at=m.now(), pages=pages, observed_index_total=2567,
        cards=len(allrows), historical_reference=q.s.ref(RUN / 'source-discovery-001.json.gz'),
        policy='First 180 index cards only; no collection-wide object or image download. Select individual artworks before detail capture. Physical versions, recto/verso, dates and holdings require review. Creator life dates are not object dates.'))


if __name__ == '__main__':
    main()
