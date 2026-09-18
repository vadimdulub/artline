#!/usr/bin/env python3
"""Read-only verification of the selected fresco import and public delivery."""
import hashlib
import importlib.util
import json
from pathlib import Path

import requests

spec = importlib.util.spec_from_file_location('fresco_import', Path(__file__).with_name('import-michelangelo-frescoes.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
records = json.loads((m.RUN/'prepared.json').read_text())
expected = {r['artwork_id']:r for r in records}
report = {'checked_at':m.core.now(), 'manifest_sha256':m.core.sha((m.RUN/'prepared.json').read_bytes()), 'databases':{}, 'public_images':[]}

for target in ('local', 'production'):
    before = json.loads((m.BACKUPS/(target+'-before.json')).read_text())
    with m.connect(target == 'production') as db, db.transaction():
        db.execute('SET TRANSACTION READ ONLY')
        db.execute("SET LOCAL statement_timeout='45s'")
        artist = db.execute('SELECT to_jsonb(a) AS row FROM artists a WHERE id=%s', (m.ARTIST,)).fetchone()['row']
        assert artist == before['artist'], target+' painter changed'
        for old in before['works']:
            row = db.execute('SELECT to_jsonb(a) AS row FROM artworks a WHERE id=%s', (old['id'],)).fetchone()['row']
            assert row == old, target+' existing artwork changed: '+old['title']
        rows = db.execute('''SELECT a.id::text,a.title,a.slug,a.status,a.work_type,a.primary_media_id::text,
            a.creation_year_start,a.creation_year_end,a.published_at,a.current_location_text,
            i.name AS institution,m.storage_path,m.checksum_sha256,m.byte_size,m.rights_status,
            m.license_url,m.attribution_text,e.external_id,
            artline_has_selection_evidence(a.id) AS selection_supported,
            (SELECT count(*) FROM artwork_location_assertions la WHERE la.artwork_id=a.id AND la.claim_type='holding' AND la.review_state='accepted') AS holding_count,
            (SELECT count(*) FROM artwork_location_assertions la WHERE la.artwork_id=a.id AND la.claim_type='display') AS display_claims,
            (SELECT count(*) FROM media_rights_evidence re WHERE re.media_id=m.id) AS rights_evidence,
            (SELECT count(*) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id) AS citations
            FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id
            JOIN media_assets m ON m.id=a.primary_media_id
            JOIN institutions i ON i.id=a.current_institution_id
            JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikidata'
            WHERE aa.artist_id=%s AND a.id=ANY(%s::uuid[])''', (m.ARTIST, list(expected))).fetchall()
        assert len(rows) == 12
        for row in rows:
            r = expected[row['id']]
            assert row['title'] == r['title'] and row['external_id'] == r['qid']
            assert row['status'] == 'review' and row['published_at'] is None and row['work_type'] == 'fresco'
            assert row['creation_year_start'] == r['first'] and row['creation_year_end'] == r['last']
            assert row['checksum_sha256'] == r['sha256'] and row['byte_size'] == r['bytes']
            assert row['primary_media_id'] == r['media_id'] and row['storage_path'] == r['path']
            assert row['rights_status'] == r['rights_status'] and row['license_url'] == r['license_url']
            assert row['attribution_text'] == r['attribution_text']
            assert row['selection_supported'] and row['holding_count'] == 1 and row['display_claims'] == 0
            assert row['rights_evidence'] == 1 and row['citations'] >= 2
        total = db.execute('SELECT count(DISTINCT artwork_id) AS n FROM artwork_artists WHERE artist_id=%s', (m.ARTIST,)).fetchone()['n']
        assert total == len(before['works']) + 12
        report['databases'][target] = {'new_frescoes':len(rows), 'total_painter_works':total, 'painter_unchanged':True, 'existing_works_unchanged':len(before['works']), 'rows':rows}
        print(target, 'database verified:', len(rows), 'frescoes;', total, 'works;', len(before['works']), 'existing works preserved', flush=True)

site = 'https://artline-web-lpuqqlugnq-ew.a.run.app'
session = requests.Session()
session.headers['User-Agent'] = 'Artline/1.0 (selected import verification)'
response = session.get(site+'/api/backend/v1/artists/michelangelo-q5592/works?limit=50', timeout=60)
response.raise_for_status()
page = response.json()
items = {w['id']:w for w in page['items']}
assert expected.keys() <= items.keys() and len(items) == 16
for aid, r in expected.items():
    w = items[aid]
    assert w['status'] == 'review' and w['work_type'] == 'fresco'
    assert w['media_url'] == r['path'] and w['attribution_text'] == r['attribution_text']
    image = session.get(site+r['path'], timeout=45)
    image.raise_for_status()
    assert image.headers['Content-Type'].startswith('image/jpeg')
    assert hashlib.sha256(image.content).hexdigest() == r['sha256']
    assert len(image.content) == r['bytes'] <= 100000
    assert hashlib.sha256((m.ROOT/'apps/web/public'/r['path'].lstrip('/')).read_bytes()).hexdigest() == r['sha256']
    report['public_images'].append({'qid':r['qid'], 'url':site+r['path'], 'status':image.status_code, 'bytes':len(image.content), 'sha256':r['sha256']})
    print('Public image verified', r['qid'], flush=True)
profile = session.get(site+'/artists/michelangelo-q5592', timeout=60)
profile.raise_for_status()
assert 'Michelangelo' in profile.text
protected = session.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/coverage/summary', timeout=45)
assert protected.status_code == 401
report['anonymous_preview'] = {'works_status':response.status_code, 'profile_status':profile.status_code, 'works_returned':len(items), 'protected_editor_get_status':protected.status_code}
report['browser_verification'] = 'Browser integration failed at bootstrap (missing sandboxPolicy); image visual review and production HTTP checks completed.'
m.core.save_new(m.RUN/'verification.json', report)
print('Verified both databases, all twelve local/cloud-delivered images, anonymous preview and protected editor access.')
