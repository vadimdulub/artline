#!/usr/bin/env python3
"""Capture attributed English Wikipedia introductions for a supplied artist roster.

Read-only network research: no database connection, writes or status changes.
Roster fields: slug, authority_id (Wikidata Q ID), rank. Cached source responses
and their URLs/checksums stay in --evidence; --output is the redistributable bundle.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

AGENT = 'ArtlineBiographyResearch/1.0 (https://artlines.org/about)'
LICENSE = 'https://creativecommons.org/licenses/by-sa/4.0/'


def capture(base, params, evidence, key):
    path = evidence / (key + '.json')
    if path.exists():
        return json.loads(path.read_text())['data']
    url = base + '?' + urlencode(params)
    for attempt in range(4):
        try:
            with urlopen(Request(url, headers={'User-Agent': AGENT}), timeout=45) as response:
                raw = response.read()
            data = json.loads(raw)
            if 'error' in data:
                raise ValueError(data['error'])
            path.write_text(json.dumps({'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'sha256': hashlib.sha256(raw).hexdigest(), 'data': data}, ensure_ascii=False, indent=2) + '\n')
            time.sleep(1.1)
            return data
        except HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise
            delay = max(60, int(error.headers.get('Retry-After', '60')))
            print(f'Source rate limit; waiting {delay}s before retrying {key}', flush=True)
            time.sleep(delay)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--roster', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    roster = json.loads(args.roster.read_text())
    assert len({a['slug'] for a in roster}) == len(roster)
    assert all(re.fullmatch(r'Q[1-9][0-9]*', a['authority_id']) for a in roster)
    args.evidence.mkdir(parents=True, exist_ok=True)
    titles, canonical_ids = {}, {}
    for start in range(0, len(roster), 50):
        group = roster[start:start+50]
        data = capture('https://www.wikidata.org/w/api.php', {'action':'wbgetentities', 'format':'json',
            'ids':'|'.join(a['authority_id'] for a in group), 'props':'sitelinks', 'sitefilter':'enwiki', 'maxlag':5}, args.evidence, f'identities-{start:04}')
        for qid, entity in data.get('entities', {}).items():
            canonical_ids[qid] = entity.get('id', qid)
            title = entity.get('sitelinks', {}).get('enwiki', {}).get('title')
            if title:
                titles[qid] = title
        print(f'Identity sources: {min(start+50,len(roster))}/{len(roster)}', flush=True)
    pages = {}
    title_values = list(titles.values())
    for start in range(0, len(title_values), 20):
        data = capture('https://en.wikipedia.org/w/api.php', {'action':'query','format':'json','formatversion':2,
            'titles':'|'.join(title_values[start:start+20]), 'prop':'extracts|pageprops|info|revisions',
            'exintro':1,'explaintext':1,'exlimit':20,'inprop':'url','rvprop':'ids|timestamp','redirects':1,'maxlag':5}, args.evidence, f'introductions-{start:04}')
        for page in data.get('query', {}).get('pages', []):
            qid = page.get('pageprops', {}).get('wikibase_item')
            if qid and 'disambiguation' not in page.get('pageprops', {}):
                pages[qid] = page
        print(f'Biography sources: {min(start+20,len(title_values))}/{len(title_values)}', flush=True)
    # Short leads often contain only a name and dates. Retrieve a bounded opening
    # excerpt from the same identity-checked page, not an invented biography.
    short = [(qid, titles[qid]) for qid in titles if len(pages.get(canonical_ids[qid], {}).get('extract', '')) < 400]
    from concurrent.futures import ThreadPoolExecutor
    def expand(item):
        qid, title = item
        data = capture('https://en.wikipedia.org/w/api.php', {'action':'query','format':'json','formatversion':2,
            'titles':title,'prop':'extracts|pageprops|info|revisions','explaintext':1,'exchars':2600,
            'inprop':'url','rvprop':'ids|timestamp','redirects':1,'maxlag':5}, args.evidence, f'expanded-{qid}')
        for page in data.get('query', {}).get('pages', []):
            if page.get('pageprops', {}).get('wikibase_item') == canonical_ids[qid] and 'disambiguation' not in page.get('pageprops', {}):
                return canonical_ids[qid], page
        return None
    with ThreadPoolExecutor(max_workers=1) as executor:
        for index, result in enumerate(executor.map(expand, short)):
            if result:
                pages[result[0]] = result[1]
            if index % 25 == 0:
                print(f'Expanded short biographies: {index+1}/{len(short)}', flush=True)
    entries, unresolved = {}, []
    for artist in roster:
        qid = artist['authority_id']
        canonical_qid = canonical_ids.get(qid, qid)
        page = pages.get(canonical_qid, {})
        extract = page.get('extract', '').strip()
        extract = re.split(r'(?m)^==+ (?:References|Sources|External links|See also|Gallery|Selected works|Further reading) ==+\s*$', extract)[0]
        extract = re.sub(r'(?m)^==+ .*? ==+\s*$', '', extract).strip()
        if extract.endswith('...') or extract.endswith('…'):
            # Drop the trailing partial sentence introduced by TextExtracts.
            extract = re.sub(r'[^.!?]*[.…]+$', '', extract).strip()
        extract = re.sub(r'\n{3,}', '\n\n', extract)
        revisions = page.get('revisions', [])
        if len(extract) < 80 or not revisions or not page.get('fullurl', '').startswith('https://en.wikipedia.org/wiki/'):
            unresolved.append({'slug':artist['slug'], 'qid':qid, 'rank':artist['rank'], 'reason':'No identity-matched English introduction of at least 80 characters'})
            continue
        entries[artist['slug']] = {'artist_id':artist['id'], 'qid':canonical_qid, 'catalogue_qid':qid, 'rank':artist['rank'], 'title':page['title'], 'text':extract,
            'source_url':page['fullurl'], 'revision_url':f"https://en.wikipedia.org/w/index.php?oldid={revisions[0]['revid']}",
            'revision_id':revisions[0]['revid'], 'revised_at':revisions[0]['timestamp'], 'license_url':LICENSE,
            'attribution':'Wikipedia contributors', 'changes':'Opening excerpt; plain-text formatting, section headings and a trailing partial sentence omitted where applicable. No factual rewriting.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(entries, ensure_ascii=False, indent=2, sort_keys=True)+'\n')
    report = {'requested':len(roster), 'matched':len(entries), 'unresolved':unresolved,
        'license_url':LICENSE, 'identity_policy':'Wikipedia pageprops.wikibase_item matches the catalogue authority ID or its explicit Wikidata entity redirect; both IDs are retained.',
        'publication_policy':'Source-attributed reference text only. Existing artist biography, catalogue facts and publication status remain unchanged.'}
    (args.evidence/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
