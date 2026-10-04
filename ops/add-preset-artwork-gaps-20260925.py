#!/usr/bin/env python3
"""Selected Met objects for early cities, classical art, Buddhism and the Sahel.

Uses pinned metadata, complete-frame image preparation and an atomic backed-up
local review import. Does not invent modern origins for ancient objects.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('core', Path(__file__).with_name('add-islamic-world-images-20260925.py'))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
PREVIOUS = core.RUN
core.CAMPAIGN = 'preset-artwork-gaps-20260925'
core.SOURCE_LABEL = 'Selected artworks for timeline presets'
core.RUN = core.ROOT / 'docs/research' / core.CAMPAIGN
core.BACKUP = core.DATA / 'backups' / core.CAMPAIGN
core.ORIGINALS = core.DATA / 'source-images' / core.CAMPAIGN
core.PROVIDERS = {'met': core.PROVIDERS['met']}
core.COUNTRIES = {'EG': ('Egypt', 'northern-africa'), 'ML': ('Mali', 'western-africa'),
    'PK': ('Pakistan', 'southern-asia'), 'CN': ('China', 'eastern-asia')}
# Unknown modern origins and unclassified museum object types remain unknown.
# Greek/Roman cultural labels are not converted into modern manufacture claims.
SELECTION = {
    329081: ('writing', None, 'unknown', 'Proto-cuneiform writing with narrative seal impressions'),
    327067: ('writing', None, 'unknown', 'Engraved cylinder seal and its explicitly modern impression'),
    544227: ('writing', 'EG', 'sculpture', 'Middle Kingdom faience hippopotamus with painted plant motifs'),
    253422: ('classical', None, 'ceramic', 'Attic Geometric vase painting and funerary culture'),
    247238: ('classical', None, 'ceramic', 'Archaic black-figure vase painting with warriors arming'),
    247993: ('classical', None, 'sculpture', 'Roman imperial portraiture of Augustus'),
    38452: ('buddhism', 'PK', 'sculpture', 'Gandharan narrative relief of the death of the Buddha'),
    38474: ('buddhism', 'PK', 'sculpture', 'Gandharan representation of Maitreya, Buddha of the future'),
    42162: ('buddhism', 'CN', 'sculpture', 'Dated Northern Wei Maitreya altarpiece'),
    314362: ('sahel', 'ML', 'sculpture', 'Middle Niger terracotta figure from the era of Sahelian cities'),
    317989: ('sahel', 'ML', 'ceramic', 'Hand-modelled Middle Niger vessel'),
    310384: ('sahel', 'ML', 'ceramic', 'Tellem pottery connected to regional trade and cultural exchange'),
}


def plan():
    records = []
    for oid, (preset, country, kind, reason) in SELECTION.items():
        o = core.load(f'captures/met-{oid}.json')
        receipt = core.load(f'captures/met-{oid}.json.receipt.json')
        assert core.sha((core.RUN / f'captures/met-{oid}.json').read_bytes()) == receipt['sha256']
        assert o['objectID'] == oid and o['isPublicDomain'] is True and not o['rightsAndReproduction']
        assert o['primaryImage'].startswith('https://images.metmuseum.org/CRDImages/')
        assert o['objectURL'] == 'https://www.metmuseum.org/art/collection/search/' + str(oid)
        lo, hi = o['objectBeginDate'], o['objectEndDate']
        assert type(lo) is int and type(hi) is int and -4000 <= lo <= hi <= 1700
        if country:
            assert core.COUNTRIES[country][0] in (o['country'] + ' ' + o['culture'])
        else:
            assert not o['country']
        maker = ' '.join(v.strip() for v in [o['artistPrefix'], o['artistDisplayName']] if v.strip()) or None
        assert maker in (None, 'Attributed to the Workshop of New York MMA 34.11.2', 'Attributed to the Amasis Painter', 'Middle Niger artist', 'Middle Niger artist(s)', 'Tellem artist'), maker
        place = ', '.join(v for v in [o['country'], o['region'], o['subregion'], o['city']] if v) or o['culture']
        if o['geographyType']:
            place = o['geographyType'] + ' ' + place
        date = o['objectDate']
        precision = ('circa' if lo == hi else 'circa_range') if date.startswith('ca.') else ('exact' if lo == hi else 'range')
        records.append({'key': 'met-'+str(oid), 'provider': 'met', 'object_id': str(oid), 'accession': o['accessionNumber'],
            'preset': preset, 'title': o['title'], 'lo': lo, 'hi': hi, 'date_display': date, 'precision': precision,
            'type': kind, 'country': country, 'culture': o['culture'], 'place_display': place, 'maker': maker,
            'url': o['objectURL'], 'image_url': o['primaryImage'], 'medium': o['medium'], 'dimensions': o['dimensions'],
            'credit': o['creditLine'], 'reason': reason, 'object': o, 'capture': receipt,
            'geography_note': 'Modern country retained only where explicitly supplied by the museum in country or geographic culture. Ancient cultural labels and uncertain origins remain verbatim; no creator nationality inferred.'})
    previous_ids = []
    for campaign in ['islamic-world-images-20260925', 'islamic-world-more-20260925', 'arab-world-images-20260925']:
        previous_ids += [c['artwork_id'] for c in json.loads((core.ROOT / 'docs/research' / campaign / 'plan.json').read_text())['records']]
    with core.connect() as db:
        institutions = {'met': db.execute("SELECT to_jsonb(i) record FROM institutions i WHERE slug='the-met' AND status<>'archived'").fetchone()['record']}
        countries = db.execute('SELECT to_jsonb(c) record FROM countries c WHERE code=ANY(%s) ORDER BY code', (list(core.COUNTRIES),)).fetchall()
        places = {}
        for code, (name, _) in core.COUNTRIES.items():
            matches = db.execute('SELECT to_jsonb(p) record FROM places p WHERE country_code=%s AND name=%s', (code, name)).fetchall()
            assert len(matches) <= 1
            if matches: places[code] = matches[0]['record']
        old = db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id', (previous_ids,)).fetchall()
        assert len(old) == 44
        for c in records:
            c['institution_id'] = institutions['met']['id']
            assert not core.duplicate(db, c), 'Existing accession: ' + c['key']
            c['artwork_id'], c['slug'] = core.uid(c['key']), 'preset-' + c['key']
    previous = json.loads((PREVIOUS / 'plan.json').read_text())
    raw = (PREVIOUS / 'captures/met-policy-web.json').read_bytes()
    assert core.sha(raw) == previous['policies']['met']['sha256']
    core.save(core.RUN / 'captures/met-policy-web.json', raw)
    core.save(core.RUN / 'plan.json', {'records': records, 'policies': {'met': previous['policies']['met']}, 'institutions': institutions,
        'country_preimages': countries, 'places': places, 'previous_artwork_preimages': old,
        'selection_bound': 'Twelve individually selected official Met objects; no collection crawl. Unknown country/type preserved. Museum attribution qualifiers and collective creator labels remain object-level labels.'})
    core.save(core.RUN / 'plan-pin.json', {'sha256': core.sha((core.RUN / 'plan.json').read_bytes())})
    print('Pinned twelve objects for four missing artwork categories.')


def verify():
    core.verify()
    p = core.pinned()
    with core.connect() as db:
        ids = [r['record']['id'] for r in p['previous_artwork_preimages']]
        assert db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id', (ids,)).fetchall() == p['previous_artwork_preimages']
    print('Previous 44 objects unchanged.')


def apply():
    core.apply()
    verify()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['plan', 'prepare', 'backup', 'apply', 'verify'])
    phase = parser.parse_args().phase
    (globals().get(phase) or getattr(core, phase))()
