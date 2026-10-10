#!/usr/bin/env python3
"""Next source rounds for library records with no usable work-specific picture."""
import argparse
import collections
import importlib.util
import re
from pathlib import Path

spec = importlib.util.spec_from_file_location('pictures', Path(__file__).with_name('library-pictures-20261010.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def articles():
    inventory = p.load(p.RUN / 'inventory.json.gz')
    entities = p.load(p.RUN / 'entities.json.gz')
    freshpath = p.RUN / 'fresh-sitelinks.json.gz'
    fresh = p.load(freshpath) if freshpath.exists() else {}
    proposed = {r['id'] for r in p.load(p.RUN / 'proposals.json.gz') if r.get('property') != 'author-portrait'}
    native = p.load(p.RUN / 'production-inventory.json.gz')
    records = {r['id']: r['record'] for cat in ['books', 'events'] for r in native[cat]}
    prior = {(r['id'], r.get('articleTitle')) for r in p.load(p.RUN / 'article-audit.json.gz') if r.get('articleTitle')}
    groups = collections.defaultdict(list)
    for row in inventory:
        if row['existing'] or row['id'] in proposed or not row['qid'].startswith('Q'):
            continue
        e = entities.get(row['qid'], {}).get('entity', {})
        links = fresh.get(row['qid'], {}).get('sitelinks') or e.get('sitelinks') or {}
        overview = records[row['id']].get('overview') or {}
        titles = []
        for lang in ['en', 'fr', 'de', 'es', 'ru', 'el', 'it', 'ja', 'zh', 'pt']:
            title = (links.get(lang + 'wiki') or {}).get('title')
            if not title and lang == 'en':
                title = overview.get('sourceTitle')
            if title and not (lang == 'en' and (row['id'], title) in prior):
                titles.append((lang, title))
        for lang, title in titles[:3]:
            groups[lang].append(row | {'articleTitle': title})
    candidates, audit = [], []
    for lang, wanted in groups.items():
        host = lang + '.wikipedia.org'
        for offset in range(0, len(wanted), 25):
            batch = wanted[offset:offset + 25]
            try:
                data, proof = p.capture({'action': 'query', 'titles': '|'.join(r['articleTitle'] for r in batch),
                    'redirects': 1, 'prop': 'pageimages|pageprops|revisions', 'piprop': 'name|original',
                    'pifilter': 'free', 'pilimit': 25, 'ppprop': 'wikibase_item', 'rvprop': 'ids|timestamp'}, host=host)
                query = data['query']
                pages = {r['title']: r for r in query['pages']}
                rename = {r['from']: r['to'] for r in query.get('normalized', []) + query.get('redirects', [])}
                for row in batch:
                    title = row['articleTitle']
                    for _ in range(10):
                        title = rename.get(title, title)
                    page = pages.get(title, {})
                    same = page.get('pageprops', {}).get('wikibase_item') == row['qid']
                    filename = page.get('pageimage')
                    decision = 'identity-mismatch' if not same else ('candidate-found' if filename else 'no-free-lead-image')
                    audit.append({'id': row['id'], 'category': row['category'], 'language': lang, 'articleTitle': title, 'decision': decision, 'source': proof})
                    if same and filename:
                        candidates.append({'category': row['category'], 'id': row['id'], 'qid': row['qid'], 'title': row['title'],
                            'file': filename, 'property': 'matched-language-article', 'workEvidence': proof, 'language': lang,
                            'articleTitle': title, 'articleRevision': page.get('revisions'), 'original': page.get('original')})
            except Exception as error:
                p.save(p.RUN / 'next-article-errors' / (lang + '-' + str(offset) + '.json'), {'error': str(error), 'at': p.now()}, immutable=False)
                if (p.RUN / 'access-holds' / (host + '.json')).exists():
                    break
            p.save(p.RUN / 'next-article-audit.json.gz', audit, immutable=False)
            p.save(p.RUN / 'next-article-candidates.json.gz', candidates, immutable=False)
            print('Next articles', lang, offset + len(batch), '/', len(wanted), 'candidate images', len(candidates), flush=True)


def sitelinks():
    proposed = {r['id'] for r in p.load(p.RUN / 'proposals.json.gz') if r.get('property') != 'author-portrait'}
    wanted = sorted({r['qid'] for r in p.load(p.RUN / 'inventory.json.gz') if not r['existing'] and r['id'] not in proposed and r['qid'].startswith('Q')})
    found = {}
    path = p.RUN / 'fresh-sitelinks.json.gz'
    if path.exists():
        found.update(p.load(path))
    wanted = [q for q in wanted if q not in found]
    for offset in range(0, len(wanted), 40):
        batch = wanted[offset:offset + 40]
        data, proof = p.capture({'action': 'wbgetentities', 'ids': '|'.join(batch), 'props': 'sitelinks',
            'sitefilter': '|'.join(lang + 'wiki' for lang in ['en', 'fr', 'de', 'es', 'ru', 'el', 'it', 'ja', 'zh', 'pt'])}, host='www.wikidata.org')
        for qid, e in data.get('entities', {}).items():
            if isinstance(e, dict):
                found[qid] = {'sitelinks': e.get('sitelinks', {}), 'evidence': proof}
        p.save(path, found, immutable=False)
        print('Fresh language links', offset + len(batch), '/', len(wanted), flush=True)


def search():
    """Bounded file search for uncovered records; captures metadata, not images."""
    inventory = p.load(p.RUN / 'inventory.json.gz')
    proposed = {r['id'] for r in p.load(p.RUN / 'proposals.json.gz')}
    wanted = [r for r in inventory if not r['existing'] and r['id'] not in proposed]
    wanted.sort(key=lambda r: (not r['top100'], r['category'], r['id']))
    candidates, audit, pages = [], [], {}
    for i, row in enumerate(wanted):
        title = row['title'].replace('"', ' ').strip()
        if len(title) < 4:
            audit.append({'id': row['id'], 'decision': 'title-too-broad'})
            continue
        query = '"' + title + '"'
        try:
            data, proof = p.capture({'action': 'query', 'generator': 'search', 'gsrsearch': query,
                'gsrnamespace': 6, 'gsrlimit': 3, 'prop': 'imageinfo', 'iiprop': 'url|size|mime|extmetadata|sha1',
                'iiextmetadatalanguage': 'en', 'iiurlwidth': 640})
            results = data.get('query', {}).get('pages', [])
            for page in results:
                filename = page['title'].removeprefix('File:')
                pages[filename] = {'page': page, 'evidence': proof, 'fresh': True}
                candidates.append({'category': row['category'], 'id': row['id'], 'qid': row['qid'], 'title': row['title'],
                    'file': filename, 'property': 'commons-search-unverified', 'workEvidence': proof, 'searchQuery': query,
                    'identityReview': 'pending: a search hit does not establish work/event identity'})
            audit.append({'id': row['id'], 'query': query, 'results': len(results), 'evidence': proof})
        except Exception as error:
            audit.append({'id': row['id'], 'query': query, 'error': str(error)})
            if (p.RUN / 'access-holds/commons.wikimedia.org.json').exists():
                break
        p.save(p.RUN / 'search-candidates.json.gz', candidates, immutable=False)
        p.save(p.RUN / 'search-commons-index.json.gz', pages, immutable=False)
        p.save(p.RUN / 'search-audit.json.gz', audit, immutable=False)
        if i % 20 == 0:
            print('Gap search', i + 1, '/', len(wanted), 'candidates', len(candidates), flush=True)


def authorsearch():
    """Research alternative portraits for creators whose books remain uncovered."""
    inventory = {r['id']: r for r in p.load(p.RUN / 'inventory.json.gz') if r['category'] == 'books' and not r['existing']}
    proposed = {r['id'] for r in p.load(p.RUN / 'proposals.json.gz')}
    creators = {r['id']: r for r in p.load(p.RUN / 'creators.json.gz') if r['record'].get('kind') == 'person'}
    held_authors = set()
    for directory in (p.RUN / 'delivery').iterdir():
        if not (directory / 'draft.json.gz').exists():
            continue
        rows = p.load(directory / 'draft.json.gz')
        for path in (directory / 'visual-reviews').glob('*.json'):
            for rejected in p.load(path).get('rejected', []):
                row = rows[rejected['index']]
                if row.get('property') == 'author-portrait':
                    held_authors.add(row['creatorId'])
    groups = collections.defaultdict(list)
    for link in p.load(p.RUN / 'creator-links.json.gz'):
        if link['position'] == 0 and link['book_id'] in inventory and link['creator_id'] in creators:
            if link['book_id'] not in proposed or link['creator_id'] in held_authors:
                groups[link['creator_id']].append(inventory[link['book_id']])
    candidates, audit, pages = [], [], {}
    for i, (qid, books) in enumerate(sorted(groups.items(), key=lambda pair:(-len(pair[1]), pair[0]))):
        creator = creators[qid]
        query = '"' + creator['name'].replace('"', ' ') + '"'
        try:
            data, proof = p.capture({'action': 'query', 'generator': 'search', 'gsrsearch': query,
                'gsrnamespace': 6, 'gsrlimit': 4, 'prop': 'imageinfo', 'iiprop': 'url|size|mime|extmetadata|sha1',
                'iiextmetadatalanguage': 'en', 'iiurlwidth': 640})
            results = data.get('query', {}).get('pages', [])
            for page in results:
                filename = page['title'].removeprefix('File:')
                pages[filename] = {'page': page, 'evidence': proof, 'fresh': True}
                for row in books:
                    candidates.append({'category': 'books', 'id': row['id'], 'qid': row['qid'], 'title': row['title'],
                        'file': filename, 'property': 'author-portrait', 'creatorId': qid, 'creatorName': creator['name'],
                        'workEvidence': proof, 'searchQuery': query, 'identityReview': 'Search lead: author identity not yet accepted',
                        'identityBasis': 'Primary book-creator link is retained. Commons search lead requires visual and source-description verification of the same creator; never represents a book cover.'})
            audit.append({'creatorId': qid, 'name': creator['name'], 'books': [r['id'] for r in books], 'results': len(results), 'evidence': proof})
        except Exception as error:
            audit.append({'creatorId': qid, 'error': str(error), 'at': p.now()})
            if (p.RUN / 'access-holds/commons.wikimedia.org.json').exists():
                break
        p.save(p.RUN / 'author-search-candidates.json.gz', candidates, immutable=False)
        p.save(p.RUN / 'author-search-commons-index.json.gz', pages, immutable=False)
        p.save(p.RUN / 'author-search-audit.json.gz', audit, immutable=False)
        if i % 10 == 0:
            print('Author alternatives', i + 1, '/', len(groups), 'bindings', len(candidates), flush=True)


def custom():
    mapping = {
        'aba-women': "Women's War", 'beijing': 'Beijing Declaration',
        'british-petition': "Women's suffrage in the United Kingdom",
        'cedaw': 'Convention on the Elimination of All Forms of Discrimination Against Women',
        'commission-status-women': 'United Nations Commission on the Status of Women',
        'doria-shafik': 'Doria Shafik', 'equal-franchise': 'Representation of the People (Equal Franchise) Act 1928',
        'iceland-day-off': "1975 Icelandic women's strike", 'international-womens-day': "International Women's Day",
        'japan-electoral-law': "Women's suffrage in Japan", 'japan-first-vote': '1946 Japanese general election',
        'meri-mangakahia': 'Meri Te Tai Mangakāhia', 'mirabal-sisters': 'Mirabal sisters',
        'new-zealand-act': "Women's suffrage in New Zealand", 'new-zealand-vote': "Women's suffrage in New Zealand",
        'nineteenth-amendment': 'Nineteenth Amendment to the United States Constitution', 'nyonin-geijutsu': 'Nyonin Geijutsu',
        'resolution-1325': 'United Nations Security Council Resolution 1325', 'seito': 'Seitō',
        'seneca-falls': 'Seneca Falls Convention', 'sojourner-truth': "Ain't I a Woman?", 'sor-juana': 'Sor Juana Inés de la Cruz',
        'south-africa-march': "Women's March (South Africa)", 'suffrage-atelier': 'Suffrage Atelier',
        'unity-dow': 'Unity Dow', 'violence-declaration': 'Declaration on the Elimination of Violence Against Women'}
    inventory = {r['id']: r for r in p.load(p.RUN / 'inventory.json.gz')}
    titles = list(dict.fromkeys(mapping.values()))
    data, proof = p.capture({'action': 'query', 'titles': '|'.join(titles), 'redirects': 1,
        'prop': 'pageimages|pageprops|revisions', 'piprop': 'name|original', 'pifilter': 'free',
        'pilimit': len(titles), 'ppprop': 'wikibase_item', 'rvprop': 'ids|timestamp'}, host='en.wikipedia.org')
    query = data['query']
    pages = {r['title']: r for r in query['pages']}
    rename = {r['from']: r['to'] for r in query.get('normalized', []) + query.get('redirects', [])}
    candidates, audit = [], []
    for suffix, title in mapping.items():
        row = inventory['event-womens-rights-' + suffix]
        for _ in range(10):
            title = rename.get(title, title)
        page = pages.get(title, {})
        filename = page.get('pageimage')
        audit.append({'id': row['id'], 'title': row['title'], 'articleTitle': title, 'articleQid': page.get('pageprops', {}).get('wikibase_item'),
            'officialSource': row['sourceUrl'], 'decision': 'candidate-needs-specific-event-context-review' if filename else 'no-free-lead-image', 'source': proof})
        if filename:
            candidates.append({'category': 'events', 'id': row['id'], 'qid': row['qid'], 'title': row['title'], 'file': filename,
                'property': 'curated-event-context', 'articleTitle': title, 'workEvidence': proof, 'officialSource': row['sourceUrl'],
                'identityReview': 'Manual subject/event mapping; verify date and whether the image is direct or contextual before selecting.'})
    p.save(p.RUN / 'custom-event-audit.json', audit)
    p.save(p.RUN / 'custom-event-candidates.json.gz', candidates)
    print('Custom event candidates', len(candidates), '/', len(mapping), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['articles', 'search', 'sitelinks', 'custom', 'authorsearch'])
    args = parser.parse_args()
    globals()[args.phase]()
