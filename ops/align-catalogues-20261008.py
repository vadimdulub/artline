#!/usr/bin/env python3
"""Auditable catalogue alignment; credentials and member data stay target-local."""
import argparse
import collections
import concurrent.futures
import datetime
import gzip
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import uuid
import unicodedata

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
OP = 'catalogue-alignment-20261008'
RUN = ROOT / 'docs/research' / OP
BACKUP = Path.home() / 'Library/Application Support/Artline/backups' / OP
ACTOR = 'local-european-research'
SKIP = {'audit_log', 'editor_accounts', 'member_accounts', 'member_sessions',
        'atlas_drafts', 'schema_migrations', 'catalogue_cache_revisions',
        'import_jobs', 'import_records', 'painter_import_cohort'}
CLOCKS = ['created_at', 'updated_at', 'retrieved_at', 'verified_at', 'checked_at',
          'imported_at', 'applied_at', 'revision', 'published_at', 'resolved_at',
          'search_text']
IDENTITY = {t: '{a}.slug' for t in ['artists', 'artworks', 'institutions',
                                  'institution_venues', 'sources', 'movements']}
IDENTITY.update({'places': 'jsonb_build_array({a}.name,{a}.country_code)::text',
                 'media_assets': '{a}.id::text', 'research_snapshots': '{a}.sha256',
                 'curated_collections': "jsonb_build_array((SELECT slug FROM institutions WHERE id={a}.institution_id),{a}.curator_kind)::text"})
ENTITY_TABLE = {'artist': 'artists', 'artwork': 'artworks', 'institution': 'institutions',
                'movement': 'movements', 'place': 'places', 'media': 'media_assets'}
