#!/usr/bin/env python3
"""Publish exactly the 38 reviewed war books; preserve unrelated catalogue data."""
import argparse
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

os.umask(0o077)
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/research/war-books-africa-20261004/plan.json'
OUT = ROOT / 'docs/research/war-books-africa-20261004/publication'
BACKUP = Path('/Users/vadimdulub/Library/Application Support/Artline/backups/war-publication-20261005')
BACKUP_ID = '1791182148526'
KEYS = {'book_records': ['id'], 'book_creators': ['id'], 'book_creator_links': ['book_id', 'creator_id'], 'book_discovery': ['book_id'], 'book_discovery_terms': ['kind', 'key']}
COLUMNS = {'book_records': ['id', 'source_id', 'status', 'record', 'source_checksum'],
           'book_creators': ['id', 'name', 'record', 'source_checksum'],
           'book_creator_links': ['book_id', 'creator_id', 'position', 'credit'],
           'book_discovery_terms': ['kind', 'key', 'name', 'evidence']}


def norm(x):
    return json.loads(json.dumps(x, ensure_ascii=False, default=str))


def digest(x):
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + '\n')


def connect(target, readonly=True):
    dsn = 'postgres://localhost/artline'
    if target == 'production':
        raw = subprocess.check_output(['gcloud', 'secrets', 'versions', 'access', 'latest', '--secret=artline-database-url', '--project=artline-508319', '--account=vadim@alingva.com'], text=True).strip()
        fields = psycopg.conninfo.conninfo_to_dict(raw)
        fields.update(host='127.0.0.1', port='55445', sslmode='disable', connect_timeout='15')
        dsn = psycopg.conninfo.make_conninfo(**fields)
    return psycopg.connect(dsn, row_factory=dict_row, options='-c statement_timeout=180000 -c lock_timeout=10000' + (' -c default_transaction_read_only=on' if readonly else ''))


def key(table, row):
    return tuple(row[k] for k in KEYS[table])


def rows(db, table, ids, column='id'):
    return norm(db.execute('SELECT * FROM ' + table + ' WHERE ' + column + '=ANY(%s) ORDER BY ' + ','.join(KEYS[table]), (ids,)).fetchall())


def state(db, ids, creators, terms):
    result = {t: rows(db, t, ids, 'id' if t == 'book_records' else 'book_id') for t in ['book_records', 'book_creator_links', 'book_discovery']}
    result['book_creators'] = rows(db, 'book_creators', creators)
    result['book_discovery_terms'] = norm([r for r in db.execute('SELECT * FROM book_discovery_terms ORDER BY kind,key') if [r['kind'], r['key']] in terms])
    return result


def totals(db):
    return dict(db.execute("SELECT count(*) books,count(*) FILTER(WHERE status='published') published,(SELECT count(*) FROM book_discovery WHERE top100) highlights FROM book_records").fetchone())


def fingerprint(db, ids, creators):
    return dict(db.execute("""SELECT
        (SELECT md5(string_agg(row_to_json(b)::text,'|' ORDER BY id)) FROM book_records b WHERE NOT(id=ANY(%s))) books,
        (SELECT md5(string_agg(row_to_json(d)::text,'|' ORDER BY book_id)) FROM book_discovery d WHERE NOT(book_id=ANY(%s))) discovery,
        (SELECT md5(string_agg(row_to_json(c)::text,'|' ORDER BY id)) FROM book_creators c WHERE NOT(id=ANY(%s))) creators""", (ids, ids, creators)).fetchone())


