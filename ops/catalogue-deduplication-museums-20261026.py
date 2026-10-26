"""Six source-confirmed museum aliases; production only, pinned row audits."""
import argparse
import json
import shutil
import uuid
from pathlib import Path

import exhibitions_common as c
from psycopg.types.json import Jsonb

OP = 'catalogue-deduplication-museums-six-20261026'
E = c.ROOT / 'docs/research/catalogue-deduplication-20261026'
D = Path.home() / 'Library/Application Support/Artline/source-metadata/catalogue-deduplication-20261026/museum-identities'
B = Path.home() / 'Library/Application Support/Artline/backups' / OP
EDITOR = 'local-european-research'
TABLES = {'institutions': 'id', 'artworks': 'current_institution_id',
          'artwork_location_assertions': 'institution_id', 'institution_venues': 'institution_id',
          'curated_collections': 'institution_id', 'exhibition_occurrences': 'institution_id',
          'exhibition_participants': 'institution_id', 'exhibition_source_coverage': 'institution_id',
          'source_institutions': 'institution_id'}
TOKENS = {'sassari': ['pinacoteca nazionale di sassari', 'piazza santa caterina'],
          'caserta': ['reggia di caserta', 'collezioni'],
          'novecento': ['museo novecento', 'firenze'],
          'muma': ['m0720', 'muma le havre', 'muma lehavre fr'],
          'unterlinden': ['musee unterlinden', 'colmar'],
          'gnam': ['galleria nazionale', 'roma']}


def uid(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, OP + '/' + key))


def rows(db, table, column, ids):
    return [r['v'] for r in db.execute('SELECT to_jsonb(t)v FROM ' + table + ' t WHERE ' + column + '=ANY(%s::uuid[])', (ids,))]


def ordered(items):
    return sorted(items, key=lambda r: json.dumps(r, sort_keys=True))


def plan():
    before = c.load(E / 'museum-merge-six-preimages.json.gz')
    sources = []
    inst = {r['id']: r for r in before['tables']['institutions']}
    alias_collections = {r['id'] for r in before['tables']['curated_collections']
                         if r['institution_id'] in [p[1] for p in before['pairs']]}
    assert not any(r['collection_id'] in alias_collections for r in before['tables']['curated_collection_items'])
    for key, alias, canonical in before['pairs']:
        receipt = c.load(E / ('identity-source-' + key + '.json'))
        assert receipt['status'] == 200
        import gzip
        raw = gzip.decompress(Path(receipt['body_path']).read_bytes())
        assert c.sha(raw) == receipt['sha256']
        text = c.norm((D / (key + '.txt')).read_text())
        assert all(c.norm(t) in text for t in TOKENS[key]), ('Identity statement missing', key)
        assert all(inst[i]['canonical_institution_id'] is None and inst[i]['status'] != 'archived' for i in [alias, canonical])
        if inst[alias]['place_id'] and inst[canonical]['place_id']:
            assert inst[alias]['place_id'] == inst[canonical]['place_id']
        sources.append(dict(key=key, alias=alias, canonical=canonical, receipt=receipt,
                            basis='Same named institutional collection and explicit municipality, corroborated by the official museum, government or municipal source. Native source spelling and identifiers remain resolvable aliases.'))
    assert all(r['claim_type'] == 'holding' for r in before['tables']['artwork_location_assertions'])
    value = dict(at=c.now(), operation=OP, sources=sources, before=before,
                 protected_selection_items=len(before['tables']['curated_collection_items']),
                 scope='Institution pointer consolidation only. Preserve every artwork, image, creator, source row, source coverage, selection and historical venue label. The unused duplicate MuMa venue is archived under the canonical institution.')
    c.save(E / 'museum-merge-six-plan.json.gz', value)
    B.mkdir(parents=True, exist_ok=True)
    B.chmod(0o700)
    c.save(B / 'plan-and-preimages.json.gz', value)
    print('Pinned', len(sources), 'source-confirmed museum aliases', flush=True)


