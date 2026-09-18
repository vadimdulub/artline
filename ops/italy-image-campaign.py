#!/usr/bin/env python3
"""Italy-only selected image research, exact attachment and verification.

No artwork imports, publication changes, migrations or replacement images.
Every write requires saved recovery evidence and exact target preimages.
"""
import argparse
import base64
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace
from urllib.parse import urlparse

import psycopg
import requests
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from PIL import Image
from google.cloud import storage

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/italy-images-4h-20260916'
BACKUP = Path('/Users/vadimdulub/Library/Application Support/Artline/backups/italy-images-4h-20260916')
SOURCE_IMAGES = Path('/Users/vadimdulub/Library/Application Support/Artline/source-images/italy-images-4h-20260916')
spec = importlib.util.spec_from_file_location('italy_core', ROOT / 'ops/enrich-artwork-images.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
core.VERSION = 'italy-selected-images-v1'
# Reuse the established research editor account; provenance carries the run ID.
core.ACTOR = 'local-european-research'
core.PROVIDERS['italy-met-authority'] = 'The Metropolitan Museum of Art'
core.PROVIDERS['italy-mia'] = 'Minneapolis Institute of Art'
core.PROVIDERS['italy-vienna'] = 'Academy of Fine Arts Vienna'
core.HOSTS.add('collection.kunstsammlungenakademie.at.zetcom.net')
core.HOSTS.add('img.artsmia.org')
core.HOSTS.update({'thumb.wikimedia.org', 'www.wikidata.org'})


def save(path, value):
    core.save_new(path, value)


def load(path):
    return json.loads(path.read_text())


def institution_policy_reason(record):
    for path in (RUN / 'institution-rights-holds').glob('*.json'):
        policy = load(path)
        slugs = policy.get('institution_slugs', [policy['institution_slug']])
        if record.get('institution_slug') in slugs:
            return policy['decision']
    return None


def audit():
    RUN.mkdir(parents=True, exist_ok=True)
    if not (RUN / 'campaign.json').exists():
        save(RUN / 'campaign.json', {'started_at': '2026-09-16T20:47:13Z',
             'minimum_finish_at': '2026-09-17T00:47:13Z', 'minimum_duration_seconds': 14400,
             'scope': 'Italy museum holdings and culturally Italy-associated artists held abroad; existing eligible selected records only',
             'authorization': 'User asked to find pictures and upload them, working at least four hours.',
             'publication': 'Review retained; no new artworks or creator assertions',
             'image_policy': 'Selected, identity-verified and rights-cleared full-frame reproductions, <=100000 bytes',
             'core_script_sha256': core.sha((ROOT / 'ops/enrich-artwork-images.py').read_bytes())})
    if (RUN / 'local-audit.json').exists():
        print('Existing audit preserved', flush=True)
        return
    geography = load(ROOT / 'docs/research/italy-museums-deep-20260916/italian-institution-geography-review.json')
    with psycopg.connect('postgres://127.0.0.1/artline', row_factory=dict_row,
                        options='-c default_transaction_read_only=on -c statement_timeout=120000') as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        institutions = db.execute('''SELECT i.id::text,i.slug,i.name,i.website_url,i.wikidata_id,
          p.country_code,coalesce((SELECT jsonb_agg(DISTINCT p2.country_code) FROM institution_venues v
          JOIN places p2 ON p2.id=v.place_id WHERE v.institution_id=i.id),'[]') venue_countries
          FROM institutions i LEFT JOIN places p ON p.id=i.place_id
          WHERE p.country_code='IT' OR i.id=ANY(%s::uuid[]) OR EXISTS(SELECT 1 FROM institution_venues v
          JOIN places p2 ON p2.id=v.place_id WHERE v.institution_id=i.id AND p2.country_code='IT')''',
          ([r['id'] for r in geography],)).fetchall()
        creators = db.execute('''SELECT ar.id::text,ar.slug,ar.display_name,ar.death_year,
          (SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'id',e.external_id)) FROM external_identifiers e
           WHERE e.entity_type='artist' AND e.entity_id=ar.id) identifiers
          FROM artists ar WHERE ar.status<>'archived' AND EXISTS(SELECT 1 FROM artist_countries c
          WHERE c.artist_id=ar.id AND c.country_code='IT' AND c.relationship_type='cultural_affiliation')''').fetchall()
        works = db.execute('''WITH scope AS MATERIALIZED(
          SELECT id FROM artworks WHERE current_institution_id=ANY(%s::uuid[])
          UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[])
           AND claim_type='holding' AND review_state IN ('review','accepted') AND superseded_by IS NULL
          UNION SELECT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[]))
          SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,a.accession_number,a.date_display,
           a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.object_form,a.status,
           a.current_institution_id::text,a.primary_media_id::text,i.slug institution_slug,
           i.name institution_name,i.website_url,i.wikidata_id institution_qid,
           artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) date_scope,
           artline_has_selection_evidence(a.id) selected,
           coalesce((SELECT jsonb_agg(jsonb_build_object('id',ar.id,'name',ar.display_name,'death',ar.death_year,
            'role',aa.attribution_role,'qid',(SELECT e.external_id FROM external_identifiers e WHERE e.entity_type='artist'
              AND e.entity_id=ar.id AND e.scheme='wikidata' LIMIT 1)))
             FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') creators,
           coalesce((SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'id',e.external_id,'url',e.canonical_url))
             FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]') identifiers
          FROM scope s JOIN artworks a ON a.id=s.id LEFT JOIN institutions i ON i.id=a.current_institution_id
          WHERE a.status<>'archived' ORDER BY a.id''',
          ([r['id'] for r in institutions], [r['id'] for r in institutions], [r['id'] for r in creators])).fetchall()
        meta = db.execute("SELECT now() snapshot_at,current_setting('transaction_read_only') read_only").fetchone()
    inst_ids = {r['id'] for r in institutions}
    gaps = []
    for w in works:
        w['scope_basis'] = 'Italian museum identity' if w['current_institution_id'] in inst_ids else 'Italian cultural affiliation or reviewed Italian holding assertion'
        if not w['primary_media_id'] and w['date_scope'] == 'eligible' and w['selected']:
            gaps.append(w)
    save(RUN / 'local-audit.json', {'snapshot': meta, 'institutions': institutions, 'italy_cultural_creators': creators,
         'works': works, 'summary': {'works': len(works), 'with_media': sum(bool(w['primary_media_id']) for w in works),
         'eligible_selected_gaps': len(gaps), 'gap_media': dict(collections.Counter(w['work_type'] for w in gaps)),
         'holding_painting_gaps': sum(w['work_type'] == 'painting' and w['current_institution_id'] in inst_ids for w in gaps)}})
    save(RUN / 'eligible-image-gaps.json', gaps)
    print(json.dumps(load(RUN / 'local-audit.json')['summary']), flush=True)


def backup():
    BACKUP.mkdir(parents=True, exist_ok=True)
    dump = BACKUP / 'local-before.dump'
    if not dump.exists():
        subprocess.run(['pg_dump', '-Fc', '--no-owner', '--no-acl', '-d', 'postgres://127.0.0.1/artline', '-f', str(dump)], check=True)
    subprocess.run(['pg_restore', '--list', str(dump)], check=True, stdout=subprocess.DEVNULL)
    description = 'Italy selected image research 20260916 four hour campaign'
    request = BACKUP / 'production-backup-request.json'
    if not request.exists():
        result = subprocess.check_output(['gcloud', 'sql', 'backups', 'create', '--instance=artline-postgres',
            '--project=artline-508319', '--description=' + description, '--format=json'])
        save(request, result)
    records = json.loads(subprocess.check_output(['gcloud', 'sql', 'backups', 'list', '--instance=artline-postgres',
                                                '--project=artline-508319', '--limit=30', '--format=json']))
    cloud = next(r for r in records if r.get('description') == description)
    if cloud['status'] != 'SUCCESSFUL':
        raise ValueError('Cloud recovery backup not yet complete')
    save(RUN / 'backups.json', {'local': {'path': str(dump), 'bytes': dump.stat().st_size,
                                       'sha256': core.sha(dump.read_bytes()), 'archive_directory_verified': True},
                              'production': cloud})
    print('Local recovery archive and Cloud SQL backup verified', flush=True)


def snapshot(candidates, dsn):
    with psycopg.connect(dsn, row_factory=dict_row, options='-c default_transaction_read_only=on') as db:
        rows = db.execute('''WITH wanted AS(SELECT * FROM jsonb_to_recordset(%s::jsonb)
          AS x(artwork_id text,scheme text,external_id text))
          SELECT w.artwork_id local_id,a.id::text target_id,a.primary_media_id::text,a.status,
           a.slug,a.title,a.creation_year_start,a.creation_year_end,a.work_type,
           artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) date_scope,
           artline_has_selection_evidence(a.id) selected,
           to_jsonb(a)-ARRAY['primary_media_id','revision','updated_at','updated_by'] metadata,
           coalesce((SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id,aa.attribution_role)
             FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]'::jsonb) creators
          FROM wanted w JOIN external_identifiers e ON e.entity_type='artwork' AND e.scheme=w.scheme AND e.external_id=w.external_id
          JOIN artworks a ON a.id=e.entity_id''', (Jsonb(candidates),)).fetchall()
    return rows


def select(provider, limit, label, work_type='painting'):
    run = RUN / label
    run.mkdir(parents=True, exist_ok=True)
    if (run / 'candidates.json').exists():
        print('Existing immutable selection', label, flush=True)
        return
    gaps = load(RUN / 'eligible-image-gaps.json')
    used = {r['artwork_id'] for p in RUN.glob('*/candidates.json') for r in load(p)['candidates']}
    scheme = 'wikidata' if provider == 'commons' else core.SCHEMES[provider]
    rows = []
    for w in gaps:
        allowed_types = ('painting', 'fresco', 'watercolor') if work_type == 'painting' else (work_type,)
        if w['artwork_id'] in used or w['work_type'] not in allowed_types:
            continue
        ids = [e for e in w['identifiers'] if e['scheme'] == scheme]
        if len(ids) != 1:
            continue
        c = dict(w, scheme=scheme, external_id=ids[0]['id'], page=ids[0]['url'], provider=provider,
                 artist='; '.join(x['name'] for x in w['creators']) or 'Unresolved creator label')
        if provider == 'commons':
            if not w['institution_qid'] or not w['creators'] or any(not a['qid'] or a['role'] != 'primary' for a in w['creators']):
                continue
            c.update(qid=ids[0]['id'], provider='night-commons')
        rows.append(c)
    rows.sort(key=lambda c: (c['scope_basis'] != 'Italian museum identity', c['work_type'] != 'painting', c['artist'], c['artwork_id']))
    if work_type in ('drawing', 'print'):
        groups = collections.defaultdict(list)
        for row in rows: groups[row['artist']].append(row)
        # Preserve a bounded, varied sample instead of taking a single oeuvre.
        rows = [group[n] for n in range(8) for group in groups.values() if n < len(group)][:limit]
    else:
        rows = rows[:limit]
    if not rows:
        save(run / 'candidates.json', {'selected_at': core.now(), 'candidates': [], 'provider': provider})
        print('No eligible bounded candidates', label, flush=True)
        return
    local = snapshot(rows, 'postgres://127.0.0.1/artline')
    remote = snapshot(rows, core.cloud_dsn())
    local_index = collections.defaultdict(list)
    remote_index = collections.defaultdict(list)
    for r in local: local_index[r['local_id']].append(r)
    for r in remote: remote_index[r['local_id']].append(r)
    selected = []
    held = []
    for c in rows:
        matches = [local_index[c['artwork_id']], remote_index[c['artwork_id']]]
        if any(len(x) != 1 for x in matches):
            held.append(dict(c, reason='Missing/ambiguous cross-database exact identity'))
            continue
        l, r = matches[0][0], matches[1][0]
        if any(x['date_scope'] != 'eligible' or not x['selected'] or x['status'] == 'archived' for x in (l, r)):
            held.append(dict(c, reason='Current eligibility differs'))
            continue
        if l['primary_media_id'] or r['primary_media_id']:
            held.append(dict(c, reason='Existing image preserved; another campaign may have enriched it'))
            continue
        if any(l[k] != r[k] or l[k] != c[k] for k in ('slug','title','creation_year_start','creation_year_end','work_type')):
            held.append(dict(c, reason='Current local/cloud metadata identity differs'))
            continue
        c['target_ids'] = {'local': l['target_id'], 'cloud': r['target_id']}
        selected.append(c)
    save(run / 'candidates.json', {'selected_at': core.now(), 'candidates': selected, 'provider': provider,
         'selection': 'Bounded existing Italy-associated artwork gaps; current local/production identities and missing media confirmed'})
    save(run / 'local-before.json', local)
    save(run / 'cloud-before.json', remote)
    save(run / 'selection-held.json', held)
    print(label, 'selected', len(selected), 'held', len(held), flush=True)


def research(label, limit):
    run = RUN / label
    rows = load(run / 'candidates.json')['candidates']
    spec = importlib.util.spec_from_file_location('italy_commons', ROOT / 'ops/overnight-commons-images.py')
    commons = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(commons)
    latest = commons.core.latest_events(run)
    rows = [r for r in rows if r['artwork_id'] not in latest][:limit]
    fetcher = commons.core.Fetcher(run / 'metadata/commons-evidence')
    for start in range(0, len(rows), 10):
        ready = commons.research_chunk(rows[start:start+10], run, fetcher)
        for c in ready:
            commons.core.event(run, {'provider': 'night-commons', 'artwork_id': c['artwork_id'],
                'external_id': c['external_id'], 'outcome': 'rights_selected'})
        print(label, 'researched', min(start+10, len(rows)), 'of', len(rows), 'rights-selected', len(ready), flush=True)


def native_research(label, limit):
    run = RUN / label
    rows = load(run / 'candidates.json')['candidates']
    fetcher = core.Fetcher(run / 'metadata/native-evidence')
    pending = [r for r in rows if r['artwork_id'] not in core.latest_events(run)][:limit]
    provider = rows[0]['provider'] if rows else ''
    nga = core.nga_index(fetcher) if provider == 'nga' else {}
    chicago = {}
    if provider == 'chicago':
        for start in range(0, len(pending), 30):
            ids = ','.join(c['external_id'] for c in pending[start:start+30])
            raw = fetcher.metadata('https://api.artic.edu/api/v1/artworks?ids=' + ids + '&fields=id,title,image_id,is_public_domain,copyright_notice,date_start,date_end,main_reference_number&limit=100')
            chicago.update({str(r['id']):r for r in raw.get('data', [])})
    for n,c in enumerate(pending, 1):
        try:
            im = core.image_record(c, fetcher, nga, chicago)
            if not im:
                raise ValueError('No explicit reusable primary museum image')
            raw = im['raw']
            field = {'met':'objectEndDate', 'cleveland':'creation_date_latest', 'chicago':'date_end'}.get(provider)
            if field and (type(raw.get(field)) is not int or not 0 < raw[field] <= 1970):
                raise ValueError('Current source creation date needs review')
            core.validate_source_image_identity(im)
            save(run / 'selected' / provider / (c['artwork_id'] + '.json'), im)
            core.event(run, {'provider':provider,'artwork_id':c['artwork_id'],'external_id':c['external_id'],'outcome':'rights_selected'})
        except Exception as e:
            core.event(run, {'provider':provider,'artwork_id':c['artwork_id'],'external_id':c['external_id'],'outcome':'manual_review','reason':str(e)[:350]})
        print(label, n, '/', len(pending), flush=True)


class ArchiveFetcher(core.Fetcher):
    def _get(self, url, limit=8_000_000):
        data, headers = super()._get(url, limit)
        if (headers.get('Content-Type') or '').startswith('image/'):
            digest = core.sha(data)
            path = SOURCE_IMAGES / (digest + '.source')
            save(path, data)
            receipt = RUN / 'source-image-receipts' / (digest + '.json')
            if not receipt.exists():
                save(receipt, {'url': url, 'path': str(path), 'sha256': digest, 'bytes': len(data),
                     'retrieved_at': core.now(), 'response_headers': headers})
        return data, headers


def prepare(label, limit):
    run = RUN / label
    assert (RUN / 'backups.json').exists(), 'Recovery backup verification required before preparation'
    rows = load(run / 'candidates.json')['candidates']
    candidates = [r for r in rows if (run / 'selected' / r['provider'] / (r['artwork_id'] + '.json')).exists()
                  and not institution_policy_reason(r)
                  and not (run / 'images' / r['provider'] / (r['artwork_id'] + '.json')).exists()][:limit]
    core.Fetcher = ArchiveFetcher
    for provider in sorted({r['provider'] for r in candidates}):
        core.PROVIDERS.setdefault(provider, 'Wikimedia Commons')
        part = [r for r in candidates if r['provider'] == provider]
        core.worker(provider, part, SimpleNamespace(run=run, prepare_only=True), '')
    print(label, 'preparation', dict(core.COUNTS), flush=True)


def apply(label, limit):
    run = RUN / label
    assert (RUN / 'backups.json').exists(), 'Recovery backup verification required'
    rows = load(run / 'candidates.json')['candidates']
    # A contact sheet or individual image must have been inspected first.
    reviews = load(run / 'visual-review.json')
    approved = {r['artwork_id']: r for r in reviews['images'] if r['outcome'] == 'approved'}
    latest = core.latest_events(run)
    chosen = []
    for c in rows:
        if institution_policy_reason(c):
            continue
        path = run / 'images' / c['provider'] / (c['artwork_id'] + '.json')
        if c['artwork_id'] not in approved or not path.exists():
            continue
        image = load(path)
        if approved[c['artwork_id']]['sha256'] != image['sha256']:
            raise ValueError('Visual review is for different image bytes')
        if latest.get(c['artwork_id'], {}).get('outcome') == 'complete':
            continue
        chosen.append(c)
    chosen = chosen[:limit]
    original_attach = core.attach
    before = {target: {r['local_id']: r for r in load(run / (target + '-before.json'))}
              for target in ('local', 'cloud')}
    for target in ('local', 'cloud'):
        save(BACKUP / label / (target + '-before.json'), (run / (target + '-before.json')).read_bytes())
    def guarded_attach(db, image, target):
        with db.transaction():
            if institution_policy_reason(image):
                raise ValueError('Institution-specific reproduction permission remains unresolved')
            expected = before[target][image['artwork_id']]
            current = db.execute('''SELECT a.id::text,a.primary_media_id::text,
              to_jsonb(a)-ARRAY['primary_media_id','revision','updated_at','updated_by'] metadata,
              coalesce((SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id,aa.attribution_role)
                FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]'::jsonb) creators
              FROM artworks a WHERE a.id=%s FOR UPDATE''', (expected['target_id'],)).fetchone()
            if not current or current['metadata'] != expected['metadata'] or current['creators'] != expected['creators']:
                raise ValueError('Catalogue metadata or creators changed since preimage; re-review required')
            # Re-run source identity/rights validation at attachment time.
            if image['provider'] == 'night-commons':
                cspec = importlib.util.spec_from_file_location('italy_rights_check', ROOT / 'ops/overnight-commons-images.py')
                commons = importlib.util.module_from_spec(cspec)
                cspec.loader.exec_module(commons)
                commons.entity_match(image, image['raw']['wikidata'],
                    require_primary_image=image.get('image_selection_basis') != 'independent_exact_commons_file')
                commons.rights_and_identity(image, image['raw']['wikidata'], image['raw']['commons'],
                    image['raw']['structured_data'], image.get('rendered_licence_evidence'))
            elif image['provider'] == 'italy-primary-photo':
                pspec = importlib.util.spec_from_file_location('italy_primary_photo_check', ROOT / 'ops/italy-primary-photo-research.py')
                primary = importlib.util.module_from_spec(pspec)
                pspec.loader.exec_module(primary)
                primary.validate_attachment(image, approved[image['artwork_id']])
                image['primary_catalogue_comparison'] = approved[image['artwork_id']]['primary_catalogue_comparison']
            elif image['provider'] == 'met-commons':
                mspec = importlib.util.spec_from_file_location('italy_met_recovery_check', ROOT / 'ops/italy-met-recovery.py')
                recovery = importlib.util.module_from_spec(mspec)
                mspec.loader.exec_module(recovery)
                recovery.validate(image)
            elif image['provider'] == 'italy-met-authority':
                mspec = importlib.util.spec_from_file_location('italy_met_authority_check', ROOT / 'ops/italy-met-authority-image.py')
                met_authority = importlib.util.module_from_spec(mspec)
                mspec.loader.exec_module(met_authority)
                met_authority.validate(image)
            elif image['provider'] == 'italy-mia':
                mspec = importlib.util.spec_from_file_location('italy_mia_check', ROOT / 'ops/italy-mia-image.py')
                mia = importlib.util.module_from_spec(mspec)
                mspec.loader.exec_module(mia)
                mia.validate(image)
            elif image['provider'] == 'italy-vienna':
                vspec = importlib.util.spec_from_file_location('italy_vienna_check', ROOT / 'ops/italy-vienna-native.py')
                vienna = importlib.util.module_from_spec(vspec)
                vspec.loader.exec_module(vienna)
                vienna.validate(image)
            result = original_attach(db, image, target)
            if result == 'attached' and image.get('creator_credit'):
                db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',
                           (image['creator_credit'], image['attribution_text'], image['media_id']))
            if result == 'attached' and image['provider'] == 'italy-primary-photo':
                db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',
                    ('Exact native catalogue identifier, official catalogue inventory/creator/holding/date and visually compared physical composition; independently sourced Commons photograph with explicit per-file licence and photographer attribution.', image['media_id']))
            return result
    core.attach = guarded_attach
    for provider in sorted({r['provider'] for r in chosen}):
        core.PROVIDERS.setdefault(provider, 'Wikimedia Commons')
        core.worker(provider, [r for r in chosen if r['provider'] == provider],
                    SimpleNamespace(run=run, upload_prepared_only=True), core.cloud_dsn())
    print(label, 'attachment results', dict(core.COUNTS), flush=True)