_dsn = None


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()
    if path.suffix == '.gz':
        raw = gzip.compress(raw, mtime=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == raw, ('immutable evidence already exists', str(path))
    else:
        path.write_bytes(raw)


def load(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connect(target, readonly=True):
    global _dsn
    if target == 'production' and _dsn is None:
        secret = subprocess.check_output(['gcloud', 'secrets', 'versions', 'access', 'latest',
            '--secret=artline-database-url', '--project=artline-508319'], text=True).strip()
        params = psycopg.conninfo.conninfo_to_dict(secret)
        params.update(host='127.0.0.1', port='55445', sslmode='disable', connect_timeout='20')
        _dsn = psycopg.conninfo.make_conninfo(**params)
    return psycopg.connect(_dsn if target == 'production' else 'postgresql://localhost/artline',
        row_factory=dict_row, options='-c timezone=UTC -c statement_timeout=180000 -c lock_timeout=10000'
        + (' -c default_transaction_read_only=on' if readonly else ''))


def metadata(db):
    tables = {}
    for r in db.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"):
        t = r['tablename']
        if t in SKIP:
            continue
        cols = db.execute("SELECT column_name,data_type,is_generated FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position", (t,)).fetchall()
        pk = [r['attname'] for r in db.execute("SELECT a.attname FROM pg_index i JOIN pg_attribute a ON a.attrelid=i.indrelid AND a.attnum=ANY(i.indkey) WHERE i.indrelid=%s::regclass AND i.indisprimary ORDER BY array_position(i.indkey,a.attnum)", (t,))]
        assert pk, t
        tables[t] = dict(columns=cols, primary_key=pk)
    foreign = db.execute("SELECT conrelid::regclass::text child,a.attname column,confrelid::regclass::text parent,b.attname parent_column FROM pg_constraint c JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=c.conkey[1] JOIN pg_attribute b ON b.attrelid=c.confrelid AND b.attnum=c.confkey[1] WHERE contype='f' AND cardinality(conkey)=1 ORDER BY 1,2").fetchall()
    foreign.append(dict(child='artwork_location_assertions', column='venue_id', parent='institution_venues', parent_column='id'))
    for t in ('research_artwork_links', 'research_resolutions'):
        foreign.append(dict(child=t, column='snapshot_id', parent='research_snapshots', parent_column='id'))
    return dict(tables=tables, foreign=foreign)


def fingerprint_query(table, meta, foreign, after=None, page_size=None):
    columns = {c['column_name']: c for c in meta['columns']}
    excluded = CLOCKS + [k for k, v in columns.items() if v['is_generated'] != 'NEVER']
    if columns.get('id', {}).get('data_type') == 'uuid':
        excluded += ['id']
    replacements, joins = {}, []
    for f in foreign:
        col, parent = f['column'], f['parent']
        if f['child'] != table or f['parent_column'] != 'id' or parent not in IDENTITY or col in replacements:
            continue
        if parent == 'media_assets':
            replacements[col] = f't."{col}"::text'
            continue
        alias = 'ref_' + col
        joins.append(f'LEFT JOIN "{parent}" {alias} ON {alias}.id=t."{col}"')
        replacements[col] = IDENTITY[parent].format(a=alias)
    if 'entity_id' in columns and 'entity_type' in columns:
        parts = []
        for kind, parent in ENTITY_TABLE.items():
            alias = 'entity_' + kind
            joins.append(f"LEFT JOIN {parent} {alias} ON t.entity_type='{kind}' AND {alias}.id=t.entity_id")
            expr = IDENTITY[parent].format(a=alias)
            parts.append(f'CASE WHEN {alias}.id IS NOT NULL THEN {expr} END')
        replacements['entity_id'] = 'coalesce(' + ','.join(parts) + ',t.entity_id::text)'
    if table == 'artwork_location_assertions':
        joins.append('LEFT JOIN artwork_location_assertions superseding ON superseding.id=t.superseded_by')
        replacements['superseded_by'] = "CASE WHEN superseding.id IS NOT NULL THEN jsonb_build_array(superseding.source_url,superseding.evidence_note,superseding.claim_type)::text END"
    payload = 'to_jsonb(t)-' + sql.Literal(excluded + list(replacements)).as_string() + '::text[]'
    if replacements:
        payload += '||jsonb_build_object(' + ','.join(sql.Literal(k).as_string() + ',' + v for k, v in replacements.items()) + ')'
    primary = 'jsonb_build_array(' + ','.join(f't."{k}"' for k in meta['primary_key']) + ')::text'
    if table in IDENTITY:
        key = IDENTITY[table].format(a='t')
    elif 'id' in columns and 'id' not in excluded:
        key = 't.id::text'
    elif table == 'external_identifiers':
        key = 'jsonb_build_array(t.scheme,t.external_id)::text'
    elif table == 'slug_redirects':
        key = 'jsonb_build_array(t.entity_type,t.old_slug)::text'
    else:
        key = 'md5((' + payload + ')::text)'
    origin, prefix, suffix = f'"{table}"', '', ''
    if page_size:
        pk = ','.join('"' + k + '"' for k in meta['primary_key'])
        where = ''
        if after is not None:
            values = dict(zip(meta['primary_key'], json.loads(after)))
            literal = sql.Literal(json.dumps(values)).as_string()
            where = f'WHERE ({pk}) > (SELECT {pk} FROM jsonb_populate_record(NULL::"{table}",{literal}::jsonb))'
        prefix = f'WITH scoped AS MATERIALIZED (SELECT * FROM "{table}" {where} ORDER BY {pk} LIMIT {page_size}) '
        origin = 'scoped'
        suffix = ' ORDER BY ' + ','.join('t."' + k + '"' for k in meta['primary_key'])
    return prefix + f'SELECT {key},md5(({payload})::text),{primary} FROM {origin} t ' + ' '.join(joins) + suffix


def capture(target):
    with connect(target) as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        db.execute('SET LOCAL enable_nestloop=on')
        db.execute('SET LOCAL max_parallel_workers_per_gather=0')
        meta = metadata(db)
        save(RUN / 'inventory' / (target + '-schema.json'), meta)
        for t, m in meta['tables'].items():
            out = RUN / 'inventory' / (target + '-' + t + '.json.gz')
            if out.exists():
                continue
            rows = collections.defaultdict(list)
            after, pages = None, 0
            while True:
                query = fingerprint_query(t, m, meta['foreign'], after, 2000)
                count = 0
                with db.cursor().copy('COPY (' + query + ') TO STDOUT') as cp:
                    for identity, checksum, pk in cp.rows():
                        rows[identity].append([checksum, pk])
                        after = pk
                        count += 1
                pages += 1
                if pages % 50 == 0:
                    print(target, t, 'audited pages', pages, flush=True)
                if count < 2000:
                    break
            save(out, dict(rows))
            print(target, t, sum(map(len, rows.values())), flush=True)


def compare():
    a, b = (load(RUN / 'inventory' / (t + '-schema.json')) for t in ('local', 'production'))
    summary = {}
    for table in sorted(a['tables'].keys() | b['tables'].keys()):
        values = [load(RUN / 'inventory' / (target + '-' + table + '.json.gz')) for target in ('local', 'production')]
        left, right = values
        row = dict(local_count=sum(map(len, left.values())), production_count=sum(map(len, right.values())),
            only_local=len(left.keys() - right.keys()), only_production=len(right.keys() - left.keys()),
            changed=sum(sorted(x[0] for x in left[k]) != sorted(x[0] for x in right[k]) for k in left.keys() & right.keys()))
        summary[table] = row
        print(table, row, flush=True)
    save(RUN / 'comparison.json', dict(at=now(), tables=summary, excluded_tables=sorted(SKIP)))


def presence():
    """Compare object identities using narrow reads, without scanning payloads."""
    meta = load(RUN / 'inventory/local-schema.json')['tables']
    tables = ['artists', 'artworks', 'institutions', 'media_assets', 'book_records',
              'book_creators', 'event_records', 'sources', 'places', 'movements',
              'institution_venues', 'curated_collections', 'research_snapshots']
    def one(target):
        with connect(target) as db:
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
            for table in tables:
                path = RUN / 'presence' / (target + '-' + table + '.json.gz')
                if path.exists():
                    continue
                primary = 'jsonb_build_array(' + ','.join('t."' + k + '"' for k in meta[table]['primary_key']) + ')::text'
                identity = IDENTITY.get(table, '{a}.id::text').format(a='t')
                rows = collections.defaultdict(list)
                with db.cursor().copy(f'COPY (SELECT {identity},{primary} FROM "{table}" t) TO STDOUT') as cp:
                    for key, pk in cp.rows():
                        rows[key].append(pk)
                save(path, dict(rows))
                print(target, 'object identities', table, sum(map(len, rows.values())), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(one, ['local', 'production']))
    result = {}
    for table in tables:
        left, right = (load(RUN / 'presence' / (target + '-' + table + '.json.gz')) for target in ['local', 'production'])
        missing = {k: left[k] for k in left.keys() - right.keys()}
        result[table] = dict(local_count=sum(map(len, left.values())),
            production_count=sum(map(len, right.values())), missing_from_production=missing,
            production_only=len(right.keys() - left.keys()))
        print(table, 'missing from production:', len(missing), flush=True)
    save(RUN / 'presence-comparison.json', dict(at=now(), direction='local_to_production', tables=result))


def select_rows(db, table, column, ids, extra=''):
    rows = []
    for offset in range(0, len(ids), 500):
        query = sql.SQL('SELECT to_jsonb(t) v FROM {} t WHERE {}=ANY(%s::uuid[]) ' + extra).format(sql.Identifier(table), sql.Identifier(column))
        rows.extend(r['v'] for r in db.execute(query, (ids[offset:offset + 500],)))
    return rows


def prepare_additions():
    comparison = load(RUN / 'presence-comparison.json')['tables']
    ids = [json.loads(pk)[0] for values in comparison['artworks']['missing_from_production'].values() for pk in values]
    media_ids = list(comparison['media_assets']['missing_from_production'])
    with connect('local') as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        data = {'artworks': select_rows(db, 'artworks', 'id', ids)}
        for t, column, extra in [
            ('artwork_artists', 'artwork_id', ''), ('artwork_location_assertions', 'artwork_id', ''),
            ('artwork_media', 'artwork_id', ''), ('artwork_places', 'artwork_id', ''),
            ('curated_collection_items', 'artwork_id', ''),
            ('citations', 'entity_id', "AND entity_type='artwork'"),
            ('external_identifiers', 'entity_id', "AND entity_type='artwork'"),
            ('research_artwork_links', 'artwork_id', ''), ('research_artwork_enrichments', 'artwork_id', ''),
            ('research_resolutions', 'artwork_id', '')]:
            data[t] = select_rows(db, t, column, ids, extra)
        all_media = sorted(set(media_ids) | {r['primary_media_id'] for r in data['artworks'] if r['primary_media_id']} | {r['media_id'] for r in data['artwork_media']})
        data['media_assets'] = select_rows(db, 'media_assets', 'id', all_media)
        data['media_rights_evidence'] = select_rows(db, 'media_rights_evidence', 'media_id', all_media)
        data['citations'] += select_rows(db, 'citations', 'entity_id', all_media, "AND entity_type='media'")
        media_attachments = select_rows(db, 'artwork_media', 'media_id', media_ids)
        media_works = select_rows(db, 'artworks', 'primary_media_id', media_ids)
        missing_media_artwork_ids = sorted({r['artwork_id'] for r in media_attachments} | {r['id'] for r in media_works})
        media_context = dict(artworks=select_rows(db, 'artworks', 'id', missing_media_artwork_ids),
            artwork_media=media_attachments,
            artwork_artists=select_rows(db, 'artwork_artists', 'artwork_id', missing_media_artwork_ids),
            external_identifiers=select_rows(db, 'external_identifiers', 'entity_id', missing_media_artwork_ids, "AND entity_type='artwork'"))
        source_ids = sorted({r['source_id'] for rows in data.values() for r in rows if r.get('source_id')})
        data['sources'] = select_rows(db, 'sources', 'id', source_ids)
    save(BACKUP / 'local-selected-source.json.gz', dict(at=now(), tables=data, media_context=media_context))
    save(RUN / 'local-selected-source-pin.json', dict(path=str(BACKUP / 'local-selected-source.json.gz'), sha256=digest(BACKUP / 'local-selected-source.json.gz'), counts={t: len(v) for t, v in data.items()}))
    print('Prepared scoped source rows', {t: len(v) for t, v in data.items()}, flush=True)
    print('Artwork review states', dict(collections.Counter(r['status'] for r in data['artworks'])),
        'images', sum(bool(r['primary_media_id']) for r in data['artworks']), flush=True)


def normal(value):
    return ' '.join(re.findall(r'[^\W_]+', ''.join(c for c in unicodedata.normalize('NFKD', value or '').casefold() if not unicodedata.combining(c))))


def identity_maps():
    maps = {}
    for table in ['artists', 'artworks', 'institutions', 'media_assets', 'sources', 'places',
                  'movements', 'institution_venues', 'curated_collections', 'research_snapshots']:
        left, right = (load(RUN / 'presence' / (target + '-' + table + '.json.gz')) for target in ['local', 'production'])
        mapping = {}
        for key in left.keys() & right.keys():
            a, b = left[key], right[key]
            if len(a) == len(b) == 1:
                mapping[json.loads(a[0])[0]] = json.loads(b[0])[0]
            else:
                for pk in set(a) & set(b):
                    mapping[json.loads(pk)[0]] = json.loads(pk)[0]
        maps[table] = mapping
    return maps


def preflight_additions():
    pin = load(RUN / 'local-selected-source-pin.json')
    assert digest(Path(pin['path'])) == pin['sha256']
    package = load(Path(pin['path']))
    data = package['tables']
    maps = identity_maps()
    ids = [r['id'] for r in data['artworks']]
    museum_ids = sorted({maps['institutions'][r['current_institution_id']] for r in data['artworks']})
    identifiers = data['external_identifiers']
    with connect('production') as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        existing_ids = select_rows(db, 'artworks', 'id', ids)
        native = []
        for offset in range(0, len(identifiers), 500):
            rows = identifiers[offset:offset + 500]
            native += [r for r in db.execute("SELECT x.entity_id local_id,e.entity_id::text production_id,e.scheme,e.external_id,e.canonical_url FROM jsonb_to_recordset(%s) x(entity_id text,scheme text,external_id text) JOIN external_identifiers e ON e.scheme=x.scheme AND e.external_id=x.external_id WHERE e.entity_type='artwork'", (Jsonb(rows),))]
        print('Native identifier matches', len(native), flush=True)
        urls = sorted({r['canonical_url'] for r in identifiers if r['canonical_url']})
        url_matches = [r for r in db.execute("SELECT entity_id::text production_id,canonical_url,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)", (urls,))]
        print('Exact native URL matches', len(url_matches), flush=True)
        columns = 'id,slug,title,normalized_title,alternate_title,unlinked_creator_label,creation_year_start,creation_year_end,work_type,medium_text,dimensions_text,accession_number,current_institution_id,status'
        scoped = [r for r in db.execute('SELECT ' + columns + ' FROM artworks WHERE current_institution_id=ANY(%s::uuid[])', (museum_ids,))]
        scoped = json.loads(json.dumps(scoped, default=str))
        print('Institution-scoped duplicate candidates', len(scoped), flush=True)
        current_institutions = select_rows(db, 'institutions', 'id', museum_ids)
        source_ids = [maps['sources'][r['id']] for r in data['sources'] if r['id'] in maps['sources']]
        current_sources = select_rows(db, 'sources', 'id', source_ids)
        media_ids = [r['id'] for r in data['media_assets']]
        missing_media_portraits = []
    # Source-native identity and institutional inventory prevent cross-source duplicates.
    matches = collections.defaultdict(set)
    bases = collections.defaultdict(list)
    for row in existing_ids:
        matches[row['id']].add(row['id']); bases[row['id']].append('same_database_object_id')
    for row in native:
        matches[row['local_id']].add(row['production_id']); bases[row['local_id']].append('exact_native_identifier')
    by_url = collections.defaultdict(set)
    for row in identifiers:
        if row['canonical_url']:
            by_url[row['canonical_url']].add(row['entity_id'])
    for row in url_matches:
        local = by_url[row['canonical_url']]
        if len(local) == 1:
            aid = next(iter(local))
            matches[aid].add(row['production_id']); bases[aid].append('exact_unique_native_object_url')
    inventories = collections.defaultdict(list)
    titles = collections.defaultdict(list)
    for row in scoped:
        if row['accession_number']:
            inventories[(row['current_institution_id'], normal(row['accession_number']).replace(' ', ''))].append(row)
        titles[(row['current_institution_id'], normal(row['title']))].append(row)
    ready, existing, held = [], [], []
    for row in data['artworks']:
        aid = row['id']; iid = maps['institutions'][row['current_institution_id']]
        same_inventory = inventories.get((iid, normal(row['accession_number']).replace(' ', '')), []) if row['accession_number'] else []
        for hit in same_inventory:
            matches[aid].add(hit['id']); bases[aid].append('same_institution_inventory')
        if matches[aid]:
            item = dict(local_id=aid, slug=row['slug'], production_ids=sorted(matches[aid]), basis=sorted(set(bases[aid])))
            (existing if len(matches[aid]) == 1 else held).append(item)
            continue
        # Similar titles are a review lead only, never automatic same-object proof.
        suspects = [hit for hit in titles.get((iid, normal(row['title'])), [])
            if (not hit['accession_number'] or not row['accession_number'])
            and hit['work_type'] == row['work_type']
            and (normal(hit['unlinked_creator_label']) == normal(row['unlinked_creator_label']) or not hit['unlinked_creator_label'])
            and (hit['creation_year_start'] == row['creation_year_start'] or hit['creation_year_start'] is None or row['creation_year_start'] is None)]
        if suspects:
            held.append(dict(local_id=aid, slug=row['slug'], reason='same_museum_title_creator_date_requires_version_check', production_ids=[h['id'] for h in suspects]))
        else:
            ready.append(aid)
    result = dict(at=now(), source_pin=pin, maps=maps, ready=ready, existing=existing, held=held,
                  production_institutions=current_institutions, production_sources=current_sources)
    save(BACKUP / 'production-identity-preflight.json.gz', dict(existing_ids=existing_ids, native=native, url_matches=url_matches, scoped=scoped))
    save(RUN / 'addition-identity-plan.json.gz', result)
    save(RUN / 'addition-identity-summary.json', dict(at=result['at'], ready=len(ready), already_present=len(existing), held=len(held), source_artworks=len(ids)))
    print('Identity result:', len(ready), 'ready;', len(existing), 'already present;', len(held), 'version checks', flush=True)


def plan_delivery():
    initial = load(RUN / 'addition-identity-plan.json.gz')
    source_pin = initial['source_pin']
    assert digest(Path(source_pin['path'])) == source_pin['sha256']
    source = load(Path(source_pin['path']))['tables']
    review = load(RUN / 'version-check-matches.json')
    ready = set(initial['ready'])
    existing = list(initial['existing'])
    decisions = []
    distinct = '61c8b69a-c6db-592b-b5bf-4b1161d514f5'
    manual = {
        '9fb521d2-cca7-5136-92cf-4f0a4a9dfb27': 'Production holding citation already identifies the exact Fitzwilliam native object /2658. Title, creator, year, museum and oil/canvas agree; preserve rounded production dimensions.',
        '82bdaa88-d4bb-5619-9d2f-00fc7e97ce6e': 'Production Wikidata reference and local native identifier both identify National Gallery of Australia IRN 61325; only HTTP/path/query capitalization differs. Creator, title, year and institution agree.',
        'dde805e6-1ab5-5fe9-a867-d9829df1686f': 'Same uniquely represented 1862 Rossetti oil painting, title and Fitzwilliam holding. Native 30.5 x 27 cm versus WikiArt 26 x 29 cm remains a source dimension discrepancy; no measurements or other production values are overwritten. Editorial same-work assessment 0.94.',
        'df159c10-bb9c-5215-bc60-7305be6acef9': 'Same Metsu oil/canvas The Cook in Thyssen, native 40 x 33.7 cm versus rounded WikiArt 40 x 33 cm and overlapping 1657–1662 / 1657–1667 dates. Native description distinguishes the Berlin full-length canvas and smaller Munich panel; existing production holding and format identify the Madrid version. Source date/dimension differences retained. Editorial same-work assessment 0.96.'}
    assert {r['local_id'] for r in review} == {r['local_id'] for r in initial['held']}
    for row in review:
        aid = row['local_id']
        if aid == distinct:
            ready.add(aid)
            decisions.append(dict(local_id=aid, action='add_distinct_work', basis='Different Joconde identities 11370002868 versus 11370003087; qualified Corot workshop versus Jacqueline Marval; 110.5 x 55.5 cm versus 50.2 x 60 cm. Same title does not establish the same object.'))
        else:
            assert row['inventory_match'] or row['url_match'] or aid in manual
            basis = manual.get(aid, 'Production retained Wikidata P217 inventory evidence equals the local native museum accession; title/date/institution cross-check retained. No duplicate object created.')
            decisions.append(dict(local_id=aid, action='already_present', production_ids=row['production_ids'], basis=basis))
            existing.append(dict(local_id=aid, production_ids=row['production_ids'], basis=[basis]))
    assert len(ready) + len(existing) == len(source['artworks'])
    maps = initial['maps']
    rows = {
        'artworks': [dict(r, current_institution_id=maps['institutions'][r['current_institution_id']]) for r in source['artworks'] if r['id'] in ready],
        'artwork_location_assertions': [dict(r, institution_id=maps['institutions'][r['institution_id']], source_id=maps['sources'].get(r['source_id'], r['source_id'])) for r in source['artwork_location_assertions'] if r['artwork_id'] in ready],
        'external_identifiers': [dict(r, source_id=maps['sources'].get(r['source_id'], r['source_id'])) for r in source['external_identifiers'] if r['entity_id'] in ready],
        'citations': [dict(r, source_id=maps['sources'].get(r['source_id'], r['source_id'])) for r in source['citations'] if r['entity_type'] == 'artwork' and r['entity_id'] in ready],
    }
    required_sources = {r['source_id'] for values in rows.values() for r in values if r.get('source_id')}
    rows['sources'] = [r for r in source['sources'] if r['id'] in required_sources and r['id'] not in maps['sources']]
    assert all(a['status'] == 'review' and a['published_at'] is None and a['primary_media_id'] is None and a['research_candidate'] and a['creation_year_end'] is not None and a['creation_year_end'] <= 1970 for a in rows['artworks'])
    assert len(rows['artwork_location_assertions']) == len(ready) == len(rows['citations'])
    assert {r['artwork_id'] for r in rows['artwork_location_assertions']} == ready
    assert {r['entity_id'] for r in rows['citations']} == ready
    assert {r['entity_id'] for r in rows['external_identifiers']} == ready
    assert all(r['claim_type'] == 'holding' and r['review_state'] == 'accepted' and r['superseded_by'] is None and r['venue_id'] is None for r in rows['artwork_location_assertions'])
    # SN is the source's "sans numéro", not a shared physical inventory identity.
    sn = [r['id'] for r in rows['artworks'] if normal(r['accession_number']) == 'sn']
    plan = dict(at=now(), direction='local_to_production_only', source_pin=source_pin,
        inserts=rows, existing=existing, decisions=decisions, required_sources=sorted(required_sources),
        institution_preimages=[r for r in initial['production_institutions'] if r['id'] in {a['current_institution_id'] for a in rows['artworks']}],
        placeholder_inventory_note=dict(ids=sn, basis='Literal SN retained; distinct Joconde identifiers, creators, dates, dimensions and titles checked. No shared inventory identity inferred.'),
        publication_changes=0, existing_artwork_updates=0, image_changes=0)
    path = BACKUP / 'delivery-plan.json.gz'
    save(path, plan)
    save(RUN / 'delivery-plan-pin.json', dict(path=str(path), sha256=digest(path), counts={k:len(v) for k,v in rows.items()}, existing=len(existing), unresolved=0))
    save(RUN / 'version-decisions.json', decisions)
    print('Pinned delivery', {t:len(v) for t,v in rows.items()}, 'already present', len(existing), flush=True)


def validate_absences(db, plan):
    rows = plan['inserts']
    ids = [r['id'] for r in rows['artworks']]
    slugs = [r['slug'] for r in rows['artworks']]
    assert not db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) OR slug=ANY(%s)', (ids, slugs)).fetchall(), 'A planned artwork is already present'
    for t in ['sources', 'artwork_location_assertions', 'external_identifiers', 'citations']:
        assert not db.execute(sql.SQL('SELECT id FROM {} WHERE id=ANY(%s::uuid[])').format(sql.Identifier(t)), ([r['id'] for r in rows[t]],)).fetchall(), ('Target ID collision', t)
    assert not db.execute('SELECT id FROM sources WHERE slug=ANY(%s)', ([r['slug'] for r in rows['sources']],)).fetchall(), 'Source identity appeared after planning'
    for offset in range(0, len(rows['external_identifiers']), 500):
        found = db.execute('SELECT e.entity_id FROM jsonb_to_recordset(%s) x(scheme text,external_id text) JOIN external_identifiers e ON e.scheme=x.scheme AND e.external_id=x.external_id', (Jsonb(rows['external_identifiers'][offset:offset+500]),)).fetchall()
        assert not found, 'Native source object appeared after planning'
    # Protect referenced museum identities and source identities without rewriting them.
    actual = {r['id']:r for r in select_rows(db, 'institutions', 'id', [r['id'] for r in plan['institution_preimages']])}
    assert actual == {r['id']:r for r in plan['institution_preimages']}, 'Museum identity changed after planning'


def verify_delivery_rows(db, plan):
    meta = load(RUN / 'inventory/production-schema.json')['tables']
    counts = {}
    for table, rows in plan['inserts'].items():
        found = {r['id']: r for r in select_rows(db, table, 'id', [r['id'] for r in rows])}
        assert len(found) == len(rows), ('Missing delivered rows', table)
        generated = {c['column_name'] for c in meta[table]['columns'] if c['is_generated'] != 'NEVER'}
        for r in rows:
            assert {k:v for k,v in found[r['id']].items() if k not in generated} == {k:v for k,v in r.items() if k not in generated}, ('Delivered content changed', table, r['id'])
        counts[table] = len(found)
    return counts


def apply_delivery():
    assert not (RUN / 'delivery-applied.json').exists()
    pin = load(RUN / 'delivery-plan-pin.json')
    assert digest(Path(pin['path'])) == pin['sha256']
    plan = load(Path(pin['path']))
    receipt = load(RUN / 'cloud-backup.json')
    assert cloud('sql', 'backups', 'describe', str(receipt['id']), '--instance=artline-postgres')['status'] == 'SUCCESSFUL'
    meta = load(RUN / 'inventory/production-schema.json')['tables']
    # Recheck selected source records on the real local DB using read-only queries.
    with connect('local') as db:
        raw = load(Path(plan['source_pin']['path']))['tables']
        source_ids = {r['id'] for r in plan['inserts']['artworks']}
        old = {r['id']:r for r in raw['artworks'] if r['id'] in source_ids}
        assert {r['id']:r for r in select_rows(db,'artworks','id',sorted(source_ids))} == old, 'Local source artworks changed'
    with connect('production', readonly=False) as db:
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (OP,))
        assert db.execute('SELECT current_database() n').fetchone()['n'] == 'artline'
        validate_absences(db, plan)
        save(BACKUP / 'delivery-locked-absences.json.gz', dict(at=now(), plan_sha256=pin['sha256'], absent_ids={t:[r['id'] for r in rows] for t,rows in plan['inserts'].items()}))
        for table in ['sources', 'artworks', 'external_identifiers', 'citations', 'artwork_location_assertions']:
            insert(db, table, plan['inserts'][table], meta[table])
            print('Inserted', table, len(plan['inserts'][table]), flush=True)
        counts = verify_delivery_rows(db, plan)
        ids = [r['id'] for r in plan['inserts']['artworks']]
        assert db.execute("SELECT count(*) n FROM audit_log WHERE entity_type='artwork' AND action='insert' AND entity_id=ANY(%s::uuid[])", (ids,)).fetchone()['n'] == len(ids)
    save(RUN / 'delivery-applied.json', dict(at=now(), plan_sha256=pin['sha256'], counts=counts,
        backup_id=receipt['id'], publication_changes=0, local_database_writes=0, existing_artwork_updates=0))
    print('Committed missing local catalogue additions', counts, flush=True)


