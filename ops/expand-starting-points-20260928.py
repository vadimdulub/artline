#!/usr/bin/env python3
"""Bounded, reviewed museum and archival selections for All starting points.

Metadata selection precedes image downloads. Imports remain in review. Archive
photographs use explicit owner selections, never invented museum holdings.
"""
import argparse
import collections
import concurrent.futures
import html
import importlib.util
import io
import json
import re
from pathlib import Path

s = importlib.util.spec_from_file_location('core', Path(__file__).with_name('add-islamic-world-images-20260925.py'))
c = importlib.util.module_from_spec(s)
s.loader.exec_module(c)
c.CAMPAIGN = 'all-starting-points-expansion-20260928'
c.RUN = c.ROOT / 'docs/research' / c.CAMPAIGN
c.BACKUP = c.DATA / 'backups' / c.CAMPAIGN
c.ORIGINALS = c.DATA / 'source-images' / c.CAMPAIGN
c.SOURCE_LABEL = 'Reviewed starting-point expansion'
c.MIGRATION = '0031_archive_institutions.sql'
c.PROVIDERS = {
    'cleveland': c.PROVIDERS['cleveland'],
    'met': c.PROVIDERS['met'],
    'artic': {'slug': 'art-institute-of-chicago', 'name': 'Art Institute of Chicago',
              'api': 'https://api.artic.edu/api/v1/artworks/', 'policy': 'https://www.artic.edu/open-access/open-access-images'},
    'nasa': {'slug': 'nasa-image-and-video-library', 'name': 'NASA Image and Video Library',
             'api': 'https://images-api.nasa.gov/', 'policy': 'https://www.nasa.gov/nasa-brand-center/images-and-media/',
             'source_type': 'collection_page'},
}
COUNTRIES = {
    'AF': ('Afghanistan', 'southern-asia'), 'BD': ('Bangladesh', 'southern-asia'),
    'CN': ('China', 'eastern-asia'), 'JP': ('Japan', 'eastern-asia'),
    'IN': ('India', 'southern-asia'), 'NP': ('Nepal', 'southern-asia'),
    'PK': ('Pakistan', 'southern-asia'), 'LK': ('Sri Lanka', 'southern-asia'),
    'TH': ('Thailand', 'south-eastern-asia'), 'KH': ('Cambodia', 'south-eastern-asia'),
    'MM': ('Myanmar', 'south-eastern-asia'), 'ID': ('Indonesia', 'south-eastern-asia'),
    'VN': ('Vietnam', 'south-eastern-asia'), 'IR': ('Iran', 'southern-asia'),
    'IQ': ('Iraq', 'western-asia'), 'SY': ('Syria', 'western-asia'),
    'TR': ('Türkiye', 'western-asia'), 'UZ': ('Uzbekistan', 'central-asia'),
    'EG': ('Egypt', 'northern-africa'), 'SD': ('Sudan', 'northern-africa'),
    'MA': ('Morocco', 'northern-africa'), 'TN': ('Tunisia', 'northern-africa'),
    'DZ': ('Algeria', 'northern-africa'), 'ML': ('Mali', 'western-africa'),
    'SN': ('Senegal', 'western-africa'), 'NG': ('Nigeria', 'western-africa'),
    'GH': ('Ghana', 'western-africa'), 'GN': ('Guinea', 'western-africa'),
    'CI': ('Côte d’Ivoire', 'western-africa'), 'BF': ('Burkina Faso', 'western-africa'),
    'SL': ('Sierra Leone', 'western-africa'), 'LR': ('Liberia', 'western-africa'),
    'ES': ('Spain', 'southern-europe'), 'PT': ('Portugal', 'southern-europe'),
    'IT': ('Italy', 'southern-europe'), 'GR': ('Greece', 'southern-europe'),
    'FR': ('France', 'western-europe'), 'DE': ('Germany', 'western-europe'),
}
TYPE = {'Painting': 'painting', 'Drawing': 'drawing', 'Print': 'print', 'Print and Drawing': 'print',
        'Sculpture': 'sculpture', 'Ceramic': 'ceramic', 'Ceramics': 'ceramic', 'Textile': 'textile',
        'Textiles': 'textile', 'Metalwork': 'metalwork', 'Silver': 'metalwork', 'Ivory': 'sculpture',
        'Calligraphy': 'calligraphy', 'Manuscript': 'manuscript_illumination', 'Photograph': 'photograph'}
