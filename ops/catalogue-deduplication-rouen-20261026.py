"""Pinned, audited consolidation of the two verified Rouen museum identities.

Production only. Preserve source identities and every artwork/image/creator.
"""
import argparse
import gzip
import hashlib
import json
import shutil
import uuid
from pathlib import Path

import exhibitions_common as c
from psycopg.types.json import Jsonb

OP = 'catalogue-deduplication-rouen-20261026'
E = c.ROOT / 'docs/research/catalogue-deduplication-20261026'
B = Path.home() / 'Library/Application Support/Artline/backups' / OP / 'attempt-002'
EDITOR = 'local-european-research'
ALIAS = '52f9db66-b148-423a-9889-c4acd20e3394'
CANONICAL = 'f92766ec-41cf-42d1-9bb1-f333fe5d2980'
TABLES = {'institutions': 'id', 'artworks': 'current_institution_id',
          'artwork_location_assertions': 'institution_id', 'institution_venues': 'institution_id',
          'curated_collections': 'institution_id', 'exhibition_occurrences': 'institution_id',
          'exhibition_participants': 'institution_id', 'exhibition_source_coverage': 'institution_id',
          'source_institutions': 'institution_id'}


def uid(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, OP + '/' + key))


def rows(db, table, column, values):
    return [r['v'] for r in db.execute('SELECT to_jsonb(t)v FROM ' + table +
                                      ' t WHERE ' + column + '=ANY(%s::uuid[])', (values,))]


def ordered(values):
    return sorted(values, key=lambda v: json.dumps(v, sort_keys=True))


def plan():
    before = c.load(E / 'rouen-premerge-snapshot.json.gz')
    selections = c.load(E / 'rouen-selection-preimages.json')
    assert not selections['items'], 'Nonempty source selections need a separate merge plan'
    inst = {r['id']: r for r in before['tables']['institutions']}
    assert inst[ALIAS]['place_id'] == inst[CANONICAL]['place_id']
    assert all(r['canonical_institution_id'] is None for r in inst.values())
    assert all(r['claim_type'] == 'holding' for r in before['tables']['artwork_location_assertions'])
    alias_works = {r['id'] for r in before['tables']['artworks'] if r['current_institution_id'] == ALIAS}
    accepted = {r['artwork_id'] for r in before['tables']['artwork_location_assertions']
                if r['institution_id'] == ALIAS and r['claim_type'] == 'holding'
                and r['review_state'] == 'accepted' and r['superseded_by'] is None}
    assert alias_works == accepted
    value = dict(at=c.now(), operation=OP, alias=ALIAS, canonical=CANONICAL,
                 primary_sources=['https://mbarouen.fr/', 'https://www.rouen.fr/fr/beauxarts'],
                 authority_code='M0729', source_authority_limit='INHA indexed authority associates M0729 with mbarouen.fr; its live page currently reports infrastructure unavailability. Existing Ministry-backed M0729 object/source identities are preserved.',
                 basis='Same full museum identity, Rouen place and official institution. French Ministry source-name variant is retained as a canonical alias, not deleted.',
                 before=before, selections=selections,
                 scope='Move all alias holdings and artwork institution pointers; archive its unused duplicate venue under the canonical institution. Preserve source associations, frozen source-coverage rows and empty original source selections. No artwork, artist, image, factual metadata or publication-state merge in this operation.')
    c.save(E / 'rouen-museum-merge-plan.json.gz', value)
    B.mkdir(parents=True, exist_ok=True)
    B.chmod(0o700)
    c.save(B / 'plan-and-preimages.json.gz', value)
    print('Pinned Rouen museum plan:', len(alias_works), 'existing artwork pointers')


