#!/usr/bin/env python3
"""Two selected paintings: museum-produced book corroborated by museum sources."""
import importlib.util
import uuid
from pathlib import Path

s = importlib.util.spec_from_file_location('p', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r


def main():
    index = p.Index()
    book = r.load(r.RUN / 'moma-kandinsky-compositions-receipt-20261005c.json')['receipt']
    assert book['status'] == 200
    institution = {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/museum/kunstsammlung-nordrhein-westfalen')),
                   'slug': 'kunstsammlung-nordrhein-westfalen', 'name': 'Kunstsammlung Nordrhein-Westfalen',
                   'normalized_name': 'kunstsammlung nordrhein westfalen', 'kind': 'museum', 'status': 'review',
                   'website_url': 'https://www.kunstsammlung.de/', 'wikidata_id': None,
                   'description': 'Institution identified by its official collection catalogue, corroborated by the Museum of Modern Art publication Kandinsky: Compositions (1995). Holding does not assert a currently accessible display venue.'}
    jobs = [
        ('338a28fa-4712-5db6-8f6d-8f06fff7efa3', 'Composition IV', '1911', institution,
         'kunstsammlung-nrw-object', '64', 'https://sammlung.kunstsammlung.de/en/works/64',
         'curated-publications-followup-20261005c', ['Komposition IV, 1911', 'Wassily Kandinsky', '159,5 x 250,5', '1013', '1965'], 115, 112, '31',
         'The English title and dimensions in MoMA catalogue entry 31 identify the German-titled current museum object, inventory 1013, acquired in 1965.'),
        ('0775f226-79ae-53b8-94c5-3633c11e90f6', 'Composition VI', '1913', index.institution('wikimedia-museum-q132783'),
         'google-arts-museum-object', 'kgExsxhp7qzWsA', 'https://artsandculture.google.com/asset/kandinsky-v-composition-vi-1913-hermitage-kandinsky-v/kgExsxhp7qzWsA',
         'kandinsky-book-followup-20261005c', ['Композиция VI. Государственный Эрмитаж', 'Wassily Kandinsky', '1913'], 116, 113, '47',
         'MoMA catalogue entry 47 identifies Composition VI, 1913, 195 x 300 cm, as Hermitage. The Tretyakov Gallery contributes the Google Arts record, but its artwork title explicitly credits the State Hermitage; the contributing museum is not treated as the holder.'),
    ]
    claims = []
    for aid, title, date, museum, scheme, oid, url, folder, tokens, pdf_page, page, number, basis in jobs:
        row = index.by_id[aid]
        assert row['artwork']['title'] == title and row['artwork']['date_display'] == date
        assert [a['name'] for a in row['artists']] == ['Wassily Kandinsky']
        captured = r.load(r.RUN / folder / ('parsed-' + r.sha(url.encode()) + '.json.gz'))
        assert captured['source_receipt']['status'] == 200 and all(t in captured['text'] for t in tokens)
        evidence = {'reviewed_source_tokens': tokens, 'manual_identity_resolution': basis,
                    'museum_publication': {'title': 'Kandinsky: Compositions', 'author': 'Magdalena Dabrowski',
                                          'publisher': 'The Museum of Modern Art, New York', 'year': 1995,
                                          'catalogue_entry': number, 'printed_page': page, 'pdf_page': pdf_page,
                                          'source_receipt': book, 'page_visually_checked': True},
                    'current_display_not_inferred': True}
        c = p.claim(row, scheme, oid, museum, captured['source_receipt'], url, evidence, basis)
        if number == '47':
            extra_url = 'https://www.wassilykandinsky.net/work-35.php'
            extra = r.load(r.RUN / 'kandinsky-book-followup-20261005c' / ('parsed-' + r.sha(extra_url.encode()) + '.json.gz'))
            assert all(t in extra['text'] for t in ['Composition VI', '1913', '195.0', '300.0', 'Hermitage Museum'])
            evidence['independent_secondary_corroboration_receipt'] = extra['source_receipt']
            c['source_class'] = 'museum_contributed_catalogue_and_museum_publication'
        else:
            c['duplicate_source_urls'] = ['https://sammlung.kunstsammlung.de/de/werke/64']
        claims.append(c)
    p.output('kandinsky-books-20261005c', claims, [])


if __name__ == '__main__':
    main()
