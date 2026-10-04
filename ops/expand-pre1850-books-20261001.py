#!/usr/bin/env python3
"""Prepare/apply a bounded, sourced local early-book selection; never publish."""
import argparse
import copy
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import urllib.request

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from book_context import excerpt, LICENSE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/research/pre1850-books-20261001'
SELECTION = ROOT / 'ops/curated-pre1850-books-20261001.json'
BACKUP = Path('/Users/vadimdulub/Library/Application Support/Artline/backups/pre1850-books-20261001')
DSN = 'postgres://127.0.0.1/artline?sslmode=disable'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


r = module('historical_books', ROOT / 'ops/research-historical-books.py')
research = module('early_research', ROOT / 'ops/research-early-books-20260923.py')
research.OUT = OUT


def normalized(value):
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + '\n')


def fetch_entities(wanted):
    result = {}
    wanted = sorted(set(wanted))
    for offset in range(0, len(wanted), 40):
        data, proof = research.capture('www.wikidata.org', {'action': 'wbgetentities', 'ids': '|'.join(wanted[offset:offset + 40]), 'props': 'info|labels|descriptions|claims', 'languages': 'en'})
        result.update({qid: {'entity': entity, 'source': proof} for qid, entity in data['entities'].items()})
    return result


def extra_source(url):
    reviews = OUT / 'additional-source-reviews.json'
    reviewed = next((item for item in json.loads(reviews.read_text())['items'] if item['url'] == url), None)
    if reviewed:
        return {'url': url, 'path': str(reviews.relative_to(ROOT)), 'sha256': hashlib.sha256(reviews.read_bytes()).hexdigest(), 'access': reviewed['access']}
    path = OUT / 'sources' / (hashlib.sha256(url.encode()).hexdigest() + '.source.gz')
    receipt = path.with_suffix('.receipt.json')
    if not path.exists():
        req = urllib.request.Request(url, headers={'User-Agent': research.AGENT if hasattr(research, 'AGENT') else 'ArtlineBookResearch/1.0'})
        with urllib.request.urlopen(req, timeout=45) as response:
            raw = response.read(8 * 1024 * 1024 + 1)
            assert len(raw) <= 8 * 1024 * 1024
            final = response.url
        path.write_bytes(gzip.compress(raw, mtime=0))
        save(receipt, {'url': url, 'finalUrl': final, 'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return json.loads(receipt.read_text())


def totals(db):
    return dict(db.execute('''SELECT count(*) books,
        count(*) FILTER (WHERE b.status='published') published,
        count(*) FILTER (WHERE b.start_year>=1 AND b.end_year<1850) early,
        count(*) FILTER (WHERE d.top100) highlights,
        count(*) FILTER (WHERE d.top100 AND b.start_year>=1 AND b.end_year<1850) early_highlights
        FROM book_records b LEFT JOIN book_discovery d ON d.book_id=b.id AND d.book_checksum=b.source_checksum''').fetchone())


def date_fields(choice, candidate):
    a, b, approximate, label, basis = choice['date']
    assert (a is None and b is None) or (isinstance(a, int) and isinstance(b, int) and 1 <= a <= b < 1850)
    assert isinstance(approximate, bool) and label and basis
    sources = [{'name': 'Wikipedia — ' + candidate['title'], 'url': 'https://en.wikipedia.org/w/index.php?oldid=' + str(candidate['revision'])}]
    sources += choice.get('additionalSources', [])
    sources += [{'name': 'Wikidata work record', 'url': 'https://www.wikidata.org/wiki/' + choice['qid']}]
    return {'startYear': a, 'endYear': b, 'approximate': approximate, 'years': label, 'dateBasis': basis, 'dateSources': sources}


def prepare():
    selection = json.loads(SELECTION.read_text())
    receipt_path = OUT / 'apply-receipt.json'
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        plan = json.loads((OUT / 'plan.json').read_text())
        assert digest(plan) == receipt['planSha256'], 'Applied plan changed; preserve the original evidence.'
        assert digest(selection) == plan['selectionSha256'], 'Use a new campaign for a changed selection.'
        print('Selection already applied; preserving the original plan and source evidence.')
        return
    assert len({item['qid'] for item in selection['items']}) == len(selection['items'])
    candidates = {item['qid']: item for item in json.loads((OUT / 'candidates.json').read_text())}
    qids = [item['qid'] for item in selection['items']]
    choices = {item['qid']: item for item in selection['items']}
    def author_ids_for(qid):
        return choices[qid].get('creatorIds', r.ids(candidates[qid]['wikidata']['entity'], 'P50'))
    reviewed_creators = [item for item in selection['items'] if item.get('creatorArticle')]
    creator_proofs = []
    if reviewed_creators:
        data, proof = research.capture('en.wikipedia.org', {'action': 'query', 'titles': '|'.join(item['creatorArticle'] for item in reviewed_creators), 'redirects': 1, 'prop': 'pageprops|extracts|revisions', 'ppprop': 'wikibase_item', 'exintro': 1, 'explaintext': 1, 'exlimit': 2, 'rvprop': 'ids|timestamp'})
        pages = {page['title']: page for page in data['query']['pages']}
        for item in reviewed_creators:
            assert [pages[item['creatorArticle']]['pageprops']['wikibase_item']] == item['creatorIds']
            assert item['creatorArticle'].split(' of ')[0] in candidates[item['qid']]['extract']
        creator_proofs.append(proof)
    for qid in qids:
        candidate = candidates[qid]
        entity = candidate['wikidata']['entity']
        assert candidate['revision'] and candidate['extract'] and entity['id'] == qid
        assert not set(r.ids(entity, 'P31')) & {'Q5', 'Q4167410', 'Q4167836', 'Q223393'}, 'Person, disambiguation, category or genre is not a work: ' + qid
        assert not r.values(entity, 'P629'), 'Edition/translation identity requires review: ' + qid
    with psycopg.connect(DSN, options='-c default_transaction_read_only=on', row_factory=dict_row) as db:
        existing = {row['source_id']: normalized(row) for row in db.execute('SELECT * FROM book_records WHERE source_id=ANY(%s)', (qids,))}
        selected_ids = [row['id'] for row in existing.values()]
        discovery = {row['book_id']: normalized(row) for row in db.execute('SELECT * FROM book_discovery WHERE book_id=ANY(%s)', (selected_ids,))}
        old_links = {id: normalized(db.execute('SELECT * FROM book_creator_links WHERE book_id=%s ORDER BY position', (id,)).fetchall()) for id in selected_ids}
        author_ids = {author for qid in qids if qid not in existing for author in author_ids_for(qid)}
        author_ids |= {link['creator_id'] for links in old_links.values() for link in links}
        existing_creators = {row['id']: normalized(row) for row in db.execute('SELECT * FROM book_creators WHERE id=ANY(%s)', (list(author_ids),))}
        existing_terms = {(row['kind'], row['key']): normalized(row) for row in db.execute('SELECT * FROM book_discovery_terms')}
        before_totals = totals(db)
    new_candidates = [candidates[qid] for qid in qids if qid not in existing]
    new_author_ids = {author for candidate in new_candidates for author in author_ids_for(candidate['qid'])}
    term_ids = {term for candidate in new_candidates for prop in ['P407', 'P495'] for term in r.ids(candidate['wikidata']['entity'], prop)}
    term_ids |= {qid for choice in selection['items'] for key in ['languages', 'countries'] for qid in choice.get(key, [])}
    metadata = fetch_entities(new_author_ids | term_ids)
    save(OUT / 'metadata.json', metadata)
    creators = dict(existing_creators)
    for qid in new_author_ids - existing_creators.keys():
        entity = metadata[qid]['entity']
        assert 'missing' not in entity and r.creator_name(entity) != 'Unnamed creator'
        record = {'id': qid, 'name': r.creator_name(entity), 'description': r.description(entity), 'birth': r.life_label(entity, 'P569'), 'death': r.life_label(entity, 'P570'), 'sourceUrl': 'https://www.wikidata.org/wiki/' + qid, 'sourceRevision': entity.get('lastrevid'), 'kind': 'person' if 'Q5' in r.ids(entity, 'P31') else 'collective', 'credit': ''}
        for choice in reviewed_creators:
            if qid in choice['creatorIds']:
                record.update(choice.get('creatorFields', {}))
        creators[qid] = {'id': qid, 'name': record['name'], 'record': record, 'source_checksum': digest(record)}
    terms = {}
    un = json.loads((ROOT / 'docs/research/historical-books-20260916/un-m49.json').read_text())
    un_by_iso = {row['ISO-alpha2 Code']: row for row in un['rows']}
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    changes, proofs = [], creator_proofs.copy()
    for choice in selection['items']:
        qid = choice['qid']
        candidate = candidates[qid]
        entity = candidate['wikidata']['entity']
        original = existing.get(qid)
        id = original['id'] if original else 'wd-' + qid.lower()
        proofs += [candidate['source'], candidate['wikidata']['source']]
        for source in choice.get('additionalSources', []):
            proofs.append(extra_source(source['url']))
        if original:
            assert original['status'] == 'review'
            links = old_links[id]
            record = copy.deepcopy(original['record'])
        else:
            links = [{'book_id': id, 'creator_id': q, 'position': i, 'credit': choice.get('creatorCredit', 'Author')} for i, q in enumerate(author_ids_for(qid))]
            record = {'id': id, 'sourceId': qid, 'title': choice.get('title', r.name(entity)), 'author': choice.get('authorLabel') or ' · '.join(creators[link['creator_id']]['name'] for link in links) or 'Creator not recorded', 'creators': [], 'era': 'Medieval', 'theme': choice['theme'], 'description': r.description(entity) or 'A description has not yet been established for this work.', 'coverTone': ['#e8ddc1', '#b6c3b4', '#d3b4a3', '#c3bfcc', '#c4cad0'][int(qid[1:]) % 5], 'coverInk': '#29251f', 'coverMark': (choice.get('title') or r.name(entity))[:1], 'sourceUrl': 'https://www.wikidata.org/wiki/' + qid, 'sourceRevision': entity.get('lastrevid'), 'selectionBasis': choice['basis'], 'status': 'review'}
            paragraphs = excerpt(candidate['extract'], 'book')
            assert paragraphs and record['title']
            record['overview'] = {'paragraphs': paragraphs, 'sourceUrl': 'https://en.wikipedia.org/w/index.php?oldid=' + str(candidate['revision']), 'sourceTitle': candidate['title'], 'revision': candidate['revision'], 'credit': 'Wikipedia contributors', 'licenseUrl': LICENSE}
        if 'date' in choice:
            record.update(date_fields(choice, candidate))
            if record['endYear'] is not None and (not original or record['era'] == 'Undated'):
                record['era'] = 'Ancient' if record['endYear'] < 500 else 'Medieval' if record['endYear'] < 1500 else 'Early modern' if record['endYear'] < 1800 else 'Modern'
        assert (record['startYear'] is None and record['endYear'] is None) or 1 <= record['startYear'] <= record['endYear'] < 1850, 'Outside selected era: ' + id
        if 'description' in choice: record['description'] = choice['description']
        full = dict(record, creators=[dict(creators[link['creator_id']]['record'], credit=link['credit']) for link in links])
        changed = not original or record != original['record']
        checksum = digest(full) if changed else original['source_checksum']
        before_projection = discovery.get(id)
        if original:
            assert before_projection and before_projection['book_checksum'] == original['source_checksum']
            projection = copy.deepcopy(before_projection)
        else:
            languages = choice.get('languages', r.ids(entity, 'P407'))
            countries = choice.get('countries', r.ids(entity, 'P495'))
            regions = set()
            for kind, values in [('language', languages), ('country', countries)]:
                for key in values:
                    entry = metadata[key]
                    if (kind, key) not in existing_terms:
                        terms[(kind, key)] = {'kind': kind, 'key': key, 'name': r.name(entry['entity']) or key, 'evidence': {'sourceUrl': 'https://www.wikidata.org/wiki/' + key, 'source': entry['source']}}
                    if kind == 'country':
                        for iso in r.values(entry['entity'], 'P297'):
                            if iso not in un_by_iso:
                                continue
                            row = un_by_iso[iso]
                            name = row['Intermediate Region Name'] or row['Sub-region Name']
                            if name:
                                region = name.lower().replace(' ', '-')
                                regions.add(region)
                                if ('region', region) not in existing_terms:
                                    terms[('region', region)] = {'kind': 'region', 'key': region, 'name': name, 'evidence': {'sourceUrl': un['url'], 'sha256': un['sha256']}}
            women = [author for author in author_ids_for(qid) if set(r.ids(metadata[author]['entity'], 'P21')) & {'Q6581072', 'Q1052281'}]
            projection = {'book_id': id, 'woman_author_ids': sorted(women), 'languages': sorted(languages), 'countries': sorted(countries), 'regions': sorted(regions), 'evidence': {'work': {'sourceId': qid, 'source': candidate['wikidata']['source'], 'languageProperty': 'P407', 'countryProperty': 'P495'}, 'creators': [{'creatorId': q, 'source': metadata[q]['source'], 'genderValues': r.ids(metadata[q]['entity'], 'P21')} for q in author_ids_for(qid)], 'contextSource': candidate['source'], 'regionBasis': 'Only direct recorded country ISO codes mapped to UN M49; no origin inferred from author or language.'}}
            if choice.get('creatorArticle'):
                projection['evidence']['creatorReview'] = {'article': choice['creatorArticle'], 'source': creator_proofs[0], 'basis': 'Named author in the matched work introduction, reconciled to the matching creator article source identity.'}
        projection['evidence']['identityReview'] = {'basis': choice.get('identityReview', ''), 'source': candidate['source'], 'languages': choice.get('languages'), 'countries': choice.get('countries')}
        projection.update(book_checksum=checksum, top100=True, checked_at=now)
        projection['evidence']['editorial'] = {'version': selection['version'], 'basis': choice['basis'], 'sourceUrl': record['sourceUrl']}
        if 'date' in choice:
            projection['evidence']['dateReview'] = {'version': selection['version'], 'basis': record['dateBasis'], 'sources': record['dateSources'], 'capture': candidate['source']}
        projection['projection_checksum'] = digest({k: v for k, v in projection.items() if k != 'projection_checksum'})
        changes.append({'id': id, 'new': original is None, 'recordChanged': changed, 'before': original, 'beforeProjection': before_projection, 'record': record, 'fullRecord': full, 'sourceChecksum': checksum, 'links': links, 'projection': projection})
    proofs += [item['source'] for item in metadata.values()]
    plan = {'version': selection['version'], 'selectionSha256': digest(selection), 'beforeTotals': before_totals, 'changes': changes, 'newCreators': [row for qid, row in creators.items() if qid not in existing_creators], 'existingCreators': list(existing_creators.values()), 'newTerms': list(terms.values()), 'sources': list({proof['path']: proof for proof in proofs}.values())}
    save(OUT / 'plan.json', plan)
    save(OUT / 'new-books.json', [change['fullRecord'] for change in changes if change['new']])
    summary = {'selected': len(changes), 'newBooks': sum(change['new'] for change in changes), 'existingDateReviews': sum(not change['new'] and change['recordChanged'] for change in changes), 'highlightsAdded': sum(not (change['beforeProjection'] or {}).get('top100', False) for change in changes), 'newCreators': len(plan['newCreators']), 'newTerms': len(plan['newTerms']), 'before': before_totals}
    save(OUT / 'prepared-summary.json', summary)
    print(json.dumps(summary, indent=2))
    for change in changes:
        if change['new']:
            print(change['id'], change['record']['title'], change['record']['years'], 'languages:', [(q, r.name(metadata[q]['entity'])) for q in change['projection']['languages']])


def check_sources(plan):
    assert plan['selectionSha256'] == digest(json.loads(SELECTION.read_text()))
    for proof in plan['sources']:
        assert hashlib.sha256((ROOT / proof['path']).read_bytes()).hexdigest() == proof['sha256'], 'Source capture changed: ' + proof['path']


def unchanged_fingerprint(db, selected_ids):
    return db.execute('''SELECT md5(string_agg(row_to_json(b)::text,'|' ORDER BY id)) records,
        (SELECT md5(string_agg(row_to_json(d)::text,'|' ORDER BY book_id)) FROM book_discovery d WHERE NOT(book_id=ANY(%s))) discovery
        FROM book_records b WHERE NOT(id=ANY(%s))''', (selected_ids, selected_ids)).fetchone()


def apply():
    plan = json.loads((OUT / 'plan.json').read_text())
    check_sources(plan)
    ids = [change['id'] for change in plan['changes']]
    with psycopg.connect(DSN, row_factory=dict_row) as db, db.transaction():
        db.execute('SELECT pg_advisory_xact_lock(202610010003)')
        db.execute('LOCK TABLE book_records,book_creators,book_creator_links,book_discovery,book_discovery_terms IN SHARE ROW EXCLUSIVE MODE')
        actual = {row['id']: normalized(row) for row in db.execute('SELECT * FROM book_records WHERE id=ANY(%s)', (ids,))}
        projections = {row['book_id']: normalized(row) for row in db.execute('SELECT * FROM book_discovery WHERE book_id=ANY(%s)', (ids,))}
        if all(actual.get(change['id'], {}).get('source_checksum') == change['sourceChecksum'] and projections.get(change['id'], {}).get('projection_checksum') == change['projection']['projection_checksum'] for change in plan['changes']):
            print('Identical early-book selection already applied; no changes.')
            return
        for change in plan['changes']:
            assert actual.get(change['id']) == change['before'], 'Book changed since preparation: ' + change['id']
            assert projections.get(change['id']) == change['beforeProjection'], 'Projection changed: ' + change['id']
        for creator in plan['existingCreators']:
            assert normalized(db.execute('SELECT * FROM book_creators WHERE id=%s', (creator['id'],)).fetchone()) == creator, 'Existing creator changed'
        before = totals(db)
        untouched = unchanged_fingerprint(db, ids)
        BACKUP.mkdir(parents=True, exist_ok=True)
        backup = BACKUP / 'preimages.json'
        assert not backup.exists(), 'Preserve and reconcile the prior backup before another apply.'
        save(backup, {'at': datetime.datetime.now(datetime.timezone.utc), 'planSha256': digest(plan), 'records': actual, 'discovery': projections, 'existingCreators': plan['existingCreators'], 'newIds': [change['id'] for change in plan['changes'] if change['new']]})
        for creator in plan['newCreators']:
            db.execute('INSERT INTO book_creators(id,name,record,source_checksum) VALUES(%s,%s,%s,%s)', (creator['id'], creator['name'], Jsonb(creator['record']), creator['source_checksum']))
        for term in plan['newTerms']:
            db.execute('INSERT INTO book_discovery_terms(kind,key,name,evidence) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING', (term['kind'], term['key'], term['name'], Jsonb(term['evidence'])))
        for change in plan['changes']:
            record = change['record']
            assert record['status'] == 'review' and ((record['startYear'] is None and record['endYear'] is None) or 1 <= record['startYear'] <= record['endYear'] < 1850)
            if change['new']:
                db.execute('INSERT INTO book_records(id,source_id,status,record,source_checksum) VALUES(%s,%s,\'review\',%s,%s)', (change['id'], record['sourceId'], Jsonb(record), change['sourceChecksum']))
                for link in change['links']:
                    db.execute('INSERT INTO book_creator_links(book_id,creator_id,position,credit) VALUES(%s,%s,%s,%s)', (link['book_id'], link['creator_id'], link['position'], link['credit']))
            elif change['recordChanged']:
                db.execute('UPDATE book_records SET record=%s,source_checksum=%s WHERE id=%s', (Jsonb(record), change['sourceChecksum'], change['id']))
            projection = change['projection']
            columns = list(projection)
            db.execute('INSERT INTO book_discovery (' + ','.join(columns) + ') VALUES (' + ','.join(['%s'] * len(columns)) + ') ON CONFLICT(book_id) DO UPDATE SET ' + ','.join(k + '=excluded.' + k for k in columns if k != 'book_id'), tuple(Jsonb(projection[k]) if k == 'evidence' else projection[k] for k in columns))
        assert unchanged_fingerprint(db, ids) == untouched, 'Unselected records changed'
        after = totals(db)
        assert after['books'] == before['books'] + sum(change['new'] for change in plan['changes'])
        assert after['highlights'] == before['highlights'] + sum(not (change['beforeProjection'] or {}).get('top100', False) for change in plan['changes'])
        assert after['published'] == before['published']
        assert db.execute('SELECT count(*) n FROM book_records b JOIN book_discovery d ON d.book_id=b.id WHERE b.id=ANY(%s) AND b.source_checksum=d.book_checksum AND d.top100', (ids,)).fetchone()['n'] == len(ids)
    receipt = {'at': datetime.datetime.now(datetime.timezone.utc), 'planSha256': digest(plan), 'before': before, 'after': after, 'backup': str(backup), 'selectedRecords': len(ids), 'status': 'Local catalogue only. All added/selected records remain in review.'}
    save(OUT / 'apply-receipt.json', receipt)
    print(json.dumps(normalized(receipt), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'apply'])
    args = parser.parse_args()
    prepare() if args.stage == 'prepare' else apply()