def prepare():
    assert not (OUT / 'plan.json').exists(), 'Preserve the reviewed publication plan.'
    source = json.loads(SOURCE.read_text())
    ids = [c['id'] for c in source['changes']]
    assert len(ids) == len(set(ids)) == 38
    with connect('local') as local, connect('production') as production:
        links = rows(local, 'book_creator_links', ids, 'book_id')
        creators = sorted({x['creator_id'] for x in links})
        discovery = rows(local, 'book_discovery', ids, 'book_id')
        terms = [list(t) for t in sorted({(kind, value) for d in discovery for kind, field in [('language', 'languages'), ('country', 'countries'), ('region', 'regions')] for value in d[field]})]
        before = {name: state(db, ids, creators, terms) for name, db in [('local', local), ('production', production)]}
        books = {r['id']: r for r in before['local']['book_records']}
        for change in source['changes']:
            row = books[change['id']]
            assert row['status'] == 'review' and row['record'] == change['record'] and row['source_checksum'] == change['sourceChecksum'], 'Selected book changed after review: ' + change['id']
            assert row['record']['dateBasis'] and row['record']['dateSources'] and row['end_year'] <= 2000
        assert not before['production']['book_records'], 'Reconcile existing selected production books before publishing.'
        assert not production.execute('SELECT id FROM book_records WHERE source_id=ANY(%s)', ([c['record']['sourceId'] for c in source['changes']],)).fetchall()
        for table in ['book_creators', 'book_creator_links', 'book_discovery_terms']:
            existing = {key(table, r): r for r in before['production'][table]}
            for row in before['local'][table]:
                if key(table, row) in existing:
                    columns = ['kind', 'key', 'name'] if table == 'book_discovery_terms' else COLUMNS[table]
                    assert all(row[c] == existing[key(table, row)][c] for c in columns), 'Dependency differs: ' + table + ' ' + str(key(table, row))
        desired = copy.deepcopy(before['local'])
        for row in desired['book_records']:
            row['status'] = 'published'  # Imported source payload/checksum stays unchanged.
        plan = {'ids': ids, 'creators': creators, 'terms': terms, 'before': before, 'desired': desired,
                'beforeTotals': {'local': totals(local), 'production': totals(production)},
                'sourcePlanSha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'cloudBackupId': BACKUP_ID}
    save(OUT / 'plan.json', plan)
    print(json.dumps({'books': len(ids), 'newProductionCreators': len(desired['book_creators']) - len(before['production']['book_creators']), 'sha256': digest(plan), 'before': plan['beforeTotals']}, indent=2))


def apply(pin):
    plan = json.loads((OUT / 'plan.json').read_text())
    assert digest(plan) == pin and hashlib.sha256(SOURCE.read_bytes()).hexdigest() == plan['sourcePlanSha256']
    backup = json.loads(subprocess.check_output(['gcloud', 'sql', 'backups', 'describe', BACKUP_ID, '--instance=artline-postgres', '--project=artline-508319', '--account=vadim@alingva.com', '--format=json'], text=True))
    assert backup['status'] == 'SUCCESSFUL', 'Wait for successful production backup.'
    save(BACKUP / 'cloud-backup.json', backup)
    for target in ['production', 'local']:
        receipt = OUT / (target + '-receipt.json')
        if receipt.exists():
            continue
        with connect(target, False) as db, db.transaction():
            db.execute('SELECT pg_advisory_xact_lock(202610050038)')
            db.execute('LOCK TABLE book_records,book_creators,book_creator_links,book_discovery,book_discovery_terms IN SHARE ROW EXCLUSIVE MODE')
            assert state(db, plan['ids'], plan['creators'], plan['terms']) == plan['before'][target], 'Catalogue changed after preparation: ' + target
            before = totals(db)
            untouched = fingerprint(db, plan['ids'], plan['creators'])
            save(BACKUP / (target + '-preimages.json'), {'planSha256': pin, 'before': plan['before'][target], 'beforeTotals': before, 'unselectedFingerprint': untouched})
            if target == 'production':
                for table in ['book_creators', 'book_discovery_terms', 'book_records', 'book_creator_links', 'book_discovery']:
                    existing = {key(table, r) for r in plan['before'][target][table]}
                    for row in plan['desired'][table]:
                        if key(table, row) in existing:
                            continue
                        columns = COLUMNS.get(table, list(row))
                        db.execute('INSERT INTO ' + table + '(' + ','.join(columns) + ') VALUES(' + ','.join(['%s'] * len(columns)) + ')',
                                   tuple(Jsonb(row[c]) if isinstance(row[c], dict) else row[c] for c in columns))
            else:
                db.execute("UPDATE book_records SET status='published' WHERE id=ANY(%s) AND status='review'", (plan['ids'],))
            actual = state(db, plan['ids'], plan['creators'], plan['terms'])
            for table in ['book_records', 'book_creator_links', 'book_discovery']:
                bykey = {key(table, r): r for r in actual[table]}
                for row in plan['desired'][table]:
                    for column in COLUMNS.get(table, list(row)):
                        found, expected = bykey[key(table, row)][column], row[column]
                        if column == 'checked_at':
                            # PostgreSQL renders timestamptz in each server's
                            # timezone; compare the instant, not its offset text.
                            found = datetime.datetime.fromisoformat(found)
                            expected = datetime.datetime.fromisoformat(expected)
                        assert found == expected, 'Verification failed: ' + table + ' ' + column
            for row in plan['before'][target]['book_creators']:
                assert next(r for r in actual['book_creators'] if r['id'] == row['id']) == row
            assert fingerprint(db, plan['ids'], plan['creators']) == untouched
            after = totals(db)
            assert after == dict(before, books=before['books'] + (38 if target == 'production' else 0), published=before['published'] + 38)
        result = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'target': target, 'planSha256': pin, 'cloudBackupId': BACKUP_ID, 'publishedBooks': 38, 'before': before, 'after': after, 'unselectedDataUnchanged': True, 'existingCreatorsUnchanged': True, 'sourcePayloadsAndDiscoveryPreserved': True}
        save(receipt, result)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'apply'])
    parser.add_argument('--sha256')
    args = parser.parse_args()
    if args.stage == 'prepare':
        prepare()
    else:
        assert args.sha256
        apply(args.sha256)
