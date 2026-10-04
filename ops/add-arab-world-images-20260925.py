#!/usr/bin/env python3
"""Twelve selected Egyptian, Iraqi and Syrian objects; local review only.

Reuse the established pinned-source, selected-image, backup and atomic import
workflow. Preserve museum uncertainty and creator roles at object level.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('islamic_core', Path(__file__).with_name('add-islamic-world-images-20260925.py'))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
PREVIOUS = core.RUN
core.CAMPAIGN = 'arab-world-images-20260925'
core.RUN = core.ROOT / 'docs/research' / core.CAMPAIGN
core.BACKUP = core.DATA / 'backups' / core.CAMPAIGN
core.ORIGINALS = core.DATA / 'source-images' / core.CAMPAIGN
core.COUNTRIES = {k: v for k, v in core.COUNTRIES.items() if k in ('EG', 'IQ', 'SY')}
CLEVELAND = {
    133460: ('IQ', 'metalwork', 'Silver-inlaid ewer with arabesques and a dated inscription'),
    123968: ('EG', 'ceramic', 'Fatimid luster painting with an ibex from Fustat'),
    124072: ('SY', 'ceramic', 'Rusapha bowl with three seated figures and abstract script'),
    95116: ('SY', 'ceramic', 'Raqqa bowl with lobed motifs and Arabic inscriptions'),
    114264: ('EG', 'drawing', 'Early Kufic calligraphy with gold verse markers'),
    170528: ('EG', 'manuscript_illumination', 'Mamluk Quranic calligraphy from Cairo'),
    95134: ('SY', 'ceramic', 'Turquoise-glazed Raqqa casket with relief ornament'),
    120202: ('SY', 'ceramic', 'Patterned ceramic jar from Ayyubid Raqqa'),
    136410: ('IQ', 'ceramic', 'Blue and turquoise Abbasid earthenware from Basra'),
    123974: ('IQ', 'manuscript_illumination', 'Persian literary illustration made in Ilkhanid Baghdad'),
}
MET = {
    449103: ('SY', 'sculpture', 'Carved vegetal ornament on an early Abbasid capital'),
    452209: ('EG', 'ceramic', 'Fatimid luster-painted ornament with scrolls and dots'),
}


def plan():
    objects = {}
    for country in ('egypt', 'syria', 'iraq'):
        path = core.RUN / 'captures' / f'cleveland-{country}.json'
        receipt = json.loads(path.with_suffix('.json.receipt.json').read_text())
        assert core.sha(path.read_bytes()) == receipt['sha256']
        for obj in json.loads(path.read_text())['data']:
            objects[obj['id']] = (obj, receipt)
    records = []
    for oid, (country, kind, reason) in CLEVELAND.items():
        o, capture = objects[oid]
        assert o['department'] == 'Islamic Art' and o['share_license_status'] == 'CC0'
        assert not o.get('copyright') and not o.get('rights_and_reproductions')
        assert o['legal_status'] == 'accessioned' and o['on_loan'] is False
        assert not o.get('cover_accession_number') and o['record_type'] in ('object', 'cover')
        makers = o.get('creators') or []
        assert not makers or (oid == 133460 and len(makers) == 1 and makers[0]['id'] == 1254 and makers[0]['role'] == 'inscription by')
        maker = 'Ahmad al-Dhaki al-Mawsili — inscription by' if makers else None
        lo, hi, date = o['creation_date_earliest'], o['creation_date_latest'], o['creation_date']
        assert type(lo) is int and type(hi) is int and 600 <= lo <= hi <= 1400
        culture = '; '.join(o['culture'])
        assert core.COUNTRIES[country][0] in culture
        assert o['type'] == {'ceramic': 'Ceramic', 'metalwork': 'Metalwork', 'drawing': 'Drawing', 'manuscript_illumination': 'Manuscript'}[kind]
        acc, image = o['accession_number'], o['images']['web']['url']
        assert image == f'https://openaccess-cdn.clevelandart.org/{acc}/{acc}_web.jpg'
        assert o['url'] == 'https://clevelandart.org/art/' + acc
        precision = ('circa' if lo == hi else 'circa_range') if date.startswith('c.') else ('exact' if lo == hi else 'range')
        records.append({'key': 'cleveland-'+str(oid), 'provider': 'cleveland', 'object_id': str(oid), 'accession': acc,
            'title': o['title'], 'lo': lo, 'hi': hi, 'date_display': date, 'precision': precision, 'type': kind,
            'country': country, 'culture': culture, 'place_display': culture, 'maker': maker,
            'url': o['url'], 'image_url': image, 'medium': o['technique'], 'dimensions': o['measurements'],
            'credit': o['creditline'], 'reason': reason, 'object': o, 'capture': capture,
            'geography_note': 'Country filtering follows the museum attribution. Source uncertainty, including Probably Egypt and possibly Mosul, is retained; no creator nationality is inferred.'})
    for oid, (country, kind, reason) in MET.items():
        o = core.load(f'captures/met-{oid}.json')
        receipt = core.load(f'captures/met-{oid}.json.receipt.json')
        assert core.sha((core.RUN / f'captures/met-{oid}.json').read_bytes()) == receipt['sha256']
        assert o['objectID'] == oid and o['isPublicDomain'] is True and not o['rightsAndReproduction']
        assert o['country'] == core.COUNTRIES[country][0] and not o['artistDisplayName']
        assert o['classification'] == {'ceramic': 'Ceramics', 'sculpture': 'Sculpture'}[kind]
        assert o['department'] == 'Islamic Art' and o['primaryImage'].startswith('https://images.metmuseum.org/CRDImages/is/original/')
        assert o['objectURL'] == 'https://www.metmuseum.org/art/collection/search/' + str(oid)
        lo, hi = o['objectBeginDate'], o['objectEndDate']
        assert 600 <= lo <= hi <= 1400
        place = o['geographyType'] + ' ' + o['country'] + (', ' + o['city'] if o['city'] else '')
        records.append({'key': 'met-'+str(oid), 'provider': 'met', 'object_id': str(oid), 'accession': o['accessionNumber'],
            'title': o['title'], 'lo': lo, 'hi': hi, 'date_display': o['objectDate'], 'precision': 'range',
            'type': kind, 'country': country, 'culture': 'Islamic Art', 'place_display': place, 'maker': None,
            'url': o['objectURL'], 'image_url': o['primaryImage'], 'medium': o['medium'], 'dimensions': o['dimensions'],
            'credit': o['creditLine'], 'reason': reason, 'object': o, 'capture': receipt,
            'geography_note': 'Museum geographic attribution retained verbatim, including Attributed to and probably Raqqa. Country filtering represents that attribution.'})
    assert len(records) == 12
    previous = json.loads((PREVIOUS / 'plan.json').read_text())
    more = json.loads((core.ROOT / 'docs/research/islamic-world-more-20260925/plan.json').read_text())
    ids = [c['artwork_id'] for p in (previous, more) for c in p['records']]
    with core.connect() as db:
        institutions = {key: db.execute("SELECT to_jsonb(i) record FROM institutions i WHERE slug=%s AND status<>'archived'", (v['slug'],)).fetchone()['record'] for key, v in core.PROVIDERS.items()}
        countries = db.execute('SELECT to_jsonb(c) record FROM countries c WHERE code=ANY(%s) ORDER BY code', (list(core.COUNTRIES),)).fetchall()
        places = {}
        for code, (name, _) in core.COUNTRIES.items():
            matches = db.execute('SELECT to_jsonb(p) record FROM places p WHERE country_code=%s AND name=%s', (code, name)).fetchall()
            assert len(matches) == 1
            places[code] = matches[0]['record']
        old = db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id', (ids,)).fetchall()
        assert len(old) == 32
        for c in records:
            c['institution_id'] = institutions[c['provider']]['id']
            assert not core.duplicate(db, c), 'Existing accession: ' + c['key']
            c['artwork_id'], c['slug'] = core.uid(c['key']), 'islamic-' + c['key']
    for file, provider in [('cleveland-policy.html', 'cleveland'), ('met-policy-web.json', 'met')]:
        raw = (PREVIOUS / 'captures' / file).read_bytes()
        assert core.sha(raw) == previous['policies'][provider]['sha256']
        core.save(core.RUN / 'captures' / file, raw)
    core.save(core.RUN / 'plan.json', {'records': records, 'policies': previous['policies'], 'institutions': institutions,
        'country_preimages': countries, 'places': places, 'previous_artwork_preimages': old,
        'selection_bound': 'Three bounded 30-record metadata searches for Egypt, Syria and Iraq; two selected Met records. Twelve reviewed parent accessions; no collection crawl.'})
    core.save(core.RUN / 'plan-pin.json', {'sha256': core.sha((core.RUN / 'plan.json').read_bytes())})
    print('Pinned 12 Arab-region objects; no duplicates; original 32 preserved.')


def verify():
    core.verify()
    p = core.pinned()
    with core.connect() as db:
        ids = [r['record']['id'] for r in p['previous_artwork_preimages']]
        assert db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id', (ids,)).fetchall() == p['previous_artwork_preimages']
    print('The previous 32 artwork records remain unchanged.')


def apply():
    core.apply()
    verify()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['plan', 'prepare', 'backup', 'apply', 'verify'])
    phase = parser.parse_args().phase
    (globals().get(phase) or getattr(core, phase))()
