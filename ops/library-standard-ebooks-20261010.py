#!/usr/bin/env python3
"""Find exact library editions in the public Standard Ebooks catalogue.

Only public metadata pages and package metadata; no ebook text/bulk feed access.
The authenticated OPDS feed is held, not retried or bypassed.
"""
import argparse
import gzip
import importlib.util
import re
import urllib.parse
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

spec = importlib.util.spec_from_file_location('pictures', __file__.replace('library-standard-ebooks', 'library-pictures'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
RUN = p.RUN / 'standard-ebooks'


def get(url):
    host = urllib.parse.urlsplit(url).hostname
    assert host in ['standardebooks.org', 'raw.githubusercontent.com']
    assert '/honeypot' not in url and '/downloads/' not in url and '/text' not in url and '/feeds/' not in url and '/opds' not in url
    key = p.sha(url.encode())
    path, receipt = RUN / 'captures' / (key + '.body.gz'), RUN / 'captures' / (key + '.json')
    if path.exists():
        proof = p.load(receipt)
        assert p.sha(path.read_bytes()) == proof['archiveSha256']
        return gzip.decompress(path.read_bytes()), proof
    hold = RUN / 'holds' / (host + '.json')
    if hold.exists():
        raise RuntimeError('Provider held: ' + host)
    p.image_core().provider_rate_slot(host)
    r = p.SESSION.get(url, timeout=(15, 60))
    if r.status_code in [401, 403, 429]:
        p.save(hold, {'url': url, 'status': r.status_code, 'at': p.now()})
    r.raise_for_status()
    assert len(r.content) < 2_000_000
    raw = gzip.compress(r.content, mtime=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    proof = {'url': r.url, 'at': p.now(), 'sha256': p.sha(r.content), 'archiveSha256': p.sha(raw), 'path': str(path.relative_to(p.ROOT))}
    p.save(receipt, proof)
    return r.content, proof


def normal(text):
    return ' '.join(re.findall(r'[^\W_]+', text.lower()))


def catalogue():
    get('https://standardebooks.org/robots.txt')
    get('https://standardebooks.org/about')
    p.save(RUN / 'opds-hold.json', {'url': 'https://standardebooks.org/feeds/opds/all', 'status': 401,
        'decision': 'Do not access authenticated feed. Public HTML book pages and catalogue navigation remain independently available.'})
    pending = ['https://standardebooks.org/ebooks']
    seen, entries = set(), {}
    while pending:
        url = pending.pop(0)
        if url in seen:
            continue
        raw, proof = get(url)
        soup = BeautifulSoup(raw, 'html.parser')
        for li in soup.select('li[typeof="schema:Book"]'):
            name, author, img = li.select_one('p:not(.author) [property="schema:name"]'), li.select_one('.author'), li.select_one('img')
            link = li.get('about')
            if not name or not author or not img or not link:
                continue
            page = urllib.parse.urljoin(url, link)
            entries[page] = {'url': page, 'title': name.get_text(' ', strip=True), 'author': author.get_text(' ', strip=True),
                'imageUrl': urllib.parse.urljoin(url, img['src']), 'evidence': proof}
        seen.add(url)
        for a in soup.select('nav.pagination a[href]'):
            href = a['href']
            if re.fullmatch(r'/ebooks\?page=\d+', href):
                next_url = urllib.parse.urljoin(url, href)
                if next_url not in seen and next_url not in pending:
                    pending.append(next_url)
        p.save(RUN / 'catalogue.json.gz', list(entries.values()), immutable=False)
        print('Standard Ebooks public catalogue', len(seen), 'pages', len(entries), 'editions', flush=True)


def matches():
    inventory = [r for r in p.load(p.RUN / 'inventory.json.gz') if r['category'] == 'books' and not r['existing']]
    entities = p.load(p.RUN / 'entities.json.gz')
    bytitle = {}
    for row in inventory:
        names = [row['title']] + [v['value'] for v in (entities.get(row['qid'], {}).get('entity', {}).get('labels') or {}).values()]
        for title in names:
            bytitle.setdefault(normal(title), []).append(row)
    matches, held = [], []
    for edition in p.load(RUN / 'catalogue.json.gz'):
        candidates = {r['id']: r for r in bytitle.get(normal(edition['title']), [])}
        if not candidates:
            continue
        raw, proof = get(edition['url'])
        soup = BeautifulSoup(raw, 'html.parser')
        wikipedia = next((a['href'] for a in soup.select('a[href]') if a.get_text(' ', strip=True) == 'This book at Wikipedia'), None)
        repo = next((a['href'] for a in soup.select('a[href]') if a.get_text(' ', strip=True) == 'This ebook’s source code at GitHub'), None)
        for row in candidates.values():
            entity = entities.get(row['qid'], {}).get('entity', {})
            title = ((entity.get('sitelinks') or {}).get('enwiki') or {}).get('title')
            article = ('https://en.wikipedia.org/wiki/' + title.replace(' ', '_') if title else None) or row.get('articleUrl')
            norm_url = lambda u: urllib.parse.unquote(u or '').replace('_', ' ')
            if not article or norm_url(wikipedia) != norm_url(article):
                held.append({'id': row['id'], 'edition': edition, 'reason': 'article-identity-not-exact', 'article': article, 'editionArticle': wikipedia})
                continue
            if not repo or not repo.startswith('https://github.com/standardebooks/'):
                held.append({'id': row['id'], 'edition': edition, 'reason': 'missing-edition-source-repository'})
                continue
            opf_url = repo.replace('https://github.com/', 'https://raw.githubusercontent.com/') + '/master/src/epub/content.opf'
            opf, opf_proof = get(opf_url)
            document = ET.fromstring(opf)
            metadata = document.find('{http://www.idpf.org/2007/opf}metadata')
            artist = next((e.text for e in metadata if e.attrib.get('id') == 'artist'), None)
            artist_url = next((e.attrib['href'] for e in metadata if e.attrib.get('refines') == '#artist' and 'en.wikipedia.org/' in e.attrib.get('href', '')), None)
            rights = next((e.text for e in metadata if e.tag.endswith('}rights')), None)
            assert rights and 'CC0 1.0' in rights
            matches.append({'category': 'books', 'id': row['id'], 'qid': row['qid'], 'title': row['title'], 'edition': edition,
                'wikipedia': wikipedia, 'sourceEvidence': proof, 'metadataEvidence': opf_proof,
                'coverArtist': artist, 'coverArtistUrl': artist_url, 'rightsStatement': rights,
                'identityBasis': 'Exact work article URL linked by both the catalogue identity and publisher edition page; title also matches a retained work label.',
                'decision': 'underlying-artwork-rights-review-pending'})
        p.save(RUN / 'matches.json.gz', matches, immutable=False)
        p.save(RUN / 'holds.json.gz', held, immutable=False)
        print('Exact publisher editions', len(matches), 'held identities', len(held), flush=True)
    p.save(RUN / 'matches.json.gz', matches, immutable=False)
    p.save(RUN / 'holds.json.gz', held, immutable=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['catalogue', 'matches'])
    args = parser.parse_args()
    globals()[args.phase]()
