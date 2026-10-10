"""Capture selected originals and bounded historical comparators, not the full archive."""
import importlib.util
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

spec = importlib.util.spec_from_file_location('t', Path(__file__).with_name('museum-expansion-theocharakis-source-20261010.py'))
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
m, RUN, q = t.m, t.RUN, t.q


def main():
    index = m.load(RUN / 'bounded-index-001.json.gz')
    cards = [c for page in index['pages'] for c in page['cards']]
    selected = []
    excluded = []
    for card in cards:
        if card['source_id'] == 'theocharakis/000163-111578':
            excluded.append(dict(card, decision='exclude_photographic_documentation_of_another_artwork'))
        else:
            selected.append(dict(card, role='historical_comparator' if card['historical_source_match'] else 'candidate'))
    # The 18th historical object lies outside this bounded index; it remains a comparator.
    old = m.load(RUN / 'source-discovery-001.json.gz')['historical_records']
    seen = {c['source_id'] for c in selected}
    for v in old:
        if v['source_id'] not in seen:
            selected.append(dict(source_id=v['source_id'], url=v['source_url'], title=v['title'],
                                 historical_source_match=True, role='historical_comparator'))
    assert len(selected) == 180
    assert sum(v['role'] == 'candidate' for v in selected) == 162
    m.save(RUN / 'object-selection-001.json', dict(at=m.now(), rows=selected, excluded=excluded,
        index_reference=q.s.ref(RUN / 'bounded-index-001.json.gz'),
        rationale='162 selected original drawing/study candidates with documented collection connection, plus all 18 previously delivered object comparators. One photograph of another artwork excluded before detail download. Unknown dates stay unknown; page identifiers are not museum accessions. No full archive download.'))
    output = []
    for number, v in enumerate(selected, 1):
        sid = v['source_id'].rsplit('-', 1)[1]
        soup, receipt = q.q.capture('selected-' + sid + '-001', v['url'])
        fields, enrichment = q.fields(soup)
        assert fields.get('Τίτλος') and fields.get('Πάροχος') and fields.get('Δημιουργός')
        links = sorted({urljoin(v['url'], a['href']) for a in soup.select('a[href]')
                        if re.search(r'exhibition\.thfdigital\.gr/projects/\d+', a['href'])})
        assert len(links) == 1, (sid, links)
        img = soup.find('img', src=lambda u: u and '/thumbnails/edm-record/' + v['source_id'] in u)
        rights = sorted({a['href'] for a in soup.select('a[href]') if 'creativecommons.org/licenses/' in a['href']})
        output.append(dict(number=number, source_id=v['source_id'], source_url=v['url'], role=v['role'],
                           index=v, fields=fields, enrichment=enrichment, native_url=links[0], receipt=receipt,
                           thumbnail_url=urljoin(v['url'], img['src']) if img else None, rights_links=rights))
        if number % 20 == 0 or number == len(selected):
            print(json.dumps(dict(captured=number, total=len(selected))), flush=True)
        time.sleep(.08)
    m.save(RUN / 'selected-source-records-001.json.gz', dict(at=m.now(), rows=output,
        selection_reference=q.s.ref(RUN / 'object-selection-001.json'), script_reference=q.s.ref(Path(__file__).resolve()),
        policy='Literal source fields and EKT enrichments stored separately. No images or database writes. Selected unknown dates need editorial review, and same-sheet/recto-verso identity is not proven by different page IDs.'))


if __name__ == '__main__':
    main()