def attachment_attribution(image):
    """Reproduce the exact credit written by either attachment path."""
    if image.get('creator_credit'):
        return image['attribution_text']
    return (image['artist']+'. '+image['title']+'. '+core.PROVIDERS[image['provider']]
            +'. '+image['license_label']+'. Compressed full-frame reproduction.')


def verify(label, all_served=False):
    run = RUN / label
    latest = core.latest_events(run)
    receipts = [load(p) for p in (run / 'images').glob('*/*.json')]
    completed = [r for r in receipts if latest.get(r['artwork_id'], {}).get('outcome') == 'complete'
                 and latest[r['artwork_id']].get('local') == 'attached'
                 and latest[r['artwork_id']].get('cloud') == 'attached']
    errors = []
    bucket = storage.Client(project='artline-508319', credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    for image in completed:
        path = ROOT / 'apps/web/public' / image['path'].lstrip('/')
        body = path.read_bytes()
        if core.sha(body) != image['sha256'] or len(body) != image['bytes'] or len(body) > 100000:
            errors.append({'id': image['artwork_id'], 'error': 'Local derivative bytes mismatch'})
        with Image.open(path) as im:
            if im.size != (image['width'], image['height']):
                errors.append({'id': image['artwork_id'], 'error': 'Image dimension mismatch'})
            im.verify()
        blob = bucket.get_blob(image['path'].lstrip('/'))
        if not blob or blob.size != len(body) or blob.md5_hash != base64.b64encode(hashlib.md5(body).digest()).decode():
            errors.append({'id': image['artwork_id'], 'error': 'Uploaded object checksum mismatch'})
    reports = {}
    for target, dsn in [('local','postgres://127.0.0.1/artline'), ('cloud',core.cloud_dsn())]:
        before = {r['local_id']: r for r in load(run / (target + '-before.json'))}
        ids = [r['target_ids'][target] for r in completed]
        with psycopg.connect(dsn, row_factory=dict_row, options='-c default_transaction_read_only=on') as db:
            rows = db.execute('''SELECT a.id::text,a.primary_media_id::text,a.status,
              to_jsonb(a)-ARRAY['primary_media_id','revision','updated_at','updated_by'] metadata,
              coalesce((SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id,aa.attribution_role)
                FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]'::jsonb) creators,
              to_jsonb(m) media,to_jsonb(e) evidence FROM artworks a
              LEFT JOIN media_assets m ON m.id=a.primary_media_id
              LEFT JOIN media_rights_evidence e ON e.media_id=m.id WHERE a.id=ANY(%s::uuid[])''', (ids,)).fetchall()
            readonly = db.execute("SELECT current_setting('transaction_read_only') readonly").fetchone()['readonly']
        indexed = {r['id']: r for r in rows}
        for image in completed:
            row = indexed.get(image['target_ids'][target])
            expected = before[image['artwork_id']]
            if not row or row['metadata'] != expected['metadata'] or row['creators'] != expected['creators']:
                errors.append({'id': image['artwork_id'], 'target': target, 'error': 'Metadata/creator preimage differs'})
                continue
            m, ev = row['media'], row['evidence']
            if row['primary_media_id'] != image['media_id'] or not m or not ev:
                errors.append({'id': image['artwork_id'], 'target': target, 'error': 'Media/evidence link missing'})
                continue
            fields = {'storage_path':'path','checksum_sha256':'sha256','byte_size':'bytes','width':'width','height':'height',
                      'rights_status':'rights_status','license_url':'policy_url'}
            if any(m[k] != image[v] for k,v in fields.items()) or ev['source_image_url'] != image['source_image_url'] or ev['source_checksum'] != core.sha(core.encode(image['raw'])):
                errors.append({'id': image['artwork_id'], 'target': target, 'error': 'Media metadata or rights evidence differs'})
            if image.get('creator_credit') and m['creator_credit'] != image['creator_credit']:
                errors.append({'id': image['artwork_id'], 'target': target, 'error': 'Photographic attribution missing'})
            if m['attribution_text'] != attachment_attribution(image):
                errors.append({'id': image['artwork_id'], 'target': target, 'error': 'Exact attribution text differs'})
            if image['provider'] == 'italy-primary-photo':
                approval = next((r for r in load(run / 'visual-review.json')['images'] if r['artwork_id'] == image['artwork_id']), {})
                if ev.get('evidence_json', {}).get('primary_catalogue_comparison') != approval.get('primary_catalogue_comparison'):
                    errors.append({'id': image['artwork_id'], 'target': target, 'error': 'Primary catalogue visual-comparison evidence differs'})
        reports[target] = {'rows': len(rows), 'read_only': readonly, 'metadata_and_creators_compared': True}
    public = []
    if completed:
        token = subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-editor-token',
                                         '--project=artline-508319'], text=True).strip()
        indices = range(len(completed)) if all_served else sorted({0, len(completed)//2, len(completed)-1})
        for index in indices:
            im = completed[index]
            asset = requests.get('https://artline-web-lpuqqlugnq-ew.a.run.app' + im['path'], timeout=35)
            api = requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/museums/' + im['institution_slug'] + '/works/' + im['target_ids']['cloud'] + '?preview=1', headers={'Authorization':'Bearer ' + token}, timeout=35)
            payload = api.json() if api.status_code == 200 else {}
            api_ok = api.status_code == 200 and all(payload.get(k) == im[v] for k,v in {
                'media_url':'path','title':'title','rights_status':'rights_status',
                'license_url':'policy_url','status':'status'}.items()) and payload.get('attribution_text') == attachment_attribution(im)
            asset_ok = asset.status_code == 200 and core.sha(asset.content) == im['sha256']
            public.append({'artwork_id':im['artwork_id'],'asset_status':asset.status_code,'asset_sha256_matches':asset_ok,
                           'preview_api_status':api.status_code,'preview_title_and_image':bool(api_ok),
                           'preview_exact_media_rights_credit_and_status':bool(api_ok)})
            if not asset_ok or not api_ok:
                errors.append({'id':im['artwork_id'],'error':'Served asset or preview API verification failed'})
    result = {'checked_at':core.now(),'complete_in_both':len(completed),'targets':reports,'public_checks':public,
              'errors':errors,'artwork_publication_status_preserved':True,'max_bytes':max([r['bytes'] for r in completed] or [0]),
              'served_checks_cover_every_completed_image':all_served,
              'completed_image_sha256s':{r['artwork_id']:r['sha256'] for r in completed},
              'completed_artwork_ids':[r['artwork_id'] for r in completed],
              'by_institution':dict(collections.Counter(r['institution_name'] for r in completed))}
    save(run / ('verification-' + str(time.time_ns()) + '.json'), result)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['audit', 'backup', 'select', 'research', 'native-research', 'prepare', 'apply', 'verify'])
    p.add_argument('--provider', default='commons')
    p.add_argument('--limit', type=int, default=100)
    p.add_argument('--label', default='round-01-italian-holdings-commons')
    p.add_argument('--work-type', choices=['painting','drawing','print'], default='painting')
    p.add_argument('--all-served', action='store_true', help='Verify each completed served image and its exact preview credits')
    a = p.parse_args()
    if a.phase == 'audit': audit()
    elif a.phase == 'backup': backup()
    elif a.phase == 'select': select(a.provider, a.limit, a.label, a.work_type)
    elif a.phase == 'research': research(a.label, a.limit)
    elif a.phase == 'native-research': native_research(a.label, a.limit)
    elif a.phase == 'prepare': prepare(a.label, a.limit)
    elif a.phase == 'apply': apply(a.label, a.limit)
    else: verify(a.label, a.all_served)
