#!/usr/bin/env python3
"""Capture official Museofile authority records for proposed museum identities."""
import concurrent.futures
import importlib.util
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('primary', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r


def main():
    index = p.Index()
    old = {i['id'] for i in index.institutions}
    claims = r.load(r.RUN / 'primary-plans/joconde-reviewed.json.gz')['claims']
    proposed = {c['institution']['id']: c['institution'] for c in claims if c['institution']['id'] not in old}

    def one(i):
        raw, receipt = r.capture(i['website_url'], tag='museum-authorities')
        soup = BeautifulSoup(raw, 'html.parser')
        for node in soup.select('script, style, nav, footer'):
            node.decompose()
        text = soup.get_text(' ', strip=True)
        possible = []
        for existing in index.institutions:
            host = urlsplit(existing.get('website_url') or '').hostname
            if host and host not in ['pop.culture.gouv.fr', 'www.pop.culture.gouv.fr', 'www.wikidata.org', 'www.wikimedia.org']:
                host = host.removeprefix('www.')
                if len(host) > 7 and host in text:
                    possible.append({'institution_id': existing['id'], 'name': existing['name'], 'website': existing['website_url']})
        result = {'institution': i, 'receipt': receipt, 'text': text,
                  'authority_code_present': i['slug'].split('-')[-1].upper() in text,
                  'existing_website_overlap': possible}
        r.save(r.RUN / 'museum-authority-reviews' / (i['slug'] + '.json'), result)
        time.sleep(0.7)
        return {k: v for k, v in result.items() if k != 'text'}

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(one, proposed.values()))
    r.save(r.RUN / 'french-museum-authority-summary.json', results)
    print('Official museum authorities:', len(results))
    for v in results:
        if v['receipt']['status'] != 200 or not v['authority_code_present'] or v['existing_website_overlap']:
            print(v['institution']['slug'], v['receipt']['status'], v['existing_website_overlap'])


if __name__ == '__main__':
    main()
