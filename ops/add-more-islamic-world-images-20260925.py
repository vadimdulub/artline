#!/usr/bin/env python3
"""Second selected Islamic-world image set. Local review only, no publication.

Uses the first set's pinned-evidence, image preparation, backup, atomic import
and read-only verification workflow. Existing artworks and place records stay
unchanged. Source metadata is reused with its original retrieval timestamp.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('islamic_core', Path(__file__).with_name('add-islamic-world-images-20260925.py'))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
PREVIOUS = core.RUN
core.CAMPAIGN = 'islamic-world-more-20260925'
core.RUN = core.ROOT / 'docs/research' / core.CAMPAIGN
core.BACKUP = core.DATA / 'backups' / core.CAMPAIGN
core.ORIGINALS = core.DATA / 'source-images' / core.CAMPAIGN
core.COUNTRIES = {k: v for k, v in core.COUNTRIES.items() if k != 'ES'}
core.COUNTRIES.update({'AF': ('Afghanistan', 'southern-asia'), 'UZ': ('Uzbekistan', 'central-asia')})

# These 20 choices were individually reviewed for period, origins, materials and
# image rights. No image is fetched before the complete selection is pinned.
CLEVELAND = {
    123432: ('IR', 'manuscript_illumination', 'Book of Kings illustration: Bahram Gur and the dragon'),
    126088: ('IR', 'metalwork', 'Feline incense burner with pierced palmette ornament'),
    126239: ('IR', 'metalwork', 'Bird-shaped bronze vessel with engraved decoration'),
    124286: ('IR', 'metalwork', 'Faceted ewer with sphinxes and animated inscriptions'),
    117918: ('SY', 'ceramic', 'Carved and glazed falcon design on Syrian fritware'),
    159535: ('UZ', 'ceramic', 'Samarkand pharmacy jar with calligraphic decoration'),
    123982: ('IQ', 'metalwork', 'Silver and gold inlay with geometric and courtly decoration'),
    124429: ('SY', 'metalwork', 'Ayyubid tray with courtly scenes and astronomical motifs'),
    128073: ('IR', 'sculpture', 'Floriated Kufic lettering carved in limestone'),
    94963: ('IR', 'ceramic', 'Star-shaped luster tile with a couple and poetry'),
    114235: ('EG', 'drawing', 'Mamluk calligraphy with illuminated rosettes'),
    149945: ('AF', 'metalwork', 'Ghaznavid salver with animated Kufic inscription'),
    124426: ('IR', 'manuscript_illumination', 'Illustrations of animals, plants and musical instruments'),
    124417: ('IR', 'manuscript_illumination', 'Illustrated natural history of ringdoves and quails'),
    135809: ('IQ', 'ceramic', 'Abbasid luster painting with a banner and peacocks'),
    116672: ('SY', 'metalwork', 'Ayyubid brass incense burner with silver inlay'),
    95151: ('SY', 'ceramic', 'Glazed fritware storage jar from Raqqa'),
    95120: ('EG', 'ceramic', 'Fatimid luster decoration from Fustat'),
}
MET = {
    449137: ('IR', 'ceramic', 'Repeating pattern of turquoise hexagons and cobalt stars'),
    451802: ('IR', 'ceramic', 'Bold Arabic calligraphy arranged around a ceramic bowl'),
}
# Explicit roles/uncertainty are retained. Authors and depicted rulers are not
# silently turned into the illustrators of their books.
MAKERS = {
    128073: "Abaidallah Murra(?) and 'Umar(?) — carvers named in the inscription",
    149945: 'Ibrahim the Decorator (or the Engraver)',
    124426: 'Muhammad Ibn Badr al-Din Jajarmi — author and scribe; illustrator not recorded',
}
MAKER_SUPPORT = {
    128073: ['names of the carvers', 'Abaidallah Murra', "'Umar"],
    149945: ['work of Ibrahim the Decorator', 'Engraver'],
    124426: ['written by the author', 'Ramadan, 741'],
}


def discover():
    # Reuse the previous, preserved same-day museum response, including receipt.
    for name in ['cleveland-islamic.json', 'cleveland-islamic.receipt.json', 'cleveland-policy.html', 'cleveland-policy.html.receipt.json', 'met-policy-web.json']:
        core.save(core.RUN / 'captures' / name, (PREVIOUS / 'captures' / name).read_bytes())
    for oid in MET:
        core.fetch(core.PROVIDERS['met']['api'] + 'objects/' + str(oid), core.RUN / 'captures' / f'met-{oid}.json')
    print('Reused bounded Cleveland metadata; captured two selected Met records. No images downloaded.')


def plan():
    capture = core.load('captures/cleveland-islamic.receipt.json')
    raw = (core.RUN / 'captures/cleveland-islamic.json').read_bytes()
    assert core.sha(raw) == capture['sha256']
    objects = {o['id']: o for o in json.loads(raw)['data']}
    evidence = (core.RUN / 'captures/geography-maker-evidence-web.json').read_bytes()
    assert b'Uzbekistan' in evidence and b'Samarkand' in evidence
    records = []
    for oid, (country, kind, reason) in CLEVELAND.items():
        o = objects[oid]
        assert o['department'] == 'Islamic Art' and o['share_license_status'] == 'CC0'
        assert not o.get('copyright') and not o.get('rights_and_reproductions')
        assert o['legal_status'] == 'accessioned' and o['on_loan'] is False
        assert not o.get('cover_accession_number') and o['record_type'] in ('object', 'cover')
        assert not o.get('creators'), 'Unexpected creator metadata requires review'
        lo, hi, date = o['creation_date_earliest'], o['creation_date_latest'], o['creation_date']
        assert type(lo) is int and type(hi) is int and 600 <= lo <= hi <= 1400
        assert not re.search(r'undated|unknown|before|after|\?', date, re.I)
        culture = '; '.join(o['culture'])
        if country == 'UZ':
            assert oid == 159535 and 'Samarkand' in culture
        else:
            assert core.COUNTRIES[country][0] in culture
        expected_type = {'ceramic':'Ceramic', 'metalwork':'Metalwork', 'sculpture':'Sculpture', 'drawing':'Drawing', 'manuscript_illumination':'Manuscript'}[kind]
        assert o['type'] == expected_type
        for fragment in MAKER_SUPPORT.get(oid, []):
            assert fragment in o['description']
        acc = o['accession_number']
        image = o['images']['web']['url']
        assert image == f'https://openaccess-cdn.clevelandart.org/{acc}/{acc}_web.jpg'
        assert o['url'] == 'https://clevelandart.org/art/' + acc
        precision = ('circa' if lo == hi else 'circa_range') if date.startswith('c.') else ('exact' if lo == hi else 'range')
        c = {'key':'cleveland-'+str(oid), 'provider':'cleveland', 'object_id':str(oid), 'accession':acc,
            'title':o['title'], 'lo':lo, 'hi':hi, 'date_display':date, 'precision':precision, 'type':kind,
            'country':country, 'culture':culture, 'place_display':culture, 'maker':MAKERS.get(oid),
            'url':o['url'], 'image_url':image, 'medium':o['technique'], 'dimensions':o['measurements'],
            'credit':o['creditline'], 'reason':reason, 'object':o, 'capture':capture}
        if country == 'UZ':
            c['geography_note'] = 'Museum specifies Samarkand; modern-country mapping to Uzbekistan corroborated by UNESCO https://whc.unesco.org/en/list/603/. No historical nationality inference.'
        records.append(c)
    for oid, (country, kind, reason) in MET.items():
        o = core.load(f'captures/met-{oid}.json')
        receipt = core.load(f'captures/met-{oid}.json.receipt.json')
        assert core.sha((core.RUN / f'captures/met-{oid}.json').read_bytes()) == receipt['sha256']
        assert o['objectID'] == oid and o['isPublicDomain'] is True and not o['rightsAndReproduction']
        assert o['country'] == 'Iran' and o['city'] == 'Nishapur' and not o['artistDisplayName']
        assert o['classification'].startswith('Ceramics') and o['department'] == 'Islamic Art'
        assert o['primaryImage'].startswith('https://images.metmuseum.org/CRDImages/is/original/')
        assert o['objectURL'] == 'https://www.metmuseum.org/art/collection/search/' + str(oid)
        lo, hi = o['objectBeginDate'], o['objectEndDate']
        assert 600 <= lo <= hi <= 1400
        place = o['geographyType'] + ' ' + o['country'] + ', ' + o['city']
        records.append({'key':'met-'+str(oid), 'provider':'met', 'object_id':str(oid), 'accession':o['accessionNumber'],
            'title':o['title'], 'lo':lo, 'hi':hi, 'date_display':o['objectDate'], 'precision':'range',
            'type':kind, 'country':country, 'culture':'Islamic Art', 'place_display':place, 'maker':None,
            'url':o['objectURL'], 'image_url':o['primaryImage'], 'medium':o['medium'], 'dimensions':o['dimensions'],
            'credit':o['creditLine'], 'reason':reason, 'object':o, 'capture':receipt,
            'geography_note':'Museum geographic attribution retained verbatim, including "Probably from" where supplied. Country filtering represents this attribution, not independent proof of manufacture.'})
    assert len(records) == 20
    previous = json.loads((PREVIOUS / 'plan.json').read_bytes())
    previous_ids = [c['artwork_id'] for c in previous['records']]
    with core.connect() as db:
        institutions = {key:db.execute("SELECT to_jsonb(i) record FROM institutions i WHERE slug=%s AND status<>'archived'", (v['slug'],)).fetchone()['record'] for key,v in core.PROVIDERS.items()}
        countries = db.execute('SELECT to_jsonb(c) record FROM countries c WHERE code=ANY(%s) ORDER BY code', (list(core.COUNTRIES),)).fetchall()
        places = {}
        for code, (name, _) in core.COUNTRIES.items():
            matches = db.execute('SELECT to_jsonb(p) record FROM places p WHERE country_code=%s AND name=%s', (code,name)).fetchall()
            assert len(matches) <= 1
            if matches:
                places[code] = matches[0]['record']
        old = db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id', (previous_ids,)).fetchall()
        assert len(old) == 12
        for c in records:
            c['institution_id'] = institutions[c['provider']]['id']
            assert not core.duplicate(db,c), 'Existing accession: ' + c['key']
            c['artwork_id'],c['slug'] = core.uid(c['key']), 'islamic-' + c['key']
    policies = previous['policies']
    for key in ['cleveland','met']:
        file = 'cleveland-policy.html' if key=='cleveland' else 'met-policy-web.json'
        assert core.sha((core.RUN/'captures'/file).read_bytes()) == policies[key]['sha256']
    core.save(core.RUN/'plan.json', {'records':records,'policies':policies,'institutions':institutions,
        'country_preimages':countries,'places':places,'previous_artwork_preimages':old,
        'additional_evidence':{'path':'captures/geography-maker-evidence-web.json','sha256':core.sha(evidence)},
        'selection_bound':'18 manually selected Cleveland parent accessions from the previous bounded 100-record metadata response; two selected Met objects. No collection crawl.'})
    core.save(core.RUN/'plan-pin.json', {'sha256':core.sha((core.RUN/'plan.json').read_bytes())})
    print('Pinned 20 additional objects; no accession duplicates; first 12 preserved.')


def prepare():
    core.prepare()
    Path('/tmp/artline-islamic-world-contact.jpg').rename('/tmp/artline-islamic-more-contact.jpg')


def verify():
    core.verify()
    p = core.pinned()
    with core.connect() as db:
        ids = [r['record']['id'] for r in p['previous_artwork_preimages']]
        assert db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id', (ids,)).fetchall() == p['previous_artwork_preimages']
    print('The original 12 artwork records remain unchanged.')


def apply():
    core.apply()
    verify()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['discover','plan','prepare','backup','apply','verify'])
    phase = parser.parse_args().phase
    (globals().get(phase) or getattr(core,phase))()
