#!/usr/bin/env python3
"""Resumable, metadata-only Wikidata research. Never writes to the database.

Selection is cross-project documentation, not a claim of a universal canon.
The source responses, revisions, claims and checksums remain auditable.
"""
import argparse
import gzip
import hashlib
import json
import pathlib
import time
import urllib.parse
import urllib.request
import urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/research/historical-books-20260916'
API = 'https://www.wikidata.org/w/api.php'
AGENT = 'ArtlineBookResearch/1.0 (local historical catalogue; metadata only)'
SEEDS = {
    'odyssey': 'Odyssey', 'iliad': 'Iliad', 'republic': 'Republic (Plato)',
    'meditations': 'Meditations', 'dhammapada': 'Dhammapada', 'bible': 'Bible',
    'confessions': 'Confessions (Augustine)', 'divine-comedy': 'Divine Comedy',
    'essays': 'Essays (Montaigne)', 'don-quixote': 'Don Quixote',
    'faust': "Goethe's Faust", 'zarathustra': 'Thus Spoke Zarathustra',
    'lost-time': 'In Search of Lost Time', 'trial': 'The Trial',
    'waste-land': 'The Waste Land', 'being-nothingness': 'Being and Nothingness',
    'one-hundred-years': 'One Hundred Years of Solitude',
}


def cached_request(name, parameters):
    path = OUT / 'sources' / (name + '.json.gz')
    if path.exists():
        return json.loads(gzip.decompress(path.read_bytes()))
    url = API + '?' + urllib.parse.urlencode({'format': 'json', **parameters})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': AGENT}), timeout=60) as response:
                raw = response.read()
            data = json.loads(raw)
            if 'error' in data:
                raise RuntimeError(data['error'])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(gzip.compress(raw, mtime=0))
            time.sleep(2)
            return data
        except Exception as error:
            print(f'{name}: retry {attempt + 1}: {error}', flush=True)
            if attempt == 4:
                raise
            retry_after = error.headers.get('Retry-After', '') if isinstance(error, urllib.error.HTTPError) else ''
            time.sleep(max(int(retry_after) if retry_after.isdigit() else 0, 60 * (attempt + 1) if isinstance(error, urllib.error.HTTPError) and error.code == 429 else min(20, 2 ** attempt)))


def entities(ids, label='entities'):
    result = {}
    ids = sorted(set(ids))
    wanted = set(ids)
    # Reuse individual entities even when the ranked selection changes batch
    # boundaries. A interrupted fetch never invalidates earlier evidence.
    for path in sorted((OUT / 'sources').glob(label + '-*.json.gz')):
        for key, entity in json.loads(gzip.decompress(path.read_bytes())).get('entities', {}).items():
            if key in wanted:
                result[key] = entity
    ids = [key for key in ids if key not in result]
    for offset in range(0, len(ids), 50):
        batch = ids[offset:offset + 50]
        key = hashlib.sha256('|'.join(batch).encode()).hexdigest()[:16]
        data = cached_request(label + '-' + key, {
            'action': 'wbgetentities', 'ids': '|'.join(batch),
            'props': 'info|labels|descriptions|claims|sitelinks', 'languages': 'en', 'sitefilter': 'enwiki',
        })
        result.update(data['entities'])
        if offset % 500 == 0:
            print(f'{label}: {min(offset + 50, len(ids))}/{len(ids)}', flush=True)
    return result


def claims(entity, prop):
    values = [c for c in entity.get('claims', {}).get(prop, []) if c.get('rank') != 'deprecated']
    preferred = [c for c in values if c.get('rank') == 'preferred']
    return preferred or values


def values(entity, prop):
    return [c['mainsnak']['datavalue']['value'] for c in claims(entity, prop) if 'datavalue' in c.get('mainsnak', {})]


def ids(entity, prop):
    return list(dict.fromkeys(v['id'] for v in values(entity, prop) if isinstance(v, dict) and 'id' in v))


def name(entity):
    return entity.get('labels', {}).get('en', {}).get('value', '')


def creator_name(entity):
    if name(entity):
        return name(entity)
    labels = entity.get('labels', {})
    if labels.get('mul', {}).get('value'):
        return labels['mul']['value']
    native = values(entity, 'P1559')
    if native and isinstance(native[0], dict) and native[0].get('text'):
        return native[0]['text']
    for language in ['fr', 'de', 'es', 'it', 'pt', 'ru', 'el', 'ar', 'zh', 'ja', 'ko'] + sorted(labels):
        if labels.get(language, {}).get('value'):
            return labels[language]['value']
    return 'Unnamed creator'


def description(entity):
    return entity.get('descriptions', {}).get('en', {}).get('value', '')


def year_label(year):
    return f'{abs(year)} BCE' if year < 0 else str(year)


