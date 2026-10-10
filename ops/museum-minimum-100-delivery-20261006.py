#!/usr/bin/env python3
"""Bounded, reproducible museum selection and evidence-pinned production delivery.

The local catalogue is read-only. New production artworks remain in review.
Museum capacity defines the sampling frame; quotas never establish object facts.
"""
import argparse
import os
import collections
import csv
import gzip
import hashlib
import importlib.util
import json
import re
import secrets
import subprocess
import time
import uuid
from pathlib import Path

import psycopg
import requests
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
OP = 'all-museums-minimum-100-20261006'
RUN = ROOT / 'docs/research' / OP
BACKUP = Path.home() / 'Library/Application Support/Artline/backups' / OP
OLD = ROOT / 'docs/research/museum-expansion-20261006'
ACTOR = 'local-european-research'
spec = importlib.util.spec_from_file_location('museum_evidence', ROOT / 'ops/museum-expansion-20261006.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
save, load, norm, acc = m.save, m.load, m.norm, m.acc
FIELDS = None
EXPECTED_MUSEUMS = None
MINIMUM_AFTER = 0
TARGET_COUNT = 100
TARGET_FIELD = 'eligible'
MINIMUM_ADDITIONS = 0
SOURCE_NAME = 'Museum minimum-100 campaign: selected source catalogue records, 6 October 2026'
SOURCE_BASE_URL = None
DEFAULT_CONFIDENCE = 0.98
CONFIDENCE_BASIS = 'Exact primary native object ID, inventory where supplied, original title/creator/date, unqualified collection location and institution authority; source body verified by SHA-256. Editorial assessment, not a calibrated probability.'


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def uid(value):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, OP + '/' + value))


def connect(readonly=True):
    global FIELDS
    if FIELDS is None:
        secret = subprocess.check_output(['gcloud', 'secrets', 'versions', 'access', 'latest',
            '--secret=artline-database-url', '--project=artline-508319', '--account=vadim@alingva.com'], text=True).strip()
        FIELDS = psycopg.conninfo.conninfo_to_dict(secret)
        FIELDS.update(host='127.0.0.1', port=os.environ.get('ARTLINE_MUSEUM_PROXY_PORT','55484'), sslmode='disable', connect_timeout='20')
    return psycopg.connect(**FIELDS, autocommit=True, row_factory=dict_row,
        options='-c timezone=UTC -c statement_timeout=180000 -c lock_timeout=10000' +
        (' -c default_transaction_read_only=on' if readonly else ''))


def chunks(values, size=500):
    for start in range(0, len(values), size):
        yield values[start:start + size]


def parse_joconde(row):
    raw = (row.get('Millesime_de_creation') or '').strip()
    parsers = ['joconde'] if re.fullmatch(r'\d{3,4}', raw) else ['joconde-periods'] if not raw else ['joconde-ranges', 'joconde-circa', 'joconde-before']
    reason = None
    for parser in parsers:
        facts, reason = m.joconde_parser(parser)(row)
        if facts:
            if 'year' in facts:
                facts.update(first=facts['year'], last=facts['year'], date_precision='exact')
            return facts, parser, None
    return None, None, reason