def verify_delivery():
    pin = load(RUN / 'delivery-plan-pin.json')
    plan = load(Path(pin['path']))
    meta = load(RUN / 'inventory/production-schema.json')['tables']
    counts = {}
    # Compute expected PostgreSQL JSON fingerprints locally, then retrieve only
    # production hashes. This avoids re-transferring every large source capture.
    with connect('local') as local, connect('production') as db:
        for table, rows in plan['inserts'].items():
            generated = [c['column_name'] for c in meta[table]['columns'] if c['is_generated'] != 'NEVER']
            expected = {}
            for offset in range(0, len(rows), 200):
                query = sql.SQL('SELECT id::text,md5((to_jsonb(t)-%s::text[])::text) fingerprint FROM jsonb_populate_recordset(NULL::{},%s) t').format(sql.Identifier(table))
                expected.update({r['id']:r['fingerprint'] for r in local.execute(query, (generated,Jsonb(rows[offset:offset+200])))})
            actual = {}
            ids = list(expected)
            for offset in range(0, len(ids), 500):
                query = sql.SQL('SELECT id::text,md5((to_jsonb(t)-%s::text[])::text) fingerprint FROM {} t WHERE id=ANY(%s::uuid[])').format(sql.Identifier(table))
                actual.update({r['id']:r['fingerprint'] for r in db.execute(query, (generated,ids[offset:offset+500]))})
            assert actual == expected, ('Independent content verification failed', table)
            counts[table] = len(actual)
            print('Verified complete row fingerprints', table, len(actual), flush=True)
        totals = {t:db.execute(sql.SQL('SELECT count(*) n FROM {}').format(sql.Identifier(t))).fetchone()['n'] for t in ['artworks','artists','institutions']}
    save(RUN / 'delivery-verification.json', dict(at=now(), counts=counts, totals=totals, plan_sha256=pin['sha256'], errors=[]))
    print('Independent read-only verification passed', counts, totals, flush=True)


