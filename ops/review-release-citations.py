#!/usr/bin/env python3
"""Inspect unmatched citation evidence without overwriting either catalogue."""
import argparse
import collections
import concurrent.futures
import importlib.util
import json
import re
from pathlib import Path

from psycopg import sql

spec = importlib.util.spec_from_file_location('release', Path(__file__).with_name('audit-production-release.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
UUID = re.compile(r'\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b', re.I)


def capture(target, root):
    other = 'cloud' if target == 'local' else 'local'
    left = json.loads((root / 'content-before' / (target + '-citations.json')).read_text())
    right = json.loads((root / 'content-before' / (other + '-citations.json')).read_text())
    ids = [json.loads(v[1])[0] for k in left.keys() - right.keys() for v in left[k]]
    entities, aliases, ambiguous = {}, {}, set()
    def register(raw, canonical):
        if raw in aliases and aliases[raw] != canonical: ambiguous.add(raw)
        aliases[raw] = canonical
    for table, kind in [('artists', 'artist'), ('artworks', 'artwork'), ('institutions', 'institution'), ('movements', 'movement')]:
        path = root / 'content-before' / (target + '-' + table + '.json')
        if not path.exists(): continue
        for key, rows in json.loads(path.read_text()).items():
            for _, native in rows:
                raw = json.loads(native)[0]; entities[(kind, raw)] = key
                register(raw, table + ':' + key)
    with r.connect(target) as db:
        db.execute("SET LOCAL timezone='UTC'")
        sources = dict(db.execute('SELECT id::text,slug FROM sources'))
        for raw, key in sources.items(): register(raw, 'sources:' + key)
        for raw, key in db.execute('SELECT id::text,sha256 FROM research_snapshots'): register(raw, 'snapshot:' + key)
        for raw, key in db.execute('SELECT id::text,idempotency_key FROM import_jobs'): register(raw, 'import:' + key)
        for raw, key in db.execute("SELECT l.id::text,jsonb_build_array(a.slug,l.claim_type,l.source_url)::text FROM artwork_location_assertions l JOIN artworks a ON a.id=l.artwork_id WHERE l.superseded_by IS NOT NULL OR l.id IN (SELECT superseded_by FROM artwork_location_assertions WHERE superseded_by IS NOT NULL)"):
            register(raw, 'assertion:' + key)
        rows = []
        for start in range(0, len(ids), 500):
            query = sql.SQL('SELECT to_jsonb(c)::text FROM citations c WHERE id=ANY({}::uuid[])').format(sql.Literal(ids[start:start+500]))
            with db.cursor().copy(sql.SQL('COPY ({}) TO STDOUT').format(query)) as copy:
                rows.extend(json.loads(row[0]) for row in copy.rows())
    for raw in ambiguous: aliases.pop(raw)
    def normalize(value):
        if isinstance(value, str):
            value = UUID.sub(lambda m: aliases.get(m[0].lower(), m[0]), value)
            if value.startswith(('{', '[')):
                try: return json.dumps(normalize(json.loads(value)), sort_keys=True, ensure_ascii=False)
                except ValueError: pass
            return value
        if isinstance(value, dict): return {k: normalize(v) for k, v in value.items()}
        if isinstance(value, list): return [normalize(v) for v in value]
        return value
    normalized = {}
    for row in rows:
        identity = [row['entity_type'], entities.get((row['entity_type'], row['entity_id']), row['entity_id']),
                    sources[row['source_id']], row['field_name'], row['source_record_id'], row['source_url'], row['page_or_locator']]
        key = json.dumps(identity, ensure_ascii=False)
        normalized.setdefault(key, []).append({'id': row['id'], 'note': normalize(row['evidence_note']), 'created_by': row['created_by']})
    r.core.save_new(root / (target + '-citation-review.json'), normalized)
    print(target, 'citation candidates', len(rows), flush=True)
    return normalized


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--root', type=Path, required=True); a = p.parse_args()
    with concurrent.futures.ThreadPoolExecutor(2) as pool: local, cloud = pool.map(lambda t: capture(t, a.root), ['local', 'cloud'])
    content = lambda rows: sorted((v['note'] or '', v['created_by'] or '') for v in rows)
    report = {'at': r.core.now(), 'only_local': {k: local[k] for k in local.keys()-cloud.keys()},
        'only_cloud': {k: cloud[k] for k in cloud.keys()-local.keys()},
        'changed': {k: {'local': local[k], 'cloud': cloud[k]} for k in local.keys()&cloud.keys() if content(local[k]) != content(cloud[k])},
        'matching_after_target_id_resolution': sum(content(local[k]) == content(cloud[k]) for k in local.keys()&cloud.keys())}
    r.core.save_new(a.root / 'citation-review.json', report)
    print({k: len(v) if isinstance(v,dict) else v for k,v in report.items()}, flush=True)
    for field in ['only_local', 'only_cloud', 'changed']:
        print(field, collections.Counter(json.loads(k)[3] for k in report[field]), flush=True)


if __name__ == '__main__': main()
