#!/usr/bin/env python3
"""Apply the second bounded pre-1850 selection using the guarded book workflow."""
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('book_workflow', ROOT / 'ops/expand-pre1850-books-20261001.py')
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)
workflow.OUT = ROOT / 'docs/research/pre1850-books-20261002'
workflow.SELECTION = ROOT / 'ops/curated-pre1850-books-20261002.json'
workflow.BACKUP = Path('/Users/vadimdulub/Library/Application Support/Artline/backups/pre1850-books-20261002')
workflow.research.OUT = workflow.OUT


def capture_extra(url):
    path = workflow.OUT / 'sources' / (hashlib.sha256(url.encode()).hexdigest() + '.html.gz')
    receipt = path.with_suffix('.receipt.json')
    if not path.exists():
        req = urllib.request.Request(url, headers={'User-Agent': 'ArtlineBookResearch/1.0 (selected historical work metadata)'})
        with urllib.request.urlopen(req, timeout=45) as response:
            raw = response.read(8 * 1024 * 1024 + 1)
            assert len(raw) <= 8 * 1024 * 1024
            final_url = response.url
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(raw, mtime=0))
        workflow.save(receipt, {'url': url, 'finalUrl': final_url, 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return json.loads(receipt.read_text())


workflow.extra_source = capture_extra


def prepare():
    already_applied = (workflow.OUT / 'apply-receipt.json').exists()
    workflow.prepare()
    if already_applied:
        return
    plan = json.loads((workflow.OUT / 'plan.json').read_text())
    candidates = json.loads((workflow.OUT / 'candidates.json').read_text())
    selected = {change['record']['sourceId'] for change in plan['changes']}
    for candidate in candidates:
        if candidate['qid'] in selected and candidate.get('fullArticle'):
            plan['sources'].append(candidate['fullArticle']['source'])
    data, proof = workflow.research.capture('en.wikipedia.org', {
        'action': 'query', 'titles': 'The Old Manor House',
        'prop': 'pageprops|categories|revisions', 'ppprop': 'wikibase_item',
        'cllimit': 100, 'rvprop': 'ids|timestamp',
    })
    page = data['query']['pages'][0]
    assert page['pageprops']['wikibase_item'] == 'Q96409526'
    assert any('English-language novels' in c['title'] for c in page['categories'])
    plan['sources'].append(proof)

    # Add sourced biographies only to genuinely new creators. Existing creator
    # records and every book outside this selection remain untouched.
    new_ids = [creator['id'] for creator in plan['newCreators']]
    if new_ids:
        data, proof = workflow.research.capture('www.wikidata.org', {
            'action': 'wbgetentities', 'ids': '|'.join(new_ids),
            'props': 'sitelinks', 'sitefilter': 'enwiki',
        })
        plan['sources'].append(proof)
        titles = [e['sitelinks']['enwiki']['title'] for e in data['entities'].values()
                  if 'enwiki' in e.get('sitelinks', {})]
        if titles:
            data, proof = workflow.research.capture('en.wikipedia.org', {
                'action': 'query', 'titles': '|'.join(titles), 'redirects': 1,
                'prop': 'pageprops|extracts|revisions', 'ppprop': 'wikibase_item',
                'exintro': 1, 'explaintext': 1, 'exlimit': 20, 'rvprop': 'ids|timestamp',
            })
            plan['sources'].append(proof)
            pages = {p.get('pageprops', {}).get('wikibase_item'): p for p in data['query']['pages']}
            for creator in plan['newCreators']:
                page = pages.get(creator['id'])
                if not page or not page.get('extract'):
                    continue
                paragraphs = workflow.excerpt(page['extract'], 'creator')
                if not paragraphs:
                    continue
                revision = page['revisions'][0]['revid']
                creator['record']['overview'] = {
                    'paragraphs': paragraphs,
                    'sourceUrl': 'https://en.wikipedia.org/w/index.php?oldid=' + str(revision),
                    'sourceTitle': page['title'], 'revision': revision,
                    'credit': 'Wikipedia contributors', 'licenseUrl': workflow.LICENSE,
                }
                creator['source_checksum'] = workflow.digest(creator['record'])
    creators = {c['id']: c for c in plan['existingCreators'] + plan['newCreators']}
    for change in plan['changes']:
        assert change['new'], 'This campaign adds missing books only.'
        full = dict(change['record'], creators=[
            dict(creators[link['creator_id']]['record'], credit=link['credit'])
            for link in change['links']
        ])
        change['fullRecord'] = full
        change['sourceChecksum'] = workflow.digest(full)
        projection = change['projection']
        projection['book_checksum'] = change['sourceChecksum']
        projection['projection_checksum'] = workflow.digest({
            k: v for k, v in projection.items() if k != 'projection_checksum'
        })
    plan['sources'] = list({p['path']: p for p in plan['sources']}.values())
    workflow.save(workflow.OUT / 'plan.json', plan)
    workflow.save(workflow.OUT / 'new-books.json', [c['fullRecord'] for c in plan['changes']])
    print('New creator biographies:', sum(bool(c['record'].get('overview')) for c in plan['newCreators']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'apply'])
    args = parser.parse_args()
    if args.stage == 'prepare':
        prepare()
    else:
        workflow.apply()
