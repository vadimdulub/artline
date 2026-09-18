#!/usr/bin/env python3
"""Fetch bounded Wikipedia introductions and prepare evidence-backed descriptions.

Read-only research: this script never writes a database. Source responses are
cached, identities checked, and every fallback is explicitly attributed.
"""
import argparse
import collections
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / 'docs/research/historical-events-20260917'
OUT = ROOT / 'docs/research/event-descriptions-20260918'
API = 'https://en.wikipedia.org/w/api.php'
CCBYSA = 'https://creativecommons.org/licenses/by-sa/4.0/'
CC0 = 'https://creativecommons.org/publicdomain/zero/1.0/'


def write(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def records():
    return json.loads((ORIGINAL / 'events.json').read_text())


def wiki_title(record):
    for source in record['sources']:
        url = urllib.parse.urlparse(source['url'])
        if url.hostname == 'en.wikipedia.org' and url.path.startswith('/wiki/'):
            return urllib.parse.unquote(url.path[6:]).replace('_', ' ')


def request(titles):
    params = {'action': 'query', 'format': 'json', 'formatversion': 2,
              'prop': 'extracts|info|pageprops', 'exintro': 1, 'explaintext': 1,
              'exchars': 1000, 'exlimit': 20, 'inprop': 'url',
              'ppprop': 'wikibase_item|disambiguation', 'redirects': 1,
              'maxlag': 5, 'titles': '|'.join(titles)}
    key = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:20]
    path = OUT / 'sources' / (key + '.json.gz')
    if path.exists():
        return json.loads(gzip.decompress(path.read_bytes()))
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(6):
        delay = min(60 * (attempt + 1), 300)
        try:
            req = urllib.request.Request(API + '?' + urllib.parse.urlencode(params), headers={
                'User-Agent': 'ArtlineEventsResearch/1.0 (+https://github.com/vadimdulub; local review metadata)',
                'Accept': 'application/json', 'Accept-Encoding': 'gzip'})
            with urllib.request.urlopen(req, timeout=45) as response:
                raw = response.read()
                if response.headers.get('Content-Encoding') == 'gzip': raw = gzip.decompress(raw)
            data = json.loads(raw)
            if 'error' in data: raise ValueError(str(data['error']))
            if 'continue' in data: raise ValueError('Unexpected continuation: keep batches bounded to 20 extracts')
            result = {'retrievedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      'request': params, 'response': data}
            path.write_bytes(gzip.compress(json.dumps(result, ensure_ascii=False).encode(), mtime=0))
            time.sleep(.8)
            return result
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            if isinstance(error, urllib.error.HTTPError):
                retry = error.headers.get('Retry-After', '')
                if retry.isdigit(): delay = max(delay, int(retry))
            print(f'Wikipedia batch {key}: retry {attempt + 1}: {error}', flush=True)
            if attempt == 5: raise
            time.sleep(delay)


def fetch():
    rows = sorted(records(), key=lambda r: (not r['top100'], r['id']))
    titles = list(dict.fromkeys(t for r in rows if (t := wiki_title(r))))
    for offset in range(0, len(titles), 20):
        request(titles[offset:offset + 20])
        if offset % 200 == 0 or offset + 20 >= len(titles):
            print(f'Wikipedia introductions: {min(offset + 20, len(titles))}/{len(titles)}', flush=True)


def short_intro(raw):
    text = re.sub(r'\s+', ' ', raw).strip()
    if not text: return ''
    # Keep at most two complete opening sentences. Do not split initials,
    # decimals or common abbreviations; preserve the source's wording.
    stops = []
    for match in re.finditer(r'[.!?](?:[”\"\u2019])?(?=\s+[A-Z0-9“\"\u2018]|$)', text):
        before = text[:match.end()]
        if any(before.count(opening) > before.count(closing) for opening, closing in [('(', ')'), ('[', ']'), ('（', '）')]): continue
        if re.search(r'\b(?:[A-Z]|St|Dr|Mr|Mrs|Ms|Prof|Jr|Sr|No|Mt|c|ca)\.$', before): continue
        if before.endswith('...'): continue
        stops.append(match.end())
    usable = [end for end in stops if end <= 850]
    if usable:
        end = usable[min(1, len(usable) - 1)]
        return text[:end]
    if len(text) <= 850 and not text.endswith('...'): return text
    return text[:800].rsplit(' ', 1)[0].rstrip(' ,;:') + '…'


def cached_pages():
    pages = {}
    for path in sorted((OUT / 'sources').glob('*.json.gz')):
        cached = json.loads(gzip.decompress(path.read_bytes()))
        query = cached['response'].get('query', {})
        by_title = {p['title']: p for p in query.get('pages', [])}
        aliases = {r['from']: r['to'] for group in ['normalized', 'redirects'] for r in query.get(group, [])}
        for title in cached['request']['titles'].split('|'):
            resolved, seen = title, set()
            while resolved in aliases and resolved not in seen:
                seen.add(resolved); resolved = aliases[resolved]
            if resolved in by_title: pages[title] = (by_title[resolved], cached['retrievedAt'], str(path.relative_to(OUT)))
    return pages


def metadata_description(record, evidence):
    if record['description'].strip():
        text = record['description'].strip()
        text = text[0].upper() + text[1:]
        return text if text.endswith(('.', '!', '?')) else text + '.'
    classes = evidence['roots']
    # These are source classifications, not inferred historical narratives.
    preferred = ['Archaeological culture', 'Peace treaty', 'Treaty', 'Constitution',
                 'Declaration of independence', 'Empire', 'Historical period',
                 'Art movement', 'Religious movement', 'Political movement',
                 'Social movement', 'Massacre', 'Genocide', 'Revolution', 'Rebellion',
                 "Coup d'état", 'Siege', 'Battle', 'Military campaign', 'War',
                 'Earthquake', 'Volcanic eruption', 'Flood', 'Epidemic', 'Pandemic',
                 'Famine', 'Expedition', 'Space mission', 'Strike action', 'Protest']
    label = next((c.lower() for c in preferred if c in classes), record['kind'].lower())
    article = 'an' if label[0] in 'aeiou' else 'a'
    return f"{record['title']} is recorded as {article} {label}. The source dates it to {record['years']}."


def compile_descriptions():
    requested = set()
    for path in (OUT / 'sources').glob('*.json.gz'):
        cached = json.loads(gzip.decompress(path.read_bytes()))
        requested.update(cached['request']['titles'].split('|'))
    expected = {title for record in records() if (title := wiki_title(record))}
    if expected - requested:
        raise RuntimeError(f'Finish fetching introductions first: {len(expected - requested)} article titles remain')
    pages = cached_pages()
    selection = {r['id']: r for r in json.loads((ORIGINAL / 'selection-evidence.json').read_text())}
    corrections = json.loads((ORIGINAL / 'top-corrections.json').read_text())
    curated = {v['description'] for v in corrections.values() if v.get('description')}
    updates, issues = [], []
    for record in records():
        title = wiki_title(record)
        match = pages.get(title)
        text, source = '', None
        if record['description'] in curated:
            # Preserve carefully sourced corrections to narrower event identities,
            # such as Sputnik's launch, and context about Indigenous societies.
            text = record['description']
            primary = next(s for s in record['sources'] if 'wikipedia.org' not in s['url'])
            source = {'name': primary['name'], 'url': primary['url'], 'kind': 'editorial',
                      'notice': 'Artline description based on the linked source.'}
        elif match:
            page, retrieved, evidence_file = match
            props = page.get('pageprops', {})
            if page.get('ns') != 0 or 'disambiguation' in props or props.get('wikibase_item') != record['sourceId']:
                issues.append({'id': record['id'], 'reason': 'Article identity is not an exact match', 'article': page.get('title'), 'wikibaseItem': props.get('wikibase_item')})
            else:
                extract = page.get('extract', '')
                # A list-navigation sentence is not a description of the event.
                text = '' if re.match(r'^(The following is a list|This is a list)', extract) else short_intro(extract)
                if text:
                    source = {'name': 'Wikipedia', 'url': page['canonicalurl'], 'kind': 'wikipedia',
                              'title': page['title'], 'revision': page['lastrevid'], 'retrievedAt': retrieved,
                              'license': 'CC BY-SA 4.0', 'licenseUrl': CCBYSA,
                              'notice': 'Wikipedia contributors · Opening excerpt, shortened and spacing normalised.',
                              'evidenceFile': evidence_file}
                else: issues.append({'id': record['id'], 'reason': 'No usable introduction', 'article': page.get('title')})
        elif title:
            issues.append({'id': record['id'], 'reason': 'Article missing from the API result', 'article': title})
        if not text:
            text = metadata_description(record, selection[record['id']])
            source = {'name': 'Wikidata', 'url': record['sourceUrl'], 'kind': 'wikidata',
                      'revision': record['sourceRevision'], 'license': 'CC0', 'licenseUrl': CC0,
                      'notice': 'Wikidata description.' if record['description'] else 'Description assembled from recorded Wikidata classification and dates.'}
        updates.append({'id': record['id'], 'previousDescription': record['description'], 'description': text, 'source': source})
    write('descriptions.json', updates)
    write('issues.json', issues)
    stats = {'count': len(updates), 'sources': dict(collections.Counter(r['source']['kind'] for r in updates)),
             'empty': sum(not r['description'].strip() for r in updates), 'maxLength': max(len(r['description']) for r in updates),
             'issues': len(issues), 'sha256': hashlib.sha256((OUT / 'descriptions.json').read_bytes()).hexdigest()}
    write('manifest.json', stats)
    print(json.dumps(stats, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['fetch', 'compile'])
    args = parser.parse_args()
    fetch() if args.stage == 'fetch' else compile_descriptions()