def apply():
    path = E / 'museum-merge-six-plan.json.gz'
    p = c.load(path)
    before = p['before']
    digest = c.sha(path.read_bytes())
    assert shutil.disk_usage(B).free > 15 * 1024**3
    changes = []
    with c.connect(write=True) as db:
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute("SET LOCAL statement_timeout='60s'")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(202610053)')
        db.execute('SELECT id FROM institutions WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE', (before['ids'],)).fetchall()
        db.execute('SELECT id FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE', (before['ids'],)).fetchall()
        for table, column in TABLES.items():
            assert ordered(rows(db, table, column, before['ids'])) == ordered(before['tables'][table]), ('Changed preimage', table)
        collection_ids = [r['id'] for r in before['tables']['curated_collections']]
        assert ordered(rows(db, 'curated_collection_items', 'collection_id', collection_ids)) == ordered(before['tables']['curated_collection_items'])
        c.save(B / 'locked-preimages.json.gz', dict(at=c.now(), plan_sha256=digest, before=before))
        for key, alias, canonical in before['pairs']:
            ids = [r['id'] for r in before['tables']['artworks'] if r['current_institution_id'] == alias]
            db.execute('UPDATE institutions SET canonical_institution_id=%s,updated_at=now() WHERE id=%s', (canonical, alias))
            db.execute("UPDATE institution_venues SET institution_id=%s,status='archived' WHERE institution_id=%s", (canonical, alias))
            db.execute('UPDATE artwork_location_assertions SET institution_id=%s WHERE institution_id=%s', (canonical, alias))
            db.execute('UPDATE artworks SET current_institution_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=ANY(%s::uuid[])', (canonical, EDITOR, ids))
        allowed = {'institutions': {'canonical_institution_id', 'updated_at'}, 'institution_venues': {'institution_id', 'status'},
                   'artwork_location_assertions': {'institution_id'}, 'artworks': {'current_institution_id', 'revision', 'updated_at', 'updated_by'}}
        mapping = {a: b for key, a, b in before['pairs']}
        for table, column in TABLES.items():
            actual_rows = rows(db, table, column, before['ids'])
            old_rows = before['tables'][table]
            if table not in allowed:
                assert ordered(actual_rows) == ordered(old_rows), ('Protected table changed', table)
                continue
            actual = {r['id']: r for r in actual_rows}
            assert set(actual) == {r['id'] for r in old_rows}
            for old in old_rows:
                new = actual[old['id']]
                assert all(new[k] == v for k, v in old.items() if k not in allowed[table]), (table, old['id'])
                if old == new:
                    continue
                if table == 'artworks':
                    assert new['current_institution_id'] == mapping[old['current_institution_id']] and new['revision'] == old['revision'] + 1
                changes.append(dict(table=table, id=old['id'], before=old, after=new))
        assert ordered(rows(db, 'curated_collection_items', 'collection_id', collection_ids)) == ordered(before['tables']['curated_collection_items'])
        with db.cursor() as cursor:
            cursor.executemany('INSERT INTO audit_log(id,action,entity_type,entity_id,request_id,before_json,after_json)VALUES(%s,%s,%s,%s,%s,%s,%s)',
                               [(uid(x['table'] + '/' + x['id']), 'museum_identity_merge', x['table'], x['id'], OP, Jsonb(x['before']), Jsonb(x['after'])) for x in changes])
        assert db.execute('SELECT count(*)n FROM audit_log WHERE request_id=%s', (OP,)).fetchone()['n'] == len(changes)
        c.save(B / 'transaction-after.json.gz', dict(at=c.now(), plan_sha256=digest, changes=changes))
    c.save(E / 'museum-merge-six-applied.json', dict(at=c.now(), operation=OP, plan_sha256=digest, aliases=6,
           changed_rows=len(changes), atomic_audits=len(changes), protected_selection_items=len(before['tables']['curated_collection_items']),
           changed_by_table={t: sum(x['table'] == t for x in changes) for t in allowed}, local_catalogue_connections=0))
    print('Committed six museum aliases:', len(changes), 'rows and operation-bound audits', flush=True)


def verify():
    changes = c.load(B / 'transaction-after.json.gz')['changes']
    p = c.load(E / 'museum-merge-six-plan.json.gz')
    with c.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        for table in {r['table'] for r in changes}:
            expected = {r['id']: r['after'] for r in changes if r['table'] == table}
            assert {r['id']: r for r in rows(db, table, 'id', list(expected))} == expected
        audits = {(r['entity_type'], str(r['entity_id'])): r for r in db.execute('SELECT entity_type,entity_id,before_json,after_json FROM audit_log WHERE request_id=%s', (OP,))}
        assert len(audits) == len(changes)
        assert all(audits[(r['table'], r['id'])]['before_json'] == r['before'] and audits[(r['table'], r['id'])]['after_json'] == r['after'] for r in changes)
        alias_ids = [a for key, a, b in p['before']['pairs']]
        assert not rows(db, 'artworks', 'current_institution_id', alias_ids)
        counts = db.execute("SELECT i.slug,count(a.id)FILTER(WHERE a.status<>'archived')active,count(a.id)FILTER(WHERE a.status<>'archived'AND a.primary_media_id IS NOT NULL)illustrated FROM institutions i LEFT JOIN artworks a ON a.current_institution_id=i.id WHERE i.id=ANY(%s::uuid[])GROUP BY i.slug ORDER BY i.slug", ([b for key, a, b in p['before']['pairs']],)).fetchall()
        cols = [r['id'] for r in p['before']['tables']['curated_collections']]
        assert ordered(rows(db, 'curated_collection_items', 'collection_id', cols)) == ordered(p['before']['tables']['curated_collection_items'])
    c.save(E / 'museum-merge-six-verification.json', dict(at=c.now(), passed=True, independently_checked_rows=len(changes),
           matching_atomic_audits=len(audits), museum_counts=counts, all_selection_items_preserved=True, local_catalogue_connections=0))
    print('Verified six museum merges:', json.dumps(counts), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['plan', 'apply', 'verify'])
    args = parser.parse_args()
    globals()[args.phase]()