def apply():
    path = E / 'rouen-museum-merge-plan.json.gz'
    p = c.load(path)
    digest = c.sha(path.read_bytes())
    rollback = c.load(E / 'rouen-museum-merge-attempt001-rollback-verification.json')
    assert rollback['passed'] and rollback['operation_audits'] == 0
    B.mkdir(parents=True, exist_ok=True)
    B.chmod(0o700)
    c.save(B / 'plan-and-preimages.json.gz', p)
    assert shutil.disk_usage(B).free > 15 * 1024**3
    changes = []
    with c.connect(write=True) as db:
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute("SET LOCAL statement_timeout='60s'")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(202610053)')
        db.execute('SELECT id FROM institutions WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE', ([ALIAS, CANONICAL],)).fetchall()
        db.execute('SELECT id FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE', ([ALIAS, CANONICAL],)).fetchall()
        for table, column in TABLES.items():
            assert ordered(rows(db, table, column, [ALIAS, CANONICAL])) == ordered(p['before']['tables'][table]), ('Changed preimages', table)
        assert not db.execute('SELECT 1 FROM institutions WHERE canonical_institution_id=ANY(%s::uuid[])', ([ALIAS, CANONICAL],)).fetchone()
        collection_ids = [r['id'] for r in p['before']['tables']['curated_collections']]
        assert not rows(db, 'curated_collection_items', 'collection_id', collection_ids)
        c.save(B / 'locked-preimages.json.gz', dict(at=c.now(), plan_sha256=digest, before=p['before']))

        db.execute('UPDATE institutions SET canonical_institution_id=%s,updated_at=now() WHERE id=%s', (CANONICAL, ALIAS))
        db.execute("UPDATE institution_venues SET institution_id=%s,status='archived' WHERE institution_id=%s", (CANONICAL, ALIAS))
        db.execute('UPDATE artwork_location_assertions SET institution_id=%s WHERE institution_id=%s', (CANONICAL, ALIAS))
        alias_ids = [r['id'] for r in p['before']['tables']['artworks'] if r['current_institution_id'] == ALIAS]
        # Holding synchronization has already normalized current_institution_id.
        # Address the pinned IDs explicitly so each moved work gains its revision.
        db.execute("UPDATE artworks SET current_institution_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=ANY(%s::uuid[])", (CANONICAL, EDITOR, alias_ids))

        allowed = {'institutions': {'canonical_institution_id', 'updated_at'},
                   'institution_venues': {'institution_id', 'status'},
                   'artwork_location_assertions': {'institution_id'},
                   'artworks': {'current_institution_id', 'revision', 'updated_at', 'updated_by'}}
        for table, column in TABLES.items():
            current = rows(db, table, column, [ALIAS, CANONICAL])
            old = p['before']['tables'][table]
            if table not in allowed:
                assert ordered(current) == ordered(old), ('Protected rows changed', table)
                continue
            actual = {r['id']: r for r in current}
            assert set(actual) == {r['id'] for r in old}
            for before in old:
                after = actual[before['id']]
                assert all(after[k] == v for k, v in before.items() if k not in allowed[table]), (table, before['id'])
                if before == after:
                    continue
                if table == 'artworks':
                    assert before['current_institution_id'] == ALIAS and after['current_institution_id'] == CANONICAL
                    assert after['revision'] == before['revision'] + 1
                changes.append(dict(table=table, id=before['id'], before=before, after=after))

        with db.cursor() as cursor:
            cursor.executemany('INSERT INTO audit_log(id,action,entity_type,entity_id,request_id,before_json,after_json) VALUES(%s,%s,%s,%s,%s,%s,%s)',
                               [(uid(change['table'] + '/' + change['id']), 'museum_identity_merge', change['table'], change['id'], OP,
                                 Jsonb(change['before']), Jsonb(change['after'])) for change in changes])
        assert db.execute('SELECT count(*) n FROM audit_log WHERE request_id=%s', (OP,)).fetchone()['n'] == len(changes)
        assert not db.execute('SELECT 1 FROM artworks WHERE current_institution_id=%s', (ALIAS,)).fetchone()
        assert not db.execute('SELECT 1 FROM artwork_location_assertions WHERE institution_id=%s', (ALIAS,)).fetchone()
        c.save(B / 'transaction-after.json.gz', dict(at=c.now(), plan_sha256=digest, changes=changes))
    c.save(E / 'rouen-museum-merge-applied.json', dict(at=c.now(), operation=OP, plan_sha256=digest,
           changed_rows=len(changes), changed_by_table={t: sum(x['table'] == t for x in changes) for t in allowed},
           atomic_audits=len(changes), artwork_images_creators_metadata_status_preserved=True,
           real_local_catalogue_connections=0, backup_directory=str(B)))
    print('Committed Rouen museum consolidation:', len(changes), 'rows and operation-bound audits', flush=True)


def verify():
    receipt = c.load(E / 'rouen-museum-merge-applied.json')
    changes = c.load(B / 'transaction-after.json.gz')['changes']
    with c.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        for table in {x['table'] for x in changes}:
            expected = {x['id']: x['after'] for x in changes if x['table'] == table}
            actual = {x['id']: x for x in rows(db, table, 'id', list(expected))}
            assert actual == expected, ('Live after-state mismatch', table)
        audit = {(x['entity_type'], str(x['entity_id'])): x for x in db.execute('SELECT entity_type,entity_id,before_json,after_json FROM audit_log WHERE request_id=%s', (OP,))}
        assert len(audit) == len(changes)
        assert all(audit[(x['table'], x['id'])]['before_json'] == x['before'] and audit[(x['table'], x['id'])]['after_json'] == x['after'] for x in changes)
        counts = db.execute("SELECT count(*) FILTER(WHERE status<>'archived') active,count(*) FILTER(WHERE status<>'archived' AND primary_media_id IS NOT NULL) illustrated FROM artworks WHERE current_institution_id=%s", (CANONICAL,)).fetchone()
        resolution = db.execute('SELECT i.slug,c.slug canonical_slug FROM institutions i JOIN institutions c ON c.id=i.canonical_institution_id WHERE i.id=%s', (ALIAS,)).fetchone()
        assert resolution['canonical_slug'] == 'musee-beaux-arts-rouen'
    c.save(E / 'rouen-museum-merge-verification.json', dict(at=c.now(), passed=True, plan_sha256=receipt['plan_sha256'],
           independently_checked_rows=len(changes), matching_operation_audits=len(audit), museum_counts=counts,
           old_url_resolution=resolution, local_catalogue_connections=0))
    print('Verified Rouen museum merge:', counts, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['plan', 'apply', 'verify'])
    args = parser.parse_args()
    globals()[args.phase]()
