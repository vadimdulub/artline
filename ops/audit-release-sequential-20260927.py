#!/usr/bin/env python3
"""Fingerprint remaining tables without random database lookups per record.

PostgreSQL hashes every non-reference content field in one sequential read.
The already-audited identity maps normalize FKs in local memory. Both targets
use this same fingerprint representation; no content, status, or evidence is
discarded. Original receipts are retained under fingerprints-v1.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

from psycopg import sql

spec = importlib.util.spec_from_file_location('a', Path(__file__).with_name('audit-release-content.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
OUT = a.r.ROOT / 'docs/research/production-release-20260927/content'
TABLES = ['citations', 'curated_collection_items', 'external_identifiers', 'media_assets',
          'media_rights_evidence', 'research_artwork_enrichments', 'research_artwork_links',
          'research_records', 'research_resolutions']
KINDS = {'artist': 'artists', 'artwork': 'artworks', 'institution': 'institutions',
         'movement': 'movements', 'place': 'places', 'media': 'media_assets'}


def main():
    snapshot = json.loads((OUT.parent / 'before/local-snapshot.json').read_text())
    metadata = {t: {'columns': m['columns'], 'primary_key': m['primary_key']} for t, m in snapshot['tables'].items()}
    del snapshot
    for target in ('local', 'cloud'):
        identities = {}
        for parent in a.IDENTITY:
            path = OUT / f'{target}-{parent}.json'
            if parent == 'media_assets' or not path.exists():
                continue
            records = json.loads(path.read_text())
            identities[parent] = {json.loads(item[1])[0]: identity for identity, group in records.items() for item in group}
        for table in TABLES:
            path = OUT / f'{target}-{table}.json'
            marker = OUT.parent / 'sequential-receipts' / f'{target}-{table}.json'
            if marker.exists():
                continue
            meta = metadata[table]
            with a.r.connect(target) as db:
                db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                db.execute("SET LOCAL timezone='UTC'")
                db.execute('SET LOCAL jit=off')
                foreign = db.execute("""SELECT col.attname,c.confrelid::regclass::text,p.attname
                    FROM pg_constraint c JOIN pg_attribute col ON col.attrelid=c.conrelid AND col.attnum=c.conkey[1]
                    JOIN pg_attribute p ON p.attrelid=c.confrelid AND p.attnum=c.confkey[1]
                    WHERE c.contype='f' AND cardinality(c.conkey)=1 AND c.conrelid=%s::regclass""", (table,)).fetchall()
                refs = {col: parent for col, parent, key in foreign if key == 'id' and parent in a.IDENTITY}
                columns = {col: typ for col, typ, _ in meta['columns']}
                polymorphic = 'entity_id' in columns and 'entity_type' in columns
                if polymorphic:
                    refs['entity_id'] = None
                excluded = a.r.CLOCKS + ['search_text', 'resolved_at'] + list(refs)
                if columns.get('id') == 'uuid':
                    excluded.append('id')
                ref_fields = list(refs) + (['entity_type'] if polymorphic else [])
                reference = ('jsonb_build_object(' + ','.join(sql.Literal(col).as_string() + ',t.' + sql.Identifier(col).as_string()
                             for col in ref_fields) + ')::text') if ref_fields else "'{}'::text"
                primary = 'jsonb_build_array(' + ','.join('t.' + sql.Identifier(k).as_string() for k in meta['primary_key']) + ')::text'
                explicit = "NULL::text"
                if table == 'media_assets':
                    explicit = 't.id::text'
                elif table == 'external_identifiers':
                    explicit = 'jsonb_build_array(t.scheme,t.external_id)::text'
                elif 'id' in columns and 'id' not in excluded:
                    explicit = 't.id::text'
                query = ('SELECT ' + primary + ',md5((to_jsonb(t)-' + sql.Literal(excluded).as_string() +
                         '::text[])::text),' + reference + ',' + explicit + ' FROM ' + sql.Identifier(table).as_string() + ' t')
                results, count = {}, 0
                with db.cursor().copy('COPY (' + query + ') TO STDOUT') as copy:
                    for primary_key, base, raw_refs, identity in copy.rows():
                        values = json.loads(raw_refs)
                        normalized = {}
                        for col, parent in refs.items():
                            value = values[col]
                            if col == 'entity_id' and polymorphic:
                                parent = KINDS.get(values['entity_type'])
                            normalized[col] = identities.get(parent, {}).get(value, value) if value is not None else None
                        digest = hashlib.sha256(json.dumps([base, normalized], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                        results.setdefault(identity or digest, []).append([digest, primary_key])
                        count += 1
                        if count % 50000 == 0:
                            print(target, table, count, flush=True)
                assert count == db.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table))).fetchone()[0]
            for group in results.values():
                group.sort()
            if path.exists():
                archive = OUT.parent / 'fingerprints-v1' / path.name
                archive.parent.mkdir(exist_ok=True)
                assert not archive.exists()
                path.rename(archive)
            a.r.core.save_new(path, results)
            a.r.core.save_new(marker, {'at': a.r.core.now(), 'target': target, 'table': table, 'count': count,
                'method': 'SHA256 of PostgreSQL non-reference content MD5 and canonical FK identities; complete repeatable-read sequential snapshot.'})
            print(target, table, 'complete', count, flush=True)
    a.compare(OUT)


if __name__ == '__main__':
    main()
