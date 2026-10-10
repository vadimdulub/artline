#!/usr/bin/env python3
"""Add only the reviewed war-book selection to the local catalogue, unpublished."""
import argparse
import datetime
import importlib.util
import json
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('book_helpers', ROOT / 'ops/expand-pre1850-books-20261001.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
OUT = ROOT / 'docs/research/war-books-africa-20261004'
SELECTION = ROOT / 'ops/curated-war-books-20261004.json'
BACKUP = Path('/Users/vadimdulub/Library/Application Support/Artline/backups/war-books-africa-20261004')
w.OUT = OUT
w.research.OUT = OUT
DSN = 'postgres://127.0.0.1/artline?sslmode=disable'


def totals(db):
    return dict(db.execute("""SELECT count(*) books,
        count(*) FILTER (WHERE status='published') published,
        (SELECT count(*) FROM book_discovery WHERE top100) highlights
        FROM book_records""").fetchone())


def prepare():
    assert not (OUT / 'apply-receipt.json').exists(), 'Preserve the applied plan.'
    selection = json.loads(SELECTION.read_text())
    candidates = {x['qid']: x for x in json.loads((OUT / 'candidates.json').read_text())}
    qids = [x['qid'] for x in selection['items']]
    assert len(qids) == len(set(qids))
    # Source full work articles as well as intros; dates, settings and original
    # composition languages must refer to the work, not an English reissue.
    full_articles = {}
    proofs = []
    for language in ['en', 'fr', 'de']:
        titles = [candidates[q]['title'] for q in qids if candidates[q].get('language', 'en') == language]
        for offset in range(0, len(titles), 10):
            data, proof = w.research.capture(language + '.wikipedia.org', {
                'action': 'query', 'titles': '|'.join(titles[offset:offset + 10]),
                'prop': 'pageprops|revisions', 'ppprop': 'wikibase_item',
                'rvprop': 'ids|timestamp|content', 'rvslots': 'main',
            })
            proofs.append(proof)
            for page in data['query']['pages']:
                page['extract'] = page['revisions'][0]['slots']['main']['content']
                full_articles[page['pageprops']['wikibase_item']] = {'page': page, 'source': proof}
    w.save(OUT / 'full-articles.json', full_articles)
    authors, term_ids = set(), set()
    for choice in selection['items']:
        c = candidates[choice['qid']]
        e = c['wikidata']['entity']
        assert not c['existing'], 'Additions only; no edits to existing books.'
        assert not set(w.r.ids(e, 'P31')) & {'Q5', 'Q4167410', 'Q4167836', 'Q11424', 'Q223393'}
        assert not w.r.ids(e, 'P629'), 'Edition identity needs reconciliation.'
        ids = choice.get('creatorIds', w.r.ids(e, 'P50'))
        assert ids, 'Missing credited creator: ' + choice['qid']
        authors.update(ids)
        term_ids.update(choice.get('languages', w.r.ids(e, 'P407')))
        term_ids.update(w.r.ids(e, 'P495'))
    metadata = w.fetch_entities(authors | term_ids)
    w.save(OUT / 'metadata.json', metadata)
    with psycopg.connect(DSN, options='-c default_transaction_read_only=on', row_factory=dict_row) as db:
        assert not db.execute('SELECT id FROM book_records WHERE source_id=ANY(%s)', (qids,)).fetchall()
        existing_creators = {x['id']: w.normalized(x) for x in db.execute('SELECT * FROM book_creators WHERE id=ANY(%s)', (list(authors),))}
        existing_terms = {(x['kind'], x['key']) for x in db.execute('SELECT kind,key FROM book_discovery_terms')}
        before = totals(db)
    creators = dict(existing_creators)
    for qid in sorted(authors - creators.keys()):
        e = metadata[qid]['entity']
        name = w.r.creator_name(e)
        assert name != 'Unnamed creator' and 'Q5' in w.r.ids(e, 'P31')
        rec = {'id': qid, 'name': name, 'description': w.r.description(e),
               'birth': w.r.life_label(e, 'P569'), 'death': w.r.life_label(e, 'P570'),
               'sourceUrl': 'https://www.wikidata.org/wiki/' + qid,
               'sourceRevision': e.get('lastrevid'), 'kind': 'person', 'credit': ''}
        creators[qid] = {'id': qid, 'name': name, 'record': rec, 'source_checksum': w.digest(rec)}
    un = json.loads((ROOT / 'docs/research/historical-books-20260916/un-m49.json').read_text())
    un_by_iso = {row['ISO-alpha2 Code']: row for row in un['rows']}
    changes, terms = [], {}
    for choice in selection['items']:
        qid = choice['qid']
        c = candidates[qid]
        e = c['wikidata']['entity']
        year = choice['year']
        assert isinstance(year, int) and 1900 <= year <= 2000
        article = full_articles[qid]['page']
        assert str(year) in article['extract'], 'Publication year requires source review: ' + qid
        author_ids = choice.get('creatorIds', w.r.ids(e, 'P50'))
        # Overrides are explicit reconciliations, never inferred from the title.
        for a in author_ids:
            if a not in w.r.ids(e, 'P50'):
                assert choice.get('creatorReview') and creators[a]['name'] in c['extract']
        id = 'wd-' + qid.lower()
        links = [{'book_id': id, 'creator_id': a, 'position': i, 'credit': 'Author'} for i, a in enumerate(author_ids)]
        source_url = 'https://' + c.get('language', 'en') + '.wikipedia.org/w/index.php?oldid=' + str(article['revisions'][0]['revid'])
        award = choice.get('award', '')
        basis = choice['basis'] + (' ' + award if award else '')
        record = {'id': id, 'sourceId': qid, 'title': choice['title'],
                  'author': ' · '.join(creators[a]['name'] for a in author_ids),
                  'creators': [], 'years': str(year), 'startYear': year, 'endYear': year,
                  'approximate': False, 'era': 'Modern', 'theme': choice['theme'],
                  'description': choice['description'], 'selectionBasis': basis,
                  'dateBasis': choice.get('dateBasis', 'First publication of the original work; later translations and adaptations are separate.'),
                  'dateSources': [{'name': 'Reviewed work article — ' + c['title'], 'url': source_url}],
                  'sourceUrl': 'https://www.wikidata.org/wiki/' + qid,
                  'sourceRevision': e.get('lastrevid'), 'status': 'review',
                  'coverTone': '#c3bfcc', 'coverInk': '#29251f', 'coverMark': choice['title'][0]}
        # Use a short attributed English introduction where available; original
        # English descriptions above also cover the French/German-only sources.
        if c.get('language', 'en') == 'en' and not choice.get('omitOverview'):
            paragraphs = w.excerpt(c['extract'], 'book')
            if paragraphs:
                record['overview'] = {'paragraphs': paragraphs,
                    'sourceUrl': 'https://en.wikipedia.org/w/index.php?oldid=' + str(c['revision']),
                    'sourceTitle': c['title'], 'revision': c['revision'],
                    'credit': 'Wikipedia contributors', 'licenseUrl': w.LICENSE}
        for source in choice.get('sources', []):
            record['dateSources'].append(source)
        full = dict(record, creators=[dict(creators[a]['record'], credit='Author') for a in author_ids])
        checksum = w.digest(full)
        languages = choice.get('languages', w.r.ids(e, 'P407'))
        countries = w.r.ids(e, 'P495')
        regions = set()
        for kind, values in [('language', languages), ('country', countries)]:
            for key in values:
                entry = metadata[key]
                if (kind, key) not in existing_terms:
                    terms[kind, key] = {'kind': kind, 'key': key, 'name': w.r.name(entry['entity']) or key, 'evidence': {'source': entry['source']}}
                if kind == 'country':
                    for iso in w.r.values(entry['entity'], 'P297'):
                        row = un_by_iso.get(iso)
                        if row:
                            name = row['Intermediate Region Name'] or row['Sub-region Name']
                            if name:
                                region = name.lower().replace(' ', '-')
                                regions.add(region)
                                if ('region', region) not in existing_terms:
                                    terms['region', region] = {'kind': 'region', 'key': region, 'name': name, 'evidence': {'sourceUrl': un['url'], 'sha256': un['sha256']}}
        projection = {'book_id': id, 'book_checksum': checksum, 'top100': False,
            'woman_author_ids': sorted(a for a in author_ids if set(w.r.ids(metadata[a]['entity'], 'P21')) & {'Q6581072', 'Q1052281'}),
            'languages': sorted(languages), 'countries': sorted(countries), 'regions': sorted(regions),
            'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'evidence': {'work': c['wikidata']['source'], 'context': full_articles[qid]['source'],
                'selection': choice, 'creators': {a: metadata[a]['source'] for a in author_ids},
                'regionBasis': 'Direct work-country statements mapped to UN M49; no citizenship or setting inference.',
                'highlightBasis': 'Existing Top 100 membership unchanged.'}}
        projection['projection_checksum'] = w.digest(projection)
        changes.append({'id': id, 'record': record, 'fullRecord': full, 'sourceChecksum': checksum, 'links': links, 'projection': projection})
        proofs.extend([c['source'], c['wikidata']['source']])
    proofs += [x['source'] for x in metadata.values()]
    plan = {'version': selection['version'], 'selectionSha256': w.digest(selection),
            'beforeTotals': before, 'changes': changes,
            'existingCreators': list(existing_creators.values()),
            'newCreators': [x for q, x in creators.items() if q not in existing_creators],
            'newTerms': list(terms.values()), 'sources': list({p['path']: p for p in proofs}.values())}
    w.save(OUT / 'plan.json', plan)
    w.save(OUT / 'new-books.json', [x['fullRecord'] for x in changes])
    print(json.dumps({'newBooks': len(changes), 'newCreators': len(plan['newCreators']), 'sha256': w.digest(plan), 'before': before}, indent=2))


