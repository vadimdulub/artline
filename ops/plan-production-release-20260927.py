#!/usr/bin/env python3
"""Build an immutable, read-only proposal from semantic catalogue differences.

This does not apply changes. Independent UUIDs are reconciled by the audited
identities; production-only records, operational receipts, and clocks remain
target-local. Every proposed update includes its exact production preimage.
"""
import collections
import importlib.util
import json
import re
from pathlib import Path

from psycopg import sql
from psycopg.types.json import Jsonb

spec = importlib.util.spec_from_file_location('audit', Path(__file__).with_name('audit-release-content.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
r = a.r
OUT = r.ROOT / 'docs/research/production-release-20260927'
IGNORE = set(r.CLOCKS + ['search_text', 'resolved_at'])
UUID = re.compile(r'\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b', re.I)


def keys(row, meta):
    return json.dumps([row[k] for k in meta['primary_key']])


def fetch(db, table, meta, records, fields=None):
    """Indexed key lookups, bounded to 400 requested records per query."""
    fields = fields or meta['primary_key']
    result = []
    for offset in range(0, len(records), 400):
        batch = records[offset:offset + 400]
        query = sql.SQL('SELECT to_jsonb(t) FROM {} t JOIN jsonb_populate_recordset(NULL::{},%s) k ON {}').format(
            sql.Identifier(table), sql.Identifier(table),
            sql.SQL(' AND ').join(sql.SQL('t.{}=k.{}').format(sql.Identifier(k), sql.Identifier(k)) for k in fields))
        result.extend(row[0] for row in db.execute(query, (Jsonb(batch),)))
    return result


def main():
    base = json.loads((OUT / 'before/local-snapshot.json').read_text())['tables']
    comp = json.loads((OUT / 'content/comparison.json').read_text())['tables']
    maps = {}
    for table, meta in base.items():
        if table not in comp or meta['primary_key'] != ['id']:
            continue
        left = json.loads((OUT / ('content/local-' + table + '.json')).read_text())
        right = json.loads((OUT / ('content/cloud-' + table + '.json')).read_text())
        maps[table] = {}
        for identity in left.keys() & right.keys():
            # Match the multiset, retaining duplicate evidence rather than
            # copying every occurrence when only one extra occurrence exists.
            same = {item[1] for item in left[identity]} & {item[1] for item in right[identity]}
            unmatched_left = [item for item in left[identity] if item[1] not in same]
            unmatched_right = [item for item in right[identity] if item[1] not in same]
            for old_record, new_record in zip(unmatched_left, unmatched_right):
                old, new = (json.loads(item[1])[0] for item in (old_record, new_record))
                if old != new:
                    maps[table][old] = new
    result = {'at': r.core.now(), 'inserts': {}, 'updates': {}, 'equivalent': {},
              'remaps': maps, 'production_only_counts': {}, 'excluded_tables': sorted(a.SKIP)}
    aliases, ambiguous = {}, set()
    for replacements in maps.values():
        for old, new in replacements.items():
            if old in aliases and aliases[old] != new:
                ambiguous.add(old)
            aliases[old] = new
    for old in ambiguous:
        aliases.pop(old)

    def normalized(value):
        if isinstance(value, str):
            return UUID.sub(lambda m: aliases.get(m[0].lower(), m[0]), value)
        if isinstance(value, list):
            return [normalized(v) for v in value]
        if isinstance(value, dict):
            return {k: normalized(v) for k, v in value.items()}
        return value
    with r.connect('local') as source, r.connect('cloud') as dest:
        for db in (source, dest):
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            db.execute("SET LOCAL timezone='UTC'")
        foreign = source.execute("""SELECT conrelid::regclass::text,a.attname,confrelid::regclass::text,b.attname
            FROM pg_constraint c JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=c.conkey[1]
            JOIN pg_attribute b ON b.attrelid=c.confrelid AND b.attnum=c.confkey[1]
            WHERE contype='f' AND cardinality(conkey)=1""").fetchall()
        # The venue reference is a composite FK; its institution component is
        # covered separately by the single-column FK above.
        foreign.append(('artwork_location_assertions', 'venue_id', 'institution_venues', 'id'))
        # These snapshot references are carried by composite research-record
        # FKs rather than a single-column FK directly to research_snapshots.
        for table in ('research_artwork_links', 'research_resolutions'):
            foreign.append((table, 'snapshot_id', 'research_snapshots', 'id'))
        result['foreign'] = foreign
        result['metadata'] = {t: {k: v for k, v in meta.items() if k in ('columns', 'primary_key')}
                              for t, meta in base.items() if t in comp}
        for table, diff in comp.items():
            result['production_only_counts'][table] = len(diff['only_cloud'])
            requested = {item[1] for group in diff['only_local'].values() for item in group}
            requested.update(item[1] for group in diff['changed'].values() for item in group['local'])
            if table == 'citations':
                review = json.loads((OUT / 'citation-review/citation-review-final.json').read_text())
                ids = {row['id'] for group in review['only_local'].values() for row in group}
                for group in review['changed'].values():
                    existing_notes = collections.Counter((row['note'], row['created_by']) for row in group['cloud'])
                    for row in group['local']:
                        signature = (row['note'], row['created_by'])
                        if existing_notes[signature]:
                            existing_notes[signature] -= 1
                        else:
                            ids.add(row['id'])
                requested = {json.dumps([i]) for i in ids}
            if not requested:
                continue
            meta = base[table]
            rows = fetch(source, table, meta, [dict(zip(meta['primary_key'], json.loads(k))) for k in sorted(requested)])
            assert len(rows) == len(requested), table
            for row in rows:
                if table in maps and 'id' in row:
                    row['id'] = maps[table].get(row['id'], row['id'])
                for child, field, parent, parent_field in foreign:
                    if child == table and parent in maps and parent_field == 'id' and row.get(field):
                        row[field] = maps[parent].get(row[field], row[field])
                if table == 'research_artwork_links':
                    row['possible_artwork_ids'] = [maps.get('artworks', {}).get(i, i) for i in row['possible_artwork_ids']]
                if row.get('entity_id') and row.get('entity_type'):
                    parent = {'artist': 'artists', 'artwork': 'artworks', 'institution': 'institutions',
                              'movement': 'movements', 'place': 'places', 'media': 'media_assets'}.get(row['entity_type'])
                    row['entity_id'] = maps.get(parent, {}).get(row['entity_id'], row['entity_id'])
            existing = {keys(row, meta): row for row in fetch(dest, table, meta, rows)}
            # Collection membership has a target-specific surrogate UUID and
            # a stable (collection, artwork) unique identity.
            if table == 'curated_collection_items':
                natural = {(row['collection_id'], row['artwork_id']): row for row in
                           fetch(dest, table, meta, rows, ['collection_id', 'artwork_id'])}
                for row in rows:
                    before = natural.get((row['collection_id'], row['artwork_id']))
                    if before:
                        row['id'] = before['id']
                        existing[keys(row, meta)] = before
            inserts, updates, equivalent = [], [], 0
            generated = {column for column, _, kind in meta['columns'] if kind != 'NEVER'}
            for row in rows:
                before = existing.get(keys(row, meta))
                if before is None:
                    inserts.append(row)
                    continue
                changed = {field: {'before': before.get(field), 'after': row.get(field)} for field in row
                           if field not in IGNORE and field not in generated and normalized(before.get(field)) != normalized(row.get(field))}
                if table == 'curated_collection_items' and set(changed) == {'position'}:
                    changed = {}  # Keep the production collection's established order.
                if table == 'research_artwork_links' and set(changed) <= {'plan_sha256', 'entry_sha256'}:
                    changed = {}  # Preserve the original target-specific import receipts.
                if table == 'book_discovery':
                    # This digest includes checked_at. Independently refreshed
                    # but otherwise identical projections keep their own valid
                    # timestamp/digest pair. A real projection change copies
                    # the source timestamp together with its pinned digest.
                    if set(changed) == {'projection_checksum'}:
                        changed = {}
                    elif changed and 'projection_checksum' in changed and before['checked_at'] != row['checked_at']:
                        changed['checked_at'] = {'before': before['checked_at'], 'after': row['checked_at']}
                if changed:
                    assert not (set(changed) & set(meta['primary_key'])), (table, changed)
                    after = {**before, **{field: row[field] for field in changed}}
                    # Generated values follow the new source fields even
                    # though they must never appear in UPDATE assignments.
                    after.update({field: row[field] for field in generated})
                    updates.append({'before': before, 'source': after, 'changes': changed})
                else:
                    equivalent += 1
            if table == 'curated_collection_items' and inserts:
                maxima = dict(dest.execute('SELECT collection_id::text,max(position) FROM curated_collection_items WHERE collection_id=ANY(%s::uuid[]) GROUP BY collection_id',
                    (sorted({row['collection_id'] for row in inserts}),)))
                for row in sorted(inserts, key=lambda x: (x['collection_id'], x['position'], x['id'])):
                    maxima[row['collection_id']] = maxima.get(row['collection_id'], 0) + 1
                    row['position'] = maxima[row['collection_id']]
                    assert row['position'] <= 100000
            result['inserts'][table] = inserts
            result['updates'][table] = updates
            result['equivalent'][table] = equivalent
            fields = collections.Counter(field for row in updates for field in row['changes'])
            print(table, 'insert', len(inserts), 'update', len(updates), 'equivalent', equivalent,
                  'fields', dict(fields), flush=True)
    r.core.save_new(OUT / 'catalogue-proposal.json', result)
    summary = {'inserts': {t: len(v) for t, v in result['inserts'].items()},
               'updates': {t: len(v) for t, v in result['updates'].items()},
               'update_fields': {t: dict(collections.Counter(f for row in v for f in row['changes']))
                                 for t, v in result['updates'].items() if v},
               'production_only_counts': result['production_only_counts']}
    r.core.save_new(OUT / 'catalogue-proposal-summary.json', summary)


if __name__ == '__main__':
    main()
