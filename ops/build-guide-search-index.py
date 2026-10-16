#!/usr/bin/env python3
"""Refresh Go's guide search projection after editing guide indexes or editions.
Run --check in release validation. This reads editorial JSON only, never the DB.
Deploy this projection with the matching web editions; its digest invalidates cursors.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / 'apps/web/content/articles'
TARGET = ROOT / 'apps/server/internal/guides/index.json'

def generate():
    entries, sources, slugs = [], {}, set()
    def read(p):
        raw = p.read_bytes()
        sources[str(p.relative_to(CONTENT))] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)
    institutions = read(CONTENT / 'museum-guides' / 'institution-links.json')
    for folder, kind in [('artist-guides', 'artist'), ('museum-guides', 'museum')]:
        for item in read(CONTENT / folder / 'index.json'):
            slug = item['slug']
            assert slug not in slugs, slug
            slugs.add(slug)
            if kind == 'museum':
                assert institutions.get(slug), f'Missing museum mapping: {slug}'
            artist = item.get('artist') or {}
            text = [item['title'], item['subtitle'], item['museum'], item['city'], item['country'], artist.get('name', '')]
            for locale in item['locales']:
                edition = read(CONTENT / folder / slug / (locale + '.json'))
                text += [edition.get(k, '') for k in ['title', 'subtitle', 'museum', 'city', 'country']]
                text.append((edition.get('artist') or {}).get('name', ''))
            entries.append(dict(slug=slug, kind=kind, href='/guides/'+slug,
                title=item['title'], label=artist.get('name') or item['museum'],
                location=artist.get('lifeDates') or ', '.join(filter(None, [item['city'], item['country']])),
                subtitle=item['subtitle'], image=item['image'], count=item['count'],
                languages=len(item['locales']), institutions=institutions.get(slug, []) if kind == 'museum' else [], search=' '.join(dict.fromkeys(text))))
    timeline = [read(CONTENT / 'timeline-guide' / (locale + '.json')) for locale in ('en', 'ru', 'it', 'de', 'zh', 'fr', 'es', 'pt', 'ja', 'ar')]
    english = timeline[0]
    timeline_text = []
    for edition in timeline:
        timeline_text += [edition['title'], edition['subtitle'], *edition['introduction']]
        for section in edition['sections']:
            timeline_text += [section['title'], *section['paragraphs']]
    entries.append(dict(slug='art-history-timeline', kind='using', href='/art-history-timeline',
        title=english['title'], label=english['title'], location='Using Artline', subtitle=english['subtitle'],
        image='', count=0, languages=len(timeline), search=' '.join(dict.fromkeys(timeline_text))))
    return json.dumps(dict(sources=sources, entries=entries), ensure_ascii=False, indent=2) + '\n'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    output = generate()
    if args.check:
        if not TARGET.exists() or TARGET.read_text() != output:
            raise SystemExit('Guide search index is stale. Run python3 ops/build-guide-search-index.py and deploy it with the guide editions.')
    else:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        TARGET.write_text(output)
    print(('Verified' if args.check else 'Generated') + ' guide search index: ' + str(len(json.loads(output)['entries'])) + ' guides')
