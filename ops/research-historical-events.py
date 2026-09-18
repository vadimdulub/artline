#!/usr/bin/env python3
"""Resumable source research for Events; metadata only, never writes a database.

Sources are cached verbatim with query text and entity revisions. This is a
documented discovery corpus, not 10,000 independently verified narratives.
"""
import argparse
import collections
import csv
import gzip
import hashlib
import importlib.util
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/research/historical-events-20260917'
spec = importlib.util.spec_from_file_location('book_research', ROOT / 'ops/research-historical-books.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.OUT = OUT
base.AGENT = 'ArtlineHistoryResearch/1.0 (local review catalogue; metadata only)'

# Titles resolve to source identities, rather than trusting remembered Q IDs.
# Categories describe the source class; an event can have several categories.
ROOTS = {
    'War': ('Conflict', 'Event'), 'Battle': ('Conflict', 'Event'),
    'Military campaign': ('Conflict', 'Event'), 'Siege': ('Conflict', 'Event'),
    'Revolution': ('Politics and society', 'Event'), 'Rebellion': ('Politics and society', 'Event'),
    "Coup d'état": ('Politics and society', 'Event'), 'Political crisis': ('Politics and society', 'Event'),
    'Treaty': ('Diplomacy and law', 'Event'), 'Peace treaty': ('Diplomacy and law', 'Event'),
    'Constitution': ('Diplomacy and law', 'Event'), 'Declaration of independence': ('Politics and society', 'Event'),
    'Social movement': ('Politics and society', 'Movement'), 'Political movement': ('Politics and society', 'Movement'),
    'Massacre': ('Persecution and human rights', 'Event'), 'Genocide': ('Persecution and human rights', 'Event'),
    'Pandemic': ('Health and environment', 'Event'), 'Epidemic': ('Health and environment', 'Event'),
    'Famine': ('Health and environment', 'Event'), 'Earthquake': ('Health and environment', 'Event'),
    'Volcanic eruption': ('Health and environment', 'Event'), 'Flood': ('Health and environment', 'Event'),
    'Spaceflight': ('Science and technology', 'Event'), 'Space mission': ('Science and technology', 'Event'),
    'Scientific discovery': ('Science and technology', 'Event'), 'Invention': ('Science and technology', 'Event'),
    'Expedition': ('Exploration and exchange', 'Event'), 'Geographical discovery': ('Exploration and exchange', 'Event'),
    'Archaeological culture': ('Cultures and empires', 'Period'), 'Empire': ('Cultures and empires', 'Period'),
    'Historical period': ('Cultures and empires', 'Period'), 'Ecumenical council': ('Religion and ideas', 'Event'),
    'Religious movement': ('Religion and ideas', 'Movement'), 'Schism': ('Religion and ideas', 'Event'),
    'Art movement': ('Culture and ideas', 'Movement'), 'World\'s fair': ('Culture and ideas', 'Event'),
    'Economic crisis': ('Economy and trade', 'Event'), 'Financial crisis': ('Economy and trade', 'Event'),
    'Strike action': ('Politics and society', 'Event'), 'Protest': ('Politics and society', 'Event'),
}


def write(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sparql(name, query):
    directory = OUT / 'sources'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (name + '.json.gz')
    (directory / (name + '.sparql')).write_text(query + '\n')
    if path.exists():
        return json.loads(gzip.decompress(path.read_bytes()))
    url = 'https://query.wikidata.org/sparql?' + urllib.parse.urlencode({'query': query, 'format': 'json'})
    for attempt in range(4):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': base.AGENT, 'Accept': 'application/sparql-results+json'})
            with urllib.request.urlopen(request, timeout=100) as response:
                raw = response.read()
            data = json.loads(raw)
            path.write_bytes(gzip.compress(raw, mtime=0))
            time.sleep(62)  # Current WDQS outage policy: one request per minute.
            return data
        except Exception as error:
            print(f'{name}: attempt {attempt + 1}: {error}', flush=True)
            if attempt == 3:
                raise
            time.sleep(65 * (attempt + 1))


def candidates():
    roots = base.cached_request('root-identities', {'action': 'wbgetentities', 'sites': 'enwiki', 'titles': '|'.join(ROOTS), 'props': 'info|labels|sitelinks', 'languages': 'en', 'sitefilter': 'enwiki'})
    by_title = {e.get('sitelinks', {}).get('enwiki', {}).get('title'): e['id'] for e in roots['entities'].values() if 'missing' not in e}
    merged, failures = {}, []
    titles = list(ROOTS)
    for offset in range(0, len(titles), 20):
        batch = {by_title[t]: t for t in titles[offset:offset + 20] if t in by_title}
        # Restrict to a single source class per query and require documentation
        # in >=3 Wikimedia projects. Fetch dates/labels later in bounded batches.
        query = f'''SELECT DISTINCT ?item ?links ?root WHERE {{
          VALUES ?root {{ {' '.join('wd:' + q for q in batch)} }}
          ?item wdt:P31 ?root; wikibase:sitelinks ?links .
          FILTER(?links >= 3)
        }} ORDER BY DESC(?links) ?item LIMIT 30000'''
        try:
            data = sparql('candidates-direct-' + str(offset), query)
        except Exception as error:
            failures.append({'titles': list(batch.values()), 'reason': str(error)})
            continue
        rows = data['results']['bindings']
        for row in rows:
            title = batch[row['root']['value'].rsplit('/', 1)[-1]]
            topic, kind = ROOTS[title]
            qid = row['item']['value'].rsplit('/', 1)[-1]
            item = merged.setdefault(qid, {'id': qid, 'links': int(row['links']['value']), 'roots': [], 'topics': [], 'kinds': []})
            for key, value in [('roots', title), ('topics', topic), ('kinds', kind)]:
                if value not in item[key]: item[key].append(value)
        write('candidate-ranking.json', sorted(merged.values(), key=lambda e: (-e['links'], int(e['id'][1:]))))
        write('candidate-query-issues.json', failures)
        print(f'{list(batch.values())}: {len(rows)} candidates; {len(merged)} unique', flush=True)
    return merged


def fetch():
    candidates = json.loads((OUT / 'candidate-ranking.json').read_text())
    dated_path = OUT / 'dated-candidate-ids.json'
    if dated_path.exists():
        dated = set(json.loads(dated_path.read_text()))
        candidates = [e for e in candidates if e['id'] in dated]
    # Metadata candidates remain outside the database. Oversample to allow
    # rejecting non-events, missing dates and records outside the cutoff.
    chosen = candidates[:15000]
    result = base.entities([e['id'] for e in chosen], 'events')
    write('fetch-summary.json', {'candidates': len(candidates), 'hydrated': len(result)})


def date_index():
    roots = json.loads(gzip.decompress((OUT / 'sources/root-identities.json.gz').read_bytes()))
    by_title = {e.get('sitelinks', {}).get('enwiki', {}).get('title'): e['id'] for e in roots['entities'].values() if 'missing' not in e}
    selected = set()
    titles = list(ROOTS)
    for offset in range(0, len(titles), 20):
        batch = [by_title[t] for t in titles[offset:offset + 20] if t in by_title]
        query = f'''SELECT DISTINCT ?item WHERE {{
          VALUES ?root {{ {' '.join('wd:' + q for q in batch)} }}
          ?item wdt:P31 ?root; wikibase:sitelinks ?links . FILTER(?links >= 3)
          VALUES ?dateProperty {{ wdt:P580 wdt:P585 wdt:P571 wdt:P577 wdt:P619 }}
          ?item ?dateProperty ?date . FILTER(YEAR(?date) >= -12000 && YEAR(?date) <= 2000)
        }} LIMIT 30000'''
        data = sparql('dated-candidates-' + str(offset), query)
        selected.update(row['item']['value'].rsplit('/', 1)[-1] for row in data['results']['bindings'])
        print(f'Date prefilter batch {offset}: {len(selected)} distinct historical candidates', flush=True)
    write('dated-candidate-ids.json', sorted(selected))


def seeds():
    entries = list(csv.DictReader((OUT / 'top100.tsv').open(), delimiter='\t'))
    resolved, missing = {}, []
    for offset in range(0, len(entries), 50):
        batch = entries[offset:offset + 50]
        data = base.cached_request('top-identities-' + str(offset), {
            'action': 'wbgetentities', 'sites': 'enwiki', 'titles': '|'.join(e['title'] for e in batch),
            'props': 'info|labels|descriptions|claims|sitelinks', 'languages': 'en', 'sitefilter': 'enwiki', 'redirects': 'yes',
        })
        for e in data['entities'].values():
            title = e.get('sitelinks', {}).get('enwiki', {}).get('title', e.get('title', ''))
            if 'missing' in e:
                missing.append(title)
            else:
                resolved[title] = {'id': e['id'], 'label': base.name(e)}
    write('top-identities.json', resolved)
    write('top-missing.json', missing)
    print(f'Top 100: {len(resolved)} resolved; missing {missing}', flush=True)


def date_span(value):
    if not isinstance(value, dict) or not value.get('time'):
        return None
    match = re.match(r'^([+-])(\d+)-', value['time'])
    if not match:
        return None
    year = int(match[2]) * (-1 if match[1] == '-' else 1)
    precision = value.get('precision', 0)
    if year == 0 or precision < 6 or abs(year) > 12000:
        return None
    unit = 10 ** max(0, 9 - precision)
    # Subyear before/after offsets are measured in months/days, not years.
    # No retained record currently uses them; preserve a future unsupported
    # claim as unplaced instead of silently converting days into whole years.
    if precision > 9 and (value.get('before', 0) or value.get('after', 0)):
        return None
    if unit == 1:
        start = end = year
    elif year < 0 and precision == 8:
        last = abs(year) // 10 * 10
        start, end = -(last + 9), -max(1, last)
    elif year < 0:
        end = -max(1, ((abs(year) - 1) // unit) * unit + 1)
        start = end - unit + 1
    else:
        start = max(1, (year // unit) * unit) if precision == 8 else ((year - 1) // unit) * unit + 1
        end = start + unit - 1
    start -= value.get('before', 0) * unit
    end += value.get('after', 0) * unit
    if start == 0: start = -1
    if end == 0: end = 1
    return start, end, precision < 9 or start != end


def span_for_claim(claim):
    span = date_span(claim.get('mainsnak', {}).get('datavalue', {}).get('value'))
    if span is None:
        return None
    start, end, approximate = span
    qualifiers = claim.get('qualifiers', {})
    earliest = [date_span(v.get('datavalue', {}).get('value')) for v in qualifiers.get('P1319', [])]
    latest = [date_span(v.get('datavalue', {}).get('value')) for v in qualifiers.get('P1326', [])]
    if any(earliest): start = min(v[0] for v in earliest if v); approximate = True
    if any(latest): end = max(v[1] for v in latest if v); approximate = True
    # P4241 can specify a time of day, such as "morning"; it is not itself
    # uncertainty about the year. Its original qualifier remains in the source.
    return start, end, approximate or bool(qualifiers.get('P1480'))


def chronology(entity, kind):
    spans = {prop: [s for c in base.claims(entity, prop) if (s := span_for_claim(c))] for prop in ['P580', 'P582', 'P585', 'P571', 'P576', 'P577', 'P619']}
    starts, ends = spans['P580'], spans['P582']
    if kind == 'Period':
        starts = starts or spans['P571']
        ends = ends or spans['P576']
    used = []
    if starts and ends:
        # Only paired source endpoints represent duration. Alternatives expand
        # the uncertain envelope, never an invented midpoint or exact date.
        start, end = min(s[0] for s in starts), max(s[1] for s in ends)
        used = starts + ends
        note = 'Recorded start and end dates.'
        if len(starts) > 1 or len(ends) > 1:
            note += ' Alternative source dates are included in the uncertain span.'
    elif spans['P585']:
        used = spans['P585']; start, end = min(s[0] for s in used), max(s[1] for s in used)
        note = 'Recorded occurrence date.'
        if len(used) > 1: note += ' Multiple recorded occurrences or alternative dates are shown together.'
    else:
        used = starts or spans['P571'] or spans['P577'] or spans['P619'] or ends
        if not used: return None, None, False, 'No date is established in the retained source evidence.'
        start, end = min(s[0] for s in used), max(s[1] for s in used)
        note = 'A single recorded date is shown; it does not establish the full duration.'
        if kind in ['Movement', 'Period']: note = 'Only one endpoint is recorded. This marker does not imply that the period ended then.'
    # Several exact dates in the same calendar year do not make that year
    # uncertain (for example, the two atomic bombings in August 1945).
    uncertain = any(s[2] for s in used) or len({s[:2] for s in starts}) > 1 or len({s[:2] for s in ends}) > 1
    if len({s[:2] for s in spans['P585']}) > 1 and not (starts and ends): uncertain = True
    if kind in ['Period', 'Movement']:
        note += ' Historical period boundaries are conventions and may differ between sources.'
        uncertain = True
    if start > end: return None, None, True, 'The retained source dates conflict; this record is unplaced.'
    return start, end, uncertain, note


def cached_entities():
    result = {}
    for path in sorted((OUT / 'sources').glob('*.json.gz')):
        for key, value in json.loads(gzip.decompress(path.read_bytes())).get('entities', {}).items():
            if 'missing' not in value and key.startswith('Q'): result[key] = value
    return result


def supplement():
    queries = ['unification of Egypt', 'printing revolution', 'Ghana independence', 'Xinhai Revolution', 'United Nations Charter', 'civil rights movement']
    results = {}
    for query in queries:
        data = base.cached_request('lookup-' + hashlib.sha256(query.encode()).hexdigest()[:12], {'action': 'wbsearchentities', 'search': query, 'language': 'en', 'limit': 5})
        results[query] = [{k: r.get(k) for k in ['id', 'label', 'description']} for r in data.get('search', [])]
        write('identity-lookups.json', results)
        print(query, results[query], flush=True)
    base.entities(['Q5933860', 'Q828435', 'Q96379430'], 'top-extra')


def class_lookups():
    results = {}
    for query in ['expedition', 'space mission', 'scientific discovery', 'peace conference', 'religious council', 'independence']:
        data = base.cached_request('class-lookup-' + hashlib.sha256(query.encode()).hexdigest()[:12], {'action': 'wbsearchentities', 'search': query, 'language': 'en', 'limit': 3})
        results[query] = [{k: r.get(k) for k in ['id', 'label', 'description']} for r in data.get('search', [])]
        write('class-lookups.json', results)
        print(query, results[query], flush=True)


def broaden(subclasses=False):
    roots = {'Q2401485': ('Expedition', 'Exploration and exchange'), 'Q2133344': ('Space mission', 'Science and technology'), 'Q7157512': ('Peace conference', 'Diplomacy and law')}
    query = '''SELECT DISTINCT ?item ?root ?links WHERE {
      VALUES ?root { wd:Q2401485 wd:Q2133344 wd:Q7157512 }
      ?item wdt:P31 ?root; wikibase:sitelinks ?links . FILTER(?links >= 3)
      VALUES ?dateProperty { wdt:P580 wdt:P585 wdt:P571 wdt:P577 wdt:P619 }
      ?item ?dateProperty ?date . FILTER(YEAR(?date) >= -12000 && YEAR(?date) <= 2000)
    } ORDER BY DESC(?links) ?item LIMIT 1500'''
    if subclasses:
        rows = []
        # Keep the property-path root constant. WDQS can otherwise choose an
        # unbounded graph traversal before applying VALUES and time out.
        for root in ['Q2401485', 'Q2133344']:
            bounded = query.replace('VALUES ?root { wd:Q2401485 wd:Q2133344 wd:Q7157512 }', f'BIND(wd:{root} AS ?root)')
            bounded = bounded.replace('?item wdt:P31 ?root;', f'?class wdt:P279* wd:{root} . ?item wdt:P31 ?class;')
            rows.extend(sparql('broader-history-' + root, bounded)['results']['bindings'])
        data = {'results': {'bindings': sorted(rows, key=lambda row: -int(row['links']['value']))}}
    else:
        data = sparql('broader-history-candidates', query)
    current = {r['id']: r for r in json.loads((OUT / 'candidate-ranking.json').read_text())}
    chosen = []
    for row in data['results']['bindings']:
        qid = row['item']['value'].rsplit('/', 1)[-1]
        label, topic = roots[row['root']['value'].rsplit('/', 1)[-1]]
        entry = current.setdefault(qid, {'id': qid, 'links': int(row['links']['value']), 'roots': [], 'topics': [], 'kinds': []})
        for key, value in [('roots', label), ('topics', topic), ('kinds', 'Event')]:
            if value not in entry[key]: entry[key].append(value)
        if qid not in chosen: chosen.append(qid)
    write('candidate-ranking.json', sorted(current.values(), key=lambda r: (-r['links'], int(r['id'][1:]))))
    print(f'Broader historical candidates: {len(chosen)}', flush=True)
    base.entities(chosen[:750], 'events-extra')


def finish_seeds():
    data = base.cached_request('top-additional-identities', {'action': 'wbgetentities', 'sites': 'enwiki', 'titles': 'Early Dynastic Period of Egypt|Gutenberg Bible', 'props': 'info|labels|descriptions|claims|sitelinks', 'languages': 'en', 'sitefilter': 'enwiki'})
    print({e.get('sitelinks', {}).get('enwiki', {}).get('title'): e.get('id') for e in data['entities'].values()}, flush=True)
    base.entities(['Q190517', 'Q171328', 'Q48537'], 'top-extra')


def enrich():
    entities = cached_entities()
    countries = {q for e in entities.values() for q in base.ids(e, 'P17')}
    corrections = json.loads((OUT / 'top-corrections.json').read_text())
    countries.update(q for row in corrections.values() for q in row.get('countryIds', []))
    # Reuse the retained country authorities already researched for Books.
    # Their original full source file and checksum are explicitly recorded.
    previous = ROOT / 'docs/research/historical-books-20260916/discovery-terms.json'
    known = json.loads(previous.read_text())
    reuse = {q: known[q] for q in countries if q in known}
    path = OUT / 'sources/countries-reused.json.gz'
    path.write_bytes(gzip.compress(json.dumps({'entities': reuse}).encode(), mtime=0))
    write('reused-country-evidence.json', {'source': str(previous.relative_to(ROOT)), 'sha256': hashlib.sha256(previous.read_bytes()).hexdigest(), 'ids': sorted(reuse)})
    identities = json.loads((OUT / 'top-identities.json').read_text())
    seed_ids = {row['id'] for row in identities.values()} | {row['sourceId'] for row in corrections.values() if row.get('sourceId')}
    context = set(countries) - set(reuse)
    for qid in seed_ids:
        e = entities.get(qid, {})
        for prop in ['P276', 'P710', 'P112']:
            context.update(base.ids(e, prop)[:16])
    context -= set(entities)
    print(f'Context: {len(countries)} country authorities, {len(reuse)} reused; {len(context)} further authorities', flush=True)
    base.entities(context, 'context')


def source_link(qid, entities):
    label = base.name(entities.get(qid, {}))
    return {'name': label, 'url': 'https://www.wikidata.org/wiki/' + qid} if label else None


def compile_events():
    entities = cached_entities()
    seed_rows = list(csv.DictReader((OUT / 'top100.tsv').open(), delimiter='\t'))
    identities = json.loads((OUT / 'top-identities.json').read_text())
    corrections_path = OUT / 'top-corrections.json'
    corrections = json.loads(corrections_path.read_text()) if corrections_path.exists() else {}
    seeds = {}
    missing = []
    for row in seed_rows:
        identity = corrections.get(row['title'], {}).get('sourceId') or identities.get(row['title'], {}).get('id')
        if not identity or identity not in entities: missing.append(row['title']); continue
        seeds[identity] = row
    candidates = {r['id']: r for r in json.loads((OUT / 'candidate-ranking.json').read_text())}
    for qid, row in seeds.items(): candidates.setdefault(qid, {'id': qid, 'links': 0, 'roots': ['Editorial selection'], 'topics': [row['topic']], 'kinds': [row['kind']]})
    un = json.loads((ROOT / 'docs/research/historical-books-20260916/un-m49.json').read_text())
    by_iso = {r['ISO-alpha2 Code']: r['Intermediate Region Name'] or r['Sub-region Name'] for r in un['rows']}
    records, exclusions = [], []
    for qid, candidate in candidates.items():
        entity = entities.get(qid)
        if not entity: continue
        seed = seeds.get(qid)
        override = corrections.get(seed['title'], {}) if seed else {}
        title = override.get('title') or (seed['title'] if seed else base.name(entity))
        kind = override.get('kind') or (seed['kind'] if seed else ('Period' if 'Period' in candidate['kinds'] else 'Movement' if 'Movement' in candidate['kinds'] else 'Event'))
        description = base.description(entity)
        excluded = not title or bool(re.search(r'\b(fictional|hypothetical|mythological|legendary battle|calendar year|calendar decade|calendar century|geological epoch|geological age)\b', description, re.I))
        if re.fullmatch(r'(\d+(s|st|nd|rd|th)?( century| millennium)?( BC| BCE)?|[12]\d{3} in .*)', title): excluded = True
        if not seed and excluded: exclusions.append({'id': qid, 'reason': 'Non-historical entity, calendar unit or missing title'}); continue
        start, end, approximate, basis = chronology(entity, kind)
        if 'startYear' in override:
            start, end = override['startYear'], override['endYear']
            approximate, basis = override.get('approximate', False), override['dateBasis']
        elif override.get('dateBasis'):
            basis = override['dateBasis']
        if (start is not None and (start < -12000 or end > 2000 or start > 2000)) or (start is None and not seed):
            exclusions.append({'id': qid, 'title': title, 'reason': 'Unestablished chronology or outside the through-2000 scope', 'start': start, 'end': end}); continue
        country_ids = override.get('countryIds', base.ids(entity, 'P17'))
        countries = sorted({base.name(entities.get(q, {})) for q in country_ids} - {''})
        regions = sorted({by_iso[iso] for q in country_ids for iso in base.values(entities.get(q, {}), 'P297') if iso in by_iso and by_iso[iso]})
        topic = [seed['topic']] if seed else candidate['topics']
        locations = [l for q in base.ids(entity, 'P276')[:16] if (l := source_link(q, entities))]
        people = [l for q in list(dict.fromkeys(base.ids(entity, 'P710') + base.ids(entity, 'P112')))[:16] if (l := source_link(q, entities))]
        sources = override.get('sources', [])[:]
        wiki_title = entity.get('sitelinks', {}).get('enwiki', {}).get('title')
        if wiki_title: sources.append({'name': 'Encyclopedia overview', 'url': 'https://en.wikipedia.org/wiki/' + urllib.parse.quote(wiki_title.replace(' ', '_'))})
        years = 'Date not established' if start is None else (('c. ' if approximate else '') + (base.year_label(start) if start == end else base.year_label(start) + '–' + base.year_label(end)))
        records.append({
            'id': 'event-' + qid.lower(), 'sourceId': qid, 'sourceRevision': entity['lastrevid'], 'sourceUrl': 'https://www.wikidata.org/wiki/' + qid,
            'title': title, 'description': override.get('description', description), 'significance': seed['significance'] if seed else '',
            'searchTerms': ' '.join([base.name(entity), seed['title'] if seed else '', *candidate['roots'], *countries]),
            'years': years, 'startYear': start, 'endYear': end, 'approximate': approximate, 'dateBasis': basis,
            'kind': kind, 'topics': topic, 'countries': countries, 'regions': regions,
            'geographyBasis': override.get('geographyBasis', 'Geographic tags are partial. Historical states and present-day locations may both appear; these tags do not represent historical borders or a complete list of participants.'),
            'locations': locations, 'people': people, 'sources': sources, 'connections': [], 'top100': bool(seed),
            'selectionBasis': ('An unranked Artline Top 100 starting point. ' if seed else '') + 'Source-linked research record, awaiting editorial validation. Documentation across Wikimedia projects is a discovery signal, not a definitive ranking of importance.',
            'status': 'review', '_links': candidate['links'], '_roots': candidate['roots'],
        })
    # Breadth first: reserve the editorial 100; then round-robin topic groups,
    # ranking within each by documentation. A single topic cannot fill the
    # selection while other available historical records remain unexplored.
    selected = sorted([r for r in records if r['top100']], key=lambda r: r['id'])
    groups = collections.defaultdict(list)
    for r in sorted(records, key=lambda r: (-r['_links'], r['id'])):
        if not r['top100']: groups[r['topics'][0]].append(r)
    while len(selected) < 10000 and any(groups.values()):
        for topic in sorted(groups):
            if groups[topic] and len(selected) < 10000: selected.append(groups[topic].pop(0))
    selected.sort(key=lambda r: (r['startYear'] if r['startYear'] is not None else 2147483647, r['id']))
    write('selection-evidence.json', [{'id': r['id'], 'sourceId': r['sourceId'], 'revision': r['sourceRevision'], 'sitelinks': r['_links'], 'roots': r['_roots']} for r in selected])
    for row in selected: row.pop('_links'); row.pop('_roots')
    write('events.json', selected)
    write('exclusions.json', exclusions)
    summary = {'cutoff': 2000, 'count': len(selected), 'top100': sum(r['top100'] for r in selected), 'missingTopIdentities': missing, 'eligibleCandidates': len(records),
               'topics': dict(collections.Counter(t for r in selected for t in r['topics'])), 'types': dict(collections.Counter(r['kind'] for r in selected)),
               'undated': sum(r['startYear'] is None for r in selected), 'withCountries': sum(bool(r['countries']) for r in selected), 'withRegions': sum(bool(r['regions']) for r in selected),
               'withDescription': sum(bool(r['description']) for r in selected), 'sha256': hashlib.sha256((OUT / 'events.json').read_bytes()).hexdigest()}
    write('manifest.json', summary)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['candidates', 'fetch', 'seeds', 'compile', 'supplement', 'finish-seeds', 'date-index', 'enrich', 'class-lookups', 'broaden', 'broaden-subclasses'])
    args = parser.parse_args()
    if args.stage == 'candidates': candidates()
    elif args.stage == 'seeds': seeds()
    elif args.stage == 'compile': compile_events()
    elif args.stage == 'supplement': supplement()
    elif args.stage == 'finish-seeds': finish_seeds()
    elif args.stage == 'date-index': date_index()
    elif args.stage == 'enrich': enrich()
    elif args.stage == 'class-lookups': class_lookups()
    elif args.stage == 'broaden': broaden()
    elif args.stage == 'broaden-subclasses': broaden(True)
    else: fetch()