def apply(expected):
    plan = json.loads((OUT / 'plan.json').read_text())
    assert expected == w.digest(plan), 'Apply only the reviewed plan hash.'
    assert plan['selectionSha256'] == w.digest(json.loads(SELECTION.read_text()))
    for proof in plan['sources']:
        assert w.hashlib.sha256((ROOT / proof['path']).read_bytes()).hexdigest() == proof['sha256']
    ids = [x['id'] for x in plan['changes']]
    with psycopg.connect(DSN, row_factory=dict_row) as db, db.transaction():
        db.execute('SELECT pg_advisory_xact_lock(202610040001)')
        db.execute('LOCK TABLE book_records,book_creators,book_creator_links,book_discovery,book_discovery_terms IN SHARE ROW EXCLUSIVE MODE')
        actual = {x['id']: x for x in db.execute('SELECT * FROM book_records WHERE id=ANY(%s)', (ids,))}
        if actual:
            assert len(actual) == len(ids)
            for change in plan['changes']:
                assert actual[change['id']]['record'] == change['record'] and actual[change['id']]['source_checksum'] == change['sourceChecksum']
                projection = db.execute('SELECT projection_checksum FROM book_discovery WHERE book_id=%s', (change['id'],)).fetchone()
                assert projection and projection['projection_checksum'] == change['projection']['projection_checksum']
            print('Identical review records already present; no writes.')
            return
        assert not db.execute('SELECT id FROM book_records WHERE source_id=ANY(%s)', ([c['record']['sourceId'] for c in plan['changes']],)).fetchall()
        for creator in plan['existingCreators']:
            assert w.normalized(db.execute('SELECT * FROM book_creators WHERE id=%s', (creator['id'],)).fetchone()) == creator
        untouched = w.unchanged_fingerprint(db, ids)
        before = totals(db)
        BACKUP.mkdir(parents=True, exist_ok=True)
        backup = BACKUP / 'preimages.json'
        assert not backup.exists(), 'Preserve earlier recovery evidence.'
        w.save(backup, {'at': datetime.datetime.now(datetime.timezone.utc), 'planSha256': expected,
                       'newBookIds': ids, 'newCreatorIds': [x['id'] for x in plan['newCreators']],
                       'existingCreators': plan['existingCreators'], 'beforeTotals': before,
                       'untouchedFingerprint': untouched, 'newTerms': plan['newTerms']})
        for creator in plan['newCreators']:
            db.execute('INSERT INTO book_creators(id,name,record,source_checksum) VALUES(%s,%s,%s,%s)',
                       (creator['id'], creator['name'], Jsonb(creator['record']), creator['source_checksum']))
        for term in plan['newTerms']:
            db.execute('INSERT INTO book_discovery_terms(kind,key,name,evidence) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING',
                       (term['kind'], term['key'], term['name'], Jsonb(term['evidence'])))
        for change in plan['changes']:
            record = change['record']
            assert record['status'] == 'review' and 1900 <= record['startYear'] == record['endYear'] <= 2000
            db.execute("INSERT INTO book_records(id,source_id,status,record,source_checksum) VALUES(%s,%s,'review',%s,%s)",
                       (change['id'], record['sourceId'], Jsonb(record), change['sourceChecksum']))
            for link in change['links']:
                db.execute('INSERT INTO book_creator_links(book_id,creator_id,position,credit) VALUES(%s,%s,%s,%s)',
                           (link['book_id'], link['creator_id'], link['position'], link['credit']))
            projection = change['projection']
            columns = list(projection)
            db.execute('INSERT INTO book_discovery (' + ','.join(columns) + ') VALUES (' + ','.join(['%s'] * len(columns)) + ')',
                       tuple(Jsonb(projection[k]) if k == 'evidence' else projection[k] for k in columns))
        assert w.unchanged_fingerprint(db, ids) == untouched
        after = totals(db)
        assert after == dict(before, books=before['books'] + len(ids))
        assert db.execute("SELECT count(*) n FROM book_records b JOIN book_discovery d ON d.book_id=b.id AND d.book_checksum=b.source_checksum WHERE b.id=ANY(%s) AND b.status='review' AND NOT d.top100", (ids,)).fetchone()['n'] == len(ids)
    receipt = {'at': datetime.datetime.now(datetime.timezone.utc), 'planSha256': expected,
               'before': before, 'after': after, 'newBooks': len(ids), 'backup': str(backup),
               'status': 'Local review records only; existing records and highlights unchanged.'}
    w.save(OUT / 'apply-receipt.json', receipt)
    print(json.dumps(w.normalized(receipt), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'apply'])
    parser.add_argument('--sha256')
    args = parser.parse_args()
    if args.stage == 'prepare':
        prepare()
    else:
        assert args.sha256, 'An exact reviewed plan hash is required.'
        apply(args.sha256)
