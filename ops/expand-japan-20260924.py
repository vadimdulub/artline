#!/usr/bin/env python3
"""Bounded Cleveland Japanese-art expansion; local review only, no publication.

Phases separate read-only planning, selected-image preparation, and a single
atomic import. Immutable source captures and a pinned plan precede downloads.
"""
import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import time
import unicodedata
import uuid
from urllib.parse import unquote, urlparse

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
import requests
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/japan-expansion-20260924'
DATA = Path('/Users/vadimdulub/Library/Application Support/Artline')
BACKUP = DATA / 'backups/japan-expansion-20260924'
ORIGINALS = DATA / 'source-images/japan-expansion-20260924'
SOURCE = 'japan-cleveland-20260924'
CAMPAIGN = 'japan-expansion-20260924'
ACTOR = 'local-european-research'
API = 'https://openaccess-api.clevelandart.org/api/artworks/'
POLICY = 'https://www.clevelandart.org/open-access'
CC0 = 'https://creativecommons.org/publicdomain/zero/1.0/'
SCHEME = 'european-cleveland-cleveland-museum-of-art-object'
SCHEMES = [SCHEME, 'cleveland-object']
CAP = 60
EISHI_AUTHORITY = 'https://www.getty.edu/vow/ULANFullDisplay?subjectid=500121365'


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def save(path, value):
    raw = value if isinstance(value, bytes) else encode(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('Immutable evidence differs: ' + str(path))
    else:
        path.write_bytes(raw)


def load(name):
    return json.loads((RUN / name).read_bytes())


def norm(value):
    text = ''.join(c for c in unicodedata.normalize('NFKD', str(value or '').casefold()) if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[^\W_]+', text))


def uid(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/' + CAMPAIGN + '/' + key))


def connect(readonly=True):
    return psycopg.connect('postgresql://localhost/artline', autocommit=True, row_factory=dict_row,
        options='-c timezone=UTC -c statement_timeout=120000' + (' -c default_transaction_read_only=on' if readonly else ''))


def fetch(url, path, params=None):
    receipt = path.with_suffix(path.suffix + '.receipt.json')
    if path.exists():
        raw = path.read_bytes()
        info = json.loads(receipt.read_bytes())
        assert sha(raw) == info['sha256']
        return raw, info
    response = requests.get(url, params=params, timeout=(15, 60),
        headers={'User-Agent': 'Artline selected Japanese museum artwork research'})
    response.raise_for_status()
    raw = response.content
    info = {'url': response.url, 'at': now(), 'sha256': sha(raw), 'bytes': len(raw), 'status': response.status_code}
    save(path, raw)
    save(receipt, info)
    return raw, info


def source_facts(o):
    """Reject ambiguous ownership, maker, dating, type, and image identities."""
    if o.get('department') != 'Japanese Art' or not any('Japan' in v for v in o.get('culture', [])):
        raise ValueError('Not museum-classified Japanese art')
    if o.get('legal_status') != 'accessioned' or o.get('on_loan') is not False:
        raise ValueError('Accessioned museum ownership not established')
    if o.get('record_type') != 'object' or o.get('cover_accession_number'):
        raise ValueError('Multipart object needs separate review')
    makers = o.get('creators') or []
    if len(makers) != 1 or makers[0].get('role') != 'artist':
        raise ValueError('Requires a single unqualified named visual creator')
    maker = makers[0]
    name = re.split(r'\s*\(', maker.get('description') or '', maxsplit=1)[0].strip()
    if maker.get('qualifier') or maker.get('extent') or not isinstance(maker.get('id'), int):
        raise ValueError('Qualified or unidentified creator')
    if not name or re.search(r'unknown|anonymous|workshop|school of|attributed|after ', name, re.I):
        raise ValueError('Not a named unqualified creator')
    if 'Japanese' not in maker.get('description', ''):
        raise ValueError('Creator Japanese context not explicit')
    lo, hi, text = o.get('creation_date_earliest'), o.get('creation_date_latest'), o.get('creation_date') or ''
    if type(lo) is not int or type(hi) is not int or not 1000 <= lo <= hi <= 1970:
        raise ValueError('Unknown creation interval or interval outside scope')
    if not text.strip() or re.search(r'\b(undated|unknown|before|after|possibly|or later|or earlier)\b|\?', text, re.I):
        raise ValueError('Source date needs editorial review')
    # Century/decade labels must overlap the museum's numeric interval. Do not
    # silently favor structured dates when the source's displayed date conflicts.
    periods = [int(v) for v in re.findall(r'\b(\d{4})s\b', text)]
    if periods and (max(periods) > hi or min(v + (99 if v % 100 == 0 else 9) for v in periods) < lo):
        raise ValueError('Museum displayed date conflicts with its numeric interval')
    birth, death = maker.get('birth_year') or '', maker.get('death_year') or ''
    if re.fullmatch(r'\d{4}', birth) and re.fullmatch(r'\d{4}', death) and hi == int(death) and lo in (int(birth), int(birth) + 15):
        raise ValueError('Possible lifespan used as artwork date')
    typ = {'Painting': 'painting', 'Print': 'print', 'Drawing': 'drawing'}.get(o.get('type'))
    if not typ:
        raise ValueError('Unselected object type')
    if typ == 'painting' and re.fullmatch(r'\d{4}', death) and lo > int(death):
        raise ValueError('Museum painting date starts after the named creator died')
    if o.get('share_license_status') != 'CC0' or o.get('copyright') or o.get('rights_and_reproductions'):
        raise ValueError('Image CC0 evidence absent or conflicting')
    image = (o.get('images') or {}).get('web') or {}
    url, accession = image.get('url') or '', o.get('accession_number') or ''
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname != 'openaccess-cdn.clevelandart.org' or unquote(parsed.path) != '/' + accession + '/' + accession + '_web.jpg':
        raise ValueError('Exact object image mapping absent')
    page = urlparse(o.get('url') or '')
    if page.scheme != 'https' or page.hostname not in ('clevelandart.org', 'www.clevelandart.org') or unquote(page.path) != '/art/' + accession:
        raise ValueError('Exact accession page mapping absent')
    approx = bool(re.search(r'\bc\.|\bca\.|circa|early|mid|late|about', text, re.I))
    precision = ('circa' if lo == hi else 'circa_range') if approx else ('exact' if lo == hi else 'range')
    return {'object_id': str(o['id']), 'name': name, 'maker': maker, 'title': o['title'], 'accession': accession,
        'work_type': typ, 'lo': lo, 'hi': hi, 'date_display': text, 'date_precision': precision, 'url': o['url'], 'image_url': url}


def totals(db):
    return db.execute("""SELECT count(DISTINCT a.id) artists,count(DISTINCT w.id) artworks,
      count(DISTINCT w.id) FILTER(WHERE w.creation_year_end<=1970) dated_by_1970,
      count(DISTINCT w.id) FILTER(WHERE w.primary_media_id IS NOT NULL) with_images
      FROM artists a JOIN artist_countries ac ON ac.artist_id=a.id AND ac.country_code='JP'
      LEFT JOIN artwork_artists aa ON aa.artist_id=a.id LEFT JOIN artworks w ON w.id=aa.artwork_id AND w.status<>'archived'
      WHERE a.status<>'archived'""").fetchone()


def discover():
    # Only three bounded pages: never download a complete collection or images here.
    pages = []
    for typ, skip, limit in [('Painting', 0, 100), ('Painting', 100, 100), ('Print', 0, 60)]:
        raw, receipt = fetch(API, RUN / 'captures' / f'{typ}-{skip}.json',
            {'department': 'Japanese Art', 'type': typ, 'cc0': 1, 'has_image': 1, 'skip': skip, 'limit': limit})
        data = json.loads(raw)
        pages.append({'path': f'captures/{typ}-{skip}.json', 'receipt': receipt, 'total': data['info']['total'], 'returned': len(data['data'])})
        print(typ, skip, len(data['data']), flush=True)
    _, policy = fetch(POLICY, RUN / 'captures/open-access.html')
    save(RUN / 'discovery.json', {'pages': pages, 'policy': policy, 'bound': '200 painting records and 60 print records; no pagination beyond this bound.'})


def plan():
    discovery = load('discovery.json')
    objects, held = {}, []
    for page in discovery['pages']:
        raw = (RUN / page['path']).read_bytes()
        assert sha(raw) == page['receipt']['sha256']
        for o in json.loads(raw)['data']:
            if o['id'] in objects:
                assert objects[o['id']]['object'] == o
            objects[o['id']] = {'object': o, 'capture': page}
    candidates = []
    for item in objects.values():
        try:
            candidates.append({**source_facts(item['object']), **item})
        except ValueError as error:
            held.append({'object_id': str(item['object']['id']), 'title': item['object']['title'], 'reason': str(error)})
    with connect() as db:
        before = totals(db)
        institution = db.execute("SELECT to_jsonb(i) record FROM institutions i WHERE slug='cleveland-museum-of-art' AND status<>'archived'").fetchone()['record']
        # Artist identities are small; artwork reads below are institution/artist/ID scoped.
        people = db.execute("""SELECT a.id::text,a.display_name,a.slug,a.birth_year,a.death_year,a.status,
          ARRAY(SELECT alias FROM artist_aliases al WHERE al.artist_id=a.id) aliases,
          ARRAY(SELECT country_code FROM artist_countries ac WHERE ac.artist_id=a.id) countries
          FROM artists a""").fetchall()
        names = collections.defaultdict(dict)
        reordered_names = collections.defaultdict(dict)
        for person in people:
            for name in [person['display_name'], *person['aliases']]:
                names[norm(name)][person['id']] = person
                if len(norm(name).split()) >= 2:
                    reordered_names[' '.join(sorted(norm(name).split()))][person['id']] = person
        # Getty ULAN 500121365 explicitly equates these two documented names.
        names[norm('Chōbunsai Eishi')].update(names[norm('Hosoda Eishi')])
        artists = {}
        for c in candidates:
            maker_id = str(c['maker']['id'])
            if maker_id in artists:
                continue
            if maker_id == '7625':
                artists[maker_id] = {'held': 'Existing Ike Taiga and Ike no Taiga profiles require reconciliation'}
                continue
            matches = list(names[norm(c['name'])].values())
            reordered = False
            if not matches:
                matches = list(reordered_names[' '.join(sorted(norm(c['name']).split()))].values())
                reordered = bool(matches)
            if len(matches) > 1 or (matches and matches[0]['status'] == 'archived'):
                artists[maker_id] = {'held': 'Artist identity ambiguity or country reconciliation needed'}
                continue
            old = matches[0] if matches else None
            if old:
                agreed = 0
                for key in ('birth_year', 'death_year'):
                    val = str(c['maker'].get(key) or '')
                    if re.fullmatch(r'\d{4}', val) and old[key] is not None:
                        if int(val) != old[key]:
                            agreed = -100
                            break
                        agreed += 1
                if agreed < (2 if reordered else 1):
                    artists[maker_id] = {'held': 'Museum life dates do not corroborate existing artist identity'}
                    continue
            artists[maker_id] = {'id': old['id'] if old else uid('artist/' + maker_id), 'new': not bool(old),
                'slug': old['slug'] if old else 'japan-cleveland-artist-' + maker_id, 'name': old['display_name'] if old else c['name'],
                'source_name': c['name'], 'source_maker_id': maker_id, 'source_maker': c['maker'], 'existing': old,
                'add_country': bool(old and 'JP' not in old['countries']),
                'match_basis': 'Getty ULAN 500121365 aliases plus agreeing life dates' if maker_id == '35477' else
                    ('Reordered full name plus both matching birth/death years' if reordered else 'Full museum name or alias plus corroborating life date' if old else 'New native museum creator identity')}
        artist_ids = [a['id'] for a in artists.values() if not a.get('held')]
        # Existing objects at this institution plus works by candidate artists.
        works = db.execute("""SELECT DISTINCT a.id::text,a.title,a.normalized_title,a.accession_number,
          a.current_institution_id::text,a.status,
          ARRAY(SELECT artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artist_ids,
          ARRAY(SELECT canonical_url FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) urls,
          ARRAY(SELECT external_id FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme=ANY(%s)) native_ids
          FROM artworks a WHERE a.current_institution_id=%s OR a.id IN
            (SELECT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[]))
          OR a.id IN (SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND
            ((scheme=ANY(%s) AND external_id=ANY(%s)) OR canonical_url=ANY(%s)))""",
            (SCHEMES, institution['id'], artist_ids, SCHEMES, [c['object_id'] for c in candidates], [c['url'] for c in candidates])).fetchall()
        eligible = []
        for c in candidates:
            a = artists[str(c['maker']['id'])]
            reason = a.get('held')
            if not reason:
                for w in works:
                    if c['object_id'] in w['native_ids'] or c['url'] in w['urls'] or (w['current_institution_id'] == institution['id'] and norm(w['accession_number']) == norm(c['accession'])):
                        reason = 'Museum physical object already represented'
                        break
                    if a['id'] in w['artist_ids'] and norm(w['title']) == norm(c['title']):
                        reason = 'Same creator and title require physical-object reconciliation'
                        break
            if reason:
                held.append({'object_id': c['object_id'], 'title': c['title'], 'reason': reason})
            else:
                eligible.append({**c, 'artist_id': a['id'], 'artist_key': str(c['maker']['id']), 'artwork_id': uid('artwork/' + c['object_id']), 'slug': 'japan-cleveland-' + c['object_id']})
        counts = collections.Counter(aid for w in works for aid in w['artist_ids'])
        groups = collections.defaultdict(list)
        for c in sorted(eligible, key=lambda c: (c['work_type'] != 'painting', c['lo'], c['object_id'])):
            groups[c['artist_key']].append(c)
        order = sorted(groups, key=lambda key: (counts[artists[key]['id']], artists[key]['name']))
        selected = []
        seen_titles = set()
        for n in range(3):
            for key in order:
                if n >= len(groups[key]):
                    continue
                c = groups[key][n]
                pair = (c['artist_id'], norm(c['title']))
                if len(selected) < CAP and pair not in seen_titles:
                    selected.append(c)
                    seen_titles.add(pair)
        chosen = {c['object_id'] for c in selected}
        held.extend({'object_id': c['object_id'], 'title': c['title'], 'reason': 'Outside bounded selection: at most three per creator and sixty total'} for c in eligible if c['object_id'] not in chosen)
        selected_artists = {c['artist_key']: artists[c['artist_key']] for c in selected}
        for key, a in selected_artists.items():
            works_for_artist = [c for c in selected if c['artist_key'] == key]
            a['first_work'] = min(c['lo'] for c in works_for_artist)
            a['last_work'] = max(c['hi'] for c in works_for_artist)
        existing_ids = [a['id'] for a in selected_artists.values() if not a['new']]
        preartists = db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY id', (existing_ids,)).fetchall()
        precountries = db.execute('SELECT to_jsonb(ac) record FROM artist_countries ac WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id,country_code,relationship_type', (existing_ids,)).fetchall()
    result = {'at': now(), 'before': before, 'institution': institution, 'artists': selected_artists, 'records': selected,
        'held': held, 'source_records_examined': len(objects), 'artist_preimages': preartists, 'country_preimages': precountries,
        'selection': 'Breadth-first: up to three unqualified museum objects per creator, prioritizing artists with less existing coverage; maximum sixty. Local review only. No current-display claims.'}
    save(RUN / 'plan.json', result)
    save(RUN / 'plan-pin.json', {'sha256': sha(encode(result)), 'works': len(selected)})
    print(json.dumps({'selected': len(selected), 'artists': len(selected_artists), 'new_artists': sum(a['new'] for a in selected_artists.values()), 'types': dict(collections.Counter(c['work_type'] for c in selected)), 'held': dict(collections.Counter(c['reason'] for c in held))}, indent=2))
    for c in selected:
        print(c['object_id'], c['name'], c['title'], c['date_display'], 'NEW ARTIST' if selected_artists[c['artist_key']]['new'] else '')


def pinned_plan():
    assert sha((RUN / 'plan.json').read_bytes()) == load('plan-pin.json')['sha256']
    return load('plan.json')


def compress(raw):
    with Image.open(io.BytesIO(raw)) as original:
        if original.width * original.height > 40_000_000:
            raise ValueError('Source image unexpectedly large')
        original.load()
        image = ImageOps.exif_transpose(original).convert('RGB')
        for edge in (1200, 1000, 843, 700, 600, 500, 400):
            image.thumbnail((edge, edge), Image.Resampling.LANCZOS)
            for quality in (90, 85, 80, 75, 70, 65, 60, 55):
                output = io.BytesIO()
                image.save(output, 'JPEG', quality=quality, optimize=True, progressive=True)
                if output.tell() <= 100000:
                    return output.getvalue(), image.width, image.height
    raise ValueError('Could not meet image limit')


def prepare():
    plan = pinned_plan()
    images = []
    for c in plan['records']:
        assert source_facts(c['object'])['image_url'] == c['image_url']
        raw, receipt = fetch(c['image_url'], ORIGINALS / (c['object_id'] + '.jpg'))
        out, width, height = compress(raw)
        digest = sha(out)
        path = f'/assets/artworks/imported/japan-expansion-20260924/{c["object_id"]}-{digest[:16]}.jpg'
        save(ROOT / 'apps/web/public' / path.lstrip('/'), out)
        images.append({'object_id': c['object_id'], 'artwork_id': c['artwork_id'], 'media_id': uid('media/' + c['object_id'] + '/' + digest),
            'path': path, 'sha256': digest, 'bytes': len(out), 'width': width, 'height': height, 'download': receipt})
        print('Prepared', len(images), '/', len(plan['records']), c['object_id'], flush=True)
    save(RUN / 'images.json', images)
    folder = Path('/tmp/artline-japan-20260924-qa')
    folder.mkdir(exist_ok=True)
    for start in range(0, len(images), 16):
        sheet = Image.new('RGB', (1600, 1400), '#eee9df')
        draw = ImageDraw.Draw(sheet)
        for n, im in enumerate(images[start:start + 16]):
            c = plan['records'][start + n]
            with Image.open(ROOT / 'apps/web/public' / im['path'].lstrip('/')) as pic:
                pic.thumbnail((380, 275))
                x, y = (n % 4) * 400, (n // 4) * 350
                sheet.paste(pic, (x + (400 - pic.width) // 2, y))
            draw.multiline_text((x + 8, y + 279), f'{start+n+1}. CMA {c["object_id"]}\n{c["name"]}\n{c["title"][:56]}\n{c["date_display"]}', fill='black')
        sheet.save(folder / f'sheet-{start//16+1}.jpg', quality=93)
    print('Contact sheets:', folder)


def backup():
    plan = pinned_plan()
    BACKUP.mkdir(parents=True, exist_ok=True)
    dump = BACKUP / 'local-before.dump'
    if not dump.exists():
        temporary = BACKUP / 'local-before.incomplete'
        subprocess.run(['pg_dump', '-h', 'localhost', '-d', 'artline', '-Fc', '-f', str(temporary)], check=True)
        subprocess.run(['pg_restore', '--list', str(temporary)], check=True, stdout=subprocess.DEVNULL)
        temporary.rename(dump)
    subprocess.run(['pg_restore', '--list', str(dump)], check=True, stdout=subprocess.DEVNULL)
    save(BACKUP / 'plan.json', (RUN / 'plan.json').read_bytes())
    save(BACKUP / 'selected-artist-preimages.json', plan['artist_preimages'])
    save(BACKUP / 'selected-country-preimages.json', plan['country_preimages'])
    if not (RUN / 'backup.json').exists():
        save(RUN / 'backup.json', {'at': now(), 'path': str(dump), 'bytes': dump.stat().st_size,
            'sha256': sha(dump.read_bytes()), 'plan_sha256': load('plan-pin.json')['sha256']})
    print('Validated local recovery dump', dump.stat().st_size, flush=True)


def insert(db, table, data):
    from psycopg import sql
    db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),
        sql.SQL(',').join(map(sql.Identifier, data)), sql.SQL(',').join(sql.Placeholder() for _ in data)), list(data.values()))


def artist_values(a):
    # Numeric birth/death fields are used only when supported by explicit source text;
    # uncertain and partial lives retain nulls and use documented works for the timeline.
    m = a['source_maker']
    description = m.get('description') or ''
    dates = {}
    for key in ('birth_year', 'death_year'):
        raw = str(m.get(key) or '')
        year = int(raw) if re.fullmatch(r'\d{4}', raw) and raw in description else None
        if year is not None and re.search(r'(after|before)\s*' + raw, description, re.I):
            year = None
        dates[key] = year
        field = key.removesuffix('_year')
        approx = year is not None and bool(re.search(r'(?:c\.|ca\.|about)\s*' + raw, description))
        dates[field + '_display'] = (('c. ' if approx else '') + raw) if year is not None else None
        dates[field + '_precision'] = ('circa' if approx else 'exact') if year is not None else None
    life = dates['birth_year'] is not None and dates['death_year'] is not None
    lo, hi = (dates['birth_year'], dates['death_year']) if life else (a['first_work'], a['last_work'])
    return {'id': a['id'], 'slug': a['slug'], 'display_name': a['name'], 'sort_name': a['name'], 'normalized_name': norm(a['name']),
        **dates, 'timeline_start_year': lo, 'timeline_end_year': hi, 'timeline_basis': 'life' if life else 'activity',
        'timeline_display': str(lo) + '–' + str(hi), 'active_start_year': None if life else lo, 'active_end_year': None if life else hi,
        'activity_display': None if life else f'Documented selected works: {lo}–{hi}', 'status': 'review', 'created_by': ACTOR, 'updated_by': ACTOR}


def apply():
    plan = pinned_plan()
    images = {x['object_id']: x for x in load('images.json')}
    qa = load('visual-review.json')
    assert qa['approved'] and qa['plan_sha256'] == load('plan-pin.json')['sha256']
    assert qa['images_sha256'] == sha((RUN / 'images.json').read_bytes())
    assert sorted(qa['reviewed_object_ids']) == sorted(images)
    recovery = load('backup.json')
    assert recovery['plan_sha256'] == load('plan-pin.json')['sha256']
    assert sha(Path(recovery['path']).read_bytes()) == recovery['sha256']
    for c in plan['records']:
        assert source_facts(c['object'])['title'] == c['title']
        im = images[c['object_id']]
        raw = (ROOT / 'apps/web/public' / im['path'].lstrip('/')).read_bytes()
        assert sha(raw) == im['sha256'] and len(raw) <= 100000
    if (RUN / 'applied.json').exists():
        verify()
        return
    with connect(False) as db, db.transaction():
        db.execute('SELECT pg_advisory_xact_lock(559220260915)')
        # Protect only the relevant catalogue tables against concurrent ingestion.
        db.execute('LOCK TABLE artists,artist_aliases,artworks,artwork_artists,external_identifiers IN SHARE ROW EXCLUSIVE MODE')
        oid = [c['object_id'] for c in plan['records']]
        urls = [c['url'] for c in plan['records']]
        assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND ((scheme=ANY(%s) AND external_id=ANY(%s)) OR canonical_url=ANY(%s)) LIMIT 1", (SCHEMES, oid, urls)).fetchone()
        assert not db.execute('SELECT 1 FROM artworks WHERE current_institution_id=%s AND accession_number=ANY(%s) LIMIT 1', (plan['institution']['id'], [c['accession'] for c in plan['records']])).fetchone()
        existing_ids = [a['id'] for a in plan['artists'].values() if not a['new']]
        current = db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY id', (existing_ids,)).fetchall()
        assert current == plan['artist_preimages'], 'Existing artist changed after planning'
        fresh_names = db.execute('SELECT display_name FROM artists UNION SELECT alias FROM artist_aliases').fetchall()
        name_set = {norm(x['display_name']) for x in fresh_names}
        for a in plan['artists'].values():
            if a['new']:
                assert norm(a['name']) not in name_set, 'New artist appeared after planning'
        countries = db.execute('SELECT to_jsonb(ac) record FROM artist_countries ac WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id,country_code,relationship_type', (existing_ids,)).fetchall()
        assert countries == plan['country_preimages']
        before = {'at': now(), 'artists': current, 'countries': countries, 'totals': totals(db), 'new_artwork_ids': [c['artwork_id'] for c in plan['records']], 'new_artist_ids': [a['id'] for a in plan['artists'].values() if a['new']]}
        preimage_path = BACKUP / ('locked-preimages-' + sha(encode(before))[:16] + '.json')
        save(preimage_path, before)
        insert(db, 'sources', {'slug': SOURCE, 'name': 'Selected Japanese artworks — Cleveland Museum of Art', 'source_type': 'museum_api', 'base_url': API, 'terms_url': POLICY})
        sid = db.execute('SELECT id FROM sources WHERE slug=%s', (SOURCE,)).fetchone()['id']
        for key, a in plan['artists'].items():
            sample = next(c for c in plan['records'] if c['artist_key'] == key)
            if a['new']:
                insert(db, 'artists', artist_values(a))
            if a['new'] or a['add_country']:
                insert(db, 'artist_countries', {'artist_id': a['id'], 'country_code': 'JP', 'relationship_type': 'cultural_affiliation', 'is_primary': False,
                    'note': 'Museum creator description explicitly says Japanese. Cultural affiliation; no modern citizenship inference. ' + sample['url']})
            if a['new']:
                insert(db, 'external_identifiers', {'entity_type': 'artist', 'entity_id': a['id'], 'scheme': 'cleveland-creator', 'external_id': key,
                    'canonical_url': sample['url'], 'source_id': sid, 'retrieved_at': sample['capture']['receipt']['at']})
            if a['new'] or a['add_country']:
                insert(db, 'citations', {'entity_type': 'artist', 'entity_id': a['id'], 'source_id': sid, 'field_name': 'museum_creator_identity',
                    'source_record_id': key, 'source_url': sample['url'], 'evidence_note': json.dumps({'maker': a['source_maker'], 'match_basis': a['match_basis'], 'new_profile': a['new'], 'capture': sample['capture']}, ensure_ascii=False),
                    'retrieved_at': sample['capture']['receipt']['at'], 'created_by': ACTOR})
        for c in plan['records']:
            im, o = images[c['object_id']], c['object']
            checked = c['capture']['receipt']['at']
            credit = c['name'] + '; The Cleveland Museum of Art; ' + (o.get('creditline') or '')
            if o.get('image_credit'):
                credit += '; ' + o['image_credit']
            insert(db, 'media_assets', {'id': im['media_id'], 'storage_kind': 'local', 'storage_path': im['path'], 'source_page_url': c['url'],
                'provider_name': 'The Cleveland Museum of Art', 'mime_type': 'image/jpeg', 'width': im['width'], 'height': im['height'],
                'byte_size': im['bytes'], 'checksum_sha256': im['sha256'], 'alt_text': c['title'] + ' — ' + c['name'], 'rights_status': 'cc0',
                'license_label': 'CC0 1.0', 'license_url': CC0, 'creator_credit': credit,
                'attribution_text': c['title'] + '. ' + credit + '. CC0 1.0. Full-frame resize and JPEG compression.',
                'retrieved_at': im['download']['at'], 'verified_at': qa['at'], 'verified_by': ACTOR})
            insert(db, 'media_rights_evidence', {'media_id': im['media_id'], 'source_id': sid, 'source_record_id': c['object_id'], 'source_checksum': sha(encode(o)),
                'source_image_url': c['image_url'], 'policy_url': POLICY, 'rights_basis': 'Exact accession image; museum share_license_status CC0; full-frame reproduction.',
                'adapter_version': CAMPAIGN, 'checked_at': checked, 'evidence_json': Jsonb({'source_object': o, 'capture': c['capture'], 'download': im['download'], 'policy': load('discovery.json')['policy']})})
            insert(db, 'artworks', {'id': c['artwork_id'], 'slug': c['slug'], 'title': c['title'], 'normalized_title': norm(c['title']),
                'date_display': c['date_display'], 'creation_year_start': c['lo'], 'creation_year_end': c['hi'], 'date_precision': c['date_precision'],
                'work_type': c['work_type'], 'medium_text': o.get('technique'), 'dimensions_text': o.get('measurements'),
                'current_institution_id': plan['institution']['id'], 'accession_number': c['accession'], 'primary_media_id': im['media_id'],
                'cultural_context': 'Japan', 'status': 'review', 'research_candidate': True, 'created_by': ACTOR, 'updated_by': ACTOR})
            insert(db, 'artwork_artists', {'artwork_id': c['artwork_id'], 'artist_id': c['artist_id'], 'attribution_role': 'primary',
                'attribution_note': 'Unqualified sole named artist in the official museum record; museum native creator identity retained.'})
            insert(db, 'artwork_media', {'artwork_id': c['artwork_id'], 'media_id': im['media_id'], 'sort_order': 0, 'view_label': 'Museum primary reproduction'})
            insert(db, 'external_identifiers', {'entity_type': 'artwork', 'entity_id': c['artwork_id'], 'scheme': SCHEME, 'external_id': c['object_id'],
                'canonical_url': c['url'], 'source_id': sid, 'retrieved_at': checked})
            insert(db, 'artwork_location_assertions', {'artwork_id': c['artwork_id'], 'claim_type': 'holding', 'institution_id': plan['institution']['id'],
                'context': 'collection', 'source_id': sid, 'source_url': c['url'], 'evidence_note': 'Official accessioned museum object; on_loan=false. Accession ' + c['accession'] + '. Holding only.',
                'checked_at': checked, 'review_state': 'accepted'})
            insert(db, 'citations', {'entity_type': 'artwork', 'entity_id': c['artwork_id'], 'source_id': sid, 'field_name': 'official_object_identity',
                'source_record_id': c['object_id'], 'source_url': c['url'], 'evidence_note': json.dumps({'object': o, 'capture': c['capture'], 'artist_match': plan['artists'][c['artist_key']]['match_basis'], 'name_authority': EISHI_AUTHORITY if c['artist_key']=='35477' else None, 'plan_sha256': load('plan-pin.json')['sha256'], 'review_only': True}, ensure_ascii=False),
                'retrieved_at': checked, 'created_by': ACTOR})
        checked = verify_rows(db, plan, images)
    save(RUN / 'applied.json', {'at': now(), 'target': 'local', 'works': len(checked), 'new_artists': sum(a['new'] for a in plan['artists'].values()), 'plan_sha256': load('plan-pin.json')['sha256'], 'preimage_path': str(preimage_path)})
    print('Committed local review artworks', len(checked))


def verify_rows(db, plan, images):
    ids = [c['artwork_id'] for c in plan['records']]
    rows = db.execute("""SELECT a.id::text,a.title,a.status,a.published_at,a.research_candidate,a.creation_year_start,a.creation_year_end,a.date_display,a.work_type,
        a.current_institution_id::text,a.accession_number,a.primary_media_id::text,m.checksum_sha256,m.byte_size,m.storage_path,m.rights_status,
        artline_has_selection_evidence(a.id) selected,
        ARRAY(SELECT artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artist_ids,
        (SELECT count(*) FROM artwork_location_assertions la WHERE la.artwork_id=a.id AND claim_type='display') displays,
        (SELECT count(*) FROM citations ci JOIN sources s ON s.id=ci.source_id WHERE ci.entity_id=a.id AND ci.entity_type='artwork' AND s.slug=%s) citations,
        (SELECT count(*) FROM media_rights_evidence e WHERE e.media_id=a.primary_media_id) rights_evidence
        FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id""", (SOURCE, ids)).fetchall()
    assert len(rows) == len(ids)
    byid = {r['id']: r for r in rows}
    for c in plan['records']:
        r, im = byid[c['artwork_id']], images[c['object_id']]
        assert r['status'] == 'review' and r['published_at'] is None and r['research_candidate']
        assert r['selected'] and r['displays'] == 0 and r['citations'] == r['rights_evidence'] == 1
        assert r['artist_ids'] == [c['artist_id']]
        assert (r['title'], r['creation_year_start'], r['creation_year_end'], r['date_display'], r['work_type']) == (c['title'], c['lo'], c['hi'], c['date_display'], c['work_type'])
        assert r['current_institution_id'] == plan['institution']['id'] and r['accession_number'] == c['accession']
        assert r['primary_media_id'] == im['media_id'] and r['checksum_sha256'] == im['sha256'] and r['byte_size'] <= 100000 and r['rights_status'] == 'cc0'
    existing_ids = [a['id'] for a in plan['artists'].values() if not a['new']]
    assert db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY id', (existing_ids,)).fetchall() == plan['artist_preimages']
    current_countries = db.execute('SELECT to_jsonb(ac) record FROM artist_countries ac WHERE artist_id=ANY(%s::uuid[])', (existing_ids,)).fetchall()
    assert all(row in current_countries for row in plan['country_preimages'])
    assert len(current_countries) == len(plan['country_preimages']) + sum(a['add_country'] for a in plan['artists'].values())
    newids = [a['id'] for a in plan['artists'].values() if a['new']]
    valid_artists = db.execute("SELECT count(*) n FROM artists a WHERE id=ANY(%s::uuid[]) AND status='review' AND published_at IS NULL AND EXISTS(SELECT 1 FROM artist_countries ac WHERE ac.artist_id=a.id AND country_code='JP')", (newids,)).fetchone()['n']
    assert valid_artists == len(newids)
    return rows


def verify():
    plan = pinned_plan()
    images = {x['object_id']: x for x in load('images.json')}
    for im in images.values():
        raw = (ROOT / 'apps/web/public' / im['path'].lstrip('/')).read_bytes()
        assert sha(raw) == im['sha256'] and len(raw) == im['bytes'] <= 100000
        with Image.open(io.BytesIO(raw)) as pic:
            assert pic.format == 'JPEG' and pic.size == (im['width'], im['height'])
            pic.verify()
    with connect() as db:
        rows = verify_rows(db, plan, images)
        after = totals(db)
    result = {'at': now(), 'target': 'local', 'before': plan['before'], 'after': after, 'works': len(rows),
        'new_artists': sum(a['new'] for a in plan['artists'].values()), 'existing_artists_linked_to_japan': sum(a['add_country'] for a in plan['artists'].values()), 'images': len(images), 'max_image_bytes': max(i['bytes'] for i in images.values()),
        'types': dict(collections.Counter(c['work_type'] for c in plan['records'])), 'review_only': True, 'new_display_claims': 0, 'existing_artist_preimages_unchanged': True,
        'records': rows, 'errors': []}
    if not (RUN / 'verification.json').exists():
        save(RUN / 'verification.json', result)
    fields = ['object_id', 'name', 'title', 'date_display', 'work_type', 'url', 'artwork_id', 'artist_id']
    with (RUN / 'added-artworks.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: c[k] for k in fields} for c in plan['records'])
    print(json.dumps({k: v for k, v in result.items() if k != 'records'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['discover', 'plan', 'prepare', 'backup', 'apply', 'verify'])
    globals()[parser.parse_args().phase]()
