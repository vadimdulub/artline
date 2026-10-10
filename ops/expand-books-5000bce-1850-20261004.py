#!/usr/bin/env python3
"""Prepare and deliver one sourced, additive selection to local and production.

Both targets require pinned source evidence and exact preimages. No publication,
existing-record edits, fixtures, migrations, or unrelated catalogue synchronization.
"""
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import urllib.request

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/research/books-5000bce-1850-20261004'
BACKUP = Path('/Users/vadimdulub/Library/Application Support/Artline/backups/books-5000bce-1850-20261004')
spec = importlib.util.spec_from_file_location('book_helpers', ROOT / 'ops/expand-pre1850-books-20261001.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
w.OUT = OUT
w.research.OUT = OUT
TABLES = ['book_records', 'book_creators', 'book_creator_links', 'book_discovery', 'book_discovery_terms']


def connect(target, readonly=True):
    dsn = 'postgres://127.0.0.1/artline?sslmode=disable'
    if target == 'cloud':
        raw = subprocess.check_output(['gcloud', 'secrets', 'versions', 'access', 'latest', '--secret=artline-database-url', '--project=artline-508319', '--account=vadim@alingva.com'], text=True).strip()
        fields = psycopg.conninfo.conninfo_to_dict(raw)
        fields.update(host='127.0.0.1', port='55439', sslmode='disable', connect_timeout='15')
        dsn = psycopg.conninfo.make_conninfo(**fields)
    return psycopg.connect(dsn, row_factory=dict_row, options='-c statement_timeout=180000' + (' -c default_transaction_read_only=on' if readonly else ''))


def totals(db):
    return dict(db.execute("""SELECT count(*) books,
        count(*) FILTER (WHERE status='published') published,
        count(*) FILTER (WHERE start_year>=-5000 AND end_year<=1850) in_range,
        (SELECT count(*) FROM book_discovery WHERE top100) highlights
        FROM book_records""").fetchone())


def state(db, ids, creators):
    return w.normalized({
        'books': db.execute('SELECT * FROM book_records WHERE id=ANY(%s) ORDER BY id', (ids,)).fetchall(),
        'creators': db.execute('SELECT * FROM book_creators WHERE id=ANY(%s) ORDER BY id', (creators,)).fetchall(),
        'links': db.execute('SELECT * FROM book_creator_links WHERE book_id=ANY(%s) ORDER BY book_id,position', (ids,)).fetchall(),
        'discovery': db.execute('SELECT * FROM book_discovery WHERE book_id=ANY(%s) ORDER BY book_id', (ids,)).fetchall(),
        'terms': db.execute('SELECT * FROM book_discovery_terms ORDER BY kind,key').fetchall(),
    })


def fingerprint(db, ids, new_creators):
    result = dict(w.unchanged_fingerprint(db, ids))
    result['creators'] = db.execute("SELECT md5(string_agg(row_to_json(c)::text,'|' ORDER BY id)) value FROM book_creators c WHERE NOT(id=ANY(%s))", (new_creators,)).fetchone()['value']
    result['links'] = db.execute("SELECT md5(string_agg(row_to_json(l)::text,'|' ORDER BY book_id,position)) value FROM book_creator_links l WHERE NOT(book_id=ANY(%s))", (ids,)).fetchone()['value']
    return result


def extra_source(url):
    reviews = json.loads((OUT / 'primary-source-reviews.json').read_text())
    reviewed = next((r for r in reviews if r['url'] == url), None)
    if reviewed:
        return reviewed
    path = OUT / 'sources' / (hashlib.sha256(url.encode()).hexdigest() + '.html.gz')
    receipt = path.with_suffix('.receipt.json')
    if not path.exists():
        request = urllib.request.Request(url, headers={'User-Agent': 'ArtlineBookResearch/1.0 (https://artlines.org/about)'})
        with urllib.request.urlopen(request, timeout=45) as response:
            raw = response.read(16 * 1024 * 1024 + 1)
            assert len(raw) <= 16 * 1024 * 1024
            final = response.url
        path.write_bytes(gzip.compress(raw, mtime=0))
        w.save(receipt, {'url': url, 'finalUrl': final, 'path': str(path.relative_to(ROOT)), 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return json.loads(receipt.read_text())


def prepare():
    assert not (OUT / 'plan.json').exists(), 'Preserve the pinned plan.'
    selection = json.loads((OUT / 'selection.json').read_text())
    candidates = {c['qid']: c for c in json.loads((OUT / 'candidates.json').read_text())}
    metadata = json.loads((OUT / 'metadata.json').read_text())
    full_articles = json.loads((OUT / 'full-articles.json').read_text())
    choices = selection['items']
    qids = [x['qid'] for x in choices]
    ids = ['wd-' + q.lower() for q in qids]
    assert len(qids) == len(set(qids))
    authors = sorted({a for x in choices for a in x.get('creatorIds', w.r.ids(candidates[x['qid']]['wikidata']['entity'], 'P50'))})
    targets = {}
    for target in ['local', 'cloud']:
        with connect(target) as db:
            assert not db.execute('SELECT id FROM book_records WHERE source_id=ANY(%s) OR id=ANY(%s)', (qids, ids)).fetchall(), 'Already present in ' + target
            targets[target] = {'before': state(db, ids, authors), 'totals': totals(db)}
    existing = {c['id']: c for c in targets['local']['before']['creators']}
    for creator in targets['cloud']['before']['creators']:
        if creator['id'] in existing:
            assert creator == existing[creator['id']], 'Existing creator differs between targets: ' + creator['id']
        existing.setdefault(creator['id'], creator)
    creators = dict(existing)
    for q in authors:
        if q in creators:
            continue
        e = metadata[q]['entity']
        assert 'Q5' in w.r.ids(e, 'P31')
        rec = {'id': q, 'name': w.r.creator_name(e), 'description': w.r.description(e), 'birth': w.r.life_label(e, 'P569'), 'death': w.r.life_label(e, 'P570'), 'sourceUrl': 'https://www.wikidata.org/wiki/' + q, 'sourceRevision': e.get('lastrevid'), 'kind': 'person', 'credit': ''}
        creators[q] = {'id': q, 'name': rec['name'], 'record': rec, 'source_checksum': w.digest(rec)}
    terms, changes, proofs = {}, [], []
    known_terms = {(t['kind'], t['key']) for target in targets.values() for t in target['before']['terms']}
    for choice in choices:
        q = choice['qid']; c = candidates[q]; e = c['wikidata']['entity']; id = 'wd-' + q.lower()
        assert not set(w.r.ids(e, 'P31')) & {'Q5', 'Q4167410', 'Q4167836', 'Q11424', 'Q223393'}
        assert not w.r.ids(e, 'P629'), 'Edition identity needs reconciliation: ' + q
        start, end, approximate, label, basis = choice['date']
        assert isinstance(start, int) and isinstance(end, int) and -5000 <= start <= end <= 1850 and start != 0 and end != 0
        author_ids = choice.get('creatorIds', w.r.ids(e, 'P50'))
        if not author_ids:
            assert choice.get('authorLabel') and q == 'Q209919'
        links = [{'book_id': id, 'creator_id': a, 'position': i, 'credit': choice.get('creatorCredit', 'Author')} for i, a in enumerate(author_ids)]
        title = choice.get('title', c['title'].replace(' (novel)', '').replace(' (poem)', '').replace(' (poetry collection)', ''))
        source_url = 'https://en.wikipedia.org/w/index.php?oldid=' + str(c['revision'])
        record = {'id': id, 'sourceId': q, 'title': title, 'author': choice.get('authorLabel') or ' · '.join(creators[a]['name'] for a in author_ids), 'creators': [], 'startYear': start, 'endYear': end, 'years': label, 'approximate': approximate, 'era': 'Ancient' if end < 500 else 'Medieval' if end < 1500 else 'Early modern' if end < 1800 else 'Modern', 'theme': choice['theme'], 'description': choice['description'], 'selectionBasis': choice['basis'], 'dateBasis': basis, 'dateSources': [{'name': 'Reviewed work article — ' + c['title'], 'url': source_url}] + choice.get('additionalSources', []), 'sourceUrl': 'https://www.wikidata.org/wiki/' + q, 'sourceRevision': e.get('lastrevid'), 'status': 'review', 'coverTone': '#e8ddc1', 'coverInk': '#29251f', 'coverMark': title[0]}
        if not choice.get('omitOverview'):
            paragraphs = w.excerpt(c['extract'], 'book')
            if paragraphs:
                record['overview'] = {'paragraphs': paragraphs, 'sourceUrl': source_url, 'sourceTitle': c['title'], 'revision': c['revision'], 'credit': 'Wikipedia contributors', 'licenseUrl': w.LICENSE}
        full = dict(record, creators=[dict(creators[l['creator_id']]['record'], credit=l['credit']) for l in links])
        checksum = w.digest(full)
        languages = choice.get('languages', w.r.ids(e, 'P407'))
        countries = w.r.ids(e, 'P495')
        for kind, values in [('language', languages), ('country', countries)]:
            for key in values:
                if (kind, key) not in known_terms:
                    terms[kind, key] = {'kind': kind, 'key': key, 'name': w.r.name(metadata[key]['entity']), 'evidence': {'source': metadata[key]['source']}}
        projection = {'book_id': id, 'book_checksum': checksum, 'top100': False, 'woman_author_ids': sorted(a for a in author_ids if set(w.r.ids(metadata[a]['entity'], 'P21')) & {'Q6581072', 'Q1052281'}), 'languages': sorted(set(languages)), 'countries': sorted(set(countries)), 'regions': [], 'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'evidence': {'work': c['wikidata']['source'], 'context': full_articles[q]['source'], 'selection': choice, 'creators': {a: metadata[a]['source'] for a in author_ids}, 'regionBasis': 'No geography inferred from language, author, or setting; direct source country claims only.', 'highlightBasis': 'No automatic highlight designation.'}}
        projection['projection_checksum'] = w.digest(projection)
        changes.append({'id': id, 'record': record, 'fullRecord': full, 'sourceChecksum': checksum, 'links': links, 'projection': projection})
        proofs += [c['source'], c['wikidata']['source'], full_articles[q]['source']]
        for source in choice.get('additionalSources', []):
            proofs.append(extra_source(source['url']))
    proofs += [m['source'] for m in metadata.values()]
    proofs.append(json.loads((OUT / 'crabbe-identity.json').read_text())['source'])
    # Include each target's existing term definitions so missing dependencies can
    # be added without replacing names or evidence that already exist there.
    for target in targets.values():
        for term in target['before']['terms']:
            terms.setdefault((term['kind'], term['key']), term)
    needed = {(kind, q) for c in changes for kind, col in [('language', 'languages'), ('country', 'countries')] for q in c['projection'][col]}
    plan = {'version': selection['version'], 'selectionSha256': w.digest(selection), 'ids': ids, 'authorIds': authors, 'targets': targets, 'changes': changes, 'creators': list(creators.values()), 'terms': [t for key, t in terms.items() if key in needed], 'sources': list({p['path']: p for p in proofs}.values())}
    w.save(OUT / 'plan.json', plan)
    w.save(OUT / 'new-books.json', [c['fullRecord'] for c in changes])
    print(json.dumps({'books': len(changes), 'creators': len(creators), 'sha256': w.digest(plan), 'before': {t: x['totals'] for t, x in targets.items()}}, indent=2))


def apply(target, pin, cloud_backup_id):
    plan = json.loads((OUT / 'plan.json').read_text())
    assert pin == w.digest(plan)
    assert plan['selectionSha256'] == w.digest(json.loads((OUT / 'selection.json').read_text()))
    for proof in plan['sources']:
        assert hashlib.sha256((ROOT / proof['path']).read_bytes()).hexdigest() == proof['sha256']
    subprocess.run(['pg_restore', '--list', str(BACKUP / 'local-before.dump')], check=True, stdout=subprocess.DEVNULL)
    backup = json.loads(subprocess.check_output(['gcloud', 'sql', 'backups', 'describe', cloud_backup_id, '--instance=artline-postgres', '--project=artline-508319', '--format=json']))
    assert backup['status'] == 'SUCCESSFUL' and backup['description'] == plan['version']
    w.save(BACKUP / 'cloud-backup.json', backup)
    ids, authors = plan['ids'], plan['authorIds']
    before_state = plan['targets'][target]['before']
    existing_creators = {c['id'] for c in before_state['creators']}
    new_creators = [c['id'] for c in plan['creators'] if c['id'] not in existing_creators]
    with connect(target, False) as db, db.transaction():
        db.execute("SET LOCAL lock_timeout='10s'")
        db.execute('SELECT pg_advisory_xact_lock(202610040502)')
        db.execute('LOCK TABLE ' + ','.join(TABLES) + ' IN SHARE ROW EXCLUSIVE MODE')
        assert state(db, ids, authors) == before_state, 'Target changed since preparation: ' + target
        assert not db.execute('SELECT id FROM book_records WHERE source_id=ANY(%s)', ([c['record']['sourceId'] for c in plan['changes']],)).fetchall()
        before, untouched = totals(db), fingerprint(db, ids, new_creators)
        preimage = BACKUP / (target + '-preimages.json')
        assert not preimage.exists(), 'Preserve previous recovery data.'
        w.save(preimage, {'planSha256': pin, 'before': before_state, 'totals': before, 'unselected': untouched})
        for c in plan['creators']:
            if c['id'] not in existing_creators:
                db.execute('INSERT INTO book_creators(id,name,record,source_checksum) VALUES(%s,%s,%s,%s)', (c['id'], c['name'], Jsonb(c['record']), c['source_checksum']))
        for t in plan['terms']:
            db.execute('INSERT INTO book_discovery_terms(kind,key,name,evidence) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING', (t['kind'], t['key'], t['name'], Jsonb(t['evidence'])))
        for c in plan['changes']:
            r = c['record']
            assert r['status'] == 'review' and -5000 <= r['startYear'] <= r['endYear'] <= 1850
            db.execute("INSERT INTO book_records(id,source_id,status,record,source_checksum) VALUES(%s,%s,'review',%s,%s)", (c['id'], r['sourceId'], Jsonb(r), c['sourceChecksum']))
            for link in c['links']:
                db.execute('INSERT INTO book_creator_links(book_id,creator_id,position,credit) VALUES(%s,%s,%s,%s)', tuple(link[k] for k in ['book_id','creator_id','position','credit']))
            projection = c['projection']; cols = list(projection)
            db.execute('INSERT INTO book_discovery (' + ','.join(cols) + ') VALUES (' + ','.join(['%s']*len(cols)) + ')', tuple(Jsonb(projection[k]) if k == 'evidence' else projection[k] for k in cols))
        assert fingerprint(db, ids, new_creators) == untouched
        after = totals(db)
        assert after['books'] == before['books'] + len(ids) and after['in_range'] == before['in_range'] + len(ids)
        assert after['published'] == before['published'] and after['highlights'] == before['highlights']
        for c in plan['changes']:
            actual = db.execute('SELECT record,source_checksum,status FROM book_records WHERE id=%s', (c['id'],)).fetchone()
            assert actual == {'record': c['record'], 'source_checksum': c['sourceChecksum'], 'status': 'review'}
        assert db.execute('SELECT count(*) n FROM book_records b JOIN book_discovery d ON d.book_id=b.id AND d.book_checksum=b.source_checksum WHERE b.id=ANY(%s)', (ids,)).fetchone()['n'] == len(ids)
    receipt = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'target': target, 'planSha256': pin, 'cloudBackupId': cloud_backup_id, 'before': before, 'after': after, 'newBooks': len(ids), 'newCreators': len(new_creators), 'unselectedUnchanged': True, 'publicationUnchanged': True}
    w.save(OUT / (target + '-apply-receipt.json'), receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'apply'])
    parser.add_argument('--target', choices=['local', 'cloud'])
    parser.add_argument('--sha256')
    parser.add_argument('--cloud-backup-id')
    args = parser.parse_args()
    if args.stage == 'prepare':
        prepare()
    else:
        assert args.target and args.sha256 and args.cloud_backup_id
        apply(args.target, args.sha256, args.cloud_backup_id)