REASONS = {
    'writing': 'Writing, belief, administration and visual culture of early cities and their ancient successors.',
    'classical': 'Greek, Etruscan and Roman visual culture: myth, civic life, ritual and craftsmanship.',
    'buddhism': 'Buddhist images, sacred architecture and narrative along the early routes across Asia.',
    'byzantium': 'Byzantine icons, mosaics, manuscript culture and decorated ritual objects.',
    'islamic-learning': 'Calligraphy, patterned objects and illustrated knowledge across Islamic societies.',
    'tang-song': 'Tang and Song visual life: landscape, poetry, Buddhist imagery, ceramics and ornament.',
    'sahel': 'West African trade, courtly and community arts; later objects are explicitly contextual traditions.',
    'mughal': 'Mughal court portraits, narratives, gardens, music and decorative arts.',
    'space-age': 'Selected historical spaceflight photography: flight, exploration and the people behind missions.',
}


def plain(value):
    return html.unescape(re.sub(r'<[^>]+>', '', value or '')).strip()


def origin_country(value):
    """Only explicit country wording; broad or contested regions stay unknown."""
    value = value.replace('Côte d\'Ivoire', 'Côte d’Ivoire')
    if re.search(r'Kashmir|Gandhara|North Africa|Eastern Mediterranean|Central Asia', value) and not re.search(r'Pakistan|Afghanistan|Uzbekistan', value):
        return None
    names = {name: code for code, (name, _) in COUNTRIES.items()}
    names.update({'Turkey': 'TR', 'Burma': 'MM', 'Ceylon': 'LK'})
    codes = {code for name, code in names.items() if re.search(r'\b' + re.escape(name) + r'\b', value, re.I)}
    return next(iter(codes)) if len(codes) == 1 else None


def captured_objects():
    result = {}
    for f in sorted((c.RUN / 'captures').glob('*.json')):
        if 'receipt' in f.name:
            continue
        if not (f.name.startswith('cma-') or f.name.startswith('aic-period-') or f.name.startswith('nasa-') or f.name.startswith('met-object-')):
            continue
        receipt = json.loads(f.with_suffix('.json.receipt.json').read_bytes())
        assert c.sha(f.read_bytes()) == receipt['sha256']
        data = json.loads(f.read_bytes())
        if f.name.startswith('met-object-'):
            result[('met', str(data['objectID']))] = (data, receipt)
        elif f.name.startswith('nasa-'):
            for item in data['collection']['items']:
                result[('nasa', item['data'][0]['nasa_id'])] = (item, receipt)
        else:
            provider = 'cleveland' if f.name.startswith('cma-') else 'artic'
            for item in data['data']:
                result[(provider, str(item['id']))] = (item, receipt)
    return result


