#!/usr/bin/env python3
"""Two Kandinsky object records and the museum's own institutional identity."""
import importlib.util
from pathlib import Path
from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('primary', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
t = importlib.util.spec_from_file_location('delivery', Path(__file__).with_name('apply-artwork-locations-20261004.py'))
d = importlib.util.module_from_spec(t)
t.loader.exec_module(d)
r = p.r


def text(raw):
    soup = BeautifulSoup(raw, 'html.parser')
    for node in soup.select('script,style,nav,footer'):
        node.decompose()
    return ' '.join(soup.get_text(' ', strip=True).split())


def main():
    index = p.Index()
    name = 'Städtische Galerie im Lenbachhaus und Kunstbau München'
    raw, authority = r.capture('https://www.lenbachhaus.de/museum/ueber-uns', tag='lenbach-20261005', timeout=40)
    assert authority['status'] == 200 and name + ' ist ein Kunstmuseum' in text(raw)
    inst = {'id': d.uid('institution/lenbachhaus-munich'), 'slug': 'lenbachhaus-munich', 'name': name, 'normalized_name': r.norm(name), 'website_url': 'https://www.lenbachhaus.de/', 'wikidata_id': None, 'kind': 'museum', 'status': 'review', 'description': 'Municipal art museum in Munich. Identity and official website verified from the museum’s own About page; authority record retained in review.'}
    for target in ['local', 'production']:
        with r.connect(target) as db:
            existing = db.execute("SELECT id FROM institutions WHERE normalized_name=%s OR name ILIKE '%%lenbach%%' OR website_url ILIKE '%%lenbach%%'", (inst['normalized_name'],)).fetchall()
            assert not existing, 'Existing Lenbachhaus authority needs reconciliation'
    jobs = [
        ('d4265b60-3ab3-560e-ac33-24ef9c73cf03', 'farbstudie-quadrate-mit-konzentrischen-ringen-30017624', 'GMS 446', ['Farbstudie – Quadrate mit konzentrischen Ringen', 'Wassily Kandinsky', '1913', '23,9 cm x 31,5 cm', 'Schenkung 1957'], 'accepted', 'Distinctive Color Study: Squares with Concentric Circles/Farbstudie – Quadrate mit konzentrischen Ringen title translation, creator and circa-1913 date agree. Museum explicitly credits the collection and donation; inventory GMS 446 distinguishes the object. Source lists a work on paper; existing type and dates are preserved.'),
        ('692bd42a-4c65-51e5-bab5-8b845c18d2cb', 'parties-diverses-30030997', 'AK 16', ['Parties diverses', 'Wassily Kandinsky', '1940', '89,5 cm x 116,4 cm', 'Dauerleihgabe'], 'review', 'Various Parts/Parties diverses title translation, creator and 1940 agree. Supplied dimensions round and reverse the museum’s 89.5 x 116.4 cm. Source explicitly identifies a permanent loan from the Gabriele Münter and Johannes Eichner Foundation; retain qualified custody in review.'),
    ]
    claims = []
    for aid, slug, inventory, tokens, state, basis in jobs:
        lead = r.load(r.RUN / 'wikiart-leads' / (aid + '.json'))
        assert lead['title'] == index.by_id[aid]['artwork']['title'] and lead['source_artist'] == 'Wassily Kandinsky'
        url = 'https://www.lenbachhaus.de/digital/sammlung-online/detail/' + slug
        raw, receipt = r.capture(url, tag='lenbach-20261005', timeout=40)
        page = text(raw)
        assert receipt['status'] == 200 and all(v in page for v in tokens + [inventory, 'Ausgestellt Nein'])
        claim = p.claim(index.by_id[aid], 'lenbachhaus-inventory', inventory, inst, receipt, url, {'reviewed_tokens': tokens, 'museum_authority_receipt': authority, 'secondary_identity_lead': lead, 'manual_identity_review': basis, 'explicit_display_text': 'Ausgestellt: Nein'}, basis)
        claim['review_state'] = state
        claim['limitation'] += ' ' + basis + ' Official page explicitly marks the object not exhibited; no positive display claim is made.'
        claims.append(claim)
    p.output('lenbach-20261005', claims, [])


if __name__ == '__main__':
    main()