def cloud(*args):
    return json.loads(subprocess.check_output(['gcloud', *args, '--project=artline-508319', '--format=json'], text=True))


def backup():
    BACKUP.mkdir(parents=True, exist_ok=True)
    description = 'Before catalogue alignment and Cyprus venue repair 20261008'
    rows = cloud('sql', 'backups', 'list', '--instance=artline-postgres', '--limit=60')
    matching = [r for r in rows if r.get('description') == description]
    if not matching:
        save(BACKUP / 'cloud-backup-operation.json', cloud('sql', 'backups', 'create', '--instance=artline-postgres', '--description=' + description, '--async'))
        print('Production recovery backup requested', flush=True)
    else:
        row = max(matching, key=lambda x: int(x['id']))
        if row['status'] == 'SUCCESSFUL':
            save(BACKUP / 'cloud-backup.json', row)
            save(RUN / 'cloud-backup.json', dict(id=row['id'], status=row['status']))
        print('Production recovery backup', row['id'], row['status'], flush=True)


def insert(db, table, rows, meta):
    if not rows:
        return
    columns = [c['column_name'] for c in meta['columns'] if c['is_generated'] == 'NEVER' and c['column_name'] in rows[0]]
    names = sql.SQL(',').join(map(sql.Identifier, columns))
    query = sql.SQL('INSERT INTO {} ({}) SELECT {} FROM jsonb_populate_recordset(NULL::{},%s)').format(sql.Identifier(table), names, names, sql.Identifier(table))
    for offset in range(0, len(rows), 200):
        db.execute(query, (Jsonb(rows[offset:offset + 200]),))