def plan():
    choices = c.load('reviewed-selection.json')
    objects = captured_objects()
    records, reused, excluded = [], [], []
    with c.connect() as db:
        institutions = {}
        for key, p in c.PROVIDERS.items():
            row = db.execute('SELECT to_jsonb(i) record FROM institutions i WHERE slug=%s', (p['slug'],)).fetchone()
            if row:
                institutions[key] = row['record']
            else:
                assert key == 'nasa'
                institutions[key] = {'id': c.uid('institution/nasa'), 'slug': p['slug'], 'name': p['name'],
                    'normalized_name': c.norm(p['name']), 'kind': 'archive', 'status': 'review',
                    'website_url': 'https://images.nasa.gov/',
                    'description': 'NASA’s digital image archive. Selected photographs are personal editorial selections, not museum-designated highlights or physical-holding assertions.'}
        for choice in choices:
            provider, oid = choice['provider'], str(choice['id'])
            o, receipt = objects[(provider, oid)]
            topics = choice['topics']
            if provider == 'cleveland':
                assert o['share_license_status'] == 'CC0' and not o.get('copyright') and not o.get('rights_and_reproductions')
                assert o['legal_status'] == 'accessioned' and not o['on_loan'] and not o.get('cover_accession_number')
                culture = '; '.join(o['culture'])
                makers = [x for x in o.get('creators', []) if x.get('use_in_caption') and x.get('role') != 'publisher']
                maker = '; '.join(' '.join(x for x in [m.get('qualifier'), m['description'].split(' (')[0],
                    '(' + m['role'] + ')' if m.get('role') not in (None, 'artist') else None] if x) for m in makers) or None
                r = {'accession': o['accession_number'], 'title': o['title'], 'lo': o['creation_date_earliest'],
                     'hi': o['creation_date_latest'], 'date_display': o['creation_date'], 'type': TYPE.get(o['type'], 'unknown'),
                     'culture': culture, 'place_display': culture, 'country': origin_country(culture), 'maker': maker,
                     'url': o['url'], 'image_url': o['images']['web']['url'], 'medium': o['technique'],
                     'dimensions': o.get('measurements'), 'credit': o['creditline']}
            elif provider == 'met':
                assert o['isPublicDomain'] is True and o['primaryImage'] and o['accessionNumber']
                assert not re.search(r'^L\.|loan', o['accessionNumber'], re.I)
                r = {'accession': o['accessionNumber'], 'title': o['title'], 'lo': o['objectBeginDate'],
                     'hi': o['objectEndDate'], 'date_display': o['objectDate'],
                     'type': next((v for k, v in [('Sculpture','sculpture'),('Textile','textile'),('Metal','metalwork'),('Ceramic','ceramic')] if k.lower() in o['classification'].lower()), 'unknown'),
                     'culture': o.get('culture'), 'place_display': ', '.join(v for v in [o.get('country'),o.get('region'),o.get('subregion')] if v),
                     'country': origin_country(o.get('country') or ''), 'maker': o.get('artistDisplayName') or None,
                     'url': o['objectURL'], 'image_url': o['primaryImage'], 'medium': o.get('medium'),
                     'dimensions': o.get('dimensions'), 'credit': o['creditLine']}
            elif provider == 'artic':
                assert o['is_public_domain'] is True and not o.get('copyright_notice') and o['image_id']
                assert int(oid) not in [4652, 69081], 'Museum API date conflicts retained for separate review'
                culture = '; '.join(o.get('style_titles') or [])
                # Cultural/collective designations remain labels, not invented people.
                r = {'accession': o['main_reference_number'], 'title': plain(o['title']), 'lo': o['date_start'],
                     'hi': o['date_end'], 'date_display': o['date_display'], 'type': TYPE.get(o['artwork_type_title'], 'unknown'),
                     'culture': culture or o.get('artist_title'), 'place_display': o.get('place_of_origin'),
                     'country': origin_country(o.get('place_of_origin') or ''), 'maker': o.get('artist_title'),
                     'url': 'https://www.artic.edu/artworks/' + oid,
                     'image_url': 'https://www.artic.edu/iiif/2/' + o['image_id'] + '/full/843,/0/default.jpg',
                     'medium': o.get('medium_display'), 'dimensions': o.get('dimensions'), 'credit': o['credit_line']}
            else:
                d = o['data'][0]
                year = int(d['date_created'][:4])
                assert 1961 <= year <= 1970
                assert re.search(r'NASA|National Aeronautics', d.get('description', '') + ' ' + d.get('photographer', ''), re.I)
                assert not re.search(r'copyright|Getty|Associated Press|United Press|emblem|insignia', d.get('description', '') + ' ' + d['title'], re.I)
                links = [x for x in o['links'] if '~medium.jpg' in x['href']]
                if not links:
                    links = [x for x in o['links'] if x.get('rel') == 'canonical' and x['href'].endswith('.jpg')]
                assert len(links) == 1
                r = {'accession': oid, 'title': d['title'].strip(), 'lo': year, 'hi': year,
                     'date_display': str(year), 'type': 'photograph', 'culture': None,
                     'place_display': d.get('location'), 'country': None, 'maker': d.get('photographer') or 'NASA; photographer not recorded',
                     'url': 'https://images.nasa.gov/details/' + oid, 'image_url': links[0]['href'],
                     'medium': 'Photograph', 'dimensions': None, 'credit': 'NASA. Original agency credit retained in source evidence.',
                     'rights_status': 'licensed', 'license_label': 'NASA media-use permission — educational/informational use',
                     'license_url': c.PROVIDERS['nasa']['policy'], 'rights_basis': 'Historical NASA-credited photograph with no third-party credit or copyright notice. The preserved NASA policy explicitly permits factual educational/informational use on Internet pages with NASA acknowledgement and without implied endorsement; no worldwide public-domain claim.',
                     'scope_note': 'Historical photograph, explicitly selected for the visual record of spaceflight. Source creation year and archival description retained. No invented individual photographer or physical museum holding.'}
            assert r['lo'] and r['hi'] and r['lo'] <= r['hi'] <= 1970
            key = provider + '-' + oid
            r.update(key=key, provider=provider, object_id=oid, object=o, capture=receipt, topics=topics,
                     reason=' '.join(REASONS[t] for t in topics), artist_id=None,
                     institution_id=institutions[provider]['id'], artwork_id=c.uid(key),
                     slug='starting-point-' + re.sub('[^a-z0-9-]', '-', key.lower()))
            approximate = bool(re.search(r'c\.|circa|about|probably|possibly|early|late|mid', r['date_display'], re.I))
            r['precision'] = ('circa' if r['lo'] == r['hi'] else 'circa_range') if approximate else ('exact' if r['lo'] == r['hi'] else 'range')
            if re.search(r'century|\b\d{2}00s\b', r['date_display'], re.I):
                r['precision'] = 'century'
            elif re.search(r'\b\d{3}0s\b', r['date_display']):
                r['precision'] = 'decade'
            elif re.search(r'before|by |after', r['date_display'], re.I):
                r['precision'] = 'circa_range'
            r['geography_note'] = 'Association from explicit museum origin/culture wording; ambiguous multi-country origins stay unassigned. No creator nationality or precise findspot inferred.'
            duplicate = c.duplicate(db, r)
            if duplicate:
                reused.append({'key': key, 'artwork_id': str(duplicate['id']), 'topics': topics})
                continue
            parts = db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s AND accession_number LIKE %s LIMIT 1', (r['institution_id'], r['accession'] + '.%')).fetchone()
            if parts:
                excluded.append({'key': key, 'reason': 'An accession component is already represented; parent not duplicated', 'existing': parts['id']})
                continue
            records.append(r)
        used = {r['country'] for r in records if r['country']}
        c.COUNTRIES = {k: v for k, v in COUNTRIES.items() if k in used}
        countries = db.execute('SELECT to_jsonb(c) record FROM countries c WHERE code=ANY(%s) ORDER BY code', (list(c.COUNTRIES),)).fetchall()
        places = {}
        for code, (name, _) in c.COUNTRIES.items():
            rows = db.execute('SELECT to_jsonb(p) record FROM places p WHERE country_code=%s AND name=%s', (code, name)).fetchall()
            if rows:
                assert len(rows) == 1
                places[code] = rows[0]['record']
    policies = {}
    for key, provider in c.PROVIDERS.items():
        if key == 'met':
            proof = c.RUN / 'captures/met-policy-web.json'
            value = json.loads(proof.read_bytes())
            assert value['url'] == provider['policy'] and 'CC0' in proof.read_text()
            policies[key] = {'url': value['url'], 'at': value['at'], 'sha256': c.sha(proof.read_bytes()), 'path': str(proof)}
            continue
        _, policies[key] = c.fetch(provider['policy'], c.RUN / 'captures' / (key + '-policy.html'))
    value = {'records': records, 'reused': reused, 'excluded': excluded, 'institutions': institutions,
             'institutions_to_create': [v for v in institutions.values() if v['id'] == c.uid('institution/nasa')],
             'country_preimages': countries, 'countries': c.COUNTRIES, 'places': places, 'policies': policies,
             'selection_bound': 'Enumerated, reviewed objects from bounded topical metadata queries. Only these pinned reproductions may be downloaded; no full-collection image crawl.'}
    c.save(c.RUN / 'plan.json', value)
    c.save(c.RUN / 'plan-pin.json', {'sha256': c.sha((c.RUN / 'plan.json').read_bytes())})
    print('Pinned', len(records), 'new records;', len(reused), 'existing identities;', len(excluded), 'parent conflicts.')


