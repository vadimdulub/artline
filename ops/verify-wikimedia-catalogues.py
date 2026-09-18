#!/usr/bin/env python3
"""Read-only verification of committed catalogue batches and public images."""
import concurrent.futures
import hashlib
import importlib.util
import io
import json
import re
from pathlib import Path

import requests
from PIL import Image

spec = importlib.util.spec_from_file_location('apply_catalogues', Path(__file__).with_name('apply-wikimedia-catalogues.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
r = m.r
SITE = 'https://artline-web-lpuqqlugnq-ew.a.run.app'


def main():
    plans = [json.loads(p.read_text()) for p in sorted((r.RUN/'batches').glob('batch-*.json')) if re.fullmatch(r'batch-\d{3}\.json', p.name)]
    items = {x['record']['qid']: x for p in plans for x in p['entries']}
    refinements = {x['qid']:x for x in json.loads((r.RUN/'title-refinements.json').read_text())['amendments']} if (r.RUN/'title-refinements.json').exists() else {}
    assert {p.stem for p in (r.RUN/'ready').glob('Q*.json')} == set(items), 'Unplanned prepared records remain'
    report = {'checked_at': r.core.now(), 'databases': {}, 'public_images': [], 'public_pages': []}
    attached = {}
    for target in ('local', 'production'):
        expected = {s['qid']: s for p in plans for s in p['targets'][target] if s['action'] != 'deferred'}
        receipts = {p.stem: json.loads(p.read_text()) for p in (r.RUN/'applied'/target).glob('Q*.json')}
        assert expected.keys() == receipts.keys(), target+' incomplete receipts'
        new_artists = {x['artist_id'] for x in receipts.values() if x['new_artist']}
        counts = {'new_artworks': 0, 'existing_enriched': 0, 'new_artists': len(new_artists), 'images_attached': 0, 'unknown_date_new_artworks': 0, 'unlinked_creator_new_artworks': 0}
        with r.base.connect(target == 'production') as db, db.transaction():
            db.execute('SET TRANSACTION READ ONLY')
            db.execute("SET LOCAL statement_timeout='120s'")
            rows = db.execute('''SELECT to_jsonb(a) AS artwork, e.external_id AS qid,
                i.slug AS institution_slug, ma.storage_path,ma.checksum_sha256,ma.byte_size,
                ma.rights_status,ma.license_url,ma.attribution_text,
                artline_has_selection_evidence(a.id) AS selection_supported,
                (SELECT count(*) FROM artwork_location_assertions la WHERE la.artwork_id=a.id AND la.claim_type='display') AS display_claims,
                (SELECT count(*) FROM media_rights_evidence re WHERE re.media_id=ma.id) AS rights_evidence,
                (SELECT count(*) FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artwork' AND c.entity_id=a.id AND s.slug='wikimedia-catalogue-scan-20260913' AND c.field_name='wikimedia_catalogue_research') AS research_citations,
                COALESCE((SELECT jsonb_agg(aa.artist_id::text) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') AS artist_ids
                FROM artworks a
                JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikidata'
                LEFT JOIN institutions i ON i.id=a.current_institution_id
                LEFT JOIN media_assets ma ON ma.id=a.primary_media_id
                WHERE a.id=ANY(%s::uuid[])''', ([s['artwork_id'] for s in expected.values()],)).fetchall()
            assert len(rows) == len(expected), target+' missing/duplicate identity rows'
            by_id = {row['artwork']['id']: row for row in rows}
            for row in rows:
                qid = row['qid']; state = expected[qid]; item = items[qid]; rec = receipts[qid]
                work = row['artwork']; date = item['record']['date']
                assert work['id'] == state['artwork_id'] and row['research_citations'] == 1
                assert work['status'] == rec['status'] == 'review' and work['published_at'] is None
                if state['action'] == 'new':
                    counts['new_artworks'] += 1
                    assert work['title'] == refinements.get(qid, {}).get('title', item['record']['title'])
                    assert work['creation_year_start'] == date['first'] and work['creation_year_end'] == date['last']
                    assert work['date_precision'] == date['precision']
                    assert work['research_candidate'] == (date['precision'] == 'unknown')
                    assert work['current_institution_id'] == state['institution_id']
                    assert row['selection_supported'] and row['display_claims'] == 0
                    if rec['artist_id']: assert rec['artist_id'] in row['artist_ids']
                    else: assert work['unlinked_creator_label'] == item['record']['creator_label']
                    counts['unknown_date_new_artworks'] += date['precision'] == 'unknown'
                    counts['unlinked_creator_new_artworks'] += not bool(rec['artist_id'])
                else: counts['existing_enriched'] += 1
                if rec['image_attached']:
                    im = item['image']; assert im and date['eligible']
                    assert work['primary_media_id'] == rec['media_id']
                    for field, key in [('storage_path','path'),('checksum_sha256','sha256'),('byte_size','bytes'),('rights_status','rights_status'),('license_url','license_url'),('attribution_text','attribution_text')]:
                        value = im[key]
                        if field == 'attribution_text' and qid in refinements: value = value.replace(qid, refinements[qid]['title'])
                        assert row[field] == value, (target, qid, field)
                    assert row['rights_evidence'] == 1
                    counts['images_attached'] += 1; attached[qid] = im
            preserved = 0
            for plan in plans:
                oldrows = json.loads((r.BACKUPS/f"batch-{plan['batch']:03d}-{target}-preimages.json").read_text())
                for old in oldrows:
                    now = by_id[old['id']]['artwork']
                    ignored = {'primary_media_id','revision','updated_at','updated_by'}
                    assert {k:v for k,v in old.items() if k not in ignored} == {k:v for k,v in now.items() if k not in ignored}, (target, old['id'], 'existing content changed')
                    if old['primary_media_id']: assert now['primary_media_id'] == old['primary_media_id']
                    preserved += 1
            painters = db.execute('''SELECT a.id::text,a.slug,a.display_name,a.status,
                (SELECT count(*) FROM artwork_artists aa WHERE aa.artist_id=a.id) AS works
                FROM artists a WHERE a.id=ANY(%s::uuid[])''', (list(new_artists),)).fetchall()
            assert len(painters) == len(new_artists) and all(p['works'] > 0 and p['status'] == 'review' for p in painters)
            institutions = db.execute("SELECT id::text,slug,name,status FROM institutions WHERE slug LIKE 'wikimedia-museum-%'").fetchall()
            assert all(i['status'] == 'review' for i in institutions)
            report['databases'][target] = {'counts': counts, 'existing_content_preserved': preserved, 'verified_records': len(rows), 'new_painters': painters, 'new_institutions': institutions, 'rows': rows}
        print(target, counts, flush=True)
    assert report['databases']['local']['counts'] == report['databases']['production']['counts']

    def verify_image(pair):
        qid, im = pair
        raw = (r.ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == im['sha256'] and len(raw) == im['bytes'] <= 100000
        with Image.open(io.BytesIO(raw)) as pic:
            assert pic.format == 'JPEG' and pic.size == (im['width'], im['height']); pic.verify()
        response = requests.get(SITE+im['path'], timeout=60)
        response.raise_for_status()
        assert response.headers['Content-Type'].startswith('image/jpeg')
        assert hashlib.sha256(response.content).hexdigest() == im['sha256'] and len(response.content) == im['bytes']
        return {'qid': qid, 'url': SITE+im['path'], 'status': response.status_code, 'sha256': im['sha256'], 'bytes': im['bytes']}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(verify_image, attached.items()):
            report['public_images'].append(result)
            if len(report['public_images']) % 50 == 0: print('Verified public images', len(report['public_images']), flush=True)
    prod = report['databases']['production']
    samples = []
    for inst in prod['new_institutions']:
        candidates = [row for row in prod['rows'] if row['institution_slug'] == inst['slug']]
        assert candidates
        samples.append(candidates[0])
    for predicate in [lambda x: x['artwork']['research_candidate'], lambda x: x['qid'] in attached, lambda x: 'byzantine' in x['institution_slug']]:
        sample = next((row for row in prod['rows'] if predicate(row)), None)
        if sample: samples.append(sample)
    for row in samples:
        url = SITE+'/api/backend/v1/museums/'+row['institution_slug']+'/works/'+row['artwork']['id']
        response = requests.get(url, timeout=120); response.raise_for_status()
        data = response.json()
        assert row['artwork']['id'] in json.dumps(data)
        report['public_pages'].append({'url':url,'status':response.status_code,'qid':row['qid']})
    for painter in prod['new_painters'][:3]:
        url = SITE+'/api/backend/v1/artists/'+painter['slug']+'/works?limit=5'
        response = requests.get(url, timeout=120); response.raise_for_status()
        assert response.json()['items']
        report['public_pages'].append({'url':url,'status':response.status_code})
    protected = requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/coverage/summary', timeout=60)
    assert protected.status_code == 401
    report['protected_editor_get_status'] = protected.status_code
    report['browser_verification'] = 'Browser integration unavailable (bootstrap missing sandboxPolicy); selected-image visual QA and public HTTP verification performed.'
    r.core.save_new(r.RUN/'verification.json', report)
    print('Verified all committed records in both databases, preserved existing content, all attached local/public images and anonymous preview.', flush=True)


if __name__ == '__main__': main()
