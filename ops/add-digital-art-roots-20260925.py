#!/usr/bin/env python3
"""Two documented visual roots of computer art; paintings, never relabelled digital.

Public-domain Commons reproductions, primary museum identity and primary
influence evidence. Bounded local review import using the shared pinned workflow.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
from bs4 import BeautifulSoup

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('core', Path(__file__).with_name('add-islamic-world-images-20260925.py'))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
core.CAMPAIGN = 'digital-art-roots-20260925'
core.SOURCE_LABEL = 'Visual roots of computer art'
core.RUN = core.ROOT / 'docs/research' / core.CAMPAIGN
core.BACKUP = core.DATA / 'backups' / core.CAMPAIGN
core.ORIGINALS = core.DATA / 'source-images' / core.CAMPAIGN
core.COUNTRIES = {}
POLICY = 'https://commons.wikimedia.org/wiki/Commons:Reuse_of_PD-Art_photographs'
core.PROVIDERS = {'commons': {'name': 'Wikimedia Commons', 'api': 'https://commons.wikimedia.org/',
    'policy': POLICY, 'source_type': 'collection_page'}}


def plan():
    indexed = core.load('captures/primary-index.json')
    mondrian = core.load('captures/mondrian-index.json')
    assert 'ML 76/3253' in indexed['result'] and '1916-1917' in mondrian['result']
    _, policy = core.fetch(POLICY, core.RUN / 'captures/commons-policy.html')
    ludwig = {'id': core.uid('institution/ludwig'), 'slug': 'museum-ludwig', 'name': 'Museum Ludwig',
        'normalized_name': core.norm('Museum Ludwig'), 'kind': 'museum', 'status': 'review'}
    with core.connect() as db:
        artists = db.execute("SELECT to_jsonb(a) record FROM artists a WHERE slug=ANY(%s) ORDER BY slug",
            (['paul-klee-q44007', 'piet-mondrian-q151803'],)).fetchall()
        assert len(artists) == 2 and all(a['record']['death_year'] < 1956 for a in artists)
        klee, piet = [a['record']['id'] for a in artists]
        km = db.execute("SELECT id::text FROM institutions WHERE slug='kroller-muller-museum'").fetchone()['id']
        candidates = [
            ('klee', 'Highway and Byways', 1929, 1929, '1929', 'ML 76/3253', ludwig['id'], klee,
             'https://www.kulturelles-erbe-koeln.de/documents/obj/05010396', 'Oil on canvas', '83.5 × 67.5 cm',
             'Paul Klee; reproduction by Marendo Müller', 'nake-inspiration.html',
             'Painting used by Frieder Nake as the basis of his 1965 Hommage à Paul Klee.'),
            ('mondrian', 'Composition in line, second state', 1916, 1917, '1916–1917', 'KM 106.482', km, piet,
             'https://krollermuller.nl/media/expositionpage/exhibition_texts_the_patron_and_the_house_painter.pdf',
             'Oil on canvas', '108 × 108 cm', 'Piet Mondrian; reproduction from catalogue.pietmondrian.nl',
             'noll-inspiration.html', 'Painting that inspired A. Michael Noll’s Computer Composition with Lines.')]
        records = []
        for key, title, lo, hi, date, accession, institution, artist, url, medium, dimensions, credit, influence, reason in candidates:
            raw = (core.RUN / f'captures/{key}-commons.html').read_bytes()
            receipt = core.load(f'captures/{key}-commons.html.receipt.json')
            assert core.sha(raw) == receipt['sha256']
            html = BeautifulSoup(raw, 'html.parser')
            assert 'faithful photographic reproduction of a two-dimensional' in html.get_text(' ', strip=True)
            assert 'public domain' in html.get_text(' ', strip=True)
            image = html.select_one('.fullImageLink a')['href'].split('?')[0]
            assert image.startswith('https://upload.wikimedia.org/wikipedia/commons/')
            c = {'key': key, 'provider': 'commons', 'object_id': accession, 'accession': accession,
                'title': title, 'lo': lo, 'hi': hi, 'date_display': date, 'precision': 'exact' if lo == hi else 'range',
                'type': 'painting', 'country': None, 'culture': None, 'place_display': None, 'maker': None,
                'artist_id': artist, 'institution_id': institution, 'url': url, 'image_page_url': receipt['url'],
                'image_url': image, 'medium': medium, 'dimensions': dimensions, 'credit': credit, 'reason': reason,
                'capture': receipt, 'rights_status': 'public_domain', 'license_label': 'Public domain (PD-Art)',
                'license_url': 'https://creativecommons.org/publicdomain/mark/1.0/',
                'rights_basis': 'Faithful two-dimensional reproduction, Commons PD-Art designation. Named painter died over 70 years ago; work publicly exhibited before 1931. Commons reproduction is distinct from restricted museum photography.',
                'view_label': 'Public-domain reproduction', 'scope_note': 'Earlier painting directly documented as inspiration for computer art. Original dates and artist identity retained. Not a computer-made artwork.',
                'holding_note': 'Museum source preserved as indexed text because the direct endpoint returned a challenge or redesigned site; no fresh display assertion.',
                'object': {'title': title, 'museum_identity_evidence': indexed if key == 'klee' else mondrian,
                    'image_page_receipt': receipt, 'influence_source': core.load('captures/'+influence+'.receipt.json')},
                'artwork_id': core.uid(key), 'slug': 'digital-roots-'+key}
            assert not core.duplicate(db, c), 'Exact accession or source already exists'
            records.append(c)
    core.save(core.RUN/'plan.json', {'records': records, 'policies': {'commons': policy},
        'institutions_to_create': [ludwig], 'artist_preimages': artists, 'country_preimages': [],
        'selection_bound': 'Exactly two historically documented precursor paintings, selected before image downloading. No new artist biographies or modern country origin assertions.'})
    core.save(core.RUN/'plan-pin.json', {'sha256': core.sha((core.RUN/'plan.json').read_bytes())})
    print('Pinned two precursor paintings; public-domain images, original dates, existing artists.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['plan', 'prepare', 'backup', 'apply', 'verify'])
    phase = parser.parse_args().phase
    (globals().get(phase) or getattr(core, phase))()