def prepare():
    p = c.pinned()
    def one(rec):
        raw, receipt = c.fetch(rec['image_url'], c.ORIGINALS / (rec['key'] + '.jpg'))
        with c.Image.open(io.BytesIO(raw)) as src:
            assert src.width * src.height < 40_000_000
            pic = c.ImageOps.exif_transpose(src).convert('RGB')
            result = None
            for edge in (1200, 1000, 843, 700, 600):
                pic.thumbnail((edge, edge), c.Image.Resampling.LANCZOS)
                for quality in (90, 85, 80, 75, 70, 65, 60):
                    out = io.BytesIO(); pic.save(out, 'JPEG', quality=quality, optimize=True, progressive=True)
                    if out.tell() <= 100000:
                        result = out.getvalue(); break
                if result:
                    break
            assert result
            digest = c.sha(result)
            path = '/assets/artworks/imported/' + c.CAMPAIGN + '/' + rec['key'] + '-' + digest[:16] + '.jpg'
            c.save(c.ROOT / 'apps/web/public' / path.lstrip('/'), result)
            return {'key': rec['key'], 'media_id': c.uid('media/' + rec['key'] + '/' + digest), 'path': path,
                    'sha256': digest, 'bytes': len(result), 'width': pic.width, 'height': pic.height, 'download': receipt}
    images, failures = [], []
    def selected(rec):
        try:
            return one(rec)
        except Exception as error:
            failures.append({'key': rec['key'], 'url': rec['image_url'], 'reason': str(error)})
            print('Unavailable', rec['key'], str(error), flush=True)
            return None
    # Chicago asks for one request per second and one worker. Other providers
    # receive at most three concurrent selected-image requests.
    for provider in c.PROVIDERS:
        records = [r for r in p['records'] if r['provider'] == provider]
        if provider == 'artic':
            for rec in records:
                im = selected(rec)
                if im:
                    images.append(im)
                print('Processed', rec['key'], flush=True); c.time.sleep(1)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
                for im in pool.map(selected, records):
                    if im:
                        images.append(im); print('Prepared', im['key'], flush=True)
    c.save(c.RUN / 'images.json', sorted(images, key=lambda v: v['key']))
    c.save(c.RUN / 'unavailable-images.json', sorted(failures, key=lambda v: v['key']))
    if failures:
        print('Review exclusions and amend the pinned plan before contact sheets:', len(failures))
    else:
        sheets()


