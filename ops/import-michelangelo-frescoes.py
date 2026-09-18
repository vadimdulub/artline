#!/usr/bin/env python3
"""Bounded, evidence-backed Michelangelo import. Prepare, inspect, then apply.

Never updates an existing artwork or painter. New rows remain in review.
Immutable manifests, database identity guards, original image checksums and
conditional cloud uploads make interruptions resumable without replacements.
"""
import argparse
import base64
import hashlib
import importlib.util
import json
import uuid
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / 'docs/research/michelangelo-frescoes-20260913'
BACKUPS = Path('/Users/vadimdulub/Library/Application Support/Artline/backups/michelangelo-frescoes-20260913')
ARTIST = 'ec44f869-0330-4d4b-846d-76db55219128'
ACTOR = 'local-european-research'
VERSION = 'michelangelo-frescoes-v1'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


core = module('image_core', ROOT / 'ops/enrich-artwork-images.py')


def identity(value):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/research/michelangelo-frescoes/' + value))


def plain(value):
    return BeautifulSoup(value, 'html.parser').get_text(' ', strip=True)


def prepare():
    if (RUN / 'prepared.json').exists():
        print('Prepared immutable manifest already exists')
        return
    records = json.loads((RUN / 'researched-records.json').read_text())
    alternatives = {}
    for filename in ('alternate-images.json', 'alternate-images-2.json'):
        batch = json.loads((RUN / filename).read_text())
        for page in batch['data']['query']['pages'].values():
            if 'imageinfo' in page:
                alternatives[page['title']] = (page, batch['receipt'])
    choices = {
        'Q3955632': 'File:Michelangelo, Separation of the Earth from the Waters 00.jpg',
        'Q500242': 'File:Michelangelo, Creation of Adam 01.jpg',
        'Q567861': 'File:Last Judgement (Michelangelo).jpg',
        'Q2432043': 'File:Michelangelo, paolina, conversione di saulo 01.jpg',
    }
    fetcher = core.Fetcher(RUN / 'captures')
    fetcher.session.headers['User-Agent'] = 'Artline/1.0 (https://github.com/vadimdulub/artline; selected art research)'
    for record in records:
        qid = record['qid']
        if qid in choices:
            record['commons_page'], record['commons_receipt'] = alternatives[choices[qid]]
            record['image_info'] = record['commons_page']['imageinfo'][0]
        if qid == 'Q3696827':
            record['alternate_title'] = record['title']
            record['title'] = 'The Creation of the Sun, Moon and Plants'
        if qid in ('Q2432043', 'Q1886263'):
            record['first'], record['last'] = (1542, 1545) if qid == 'Q2432043' else (1545, 1550)
            record['date_basis'] = 'Individual fresco campaign documented by the Vatican Pauline Chapel history'
        info = record['image_info']
        meta = info['extmetadata']
        field = lambda key: meta.get(key, {}).get('value', '')
        label = field('LicenseShortName')
        assert not field('Restrictions'), 'Image has additional restrictions'
        assert (label == 'Public domain' and field('Copyrighted') == 'False') or label == 'CC BY 3.0'
        record['rights_status'] = 'public_domain' if label == 'Public domain' else 'cc_by'
        record['rights_cleared'] = True
        record['license_label'] = label
        record['license_url'] = 'https://creativecommons.org/publicdomain/mark/1.0/' if label == 'Public domain' else field('LicenseUrl')
        record['commons_creator_credit'] = field('Artist')
        record['commons_credit'] = field('Credit')
        record['creator_credit'] = plain(field('Artist'))
        assert record['creator_credit']
        record['attribution_text'] = f"Michelangelo. {record['title']}. Image credit: {record['creator_credit']}. Wikimedia Commons. {label} ({record['license_url']}). Resized and JPEG-compressed; composition preserved."
        original = BACKUPS / 'selected-originals' / (qid + '.image')
        receipt_path = RUN / 'image-receipts' / (qid + '.json')
        if original.exists():
            raw = original.read_bytes()
            receipt = json.loads(receipt_path.read_text())
            assert core.sha(raw) == receipt['sha256']
        else:
            raw, headers = fetcher.get(info['url'], 20_000_000)
            # Commons imageinfo returns a hexadecimal SHA-1 for this API.
            assert hashlib.sha1(raw).hexdigest() == info['sha1']
            assert len(raw) == info['size']
            receipt = {'url': info['url'], 'sha256': core.sha(raw), 'sha1': hashlib.sha1(raw).hexdigest(), 'bytes': len(raw), 'retrieved_at': core.now(), 'headers': headers}
            core.save_new(original, raw)
            core.save_new(receipt_path, receipt)
        assert hashlib.sha1(raw).hexdigest() == info['sha1']
        data, width, height, quality = core.compress(raw)
        digest = core.sha(data)
        path = f'/assets/artworks/imported/michelangelo/{qid.lower()}-{digest[:16]}.jpg'
        core.save_new(ROOT / 'apps/web/public' / path.lstrip('/'), data)
        record.update(artwork_id=identity(qid), media_id=identity(qid + '/image/' + digest),
                      slug='michelangelo-fresco-' + qid.lower(), path=path, sha256=digest,
                      bytes=len(data), width=width, height=height, quality=quality,
                      image_receipt=receipt, checked_at=core.now())
        print('Prepared', qid, record['title'], len(data), label, flush=True)
    core.save_new(RUN / 'prepared.json', records)
    sheet = Image.new('RGB', (1200, 1100), '#eee9df')
    draw = ImageDraw.Draw(sheet)
    for i, record in enumerate(records):
        im = Image.open(ROOT / 'apps/web/public' / record['path'].lstrip('/'))
        im.thumbnail((380, 225))
        x, y = (i % 3) * 400, (i // 3) * 275
        sheet.paste(im, (x + (400-im.width)//2, y))
        draw.text((x+8, y+230), record['qid']+' '+record['title'][:42], fill='black')
    sheet.save('/tmp/artline-michelangelo-contact-sheet.jpg')


def connect(cloud):
    access = module('db_access', str(Path(__file__).with_name('artline-db-access.py')))
    env = access.environment(cloud)
    db = psycopg.connect(host=env['PGHOST'], port=env['PGPORT'], dbname=env['PGDATABASE'],
                          user=env.get('PGUSER'), password=env.get('PGPASSWORD'),
                          connect_timeout=20, autocommit=True, row_factory=dict_row)
    db.execute("SET TIME ZONE 'UTC'")
    return db


def insert(db, table, values):
    # Identifiers here are exclusively this script's static literals.
    columns = ','.join(values)
    marks = ','.join(['%s'] * len(values))
    db.execute(f'INSERT INTO {table} ({columns}) VALUES ({marks})', list(values.values()))


def source(db, slug, name, kind, url):
    db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(slug) DO NOTHING',
               (identity('source/'+slug), slug, name, kind, url))
    row = db.execute('SELECT id,is_active FROM sources WHERE slug=%s', (slug,)).fetchone()
    assert row['is_active']
    return row['id']


def apply(target):
    records = json.loads((RUN / 'prepared.json').read_text())
    assert len(records) == 12 and len({r['qid'] for r in records}) == 12
    assert (RUN / 'visual-review.json').exists(), 'Inspect all twelve images before application'
    assert json.loads((RUN / 'visual-review.json').read_text())['manifest_sha256'] == core.sha((RUN / 'prepared.json').read_bytes())
    assert all(r['rights_cleared'] and r['first'] <= r['last'] <= 1970 for r in records)
    assert (BACKUPS / (target+'-before.json')).exists()
    if target == 'production':
        assert json.loads((BACKUPS / 'production-managed-backup.json').read_text())['status'] == 'SUCCESSFUL'
    # Upload before any database reference can become visible.
    bucket = core.storage.Client(project='artline-508319', credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    for record in records:
        data = (ROOT / 'apps/web/public' / record['path'].lstrip('/')).read_bytes()
        assert core.sha(data) == record['sha256'] and len(data) <= 100000
        blob = bucket.blob(record['path'].lstrip('/'))
        if not blob.exists():
            blob.metadata = {'sha256': record['sha256'], 'license': record['license_label'], 'wikidata': record['qid']}
            blob.cache_control = 'public,max-age=31536000,immutable'
            blob.upload_from_string(data, content_type='image/jpeg', if_generation_match=0)
        blob.reload()
        assert blob.size == len(data)
        assert blob.md5_hash == base64.b64encode(hashlib.md5(data).digest()).decode()
    with connect(target == 'production') as db, db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute("SET LOCAL statement_timeout='45s'")
        db.execute('SELECT pg_advisory_xact_lock(%s)', (559220260913,))
        artist = db.execute("SELECT a.id FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata' AND e.external_id='Q5592' WHERE a.slug='michelangelo-q5592' FOR SHARE OF a").fetchone()
        assert artist and str(artist['id']) == ARTIST
        assert db.execute('SELECT 1 FROM editor_accounts WHERE user_id=%s AND is_active', (ACTOR,)).fetchone()
        vatican = source(db, 'michelangelo-vatican-frescoes', 'Vatican Museums and Apostolic Palace — Michelangelo frescoes', 'collection_page', 'https://www.museivaticani.va/')
        wiki = source(db, 'michelangelo-wikidata-authority', 'Wikidata — Michelangelo fresco identities', 'authority_data', 'https://www.wikidata.org/')
        commons = source(db, 'michelangelo-commons-images', 'Wikimedia Commons — selected Michelangelo fresco images', 'collection_page', 'https://commons.wikimedia.org/')
        institutions = {}
        for slug, name, url in [('sistine-chapel', 'Sistine Chapel', records[0]['official_evidence'][0]['url']), ('pauline-chapel', 'Pauline Chapel', records[-1]['official_evidence'][0]['url'])]:
            existing = db.execute('SELECT id FROM institutions WHERE slug=%s', (slug,)).fetchone()
            if existing:
                institutions[slug] = existing['id']
            else:
                iid = identity('institution/'+slug)
                insert(db, 'institutions', dict(id=iid, slug=slug, name=name, normalized_name=name.lower(), website_url=url, kind='historic_site', status='review', description='Chapel in the Apostolic Palace, Vatican City. Holdings documented by Vatican sources; current visitor access is not asserted.'))
                institutions[slug] = iid
            db.execute('INSERT INTO source_institutions(source_id,institution_id) VALUES(%s,%s) ON CONFLICT DO NOTHING', (vatican, institutions[slug]))
        added = 0
        for r in records:
            found = db.execute("SELECT a.id,a.primary_media_id,a.status FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme='wikidata' AND e.external_id=%s", (r['qid'],)).fetchone()
            if found:
                assert str(found['id']) == r['artwork_id'] and str(found['primary_media_id']) == r['media_id'] and found['status'] == 'review', 'Existing identity must be reviewed instead of replaced'
                continue
            # This creator's bounded collection is also checked for title duplicates.
            duplicate = db.execute('SELECT a.id FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s AND a.normalized_title=ANY(%s)', (ARTIST, [r['title'].lower(), r.get('alternate_title', r['title']).lower()])).fetchone()
            assert duplicate is None, 'Existing title requires manual identity review'
            iid = institutions[r['institution_slug']]
            mid, aid, checked = r['media_id'], r['artwork_id'], r['checked_at']
            page = r['image_info']['descriptionurl']
            insert(db, 'media_assets', dict(id=mid, storage_kind='local', storage_path=r['path'], source_page_url=page, provider_name='Wikimedia Commons', mime_type='image/jpeg', width=r['width'], height=r['height'], byte_size=r['bytes'], checksum_sha256=r['sha256'], alt_text=r['title']+' — Michelangelo', rights_status=r['rights_status'], license_label=r['license_label'], license_url=r['license_url'], creator_credit=r['creator_credit'], attribution_text=r['attribution_text'], retrieved_at=r['image_receipt']['retrieved_at'], verified_at=checked, verified_by=ACTOR))
            insert(db, 'media_rights_evidence', dict(media_id=mid, source_id=commons, source_record_id=r['commons_page']['title'], source_checksum=r['commons_receipt']['sha256'], source_image_url=r['image_info']['url'], policy_url=r['license_url'], rights_basis='Per-file Commons licence, original SHA-1 match, and visual fresco identity review; photographer attribution preserved.', adapter_version=VERSION, checked_at=checked, evidence_json=Jsonb({'commons_page':r['commons_page'], 'commons_receipt':r['commons_receipt'], 'download':r['image_receipt'], 'attribution':r['attribution_text'], 'derivative_sha256':r['sha256']})))
            date_display = f"{r['first']}–{r['last']}" + (' (ceiling campaign)' if r['first'] == 1508 else '')
            description = f"Fresco by Michelangelo in the {r['location']}. {r['date_basis']}.\n\nResearch record supported by Vatican documentation and Wikidata; awaiting editorial review."
            insert(db, 'artworks', dict(id=aid, slug=r['slug'], title=r['title'], alternate_title=r.get('alternate_title'), normalized_title=r['title'].lower(), date_display=date_display, creation_year_start=r['first'], creation_year_end=r['last'], date_precision='range', work_type='fresco', medium_text='Fresco', description_md=description, creation_place_display=r['location'], current_institution_id=iid, current_location_text=r['location'], location_checked_at=checked, primary_media_id=mid, status='review', created_by=ACTOR, updated_by=ACTOR))
            insert(db, 'artwork_artists', dict(artwork_id=aid, artist_id=ARTIST, attribution_role='primary', attribution_note='Michelangelo Buonarroti (Wikidata Q5592); Vatican attribution corroborated by artwork authority identity.'))
            insert(db, 'artwork_media', dict(artwork_id=aid, media_id=mid, sort_order=0, view_label='Fresco'))
            insert(db, 'external_identifiers', dict(entity_type='artwork', entity_id=aid, scheme='wikidata', external_id=r['qid'], canonical_url='https://www.wikidata.org/wiki/'+r['qid'], source_id=wiki, retrieved_at=r['entity_receipt']['retrieved_at']))
            for evidence in r['official_evidence']:
                insert(db, 'citations', dict(entity_type='artwork', entity_id=aid, field_name='identity_dates_location', source_id=vatican, source_record_id=r['qid'], source_url=evidence['url'], evidence_note=r['date_basis']+'. Official chapel documentation supports creator, fresco identity and location. Capture SHA-256: '+evidence['sha256'], retrieved_at=evidence['retrieved_at'], created_by=ACTOR))
            insert(db, 'citations', dict(entity_type='artwork', entity_id=aid, field_name='external_identity', source_id=wiki, source_record_id=r['qid'], source_url='https://www.wikidata.org/wiki/'+r['qid'], evidence_note='Creator P170=Q5592. Wikidata entity capture SHA-256: '+r['entity_receipt']['sha256'], retrieved_at=r['entity_receipt']['retrieved_at'], created_by=ACTOR))
            insert(db, 'artwork_location_assertions', dict(artwork_id=aid, claim_type='holding', institution_id=iid, context='collection', source_id=vatican, source_url=r['official_evidence'][0]['url'], evidence_note='Vatican documentation identifies this fresco as part of '+r['location']+'. This is a holding/location assertion, not a current on-view or visitor-access claim.', checked_at=checked, review_state='accepted'))
            added += 1
        rows = db.execute('SELECT id,primary_media_id,status,artline_has_selection_evidence(id) AS supported FROM artworks WHERE id=ANY(%s::uuid[])', ([r['artwork_id'] for r in records],)).fetchall()
        assert len(rows) == 12 and all(x['status'] == 'review' and x['supported'] and x['primary_media_id'] for x in rows)
    receipt = {'at':core.now(), 'target':target, 'added':added, 'verified':len(rows), 'manifest_sha256':core.sha((RUN/'prepared.json').read_bytes()), 'artwork_ids':[r['artwork_id'] for r in records]}
    path = RUN / (target+'-applied.json')
    if not path.exists():
        core.save_new(path, receipt)
    print(target, 'committed', added, 'new frescoes;', len(rows), 'verified', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'local', 'production'])
    args = parser.parse_args()
    prepare() if args.action == 'prepare' else apply(args.action)