def date_span(value):
    # Wikibase signed historical years have no year zero. Retain precision and
    # uncertainty; never turn a century or decade into an exact year.
    if not isinstance(value, dict) or not value.get('time'):
        return None
    year = int(value['time'].split('-')[0]) if value['time'][0] != '-' else -int(value['time'][1:].split('-')[0])
    precision = value.get('precision', 0)
    if not year or precision < 6 or abs(year) > 5000:
        return None
    unit = 10 ** max(0, 9 - precision)
    if unit == 1:
        start = end = year
    elif year < 0 and precision == 8:
        base = abs(year) // 10 * 10
        start, end = -(base + 9), -max(1, base)
    elif year < 0:
        end = -max(1, ((abs(year) - 1) // unit) * unit + 1)
        start = end - unit + 1
    else:
        start = max(1, (year // unit) * unit) if precision == 8 else ((year - 1) // unit) * unit + 1
        end = start + unit - 1
    if precision <= 9:
        start -= value.get('before', 0) * unit
        end += value.get('after', 0) * unit
    return start, end, precision < 9 or start != end


def claim_span(claim):
    value = claim.get('mainsnak', {}).get('datavalue', {}).get('value')
    span = date_span(value)
    qualifiers = claim.get('qualifiers', {})
    earliest = [date_span(s.get('datavalue', {}).get('value')) for s in qualifiers.get('P1319', [])]
    latest = [date_span(s.get('datavalue', {}).get('value')) for s in qualifiers.get('P1326', [])]
    earliest, latest = [s for s in earliest if s], [s for s in latest if s]
    if not span and earliest and latest:
        return min(s[0] for s in earliest), max(s[1] for s in latest), True
    if span:
        a, b, approximate = span
        if earliest:
            a = min(s[0] for s in earliest)
        if latest:
            b = max(s[1] for s in latest)
        if a > b:
            return None
        return a, b, approximate or bool(qualifiers.get('P1480') or qualifiers.get('P4241') or earliest or latest)
    return None


def life_label(entity, prop):
    spans = [claim_span(c) for c in claims(entity, prop)]
    spans = sorted(set(s for s in spans if s))
    if not spans:
        return None
    # Conflicting claims stay alternatives rather than a fictitious lifespan.
    return ' or '.join((('c. ' if approximate else '') + (year_label(a) if a == b else f'{year_label(a)}–{year_label(b)}')) for a, b, approximate in spans)


def work_dates(entity):
    for prop, basis in [('P571', 'Recorded inception/composition'), ('P577', 'Earliest recorded publication')]:
        spans = sorted(s for c in claims(entity, prop) if (s := claim_span(c)))
        if spans:
            return spans, basis
    return [], 'No usable work date in source'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidates', type=pathlib.Path, required=True)
    parser.add_argument('--count', type=int, default=10000)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    candidate_bytes = args.candidates.read_bytes()
    if args.candidates.suffix == '.gz':
        candidate_bytes = gzip.decompress(candidate_bytes)
    candidates = json.loads(candidate_bytes)['results']['bindings']
    scores = {r['book']['value'].rsplit('/', 1)[-1]: int(r['links']['value']) for r in candidates}
    (OUT / 'candidate-ranking.json').write_text(json.dumps(scores, indent=2) + '\n')
    seed_data = cached_request('seed-identities', {'action': 'wbgetentities', 'sites': 'enwiki', 'titles': '|'.join(SEEDS.values()), 'props': 'labels|descriptions|claims|sitelinks', 'languages': 'en', 'sitefilter': 'enwiki'})['entities']
    title_ids = {v.get('sitelinks', {}).get('enwiki', {}).get('title'): k for k, v in seed_data.items()}
    seed_ids = {slug: title_ids.get(title) for slug, title in SEEDS.items()}
    if not all(seed_ids.values()):
        raise RuntimeError(f'Unresolved seed identities: {seed_ids}')
    all_entities = entities(list(scores) + list(seed_ids.values()), 'works')
    excluded = []
    eligible = []
    for qid in sorted(scores, key=lambda q: (-scores[q], int(q[1:]))):
        e = all_entities[qid]
        # Avoid editions/translations, series, articles and screen works.
        # Formats and cultural origins are not exclusion criteria.
        types = set(ids(e, 'P31') + ids(e, 'P7937'))
        if qid in seed_ids.values():
            continue
        book_identity = 'Q7725634' in types or any(isinstance(v, str) and v.startswith('OL') and v.endswith('W') for v in values(e, 'P648'))
        future_dates, _ = work_dates(e)
        reason = 'missing English title' if not name(e) else 'edition or translation' if values(e, 'P629') else 'series/article/screen work' if types & {'Q277759', 'Q13442814', 'Q3331189', 'Q1002697', 'Q11424', 'Q5398426'} else 'no literary-work or Open Library work identity' if not book_identity else 'future publication' if future_dates and all(s[0] > 2026 for s in future_dates) else ''
        if reason:
            excluded.append({'id': qid, 'reason': reason})
        else:
            eligible.append(qid)
    chosen = list(seed_ids.values()) + eligible[:args.count - len(seed_ids)]
    if len(chosen) != args.count:
        raise RuntimeError(f'Only {len(chosen)} eligible works; broaden the documented candidate query.')
    creator_ids = {a for qid in chosen for a in ids(all_entities[qid], 'P50')} | {'Q9441'}
    creators = entities(creator_ids, 'creators')
    missing_names = sorted(q for q, e in creators.items() if not name(e))
    for offset in range(0, len(missing_names), 50):
        batch = missing_names[offset:offset + 50]
        key = hashlib.sha256('|'.join(batch).encode()).hexdigest()[:16]
        # Fetch complete source records with original-language names, rather
        # than displaying internal IDs or inventing an English transliteration.
        creators.update(cached_request('creator-original-names-' + key, {'action': 'wbgetentities', 'ids': '|'.join(batch), 'props': 'info|labels|descriptions|claims'})['entities'])
    terms = entities({t for qid in chosen for p in ['P136', 'P7937', 'P31'] for t in ids(all_entities[qid], p)}, 'terms')
    seed_books = {b['id']: b for b in json.loads((ROOT / 'apps/server/internal/books/selection.json').read_text())}
    slug_by_id = {v: k for k, v in seed_ids.items()}
    result = []
    for qid in chosen:
        e = all_entities[qid]
        authors = []
        for aid in (['Q9441'] if qid == seed_ids['dhammapada'] else ids(e, 'P50')):
            a = creators[aid]
            authors.append({'id': aid, 'name': creator_name(a), 'description': description(a), 'birth': life_label(a, 'P569'), 'death': life_label(a, 'P570'), 'sourceUrl': f'https://www.wikidata.org/wiki/{aid}', 'sourceRevision': a.get('lastrevid'), 'kind': 'collective' if aid in {'Q2818964', 'Q1690980'} else 'person' if 'Q5' in ids(a, 'P31') else 'unknown', 'credit': 'Traditional attribution; not a claim of direct authorship' if aid == 'Q9441' and qid == seed_ids['dhammapada'] else 'Traditional attribution' if aid == 'Q6691' else 'Author'})
        # Dates belong to the work record, never the creator's lifespan. Keep
        # alternative publication dates in evidence and label the earliest as
        # the earliest recorded publication, not a verified first edition.
        spans, date_basis = work_dates(e)
        spans = [s for s in spans if s[0] <= 2026]
        span = spans[0] if spans else None
        a, b, approximate = span if span else (None, None, False)
        themes = list(dict.fromkeys(name(terms[t]) for p in ['P136', 'P7937', 'P31'] for t in ids(e, p) if name(terms[t]) and name(terms[t]).lower() not in {'literary work', 'written work', 'book'}))
        book = {
            'id': slug_by_id.get(qid, 'wd-' + qid.lower()), 'sourceId': qid, 'title': name(e),
            'author': ' · '.join(x['name'] for x in authors) or 'Creator not recorded',
            'creators': authors, 'years': (('c. ' if approximate else '') + (year_label(a) if a == b else f'{year_label(a)}–{year_label(b)}')) if span else 'Date not established',
            'startYear': a, 'endYear': b, 'approximate': approximate,
            'era': 'Undated' if a is None else 'Ancient' if b < 500 else 'Medieval' if b < 1500 else 'Early modern' if b < 1800 else 'Modern',
            'theme': ' · '.join(themes[:4]) or 'Literature and ideas',
            'description': description(e) or 'A description has not yet been established for this work.',
            'coverTone': ['#e8ddc1', '#b6c3b4', '#d3b4a3', '#c3bfcc', '#c4cad0'][int(qid[1:]) % 5], 'coverInk': '#29251f', 'coverMark': name(e)[:1],
            'sourceUrl': f'https://www.wikidata.org/wiki/{qid}', 'sourceRevision': e.get('lastrevid'),
            'selectionBasis': 'Original editorial selection' if qid in slug_by_id else f'Cross-project documentation: {scores[qid]} Wikimedia sitelinks; ranked within the recorded literary-work candidate set.',
            'dateBasis': date_basis + ' in Wikidata; alternatives retained in source evidence' if span else 'No usable work date in source',
            'status': 'review',
        }
        if qid in slug_by_id:
            original = seed_books[slug_by_id[qid]]
            book.update(original)
            book['years'] = book['years'].replace(' CE', '')
            book['dateBasis'] = 'Existing editorial composition/publication interval; retained for review'
        elif any(term.lower() in {'religious text', 'sacred text', 'scripture', 'sutra', 'sūtra', 'buddhist text'} for term in themes):
            book['era'] = 'Sacred and contemplative'
        result.append(book)
    (OUT / 'books.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    (OUT / 'excluded.json').write_text(json.dumps(excluded, indent=2) + '\n')
    manifest = {'count': len(result), 'creators': len(creators), 'undated': sum(b['startYear'] is None for b in result), 'bce': sum(b['startYear'] is not None and b['startYear'] < 0 for b in result), 'status': 'review', 'license': 'CC0', 'retrieved': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'sha256': hashlib.sha256((OUT / 'books.json').read_bytes()).hexdigest(), 'sourceFiles': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((OUT / 'sources').glob('*.gz'))}}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print({k: v for k, v in manifest.items() if k != 'sourceFiles'}, flush=True)


if __name__ == '__main__':
    main()
