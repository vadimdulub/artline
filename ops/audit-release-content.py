#!/usr/bin/env python3
"""Read-only content parity, resolving independent local/cloud UUIDs by identity.

Use streaming COPY rather than one network roundtrip per small cursor page.
Content digests retain metadata, status, rights and evidence. No reconciliation
is inferred from differing IDs. Operational import receipts stay target-local.
"""
import argparse
import concurrent.futures
import importlib.util
import json
from pathlib import Path

from psycopg import sql

spec = importlib.util.spec_from_file_location('release', Path(__file__).with_name('audit-production-release.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
IDENTITY = {t: '{a}.slug' for t in ['artists', 'artworks', 'institutions', 'institution_venues', 'sources', 'movements']}
IDENTITY.update({'places': "jsonb_build_array({a}.name,{a}.country_code)::text",
                 'media_assets': '{a}.id::text', 'research_snapshots': '{a}.sha256',
                 'curated_collections': "jsonb_build_array((SELECT slug FROM institutions WHERE id={a}.institution_id),{a}.curator_kind)::text",
                 'import_jobs': '{a}.idempotency_key'})
SKIP = r.OPERATIONAL | {'import_jobs', 'import_records', 'painter_import_cohort'}


def statement(table, meta, foreign, page_size=None, after=None):
    cols = {c[0] for c in meta['columns']}
    excluded = r.CLOCKS + ['search_text', 'resolved_at']
    if 'id' in cols and next(c[1] for c in meta['columns'] if c[0] == 'id') == 'uuid':
        excluded += ['id']
    replacements, joins = {}, []
    for column, parent, parent_col in foreign:
        if parent_col != 'id' or parent not in IDENTITY or column in replacements:
            continue
        if IDENTITY[parent] == '{a}.id::text':
            # Media IDs are shared identities already: do not read the whole
            # media index merely to recover the exact FK value we already have.
            replacements[column] = f't."{column}"::text'
            continue
        alias = 'ref_' + column
        joins.append(f'LEFT JOIN "{parent}" {alias} ON {alias}."id"=t."{column}"')
        replacements[column] = IDENTITY[parent].format(a=alias)
    if 'entity_id' in cols and 'entity_type' in cols:
        options = []
        for kind, parent in [('artist', 'artists'), ('artwork', 'artworks'), ('institution', 'institutions'),
                             ('movement', 'movements'), ('place', 'places'), ('media', 'media_assets')]:
            alias = 'entity_' + kind
            joins.append(f"LEFT JOIN {parent} {alias} ON t.entity_type='{kind}' AND {alias}.id=t.entity_id")
            options.append(IDENTITY[parent].format(a=alias) if parent != 'places' else
                           f'CASE WHEN {alias}.id IS NOT NULL THEN ' + IDENTITY[parent].format(a=alias) + ' END')
        replacements['entity_id'] = 'coalesce(' + ','.join(options) + ',t.entity_id::text)'
    if table == 'artwork_location_assertions':
        # The target-specific pointer is replaced by the referenced assertion's
        # sourced identity, retaining supersession rather than dropping it.
        joins.append('LEFT JOIN artwork_location_assertions superseding ON superseding.id=t.superseded_by')
        replacements['superseded_by'] = "CASE WHEN superseding.id IS NOT NULL THEN jsonb_build_array(superseding.source_url,superseding.evidence_note,superseding.claim_type)::text END"
    payload = 'to_jsonb(t)-' + sql.Literal(excluded + list(replacements)).as_string() + '::text[]'
    if replacements:
        payload += ' || jsonb_build_object(' + ','.join(sql.Literal(k).as_string() + ',' + v for k, v in replacements.items()) + ')'
    primary = 'jsonb_build_array(' + ','.join(f't."{k}"' for k in meta['primary_key']) + ')::text'
    if table in IDENTITY:
        key = IDENTITY[table].format(a='t')
    elif 'id' in cols and 'id' not in excluded:
        key = 't.id::text'
    elif table == 'external_identifiers':
        key = 'jsonb_build_array(t.scheme,t.external_id)::text'
    elif table == 'slug_redirects':
        key = 'jsonb_build_array(t.entity_type,t.old_slug)::text'
    else:
        # Relationship/evidence rows have independently generated surrogate IDs.
        # Use full normalized content as multiset identity, retaining duplicates.
        key = 'md5((' + payload + ')::text)'
    prefix = ''
    origin = f'"{table}"'
    suffix = ''
    if page_size:
        pk = ','.join('"' + name + '"' for name in meta['primary_key'])
        where = ''
        if after is not None:
            values = dict(zip(meta['primary_key'], json.loads(after)))
            literal = sql.Literal(json.dumps(values)).as_string()
            where = f'WHERE ({pk}) > (SELECT {pk} FROM jsonb_populate_record(NULL::"{table}",{literal}::jsonb))'
        prefix = f'WITH scoped AS MATERIALIZED (SELECT * FROM "{table}" {where} ORDER BY {pk} LIMIT {int(page_size)}) '
        origin = 'scoped'
        suffix = ' ORDER BY ' + ','.join('t."' + name + '"' for name in meta['primary_key'])
    return prefix + f'SELECT {key},md5(({payload})::text),{primary} FROM {origin} t ' + ' '.join(joins) + suffix


def capture(target, port, output, selected=None, resume=False, page_size=None):
    baseline = json.loads((output.parent / 'before/local-snapshot.json').read_text())
    out = {}
    with r.connect(target, port) as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        db.execute("SET LOCAL timezone='UTC'")
        # This is a full-table audit, not an application lookup. Avoid a nested
        # random lookup for every citation on the small production instance.
        db.execute('SET LOCAL enable_nestloop=' + ('on' if page_size else 'off'))
        db.execute('SET LOCAL max_parallel_workers_per_gather=0')
        foreign = db.execute("""SELECT conrelid::regclass::text,a.attname,confrelid::regclass::text,b.attname
            FROM pg_constraint c JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=c.conkey[1]
            JOIN pg_attribute b ON b.attrelid=c.confrelid AND b.attnum=c.confkey[1]
            WHERE contype='f' AND cardinality(conkey)=1""").fetchall()
        for table, meta in baseline['tables'].items():
            if table in SKIP or (selected and table not in selected): continue
            cache = output / (target + '-' + table + '.json')
            if resume and cache.exists():
                out[table] = json.loads(cache.read_text())
                continue
            rows = {}
            after = None
            pages = 0
            while True:
                query = statement(table, meta, [(col, parent, pc) for t, col, parent, pc in foreign if t == table], page_size, after)
                count = 0
                with db.cursor().copy('COPY (' + query + ') TO STDOUT') as copy:
                    for key, digest, primary in copy.rows():
                        rows.setdefault(key, []).append([digest, primary])
                        count += 1
                        after = primary
                pages += 1
                if pages % 25 == 0: print(target, table, 'pages', pages, flush=True)
                if not page_size or count < page_size: break
            for records in rows.values(): records.sort()
            out[table] = rows
            r.core.save_new(output / (target + '-' + table + '.json'), rows)
            print(target, table, sum(map(len, rows.values())), flush=True)
    return out


def compare(output):
    local = {p.name[len('local-'):-5]: json.loads(p.read_text()) for p in output.glob('local-*.json')}
    cloud = {p.name[len('cloud-'):-5]: json.loads(p.read_text()) for p in output.glob('cloud-*.json')}
    assert local.keys() == cloud.keys()
    result = {'at': r.core.now(), 'tables': {}}
    for table, a in local.items():
        b = cloud[table]
        diff = {'only_local': {k: a[k] for k in a.keys() - b.keys()},
                'only_cloud': {k: b[k] for k in b.keys() - a.keys()},
                'changed': {k: {'local': a[k], 'cloud': b[k]} for k in a.keys() & b.keys()
                            if sorted(v[0] for v in a[k]) != sorted(v[0] for v in b[k])},
                'local_count': sum(map(len, a.values())), 'cloud_count': sum(map(len, b.values()))}
        result['tables'][table] = diff
        print(table, 'local-only/cloud-only/changed', len(diff['only_local']), len(diff['only_cloud']), len(diff['changed']), flush=True)
    r.core.save_new(output / 'comparison.json', result)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--port', type=int, default=55434)
    p.add_argument('--table', action='append')
    p.add_argument('--resume', action='store_true', help='Reuse completed immutable per-table receipts after an interrupted audit')
    p.add_argument('--page-size', type=int, choices=[500,1000,2000], help='Bound each keyset audit query on small production instances')
    a = p.parse_args()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda t: capture(t, a.port, a.output, a.table, a.resume, a.page_size), ('local', 'cloud')))
    compare(a.output)


if __name__ == '__main__': main()