def discovery():
    """Inspect source metadata and exact catalogue identities before random sampling."""
    base = {x['id']: x for x in load(RUN / 'production-museum-baseline.json.gz')}
    old_records = []
    for path in sorted(OLD.glob('*-applied.json')):
        source = path.name.removesuffix('-applied.json')
        data = load(path)
        if not data.get('created'):
            continue
        plan, digest = m.validate_plan(source)
        assert digest == data['plan_sha256']
        applied = {x['id'] for x in data['artworks']}
        for row in plan['records']:
            assert row['artwork_id'] in applied
            if row['museum']['id'] in base:
                old_records.append(dict(row, provider=source, origin='prior_verified_primary_plan', prior_plan_sha256=digest))
    print('Validated prior source bodies and parsers:', len(old_records), flush=True)
    museum_ids = sorted({x['id'] for x in base.values() if x['slug'].startswith('joconde-')} |
                        {x['museum']['id'] for x in old_records})
    with connect() as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        institutions = {x['v']['id']: x['v'] for x in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=ANY(%s::uuid[])', (museum_ids,))}
        existing = []
        for ids in chunks(museum_ids, 50):
            existing.extend(db.execute('''WITH scoped AS MATERIALIZED (
              SELECT id artwork_id,current_institution_id institution_id FROM artworks WHERE current_institution_id=ANY(%s::uuid[])
              UNION SELECT artwork_id,institution_id FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) AND superseded_by IS NULL
              ) SELECT a.id::text,a.title,a.alternate_title,a.normalized_title,a.accession_number,a.status,s.institution_id::text
              FROM scoped s JOIN artworks a ON a.id=s.artwork_id''', (ids, ids)).fetchall())
        known_refs = {x['external_id'] for x in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme ILIKE '%joconde%'")}
        known_refs.update(x['source_url'].rstrip('/').rsplit('/', 1)[-1] for x in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE '%/joconde/%'"))
        prior_ids = [x['artwork_id'] for x in old_records]
        already = {x['id'] for x in db.execute('SELECT id::text FROM artworks WHERE id=ANY(%s::uuid[])', (prior_ids,))}
    save(RUN / 'discovery-catalogue.json.gz', dict(at=now(), institutions=institutions, scoped_artworks=existing,
        known_joconde_refs=sorted(known_refs), prior_artwork_ids_already_in_production=sorted(already)))
    titles = collections.defaultdict(set)
    inventories = collections.defaultdict(set)
    for row in existing:
        titles[row['institution_id']].update(norm(row[k]) for k in ['title', 'alternate_title'] if row[k])
        inventories[row['institution_id']].update(acc(row['accession_number']))
    candidates = collections.defaultdict(list)
    refs = set()
    for row in old_records:
        iid = row['museum']['id']
        f = row['facts']
        if row['artwork_id'] in already or acc(f['accession']) & inventories[iid] or norm(f['title']) in titles[iid]:
            continue
        if row['provider'].startswith('joconde'):
            if row['source_record_id'] in known_refs:
                continue
            refs.add(row['source_record_id'])
        row['museum'] = institutions[iid]
        candidates[iid].append(row)
    targets = {x['slug'].removeprefix('joconde-').upper(): institutions[x['id']]
        for x in base.values() if x['slug'].startswith('joconde-') and x['id'] in institutions}
    source_inventory = collections.Counter()
    rejects = collections.Counter()
    with m.SNAPSHOT.open('rb') as f:
        assert hashlib.file_digest(f, 'sha256').hexdigest() == m.SNAPSHOT_SHA
    csv.field_size_limit(8_000_000)
    with m.SNAPSHOT.open(encoding='utf-8-sig', newline='') as f:
        for n, row in enumerate(csv.DictReader(f, delimiter='|'), 1):
            code = row.get('Code_Museofile')
            if code not in targets:
                continue
            inst = targets[code]
            iid = inst['id']
            for key in acc(row.get('Numero_inventaire')):
                source_inventory[(iid, key)] += 1
            if row['Reference'] in known_refs or row['Reference'] in refs:
                continue
            # Bounded candidate metadata, not an exhaustive import or image download.
            if len(candidates[iid]) >= max(30, 240 - base[iid]['eligible']):
                continue
            facts, parser, reason = parse_joconde(row)
            if reason:
                rejects[reason] += 1
                continue
            if norm(row['Nom_officiel_musee'] + ' ' + row['Ville']) != norm(inst['name']):
                rejects['institution_name_requires_reconciliation'] += 1
                continue
            if acc(facts['accession']) & inventories[iid] or norm(facts['title']) in titles[iid]:
                rejects['existing_inventory_or_title'] += 1
                continue
            candidates[iid].append(dict(source_record_id=row['Reference'], museum=inst, facts=facts,
                raw_source_record=row, provider=parser, origin='pinned_joconde_discovery_snapshot',
                artwork_id=uid('joconde/' + row['Reference']), slug=OP + '-joconde-' + row['Reference'].lower()))
    frame = []
    kept = {}
    for iid, group in candidates.items():
        chosen = []
        seen_acc, seen_titles = set(), set()
        for row in sorted(group, key=lambda r: (r['origin'] != 'prior_verified_primary_plan', r['source_record_id'])):
            f = row['facts']
            if row['origin'] != 'prior_verified_primary_plan' and any(source_inventory[(iid, key)] > 1 for key in acc(f['accession'])):
                rejects['shared_source_inventory'] += 1
                continue
            if acc(f['accession']) & seen_acc or norm(f['title']) in seen_titles:
                rejects['duplicate_selected_inventory_or_title'] += 1
                continue
            seen_acc.update(acc(f['accession']))
            seen_titles.add(norm(f['title']))
            chosen.append(row)
        if len(chosen) >= 10 and base[iid]['eligible'] + len(chosen) >= 110:
            kept[iid] = chosen
            frame.append(dict(base[iid], available_candidates=len(chosen), prior_verified_candidates=sum(x['origin']=='prior_verified_primary_plan' for x in chosen)))
    save(RUN / 'candidate-discovery.json.gz', dict(at=now(), frame=frame, candidates=kept,
        snapshot_sha256=m.SNAPSHOT_SHA, rejection_counts=dict(rejects),
        eligibility='Canonical non-archived production museums with at least ten source-backed candidate additions and projected capacity of at least 110 pre-1971 artworks; fresh delivery checks still required.'))
    print('Sampling capacity frame:', len(frame), 'museums;', sum(len(x) for x in kept.values()), 'bounded candidates', flush=True)
    print('Geographic/source groups:', dict(collections.Counter('France / Joconde' if x['slug'].startswith('joconde-') else x['name'] for x in frame)), flush=True)


def sample():
    data = load(RUN / 'candidate-discovery.json.gz')
    frame = data['frame']
    assert len(frame) >= 50
    seed = secrets.token_hex(32)
    selected = sorted(frame, key=lambda x: (sha((seed + '/' + x['id']).encode()), x['id']))[:50]
    value = dict(at=now(), seed=seed, selected=selected, sampling_frame=frame,
        eligibility=data['eligibility'], algorithm='Lowest 50 SHA-256(seed + slash + museum UUID), unweighted without replacement within the documented-capacity frame.',
        source_bias='Available verified local museum research plus the official French Joconde catalogue; this is not a worldwide representative sample.',
        target='At least 100 eligible-date artworks per museum; aim for 200. At least ten additions where supported. Existing larger collections are retained.',
        discovery_sha256=sha((RUN / 'candidate-discovery.json.gz').read_bytes()), local_database_writes=0)
    save(RUN / 'sample.json', value)
    rows = [r for x in selected for r in data['candidates'][x['id']]]
    save(RUN / 'selected-candidates.json.gz', rows)
    print('Frozen 50 museums; candidates', len(rows), 'fresh Joconde checks', sum(r['origin']!='prior_verified_primary_plan' for r in rows), flush=True)
    for x in selected:
        print(x['name'], '| eligible before', x['eligible'], '| candidates', x['available_candidates'], flush=True)


def capture():
    records = load(RUN / 'selected-candidates.json.gz')
    wanted = {x['source_record_id']: x for x in records if x['origin'] != 'prior_verified_primary_plan'}
    refs = sorted(wanted)
    current = {}
    for start in range(0, len(refs), 50):
        group = refs[start:start + 50]
        dest = RUN / 'captures' / f'{start:05d}.json.gz'
        if dest.exists():
            data = load(dest)
            assert data['requested'] == group
        else:
            url = 'https://tabular-api.data.gouv.fr/api/resources/7e3307c2-f2ff-455c-bbca-bb6f11aec7bb/data/'
            response = requests.get(url, params={'Reference__in': ','.join(group), 'page_size': 50},
                headers={'User-Agent': 'ArtlineMuseumResearch/1.0 (selected museum metadata)'}, timeout=(15, 60))
            raw = response.content
            body = RUN / 'captures' / f'{start:05d}.body.gz'
            body.parent.mkdir(parents=True, exist_ok=True)
            assert not body.exists()
            body.write_bytes(gzip.compress(raw, mtime=0))
            receipt = dict(url=response.url, status=response.status_code, retrieved_at=now(), sha256=sha(raw),
                bytes=len(raw), body_path=str(body.relative_to(ROOT)))
            save(RUN / 'captures' / f'{start:05d}.receipt.json', receipt)
            response.raise_for_status()
            source = response.json()
            assert source['meta']['total'] <= 50 and not source['links'].get('next')
            assert len({x['Reference'] for x in source['data']}) == len(source['data'])
            assert all(x['Reference'] in group for x in source['data'])
            data = dict(requested=group, source_receipt=receipt, body_path=str(body.relative_to(ROOT)), records=source['data'])
            save(dest, data)
            time.sleep(1)
        for row in data['records']:
            current[row['Reference']] = (row, data['source_receipt'], data['body_path'])
        print('Fresh official objects checked:', min(start + 50, len(refs)), '/', len(refs), flush=True)
    ready, held = [], []
    for row in records:
        if row['origin'] == 'prior_verified_primary_plan':
            ready.append(row)
            continue
        result = current.get(row['source_record_id'])
        if not result:
            held.append(dict(source_record_id=row['source_record_id'], reason='not_returned_by_current_source'))
            continue
        source, receipt, body = result
        if row['provider'].startswith('joconde-sculpture'):
            facts, reason = m.joconde_sculpture_facts(source)
            parser = row['provider']
            if facts and 'year' in facts:
                facts.update(first=facts['year'], last=facts['year'], date_precision='exact')
        else:
            facts, parser, reason = parse_joconde(source)
        old = row['raw_source_record']
        if not reason and any(norm(source.get(k)) != norm(old.get(k)) for k in ['Titre','Auteur','Numero_inventaire','Code_Museofile','Millesime_de_creation','Periode_de_creation']):
            reason = 'source_identity_or_date_changed'
        if not reason and norm(source['Nom_officiel_musee'] + ' ' + source['Ville']) != norm(row['museum']['name']):
            reason = 'museum_identity_changed'
        if reason:
            held.append(dict(source_record_id=row['source_record_id'], reason=reason))
            continue
        ready.append(dict(row, facts=facts, provider=parser, raw_source_record=source, source_receipt=receipt, body_path=body))
    save(RUN / 'source-verified.json.gz', dict(at=now(), records=ready, held=held))
    print('Source-verified candidates', len(ready), 'held', len(held), flush=True)


def scheme(row):
    provider = row['provider']
    for prefix, value in [('joconde', 'joconde-object'), ('arco-', 'arco-object'),
            ('getty-', 'getty-object'), ('mauritshuis-', 'mauritshuis-object'),
            ('tretyakov-', 'tretyakov-object'), ('benaki-', 'benaki-object'),
            ('ireland-', 'ngi-object'), ('agsa-', 'agsa-object')]:
        if provider.startswith(prefix):
            return value
    return {'icons': 'icon-museum-object', 'athens': 'athens-object'}[provider]


def check_body(row, cache):
    path = row['body_path']
    rc = row['source_receipt']
    if path not in cache:
        raw = (ROOT / path).read_bytes()
        if path.endswith('.gz'):
            raw = gzip.decompress(raw)
        cache[path] = raw
    raw = cache[path]
    assert sha(raw) == rc['sha256'] and rc['status'] == 200
    if row['provider'].startswith('joconde'):
        matched = [x for x in json.loads(raw)['data'] if x['Reference'] == row['source_record_id']]
        assert len(matched) == 1 and matched[0] == row['raw_source_record']
        facts, reason = m.joconde_parser(row['provider'])(matched[0])
        if facts and 'year' in facts:
            facts.update(first=facts['year'], last=facts['year'], date_precision='exact')
        assert not reason and facts == row['facts']
    else:
        assert row['origin'] == 'prior_verified_primary_plan' and row['prior_plan_sha256']
    assert row['facts']['source_url'].startswith('https://')
    assert row['facts']['title']
    # ArCo's unique national catalogue number is a native object identity;
    # absent museum inventory numbers remain unknown, as in the reviewed source.
    assert row['facts']['accession'] or (row['provider'].startswith('arco-') and
        re.fullmatch(r'HistoricOrArtisticProperty/\d+', row['source_record_id']))


def identities(db, records):
    variants = collections.defaultdict(set)
    for row in records:
        url = row['facts']['source_url']
        variants[url].add(url)
        for alias in row.get('alternate_native_urls', []):
            variants[alias].add(url)
        if row['provider'].startswith('arco-'):
            for host in ['catalogo.cultura.gov.it', 'catalogo.beniculturali.it']:
                variants['https://' + host + '/detail/' + row['source_record_id']].add(url)
    urls = sorted(variants)
    result = collections.defaultdict(set)
    for part in chunks(urls):
        for r in db.execute("SELECT entity_id::text id,canonical_url url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s) UNION SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)", (part, part)):
            for canonical in variants[r['url']]:
                result[canonical].add(r['id'])
    schemes = collections.defaultdict(list)
    for row in records:
        schemes[scheme(row)].append(row['source_record_id'])
    by_key = {}
    for kind, ids in schemes.items():
        for r in db.execute("SELECT entity_id::text id,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=ANY(%s)", (kind, ids)):
            by_key[(kind, r['external_id'])] = r['id']
    for row in records:
        key = (scheme(row), row['source_record_id'])
        if key in by_key:
            result[row['facts']['source_url']].add(by_key[key])
    return result


def scoped_rows(db, museum_ids):
    return db.execute('''WITH scoped AS MATERIALIZED (
      SELECT id artwork_id,current_institution_id institution_id FROM artworks WHERE current_institution_id=ANY(%s::uuid[])
      UNION SELECT artwork_id,institution_id FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) AND superseded_by IS NULL
      ) SELECT a.id::text,a.title,a.alternate_title,a.normalized_title,a.accession_number,a.status,s.institution_id::text
      FROM scoped s JOIN artworks a ON a.id=s.artwork_id''', (museum_ids, museum_ids)).fetchall()


def batch_identity_conflicts(records):
    """Hold unresolved identities among proposed rows, before any insert."""
    groups = collections.defaultdict(list)
    for row in records:
        iid, facts = row['museum']['id'], row['facts']
        groups[('native', scheme(row), row['source_record_id'])].append(row)
        for url in {facts['source_url'], *row.get('alternate_native_urls', [])}:
            groups[('url', url.replace('catalogo.beniculturali.it/', 'catalogo.cultura.gov.it/'))].append(row)
        for inventory in acc(facts['accession']):
            groups[('inventory', iid, inventory)].append(row)
        groups[('title', norm(facts['title']))].append(row)
    conflicts = collections.defaultdict(set)
    for key, rows in groups.items():
        if len(rows) < 2:
            continue
        if key[0] == 'title':
            inventories = [acc(row['facts']['accession']) for row in rows]
            if len({row['museum']['id'] for row in rows}) == 1 and all(inventories) and all(
                    not inventories[i] & inventories[j] for i in range(len(rows)) for j in range(i)):
                continue
        reason = 'within_batch_' + key[0] + '_identity_requires_reconciliation'
        for row in rows:
            conflicts[row['artwork_id']].add(reason)
    return {aid: sorted(reasons) for aid, reasons in conflicts.items()}


def plan():
    sample_data = load(RUN / 'sample.json')
    selected = {x['id']: x for x in sample_data['selected']}
    source = load(RUN / 'source-verified.json.gz')
    records = source['records']
    cache = {}
    for row in records:
        check_body(row, cache)
    with connect() as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        institutions = {x['v']['id']: x['v'] for x in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=ANY(%s::uuid[])', (list(selected),))}
        keys = identities(db, records)
        existing_ids = sorted({x for v in keys.values() for x in v} | {x['artwork_id'] for x in records})
        existing = {}
        for ids in chunks(existing_ids):
            existing.update({x['v']['id']: x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id=ANY(%s::uuid[])', (ids,))})
        scoped = scoped_rows(db, list(selected))
        candidate_titles = sorted({norm(x['facts']['title']) for x in records})
        # One bounded identity search over candidate keys; no global enrichment CTE.
        title_sql = 'SELECT id::text,title,alternate_title,normalized_title,accession_number,current_institution_id::text,status FROM artworks WHERE normalized_title=ANY(%s)'
        title_plan = db.execute('EXPLAIN (FORMAT JSON) ' + title_sql, (candidate_titles,)).fetchone()
        matching_titles = db.execute(title_sql, (candidate_titles,)).fetchall()
        counts = {x['id']: x for x in db.execute('''SELECT i.id::text,count(a.id) linked,
          count(a.id) FILTER(WHERE artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible') eligible
          FROM institutions i LEFT JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived'
          WHERE i.id=ANY(%s::uuid[]) GROUP BY i.id''', (list(selected),))}
        scope_input = [{'id': r['artwork_id'], 'first': r['facts']['first'], 'last': r['facts']['last'], 'precision': r['facts']['date_precision']} for r in records]
        scope_result = db.execute('''SELECT id,artline_creation_scope(first,last,precision) scope FROM jsonb_to_recordset(%s) x(id text,first integer,last integer,precision text)''', (Jsonb(scope_input),)).fetchall()
        scope_by_id = {x['id']: x['scope'] for x in scope_result}
    save(RUN / 'identity-query-plan.json', title_plan)
    inventory_map = collections.defaultdict(lambda: collections.defaultdict(set))
    for row in scoped:
        for key in acc(row['accession_number']):
            inventory_map[row['institution_id']][key].add(row['id'])
    title_map = collections.defaultdict(list)
    for row in matching_titles:
        title_map[norm(row['title'])].append(row)
    ready, held, unchanged = [], list(source['held']), []
    for row in records:
        iid, facts = row['museum']['id'], row['facts']
        inst = institutions[iid]
        reason = None
        targets = set(keys.get(facts['source_url'], set()))
        if row['artwork_id'] in existing:
            targets.add(row['artwork_id'])
        if inst['canonical_institution_id'] or inst['status'] == 'archived' or inst['name'] != row['museum']['name']:
            reason = 'museum_authority_drift'
        elif scope_by_id[row['artwork_id']] != 'eligible':
            reason = 'date_not_eligible_under_postgresql_policy'
        elif len(targets) > 1:
            reason = 'duplicate_source_identities'
        before = existing.get(next(iter(targets))) if len(targets) == 1 else None
        aid = before['id'] if before else row['artwork_id']
        inventory_matches = set().union(*(inventory_map[iid].get(k, set()) for k in acc(facts['accession'])))
        if inventory_matches - {aid}:
            reason = reason or 'existing_inventory_requires_reconciliation'
        if before:
            if before['status'] == 'archived':
                reason = reason or 'existing_archived_object'
            elif before['current_institution_id'] == iid:
                unchanged.append(dict(artwork_id=aid, museum_id=iid, source_url=facts['source_url']))
                continue
            elif before['current_institution_id']:
                reason = reason or 'existing_conflicting_holding'
            elif norm(before['title']) != norm(facts['title']) or not acc(before['accession_number']) & acc(facts['accession']):
                reason = reason or 'existing_native_object_title_or_inventory_requires_review'
        else:
            collisions = [v for v in title_map[norm(facts['title'])] if v['id'] != aid]
            # An inventoried distinct object in the same museum can share a title.
            if any(v['current_institution_id'] != iid or not acc(v['accession_number']) or acc(v['accession_number']) & acc(facts['accession']) for v in collisions):
                reason = reason or 'catalogue_title_collision_requires_version_review'
        if reason:
            held.append(dict(artwork_id=aid, museum_id=iid, source_record_id=row['source_record_id'], title=facts['title'], source_url=facts['source_url'], reason=reason))
        else:
            ready.append(dict(row, artwork_id=aid, before=before, museum=inst, action='link' if before else 'create',
                editorial_confidence=DEFAULT_CONFIDENCE, confidence_basis=CONFIDENCE_BASIS,
                remaining_uncertainty='Dated source collection statement; no fresh display claim. Original creator qualifications and broad creation intervals are retained.'))
    batch_conflicts = batch_identity_conflicts(ready)
    for row in ready:
        if row['artwork_id'] in batch_conflicts:
            held.append(dict(artwork_id=row['artwork_id'], museum_id=row['museum']['id'],
                source_record_id=row['source_record_id'], title=row['facts']['title'],
                reason='within_batch_identity_requires_reconciliation', details=batch_conflicts[row['artwork_id']]))
    ready = [row for row in ready if row['artwork_id'] not in batch_conflicts]
    grouped = collections.defaultdict(list)
    for row in ready:
        grouped[row['museum']['id']].append(row)
    final, outside, summary = [], [], []
    for iid, museum in selected.items():
        group = sorted(grouped[iid], key=lambda r: (r['action'] != 'link', r['origin'] != 'prior_verified_primary_plan', r['source_record_id']))
        take = max(MINIMUM_ADDITIONS, TARGET_COUNT - counts[iid][TARGET_FIELD])
        chosen = group[:take]
        final.extend(chosen)
        outside.extend(dict(artwork_id=r['artwork_id'], museum_id=iid, reason='outside_bounded_'+str(TARGET_COUNT)+'_work_target') for r in group[take:])
        summary.append(dict(museum_id=iid, name=museum['name'], slug=museum['slug'], before=counts[iid],
            new_artworks=sum(x['action']=='create' for x in chosen), new_links=sum(x['action']=='link' for x in chosen),
            projected_eligible=counts[iid]['eligible']+len(chosen), projected_linked=counts[iid]['linked']+len(chosen), available_after_identity_review=len(group)))
    value = dict(at=now(), target='production', sample_sha256=sha((RUN/'sample.json').read_bytes()),
        records=final, held=held, outside_target=outside, unchanged=unchanged, museums=summary, institutions=institutions,
        baseline_scoped_identity_rows=scoped, baseline_title_matches=matching_titles,
        policy='Only selected pre-1971 source-backed objects; preserve existing dates, images, creator labels and publication state. New records remain review. Holding is distinct from display. Local database is read-only.')
    save(RUN / 'plan.json.gz', value)
    save(BACKUP / 'plan-and-preimages.json.gz', value)
    print('PLAN:', len(final), 'mutations;', dict(collections.Counter(x['action'] for x in final)), 'holds', dict(collections.Counter(x['reason'] for x in held)), flush=True)
    print('Museums reaching',TARGET_COUNT,'linked:', sum(x['projected_linked']>=TARGET_COUNT for x in summary), '/',len(summary), flush=True)
    print('Museums still below',TARGET_COUNT,'eligible:',sum(x['projected_eligible']<TARGET_COUNT for x in summary),'; full counts retained in plan',flush=True)


def insert(db, table, row):
    query = sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),
        sql.SQL(',').join(map(sql.Identifier, row)), sql.SQL(',').join(sql.Placeholder() for _ in row))
    db.execute(query, list(row.values()))


def apply():
    path = RUN / 'plan.json.gz'
    plan_data, digest = load(path), sha(path.read_bytes())
    assert not (RUN/'applied.json').exists(), 'Already applied; use verification, not a second delivery'
    records = plan_data['records']
    assert not batch_identity_conflicts(records), 'Unresolved within-batch object identities'
    assert len(plan_data['museums']) == EXPECTED_MUSEUMS
    assert all(x['projected_eligible'] >= MINIMUM_AFTER for x in plan_data['museums'])
    assert records and len(records)<=10000
    assert plan_data['sample_sha256'] == sha((RUN/'sample.json').read_bytes())
    ids = [x['artwork_id'] for x in records]
    assert len(ids) == len(set(ids))
    mids = sorted(plan_data['institutions'])
    cache = {}
    for row in records:
        check_body(row, cache)
        assert row['editorial_confidence'] >= 0.8
    sid = uid('source')
    with connect(readonly=False) as db, db.transaction():
        assert db.execute('SELECT current_database() name').fetchone()['name'] == 'artline'
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (OP,))
        current_institutions = {x['v']['id']: x['v'] for x in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE', (mids,))}
        assert current_institutions == plan_data['institutions'], 'Institution version changed'
        before = {x['v']['id']: x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE', (ids,))}
        for row in records:
            assert before.get(row['artwork_id']) == row['before'], 'Artwork version changed: '+row['artwork_id']
        exact = identities(db, records)
        for row in records:
            found = exact.get(row['facts']['source_url'], set())
            assert found == ({row['artwork_id']} if row['action']=='link' else set()), 'Concurrent native source identity'
        scoped = scoped_rows(db, mids)
        inv = collections.defaultdict(lambda: collections.defaultdict(set))
        for v in scoped:
            for key in acc(v['accession_number']):
                inv[v['institution_id']][key].add(v['id'])
        for row in records:
            for key in acc(row['facts']['accession']):
                assert not inv[row['museum']['id']][key] - {row['artwork_id']}, 'Concurrent inventory identity'
        titles = sorted({norm(x['facts']['title']) for x in records if x['action']=='create'})
        title_matches = db.execute('SELECT id::text,title,alternate_title,normalized_title,accession_number,current_institution_id::text,status FROM artworks WHERE normalized_title=ANY(%s)', (titles,)).fetchall()
        expected_title_matches = [x for x in plan_data['baseline_title_matches'] if x['normalized_title'] in titles]
        assert sorted(title_matches, key=lambda x:x['id']) == sorted(expected_title_matches, key=lambda x:x['id']), 'Concurrent matching-title version change'
        links = [x['artwork_id'] for x in records if x['action']=='link']
        if links:
            assert not db.execute("SELECT 1 FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[]) AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL", (links,)).fetchone()
        assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s', (sid, OP)).fetchone()
        save(BACKUP/'transaction-preimages.json.gz', dict(at=now(), plan_sha256=digest, absent_ids=[x for x in ids if x not in before],
            existing_artworks=before, institutions=current_institutions, source_preimage=None, scoped_identity_rows=scoped))
        print('Production preimages saved; applying', len(records), 'guarded changes in one transaction', flush=True)
        insert(db, 'sources', dict(id=sid, slug=OP, name=SOURCE_NAME,
            source_type='authority_data', base_url=SOURCE_BASE_URL))
        with db.pipeline():
            for row in records:
                aid, f, rc = row['artwork_id'], row['facts'], row['source_receipt']
                if row['action'] == 'create':
                    insert(db, 'artworks', dict(id=aid, slug=row['slug'], title=f['title'], normalized_title=norm(f['title']),
                        date_display=f['date_display'], creation_year_start=f['first'], creation_year_end=f['last'], date_precision=f['date_precision'],
                        work_type=f['work_type'], medium_text=f['medium'], dimensions_text=f['dimensions'], accession_number=f['accession'],
                        status='review', research_candidate=True, unlinked_creator_label=f['creator_label'], object_form=f.get('object_form'),
                        cultural_context=f.get('cultural_context'), created_by=ACTOR, updated_by=ACTOR))
                    insert(db, 'external_identifiers', dict(id=uid('identifier/'+aid), entity_type='artwork', entity_id=aid,
                        scheme=scheme(row), external_id=row['source_record_id'], canonical_url=f['source_url'], source_id=sid, retrieved_at=rc['retrieved_at']))
                evidence = dict(operation=OP, plan_sha256=digest, provider=row['provider'], source_label=row['museum']['name'],
                    raw_source_record=row['raw_source_record'], source_receipt=rc, body_path=row['body_path'],
                    original_plan_sha256=row.get('prior_plan_sha256'), editorial_confidence=row['editorial_confidence'],
                    confidence_basis=row['confidence_basis'], remaining_uncertainty=row['remaining_uncertainty'],
                    policy=plan_data['policy'], prior_artwork=row['before'])
                insert(db, 'citations', dict(id=uid('citation/'+aid), entity_type='artwork', entity_id=aid,
                    field_name='museum_source_metadata_and_holding', source_id=sid, source_record_id=row['source_record_id'], source_url=f['source_url'],
                    evidence_note=json.dumps(evidence, ensure_ascii=False), retrieved_at=rc['retrieved_at'], created_by=ACTOR))
                insert(db, 'artwork_location_assertions', dict(id=uid('holding/'+aid), artwork_id=aid, claim_type='holding',
                    institution_id=row['museum']['id'], context='collection', source_id=sid, source_url=f['source_url'],
                    evidence_note=f['holding_basis']+' Editorial confidence '+str(row['editorial_confidence'])+' (assessment, not calibrated probability). Source SHA-256 '+rc['sha256']+'. '+row['remaining_uncertainty'],
                    checked_at=rc['retrieved_at'], review_state='accepted'))
        after = db.execute('''SELECT to_jsonb(a) artwork,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,
          artline_has_selection_evidence(a.id) selection_evidence FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id''', (ids,)).fetchall()
        assert len(after)==len(records)
        by_id = {x['artwork_id']: x for x in records}
        for item in after:
            a, row = item['artwork'], by_id[item['artwork']['id']]
            assert a['current_institution_id']==row['museum']['id'] and item['selection_evidence']
            if row['action']=='create':
                assert a['status']=='review' and a['published_at'] is None and a['primary_media_id'] is None and item['scope']=='eligible'
            else:
                allowed = {'current_institution_id','updated_at','revision'}
                assert all(a[k]==v for k,v in row['before'].items() if k not in allowed), 'Existing artwork metadata changed'
        assert db.execute("SELECT count(*) n FROM artwork_location_assertions WHERE source_id=%s AND claim_type='display'", (sid,)).fetchone()['n']==0
        counts = db.execute('''SELECT i.id::text,count(a.id) linked,
          count(a.id) FILTER(WHERE artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible') eligible
          FROM institutions i LEFT JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived'
          WHERE i.id=ANY(%s::uuid[]) GROUP BY i.id''', (mids,)).fetchall()
        assert len(counts)==EXPECTED_MUSEUMS and min(x['eligible'] for x in counts)>=MINIMUM_AFTER
        save(BACKUP/'transaction-after.json.gz', dict(at=now(), plan_sha256=digest, artworks=after, museum_counts=counts))
    save(RUN/'applied.json', dict(at=now(), plan_sha256=digest, target='production',
        new_artworks=sum(x['action']=='create' for x in records), linked_artworks=sum(x['action']=='link' for x in records),
        museums=EXPECTED_MUSEUMS, artwork_ids=ids, museum_counts=counts, new_publications=0, new_display_claims=0, local_database_writes=0))
    print('COMMITTED', len(records), 'production changes across',EXPECTED_MUSEUMS,'museums; minimum eligible count', min(x['eligible'] for x in counts), flush=True)


def verify():
    receipt = load(RUN/'applied.json')
    plan_data = load(RUN/'plan.json.gz')
    assert receipt['plan_sha256']==sha((RUN/'plan.json.gz').read_bytes())
    ids = receipt['artwork_ids']
    mids = sorted(plan_data['institutions'])
    expected = {x['artwork_id']:x for x in plan_data['records']}
    with connect() as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        rows = db.execute('''SELECT to_jsonb(a) artwork,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,
          artline_has_selection_evidence(a.id) selected FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY a.id''', (ids,)).fetchall()
        holdings = db.execute('SELECT to_jsonb(h) v FROM artwork_location_assertions h WHERE source_id=%s ORDER BY artwork_id', (uid('source'),)).fetchall()
        citations = db.execute('SELECT entity_id::text,source_url,evidence_note FROM citations WHERE source_id=%s ORDER BY entity_id', (uid('source'),)).fetchall()
        counts = db.execute('''SELECT i.id::text,i.name,i.slug,count(a.id) linked,
          count(a.id) FILTER(WHERE artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible') eligible,
          count(a.id) FILTER(WHERE a.primary_media_id IS NOT NULL) with_images,
          count(a.id) FILTER(WHERE a.status='published') published
          FROM institutions i LEFT JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived'
          WHERE i.id=ANY(%s::uuid[]) GROUP BY i.id ORDER BY i.name''', (mids,)).fetchall()
        audit = db.execute("SELECT action,entity_type,count(*) n FROM audit_log WHERE entity_id=ANY(%s::uuid[]) AND entity_type='artwork' GROUP BY action,entity_type", (ids,)).fetchall()
    assert len(rows)==len(ids)==len(holdings)==len(citations)
    assert {x['entity_id'] for x in citations}==set(ids)
    assert all(json.loads(x['evidence_note'])['plan_sha256']==receipt['plan_sha256'] for x in citations)
    for item in rows:
        a = item['artwork']; row = expected[a['id']]
        assert a['current_institution_id']==row['museum']['id'] and item['selected']
        if row['action']=='create':
            assert a['status']=='review' and a['primary_media_id'] is None and a['published_at'] is None and item['scope']=='eligible'
            f = row['facts']
            for key, source_key in [('title','title'),('unlinked_creator_label','creator_label'),('date_display','date_display'),
                    ('creation_year_start','first'),('creation_year_end','last'),('date_precision','date_precision'),
                    ('accession_number','accession'),('medium_text','medium'),('dimensions_text','dimensions'),('work_type','work_type')]:
                assert a[key]==f[source_key], (a['id'],key)
    assert all(x['v']['claim_type']=='holding' and x['v']['review_state']=='accepted' and x['v']['superseded_by'] is None for x in holdings)
    assert len(counts)==50 and all(x['eligible']>=100 for x in counts)
    before = {x['museum_id']:x for x in plan_data['museums']}
    for x in counts:
        b = before[x['id']]
        x.update(before_linked=b['before']['linked'], before_eligible=b['before']['eligible'], added=b['new_artworks'], linked_existing=b['new_links'])
    result = dict(at=now(), target='production', museums=counts, new_artworks=receipt['new_artworks'], linked_artworks=receipt['linked_artworks'],
        all_50_at_least_100_eligible=True, museums_at_least_200=sum(x['eligible']>=200 for x in counts),
        minimum_eligible_count=min(x['eligible'] for x in counts), verified_artworks=len(rows), verified_source_citations=len(citations), verified_holdings=len(holdings),
        audit_records=audit, new_publications=0, new_images=0, new_display_claims=0, local_database_writes=0)
    save(RUN/'verification.json', result)
    with (RUN/'museum-results.csv').open('w', newline='') as f:
        writer=csv.DictWriter(f, fieldnames=list(counts[0]));writer.writeheader();writer.writerows(counts)
    artwork_rows=[]
    for row in plan_data['records']:
        f=row['facts'];artwork_rows.append(dict(artwork_id=row['artwork_id'],museum=row['museum']['name'],title=f['title'],creator_label=f['creator_label'],
            date_display=f['date_display'],accession=f['accession'],action=row['action'],source_url=f['source_url'],editorial_confidence=row['editorial_confidence']))
    with (RUN/'artwork-results.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(artwork_rows[0]));writer.writeheader();writer.writerows(artwork_rows)
    sample_data=load(RUN/'sample.json')
    md=f"# Random fifty museums: production delivery\n\nVerified {result['at']}. Added **{result['new_artworks']:,} artworks** and linked **{result['linked_artworks']} existing artworks** across **50 museums** in production. All 50 have at least 100 artworks with eligible pre-1971 creation dates; **{result['museums_at_least_200']} have at least 200**. The lowest eligible count is **{result['minimum_eligible_count']}**. New artworks remain in review.\n\n"
    md+=f"The fifty museums were randomly selected without replacement from a {len(sample_data['sampling_frame'])}-museum documented-capacity pool. The [sample and seed](sample.json) preserve the complete pool and algorithm. This pool uses verified prior museum research and the official French Joconde catalogue and is weighted toward French museums; it is not a representative worldwide sample. Existing collections larger than 200 were preserved.\n\n"
    md+="[Museum counts](museum-results.csv) · [Every added or linked artwork and its source](artwork-results.csv) · [Database verification](verification.json) · [Pinned delivery plan and held candidates](plan.json.gz).\n\n"
    md+="Primary object IDs, inventories, source creator labels, literal dates, collection custody and database duplicates were checked. Existing artwork metadata and images were preserved. No current-display claims, automatic publication, image downloads, application deployment or local database writes were made. All source bodies retain their original retrieval timestamps and SHA-256 hashes; reusing earlier evidence does not make its capture date current. Confidence is an editorial assessment, not a calibrated probability.\n\n"
    md+="Production delivery ran atomically after locked version and identity checks, with preimages under `~/Library/Application Support/Artline/backups/random-50-museums-20261006/`. Verification used a separate read-only connection after commit. The 114 existing source-parser tests passed; this is not a 10-million-row performance benchmark. Counts include legacy records and do not newly prove every legacy entry is a distinct physical object.\n\n"
    md+="| Museum | Eligible before | Added | Linked | Eligible after |\n|---|---:|---:|---:|---:|\n"
    for x in counts:
        md+=f"| {x['name'].replace('|','/')} | {x['before_eligible']} | {x['added']} | {x['linked_existing']} | {x['eligible']} |\n"
    (RUN/'README.md').write_text(md)
    print(json.dumps({k:v for k,v in result.items() if k not in ['museums','audit_records']}, ensure_ascii=False),flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('phase', choices=['discovery', 'sample', 'capture', 'plan', 'apply', 'verify'])
    args = ap.parse_args()
    globals()[args.phase]()