def plan_venues():
    with connect('production') as db:
        museums = [r['v'] for r in db.execute("SELECT to_jsonb(i) v FROM institutions i JOIN places p ON p.id=i.place_id WHERE p.country_code='CY' AND i.status<>'archived' AND EXISTS(SELECT 1 FROM artworks a WHERE a.current_institution_id=i.id) ORDER BY i.slug")]
        ids = [r['id'] for r in museums]
        assert not db.execute('SELECT id FROM institution_venues WHERE institution_id=ANY(%s::uuid[])', (ids,)).fetchall()
        citations = [r['v'] for r in db.execute("SELECT to_jsonb(c) v FROM citations c WHERE entity_type='institution' AND entity_id=ANY(%s::uuid[]) AND field_name='verified_museum_identity_and_geography' ORDER BY source_url", (ids,))]
    venues, evidence = [], []
    for museum in museums:
        options = [c for c in citations if c['entity_id'] == museum['id']]
        options.sort(key=lambda c: (0 if 'www.visitcyprus.com/discover' in c['source_url'] else 1, c['source_url']))
        if museum['slug'] == 'state-gallery-cyprus':
            options = [c for c in options if 'visitnicosia.com.cy/meet-nicosia' in c['source_url']]
        c = options[0]
        note = json.loads(c['evidence_note'])
        receipt = note['source'].get('receipt', note['source'])
        raw = gzip.decompress((ROOT / receipt['body_path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == receipt['sha256']
        assert receipt['status'] == 200 and c['source_url'].startswith('https://')
        variants = [('location', museum['name'])]
        if museum['slug'] == 'state-gallery-cyprus':
            assert b'SPEL' in raw and b'Majestic' in raw
            variants = [('spel', museum['name'] + ' — SPEL'), ('majestic', museum['name'] + ' — Majestic')]
        for suffix, name in variants:
            slug = museum['slug'] + '-' + suffix
            venue = dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, OP + '/venue/' + slug)),
                institution_id=museum['id'], slug=slug, name=name, place_id=museum['place_id'],
                visit_url=c['source_url'], source_url=c['source_url'],
                checked_at=receipt['retrieved_at'], status='review')
            venues.append(venue)
            evidence.append(dict(venue_id=venue['id'], institution_id=museum['id'],
                source_citation=c, receipt=receipt, address=note.get('facts', {}).get('address'),
                editorial_confidence=0.95,
                basis='Reviewed primary museum/directory location evidence. Source retrieval time retained. No current-opening or artwork display claim; no institution publication change.'))
    plan = dict(at=now(), museums=museums, venues=venues, evidence=evidence)
    save(BACKUP / 'venue-plan-preimages.json.gz', plan)
    save(RUN / 'venue-plan.json.gz', plan)
    save(RUN / 'venue-plan-pin.json', dict(sha256=digest(RUN / 'venue-plan.json.gz'), venues=len(venues), museums=len(museums)))
    print('Pinned', len(venues), 'venues for', len(museums), 'Cyprus institutions', flush=True)


