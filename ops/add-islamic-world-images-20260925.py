#!/usr/bin/env python3
"""Twelve selected Islamic-world objects, local review only. Never publishes.

Plan and preserve primary metadata first; download only that pinned selection.
Require visual review and a validated backup before the atomic local import.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import time
import unicodedata
import uuid

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
import requests
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = 'islamic-world-images-20260925'
RUN = ROOT / 'docs/research' / CAMPAIGN
DATA = Path('/Users/vadimdulub/Library/Application Support/Artline')
BACKUP = DATA / 'backups' / CAMPAIGN
ORIGINALS = DATA / 'source-images' / CAMPAIGN
ACTOR = 'local-european-research'
SOURCE_LABEL = 'Selected Islamic-world objects'
CC0 = 'https://creativecommons.org/publicdomain/zero/1.0/'
MIGRATION = '0028_decorative_art_types.sql'
# Museum-classified objects; never infer a maker or use the book author's life
# as the date of an illustration. Parent accession = one object, not two sides.
SELECTION = {
    133598: ('IR', 'ceramic', 'Stylized bird and ornamental borders'),
    95115: ('IR', 'ceramic', 'Luster-painted wall decoration'),
    95123: ('IR', 'ceramic', 'Star-shaped tile with floral relief'),
    94658: ('IQ', 'ceramic', 'Abbasid blue-and-green geometric decoration'),
    123967: ('EG', 'ceramic', 'Fatimid luster painting with an antelope'),
    114247: ('IR', 'calligraphy', 'Ornamental Kufic calligraphy with illuminated medallions'),
    114190: ('ES', 'calligraphy', 'Maghribi script from Islamic Spain'),
    124420: ('SY', 'manuscript_illumination', 'Illustrated mechanical knowledge: a peacock automaton'),
    123985: ('IR', 'metalwork', 'Inlaid metalwork with animated script and interlacing bands'),
    423612: ('ES', 'sculpture', 'Carved architectural ornament from Madinat al-Zahra'),
    149172: ('IQ', 'manuscript_illumination', 'Illustrated medicine in Abbasid Baghdad'),
}
COUNTRIES = {'IR': ('Iran', 'southern-asia'), 'IQ': ('Iraq', 'western-asia'),
    'EG': ('Egypt', 'northern-africa'), 'ES': ('Spain', 'southern-europe'), 'SY': ('Syria', 'western-asia')}
PROVIDERS = {
    'cleveland': {'slug': 'cleveland-museum-of-art', 'name': 'The Cleveland Museum of Art',
        'api': 'https://openaccess-api.clevelandart.org/api/artworks/', 'policy': 'https://www.clevelandart.org/open-access'},
    'met': {'slug': 'the-met', 'name': 'The Metropolitan Museum of Art',
        'api': 'https://collectionapi.metmuseum.org/public/collection/v1/', 'policy': 'https://www.metmuseum.org/policies/image-resources'},
}


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def uid(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/' + CAMPAIGN + '/' + key))


def norm(value):
    return ' '.join(re.findall(r'[^\W_]+', ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))))


def save(path, value):
    raw = value if isinstance(value, bytes) else encode(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == raw, 'Evidence already exists with different contents: ' + str(path)
    else:
        path.write_bytes(raw)


def load(name):
    return json.loads((RUN / name).read_bytes())


def connect(readonly=True):
    return psycopg.connect('postgresql://localhost/artline', autocommit=True, row_factory=dict_row,
        options='-c timezone=UTC -c statement_timeout=120000' + (' -c default_transaction_read_only=on' if readonly else ''))


def fetch(url, path):
    receipt_path = path.with_suffix(path.suffix + '.receipt.json')
    if path.exists():
        raw, receipt = path.read_bytes(), json.loads(receipt_path.read_bytes())
        assert receipt['url'] == url and receipt['sha256'] == sha(raw)
        return raw, receipt
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=(15, 45), headers={'User-Agent': 'Artline selected museum image research'})
            response.raise_for_status()
            break
        except (requests.ConnectionError, requests.Timeout):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)
    raw = response.content
    receipt = {'url': response.url, 'at': now(), 'bytes': len(raw), 'sha256': sha(raw), 'status': response.status_code}
    save(path, raw)
    save(receipt_path, receipt)
    return raw, receipt


def discover():
    url = requests.Request('GET', PROVIDERS['cleveland']['api'], params={
        'department': 'Islamic Art', 'cc0': 1, 'has_image': 1, 'limit': 100,
        'created_before': 1400, 'created_after': 600}).prepare().url
    fetch(url, RUN / 'captures/cleveland-islamic.json')
    fetch(PROVIDERS['met']['api'] + 'objects/449537', RUN / 'captures/met-mihrab.json')
    print('One bounded metadata page and one selected Met object captured; no images downloaded.')


def plan():
    raw = (RUN / 'captures/cleveland-islamic.json').read_bytes()
    receipt = load('captures/cleveland-islamic.receipt.json')
    assert sha(raw) == receipt['sha256']
    objects = {o['id']: o for o in json.loads(raw)['data']}
    records = []
    for oid, (country, kind, reason) in SELECTION.items():
        o = objects[oid]
        assert o['department'] == 'Islamic Art' and o['share_license_status'] == 'CC0'
        assert not o.get('copyright') and not o.get('rights_and_reproductions')
        assert o['legal_status'] == 'accessioned' and o['on_loan'] is False and not o.get('cover_accession_number')
        assert o['record_type'] in ('object', 'cover')
        lo, hi = o['creation_date_earliest'], o['creation_date_latest']
        assert 600 <= lo <= hi <= 1400
        assert COUNTRIES[country][0] in ' '.join(o['culture'])
        acc = o['accession_number']
        image = o['images']['web']['url']
        assert image == 'https://openaccess-cdn.clevelandart.org/' + acc + '/' + acc + '_web.jpg'
        assert o['url'] == 'https://clevelandart.org/art/' + acc
        makers = o.get('creators') or []
        # Keep the one documented named maker at object level pending identity
        # reconciliation. No invented artist profile or birth/death years.
        assert not makers or (oid == 149172 and len(makers) == 1 and makers[0]['id'] == 59123)
        approx = o['creation_date'].startswith('c.')
        precision = 'circa_range' if approx else ('exact' if lo == hi else 'range')
        records.append({'key': 'cleveland-' + str(oid), 'provider': 'cleveland', 'object_id': str(oid),
            'accession': acc, 'title': o['title'], 'lo': lo, 'hi': hi, 'date_display': o['creation_date'],
            'precision': precision, 'type': kind, 'country': country, 'culture': '; '.join(o['culture']),
            'place_display': '; '.join(o['culture']), 'maker': 'Abdallah ibn al-Fadl' if makers else None,
            'url': o['url'], 'image_url': image, 'medium': o['technique'], 'dimensions': o['measurements'],
            'credit': o['creditline'], 'reason': reason, 'object': o, 'capture': receipt})
    o = load('captures/met-mihrab.json')
    receipt = load('captures/met-mihrab.receipt.json')
    assert sha((RUN / 'captures/met-mihrab.json').read_bytes()) == receipt['sha256']
    assert o['objectID'] == 449537 and o['isPublicDomain'] is True and not o['rightsAndReproduction']
    assert o['country'] == 'Iran' and o['city'] == 'Isfahan' and not o['artistDisplayName']
    assert (o['objectBeginDate'], o['objectEndDate']) == (1354, 1355)
    records.append({'key': 'met-449537', 'provider': 'met', 'object_id': '449537', 'accession': o['accessionNumber'],
        'title': o['title'], 'lo': 1354, 'hi': 1355, 'date_display': o['objectDate'], 'precision': 'range',
        'type': 'ceramic', 'country': 'IR', 'culture': 'Islamic Art', 'place_display': 'Isfahan, Iran', 'maker': None,
        'url': o['objectURL'], 'image_url': o['primaryImage'], 'medium': o['medium'], 'dimensions': o['dimensions'],
        'credit': o['creditLine'], 'reason': 'Geometric tile mosaic and architectural calligraphy', 'object': o, 'capture': receipt})
    assert len(records) == 12
    policies = {}
    for key, provider in PROVIDERS.items():
        if key == 'met' and (RUN / 'captures/met-policy-web.json').exists():
            # The official policy was read through the web tool after the direct
            # HTTP endpoint returned 429; preserve that primary-source capture.
            raw = (RUN / 'captures/met-policy-web.json').read_bytes()
            assert b'Creative Commons Zero' in raw and b'unrestricted' in raw
            policies[key] = {'url': provider['policy'], 'retrieved_date': '2026-09-25', 'sha256': sha(raw), 'capture': 'captures/met-policy-web.json', 'transport': 'web tool'}
        else:
            _, policies[key] = fetch(provider['policy'], RUN / 'captures' / (key + '-policy.html'))
    with connect() as db:
        institutions = {key: db.execute('SELECT to_jsonb(i) record FROM institutions i WHERE slug=%s AND status<>\'archived\'', (p['slug'],)).fetchone()['record'] for key, p in PROVIDERS.items()}
        countries = db.execute('SELECT to_jsonb(c) record FROM countries c WHERE code=ANY(%s) ORDER BY code', (list(COUNTRIES),)).fetchall()
        for c in records:
            c['institution_id'] = institutions[c['provider']]['id']
            assert not duplicate(db, c), 'Existing accession or canonical URL: ' + c['key']
            c['artwork_id'] = uid(c['key'])
            c['slug'] = 'islamic-' + c['key']
    save(RUN / 'plan.json', {'records': records, 'policies': policies, 'institutions': institutions, 'country_preimages': countries,
        'selection_bound': '11 manually selected Cleveland objects from one 100-record metadata page; one explicitly selected Met object. No full-collection or image crawl.'})
    save(RUN / 'plan-pin.json', {'sha256': sha((RUN / 'plan.json').read_bytes())})
    print('Pinned 12 source-backed objects; no duplicates; countries', list(COUNTRIES))


def duplicate(db, c):
    # Museum accession + exact source identities, never fuzzy title merging.
    return db.execute('''SELECT id FROM artworks WHERE current_institution_id=%s AND accession_number=%s
      UNION SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND
      (canonical_url=ANY(%s) OR (scheme=ANY(%s) AND external_id=%s)) LIMIT 1''',
      (c['institution_id'], c['accession'], [c['url'], c['url'].replace('https://clevelandart.org', 'https://www.clevelandart.org')],
       ['cleveland-object', 'european-cleveland-cleveland-museum-of-art-object'] if c['provider']=='cleveland' else ['met-object', 'met-object-id'], c['object_id'])).fetchone()


def pinned():
    assert sha((RUN / 'plan.json').read_bytes()) == load('plan-pin.json')['sha256']
    return load('plan.json')


def prepare():
    p = pinned()
    images = []
    sheet = Image.new('RGB', (1600, 410 * ((len(p['records']) + 3) // 4)), '#eee9df')
    draw = ImageDraw.Draw(sheet)
    for n, c in enumerate(p['records']):
        raw, receipt = fetch(c['image_url'], ORIGINALS / (c['key'] + '.jpg'))
        with Image.open(io.BytesIO(raw)) as source:
            assert source.width * source.height < 40_000_000
            pic = ImageOps.exif_transpose(source).convert('RGB')
            result = None
            for edge in (1200, 1000, 843, 700, 600):
                pic.thumbnail((edge, edge), Image.Resampling.LANCZOS)
                for quality in (90, 85, 80, 75, 70, 65, 60):
                    out = io.BytesIO()
                    pic.save(out, 'JPEG', quality=quality, optimize=True, progressive=True)
                    if out.tell() <= 100000:
                        result = out.getvalue()
                        break
                if result:
                    break
            assert result
            digest = sha(result)
            path = '/assets/artworks/imported/' + CAMPAIGN + '/' + c['key'] + '-' + digest[:16] + '.jpg'
            save(ROOT / 'apps/web/public' / path.lstrip('/'), result)
            images.append({'key': c['key'], 'media_id': uid('media/' + c['key'] + '/' + digest), 'path': path,
                'sha256': digest, 'bytes': len(result), 'width': pic.width, 'height': pic.height, 'download': receipt})
            with Image.open(io.BytesIO(result)) as preview:
                preview.thumbnail((375, 330))
                x, y = (n % 4) * 400, (n // 4) * 410
                sheet.paste(preview, (x + (400-preview.width)//2, y))
                draw.multiline_text((x+8,y+335), f'{n+1}. {c["key"]}\n{c["title"][:48]}\n{c["date_display"]} | {c["country"]}', fill='black')
        print('Prepared', c['key'], len(result), flush=True)
    save(RUN / 'images.json', images)
    sheet.save('/tmp/artline-islamic-world-contact.jpg', quality=94)


def backup():
    pinned()
    BACKUP.mkdir(parents=True, exist_ok=True)
    dump = BACKUP / 'local-before.dump'
    if not dump.exists():
        temporary = BACKUP / 'local-before.incomplete'
        subprocess.run(['pg_dump', '-h', 'localhost', '-d', 'artline', '-Fc', '-f', str(temporary)], check=True)
        subprocess.run(['pg_restore', '--list', str(temporary)], check=True, stdout=subprocess.DEVNULL)
        temporary.rename(dump)
    subprocess.run(['pg_restore', '--list', str(dump)], check=True, stdout=subprocess.DEVNULL)
    save(BACKUP / 'plan.json', (RUN / 'plan.json').read_bytes())
    save(RUN / 'backup.json', {'path': str(dump), 'sha256': sha(dump.read_bytes()), 'bytes': dump.stat().st_size})
    print('Recovery dump validated:', dump.stat().st_size)


def insert(db, table, values):
    db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),
        sql.SQL(',').join(map(sql.Identifier, values)), sql.SQL(',').join(sql.Placeholder() for _ in values)), list(values.values()))


def verify_rows(db, p, images):
    rows = db.execute('''SELECT a.id::text,a.title,a.status,a.published_at,a.unlinked_creator_label,a.work_type,
      a.creation_year_start,a.creation_year_end,a.date_display,a.primary_media_id::text,a.research_candidate,
      m.storage_path,m.byte_size,m.checksum_sha256,m.rights_status,artline_has_selection_evidence(a.id) selected,
      (SELECT count(*) FROM artwork_artists aa WHERE aa.artwork_id=a.id) artists,
      (SELECT count(*) FROM artwork_location_assertions la WHERE la.artwork_id=a.id AND claim_type='display') displays,
      (SELECT count(*) FROM media_rights_evidence e WHERE e.media_id=m.id) rights,
      ARRAY(SELECT p.country_code::text FROM artwork_places ap JOIN places p ON p.id=ap.place_id WHERE ap.artwork_id=a.id) countries
      FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',
      ([c['artwork_id'] for c in p['records']],)).fetchall()
    assert len(rows) == len(p['records'])
    for c in p['records']:
        r = next(r for r in rows if r['id'] == c['artwork_id'])
        im = images[c['key']]
        assert r['status'] == 'review' and r['published_at'] is None and r['research_candidate']
        assert r['selected'] and r['displays'] == 0 and r['artists'] == int(bool(c.get('artist_id'))) and r['rights'] == 1
        assert r['countries'] == ([c['country']] if c['country'] else []) and r['unlinked_creator_label'] == c['maker']
        assert (r['work_type'], r['date_display'], r['creation_year_start'], r['creation_year_end']) == (c['type'], c['date_display'], c['lo'], c['hi'])
        assert r['primary_media_id'] == im['media_id'] and r['checksum_sha256'] == im['sha256']
        assert r['byte_size'] == im['bytes'] <= 100000 and r['rights_status'] == c.get('rights_status', 'cc0')
        if c.get('artist_id'):
            assert db.execute("SELECT 1 FROM artwork_artists WHERE artwork_id=%s AND artist_id=%s AND attribution_role='primary'", (c['artwork_id'], c['artist_id'])).fetchone()
    return rows


def apply():
    p = pinned()
    if (RUN / 'applied.json').exists():
        verify()
        return
    images = {im['key']: im for im in load('images.json')}
    qa, recovery = load('visual-review.json'), load('backup.json')
    assert qa['approved'] and qa['plan_sha256'] == load('plan-pin.json')['sha256']
    assert qa['images_sha256'] == sha((RUN / 'images.json').read_bytes()) and sorted(qa['keys']) == sorted(images)
    assert sha(Path(recovery['path']).read_bytes()) == recovery['sha256']
    for im in images.values():
        raw = (ROOT / 'apps/web/public' / im['path'].lstrip('/')).read_bytes()
        assert sha(raw) == im['sha256'] and len(raw) == im['bytes'] <= 100000
    with connect(False) as db, db.transaction():
        assert db.execute('SELECT 1 FROM editor_accounts WHERE user_id=%s AND is_active', (ACTOR,)).fetchone(), 'Active local review account required'
        db.execute('SELECT pg_advisory_xact_lock(559220260915)')
        db.execute('SELECT pg_advisory_xact_lock(20250907001)')
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute('LOCK TABLE artworks,external_identifiers IN SHARE ROW EXCLUSIVE MODE')
        for c in p['records']:
            assert not duplicate(db, c), 'Accession appeared after selection'
        for institution in p.get('institutions_to_create', []):
            assert not db.execute('SELECT 1 FROM institutions WHERE slug=%s OR normalized_name=%s', (institution['slug'], institution['normalized_name'])).fetchone()
            insert(db, 'institutions', institution)
        for artist in p.get('artist_preimages', []):
            assert db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=%s', (artist['record']['id'],)).fetchone() == artist
        for collection in p.get('collection_preimages', []):
            current = db.execute('SELECT to_jsonb(c) record FROM curated_collections c WHERE id=%s FOR UPDATE', (collection['record']['id'],)).fetchone()
            assert current == {'record': collection['record']}, 'Selected collection changed after planning'
            assert db.execute('SELECT COALESCE(max(position),0) n FROM curated_collection_items WHERE collection_id=%s', (collection['record']['id'],)).fetchone()['n'] == collection['max_position']
        countries = db.execute('SELECT to_jsonb(c) record FROM countries c WHERE code=ANY(%s) ORDER BY code', (list(COUNTRIES),)).fetchall()
        assert countries == p['country_preimages']
        save(BACKUP / 'locked-preimages.json', {'countries': countries, 'new_artwork_ids': [c['artwork_id'] for c in p['records']],
            'migration': MIGRATION, 'migration_sha256': sha((ROOT/'apps/server/db/migrations'/MIGRATION).read_bytes())})
        if not db.execute('SELECT 1 FROM schema_migrations WHERE filename=%s', (MIGRATION,)).fetchone():
            db.execute((ROOT/'apps/server/db/migrations'/MIGRATION).read_text())
            insert(db, 'schema_migrations', {'filename': MIGRATION})
        existing = {r['record']['code'] for r in countries}
        for code, (name, region) in COUNTRIES.items():
            if code not in existing:
                insert(db, 'countries', {'code': code, 'name': name, 'region_code': region})
            place = p.get('places', {}).get(code)
            if place:
                current = db.execute('SELECT to_jsonb(p) record FROM places p WHERE id=%s', (place['id'],)).fetchone()
                assert current and current['record'] == place, 'Selected origin place changed after planning'
            else:
                insert(db, 'places', {'id': uid('place/'+code), 'name': name, 'normalized_name': norm(name), 'country_code': code})
        sources = {}
        for key, provider in PROVIDERS.items():
            sid = uid('source/'+key)
            sources[key] = sid
            insert(db, 'sources', {'id': sid, 'slug': CAMPAIGN+'-'+key, 'name': SOURCE_LABEL+' — '+provider['name'],
                'source_type': provider.get('source_type', 'museum_api'), 'base_url': provider['api'], 'terms_url': provider['policy']})
        for c in p['records']:
            im, provider, sid = images[c['key']], PROVIDERS[c['provider']], sources[c['provider']]
            checked = c['capture']['at']
            credit = provider['name'] + '; ' + c['credit']
            license_label, license_url = c.get('license_label', 'CC0 1.0'), c.get('license_url', CC0)
            insert(db, 'media_assets', {'id': im['media_id'], 'storage_kind': 'local', 'storage_path': im['path'], 'source_page_url': c.get('image_page_url', c['url']),
                'provider_name': provider['name'], 'mime_type': 'image/jpeg', 'width': im['width'], 'height': im['height'], 'byte_size': im['bytes'],
                'checksum_sha256': im['sha256'], 'alt_text': c['title'] + ' — ' + c['reason'], 'rights_status': c.get('rights_status', 'cc0'),
                'license_label': license_label, 'license_url': license_url, 'creator_credit': credit,
                'attribution_text': c['title'] + '. ' + credit + '. ' + license_label + '. Full-frame resize and JPEG compression.',
                'retrieved_at': im['download']['at'], 'verified_at': qa['at'], 'verified_by': ACTOR})
            insert(db, 'media_rights_evidence', {'media_id': im['media_id'], 'source_id': sid, 'source_record_id': c['object_id'],
                'source_checksum': sha(encode(c['object'])), 'source_image_url': c['image_url'], 'policy_url': provider['policy'],
                'rights_basis': c.get('rights_basis', 'Exact museum primary image; explicit CC0/public-domain designation and museum open-access policy.'),
                'adapter_version': CAMPAIGN, 'checked_at': checked, 'evidence_json': Jsonb({'object': c['object'], 'capture': c['capture'], 'download': im['download'], 'policy': p['policies'][c['provider']]})})
            insert(db, 'artworks', {'id': c['artwork_id'], 'slug': c['slug'], 'title': c['title'], 'normalized_title': norm(c['title']),
                'date_display': c['date_display'], 'creation_year_start': c['lo'], 'creation_year_end': c['hi'], 'date_precision': c['precision'],
                'work_type': c['type'], 'medium_text': c['medium'], 'dimensions_text': c['dimensions'], 'creation_place_display': c['place_display'],
                'current_institution_id': c['institution_id'], 'accession_number': c['accession'], 'primary_media_id': im['media_id'],
                'cultural_context': c['culture'] or None, 'unlinked_creator_label': c['maker'], 'status': 'review', 'research_candidate': True,
                'created_by': ACTOR, 'updated_by': ACTOR})
            if c.get('artist_id'):
                insert(db, 'artwork_artists', {'artwork_id': c['artwork_id'], 'artist_id': c['artist_id'], 'attribution_role': 'primary',
                    'attribution_note': 'Named creator in the preserved source record. ' + c['url']})
            if c['country']:
                insert(db, 'artwork_places', {'artwork_id': c['artwork_id'], 'place_id': p.get('places', {}).get(c['country'], {}).get('id', uid('place/'+c['country'])), 'relationship_type': 'created',
                    'note': c.get('geography_note', 'Country-level object origin from the museum; no maker nationality inferred.')+' Source wording: '+c['place_display']+'. '+c['url']})
            insert(db, 'artwork_media', {'artwork_id': c['artwork_id'], 'media_id': im['media_id'], 'sort_order': 0, 'view_label': c.get('view_label', 'Museum primary reproduction')})
            insert(db, 'external_identifiers', {'entity_type': 'artwork', 'entity_id': c['artwork_id'], 'scheme': c['provider']+'-object',
                'external_id': c['object_id'], 'canonical_url': c['url'], 'source_id': sid, 'retrieved_at': checked})
            insert(db, 'artwork_location_assertions', {'artwork_id': c['artwork_id'], 'claim_type': 'holding', 'institution_id': c['institution_id'],
                'context': 'collection', 'source_id': sid, 'source_url': c['url'], 'evidence_note': 'Museum collection object, accession '+c['accession']+'. Holding only; no display claim. ' + c.get('holding_note', ''),
                'checked_at': checked, 'review_state': 'accepted'})
            insert(db, 'citations', {'entity_type': 'artwork', 'entity_id': c['artwork_id'], 'source_id': sid, 'field_name': 'official_object_identity',
                'source_record_id': c['object_id'], 'source_url': c['url'], 'evidence_note': json.dumps({'selection_reason': c['reason'],
                    'source_object': c['object'], 'capture': c['capture'], 'plan_sha256': load('plan-pin.json')['sha256'],
                    'scope': c.get('scope_note', 'One parent accession, including both sides where supplied. Maker retained at object level; no invented biography. Modern countries describe object origin, not historic citizenship.')}, ensure_ascii=False),
                'retrieved_at': checked, 'created_by': ACTOR})
        # Optional, explicitly pinned editorial choices. Owner selections remain
        # distinct from a museum's own highlight designation.
        for selection in p.get('curated_items', []):
            c = next(c for c in p['records'] if c['artwork_id'] == selection['artwork_id'])
            collection = next(x['record'] for x in p['collection_preimages'] if x['record']['id'] == selection['collection_id'])
            if collection['curator_kind'] == 'museum':
                assert c['object'].get('is_highlight') is True
            insert(db, 'curated_collection_items', {**selection, 'source_id': sources[c['provider']], 'source_url': c['url'], 'checked_at': c['capture']['at']})
        for collection in p.get('collection_preimages', []):
            db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s', (collection['record']['id'],))
        verify_rows(db, p, images)
    save(RUN/'applied.json', {'at': now(), 'target': 'local', 'works': len(p['records']), 'plan_sha256': load('plan-pin.json')['sha256'], 'review_only': True})
    verify()


def verify():
    p = pinned()
    images = {im['key']: im for im in load('images.json')}
    for im in images.values():
        raw = (ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        assert sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
        with Image.open(io.BytesIO(raw)) as pic:
            assert pic.size==(im['width'],im['height'])
            pic.verify()
    with connect() as db:
        rows = verify_rows(db, p, images)
    result = {'at': now(), 'target': 'local', 'works': len(rows), 'max_image_bytes': max(i['bytes'] for i in images.values()),
        'records': rows, 'review_only': True, 'new_display_claims': 0, 'new_artist_profiles': 0}
    if not (RUN/'verification.json').exists():
        save(RUN/'verification.json', result)
    print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['discover','plan','prepare','backup','apply','verify'])
    globals()[parser.parse_args().phase]()