def sheets():
    p = c.pinned(); images = {im['key']: im for im in c.load('images.json')}
    dest = c.BACKUP / 'contact-sheets'; dest.mkdir(parents=True, exist_ok=True)
    ordered = sorted(p['records'], key=lambda r: (r['topics'][0], r['key']))
    index = []
    for page, start in enumerate(range(0, len(ordered), 20), 1):
        records = ordered[start:start + 20]
        sheet = c.Image.new('RGB', (1600, 400 * ((len(records) + 3) // 4)), '#eee9df')
        draw = c.ImageDraw.Draw(sheet)
        for n, rec in enumerate(records):
            with c.Image.open(c.ROOT / 'apps/web/public' / images[rec['key']]['path'].lstrip('/')) as pic:
                pic.thumbnail((380, 320)); x, y = n % 4 * 400, n // 4 * 400
                sheet.paste(pic, (x + (400-pic.width)//2, y))
                draw.multiline_text((x+6,y+326), f'{rec["key"]}\n{rec["title"][:55]}\n{rec["date_display"][:55]} | {rec["topics"][0]}', fill='black')
        path = dest / f'{page:02d}.jpg'; sheet.save(path, quality=94)
        index.append({'path': str(path), 'keys': [r['key'] for r in records], 'sha256': c.sha(path.read_bytes())})
    c.save(c.RUN / 'contact-sheets.json', index)
    print('Prepared', len(images), 'images on', len(index), 'contact sheets.')


def apply():
    p = c.pinned(); c.COUNTRIES = p['countries']
    recovery = c.load('backup.json')
    assert c.sha(Path(recovery['path']).read_bytes()) == recovery['sha256']
    # Required before an institution with the new archive kind is inserted.
    with c.connect(False) as db, db.transaction():
        if not db.execute('SELECT 1 FROM schema_migrations WHERE filename=%s', (c.MIGRATION,)).fetchone():
            db.execute("SET LOCAL lock_timeout='5s'")
            db.execute((c.ROOT / 'apps/server/db/migrations' / c.MIGRATION).read_text())
            c.insert(db, 'schema_migrations', {'filename': c.MIGRATION})
    original_insert = c.insert
    nasa = {r['artwork_id']: r for r in p['records'] if r['provider'] == 'nasa'}
    def insert(db, table, values):
        if table == 'artwork_location_assertions' and values['artwork_id'] in nasa:
            return  # The digital archive does not establish physical custody.
        if table == 'artwork_media' and values['artwork_id'] in nasa:
            values = {**values, 'view_label': 'NASA archival photograph'}
        if table == 'artworks' and values['id'] in nasa:
            values = {**values, 'current_institution_id': None,
                      'description_md': 'A selected historical NASA photograph. The linked archive preserves this image; no physical museum holding or current display is asserted.'}
        original_insert(db, table, values)
        if table == 'sources' and values['id'] == c.uid('source/nasa'):
            original_insert(db, 'curated_collections', {'id': c.uid('collection/nasa'), 'institution_id': p['institutions']['nasa']['id'],
                'curator_kind': 'owner', 'title': 'Selected visual history of spaceflight', 'status': 'review'})
        if table == 'artworks' and values['id'] in nasa:
            rec = nasa[values['id']]
            original_insert(db, 'curated_collection_items', {'id': c.uid('selection/' + rec['key']), 'collection_id': c.uid('collection/nasa'),
                'artwork_id': values['id'], 'position': list(nasa).index(values['id']) + 1, 'reason': rec['reason'],
                'source_id': c.uid('source/nasa'), 'source_url': rec['url'], 'checked_at': rec['capture']['at']})
    c.insert = insert
    c.apply()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['plan', 'prepare', 'sheets', 'backup', 'apply', 'verify'])
    phase = parser.parse_args().phase
    if phase not in ['plan']:
        c.COUNTRIES = c.pinned()['countries']
    (globals().get(phase) or getattr(c, phase))()