def apply_venues():
    assert not (RUN / 'venues-applied.json').exists()
    pin = load(RUN / 'venue-plan-pin.json')
    assert digest(RUN / 'venue-plan.json.gz') == pin['sha256']
    plan = load(RUN / 'venue-plan.json.gz')
    receipt = load(RUN / 'cloud-backup.json')
    current = cloud('sql', 'backups', 'describe', str(receipt['id']), '--instance=artline-postgres')
    assert current['status'] == 'SUCCESSFUL'
    for e in plan['evidence']:
        rc = e['receipt']
        assert hashlib.sha256(gzip.decompress((ROOT / rc['body_path']).read_bytes())).hexdigest() == rc['sha256']
    ids = [r['id'] for r in plan['museums']]
    with connect('production', readonly=False) as db:
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        assert db.execute('SELECT current_database() n').fetchone()['n'] == 'artline'
        actual = {r['v']['id']: r['v'] for r in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE', (ids,))}
        assert actual == {r['id']: r for r in plan['museums']}
        assert not db.execute('SELECT id FROM institution_venues WHERE institution_id=ANY(%s::uuid[])', (ids,)).fetchall()
        meta = metadata(db)['tables']
        insert(db, 'institution_venues', plan['venues'], meta['institution_venues'])
        for e in plan['evidence']:
            venue = next(v for v in plan['venues'] if v['id'] == e['venue_id'])
            c = e['source_citation']
            db.execute("INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'institution',%s,'verified_venue_geography',%s,%s,%s,%s,%s)",
                (str(uuid.uuid5(uuid.NAMESPACE_URL, OP + '/venue-citation/' + venue['id'])), venue['institution_id'], c['source_id'], c['source_url'], json.dumps(dict(operation=OP, venue=venue, evidence=e), ensure_ascii=False), e['receipt']['retrieved_at'], ACTOR))
            db.execute("INSERT INTO audit_log(action,entity_type,entity_id,after_json) VALUES('insert','institution_venue',%s,%s)", (venue['id'], Jsonb(venue)))
        after = [r['v'] for r in db.execute('SELECT to_jsonb(v) v FROM institution_venues v WHERE institution_id=ANY(%s::uuid[]) ORDER BY slug', (ids,))]
        assert len(after) == len(plan['venues'])
        assert {r['v']['id']: r['v'] for r in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=ANY(%s::uuid[])', (ids,))} == actual
        save(BACKUP / 'venue-transaction-after.json.gz', after)
    save(RUN / 'venues-applied.json', dict(at=now(), venues=len(after), museums=len(ids),
        plan_sha256=pin['sha256'], backup_id=receipt['id'], publication_changes=0, display_claims=0))
    print('Committed', len(after), 'source-backed Cyprus venues', flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['capture', 'compare', 'presence', 'prepare_additions', 'preflight_additions', 'plan_delivery', 'apply_delivery', 'verify_delivery', 'backup', 'plan_venues', 'apply_venues'])
    p.add_argument('--target', choices=['local', 'production'])
    args = p.parse_args()
    if args.phase == 'capture':
        if args.target:
            capture(args.target)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                list(pool.map(capture, ['local', 'production']))
    else:
        globals()[args.phase]()


if __name__ == '__main__':
    main()
