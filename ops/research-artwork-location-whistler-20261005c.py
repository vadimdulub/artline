#!/usr/bin/env python3
"""Reconcile selected works with Glasgow's published Whistler catalogue raisonne."""
import collections
import gzip
import importlib.util
import re
from pathlib import Path
from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('p', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r


def datekey(text):
    return p.datekey(re.sub(r'(?<=\d)/(?=\d)', '-', text or '').removeprefix('Unverified date: '))


def main():
    index = p.Index()
    museums = {i['slug']: i for i in index.institutions}
    for v in r.load(r.RUN / 'glasgow-kunstsammlung-institution-check-20261005c.json'):
        museums[v['v']['slug']] = v['v']
    authority = r.load(r.RUN / 'smithsonian-freer-authority-20261005c.json')
    assert authority['receipt']['status'] == 200
    assert 'National Museum of Asian Art' in authority['text'] and 'Freer Gallery of Art' in authority['text']
    groups = collections.defaultdict(dict)
    for path in ['whistler-painting-candidates-20261005c.json.gz', 'whistler-paper-candidates-20261005c.json.gz']:
        for v in r.load(r.RUN / path):
            for hit in v['hits']:
                groups[v['row']['artwork']['id']][hit['url']] = hit
    claims, holds = [], []
    for aid, hits in groups.items():
        row = index.by_id[aid]
        # Repeated titles are not disambiguated from an unverified museum label.
        if len(hits) != 1:
            holds.append({'artwork_id': aid, 'reason': 'repeated_title_requires_inventory', 'source_urls': list(hits)})
            continue
        hit = next(iter(hits.values()))
        oid = hit['url'].rsplit('=', 1)[-1]
        captured = r.load(r.RUN / 'whistler-full-entries-20261005c' / ('parsed-' + oid + '.json.gz'))
        raw = gzip.decompress((r.ROOT / captured['source_receipt']['body_path']).read_bytes())
        sp = BeautifulSoup(raw, 'html.parser')
        fields = {}
        for node in sp.select('span.meta'):
            label = node.select_one('span.tag')
            if label:
                fields[label.get_text(strip=True).rstrip(':')] = node.get_text(' ', strip=True).removeprefix(label.get_text(strip=True)).strip()
        title = sp.h2.get_text('|', strip=True).split('|')[-1]
        if p.titlekey(title) != p.titlekey(row['artwork']['title']) or fields.get('Artist') != 'James McNeill Whistler':
            holds.append({'artwork_id': aid, 'reason': 'current_title_or_attribution_requires_review', 'source_url': hit['url'], 'source_receipt': captured['source_receipt']})
            continue
        collection = ' '.join(fields.get('Collection', '').split())
        slug = {'Freer Gallery of Art, Washington, DC': 'smithsonian-national-museum-of-asian-art',
                'The Hunterian, University of Glasgow': 'museum-authority-q1465387',
                'National Gallery of Art, Washington, DC': 'national-gallery-of-art',
                'Cincinnati Art Museum, OH': 'wikimedia-museum-q2970522',
                'Art Institute of Chicago': 'art-institute-of-chicago'}.get(collection)
        if not slug:
            holds.append({'artwork_id': aid, 'reason': 'collection_not_reconciled', 'collection': collection, 'source_url': hit['url'], 'source_receipt': captured['source_receipt']})
            continue
        local_dates = [c[2] for c in row['supplied'] or []] or [row['artwork'].get('date_display', '')]
        flags = []
        if datekey(fields.get('Date')) not in {datekey(v) for v in local_dates}:
            flags.append('catalogue_date_differs')
        accession = row['artwork'].get('accession_number')
        if accession and p.acckey(accession) != p.acckey(fields.get('Accession Number')):
            flags.append('inventory_conflict')
        evidence = {'catalogue_number': oid, 'current_entry_fields': fields, 'title_index_receipt': hit['receipt'],
                    'qualifications': flags, 'publication': 'University of Glasgow, The Paintings of James McNeill Whistler, online catalogue raisonne; incorporates and updates the 1980 paintings and 1995 drawings/pastels/watercolours catalogues.',
                    'complete_provenance_and_bibliography_in_source_capture': True}
        if slug == 'smithsonian-national-museum-of-asian-art':
            evidence['institution_name_authority_receipt'] = authority['receipt']
        c = p.claim(row, 'whistler-catalogue', oid, museums[slug], captured['source_receipt'], hit['url'], evidence,
                    'Unique catalogue title across paintings and paper indexes; exact named artist and creation date checked; current catalogue collection and inventory recorded')
        c['source_class'] = 'university_scholarly_catalogue_raisonne'
        if flags:
            c['review_state'] = 'review'
            c['limitation'] = 'Museum candidate from scholarly catalogue retained in review: ' + ', '.join(flags) + '. Original date and publication status preserved; no current display asserted.'
        claims.append(c)
    p.output('whistler-20261005c', claims, holds)
    print('States', collections.Counter(c.get('review_state', 'accepted') for c in claims))


if __name__ == '__main__':
    main()
