#!/usr/bin/env python3
"""Refresh the local, record-by-record picture coverage ledger."""
import collections
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('pictures', Path(__file__).with_name('library-pictures-20261010.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

inventory = p.load(p.RUN / 'inventory.json.gz')
selected_path = p.RUN / 'selected-local.json.gz'
selected = {r['id']: r for r in p.load(selected_path)} if selected_path.exists() else {}
proposals = {r['id']: r for r in p.load(p.RUN / 'proposals.json.gz')}
prepared, rejected = {}, collections.defaultdict(list)
for directory in (p.RUN / 'delivery').iterdir():
    if not directory.is_dir():
        continue
    for path in (directory / 'prepared').glob('*.json'):
        r = p.load(path)
        prepared[r['id']] = {'batch': directory.name, 'path': r['path'], 'sha256': r['sha256'], 'sourceUrl': r['sourceMetadata']['sourceUrl']}
    for path in (directory / 'visual-reviews').glob('*.json'):
        for r in p.load(path)['rejected']:
            rejected[r['id']].append({'batch': directory.name, 'file': r['file'], 'reason': r['reason'], 'evidence': str(path.relative_to(p.ROOT))})
post = p.RUN / 'post-review-holds.json'
if post.exists():
    for r in p.load(post):
        rejected[r['id']].append(r)
ledger = []
for row in inventory:
    image = row['existing']
    state = 'existing-picture-preserved' if image else 'unresolved'
    if row['id'] in selected:
        image, state = selected[row['id']]['entry'], 'added-to-local-manifest'
    elif not image and row['id'] in prepared:
        state = 'prepared-awaiting-review' if not rejected[row['id']] else 'prepared-held'
    elif not image and row['id'] in proposals:
        state = 'source-eligible-awaiting-preparation-and-review'
    ledger.append({k: row[k] for k in ['category', 'id', 'qid', 'title', 'author', 'startYear', 'endYear']} | {
        'pictureState': state, 'selectedPicture': image, 'localSelectionEvidence': selected.get(row['id']),
        'prepared': prepared.get(row['id']), 'holds': rejected[row['id']],
        'candidateFile': proposals.get(row['id'], {}).get('file'),
        'candidateSource': proposals.get(row['id'], {}).get('reviewed', {}).get('sourceUrl')})
p.save(p.RUN / 'picture-coverage-index.json.gz', ledger, immutable=False)
summary = {'at': p.now(), 'records': len(ledger), 'databaseMode': 'Read-only local and production inventory',
    'delivery': 'Local files and embedded manifests only; no deployment or production database mutation.',
    'categories': {cat: dict(collections.Counter(r['pictureState'] for r in ledger if r['category'] == cat)) for cat in ['books', 'events']},
    'newImageKinds': dict(collections.Counter((r.get('visualKind') or 'individually-captioned') for r in selected.values())),
    'preparedDerivatives': len(prepared), 'recordsWithHeldCandidates': len([v for v in rejected.values() if v])}
p.save(p.RUN / 'coverage-summary.json', summary, immutable=False)
lines = ['# Library pictures — 10 October 2026', '',
    'The user requested a picture for every book and event, preferred usable covers or recognisable related images, and authorised continued research rounds without approval prompts.', '',
    '**Work in progress.** This directory retains discovery, source evidence, rights decisions, visual reviews and local delivery. A candidate is not an accepted image. Existing selections are preserved. Database access remains read-only; new pictures are attached through Artline’s existing versioned image manifests.', '',
    '| Catalogue | Existing pictures | New local pictures | Other records |', '|---|---:|---:|---:|']
for cat in ['books', 'events']:
    c = summary['categories'][cat]
    old, new = c.get('existing-picture-preserved', 0), c.get('added-to-local-manifest', 0)
    total = sum(c.values())
    lines.append(f'| {cat.title()} | {old:,} | {new:,} | {total-old-new:,} |')
lines += ['', 'Updated: ' + summary['at'], '',
    '- `picture-coverage-index.json.gz`: one record for each of the 20,162 active books and events, including selected picture, source link, preparation state and unresolved evidence.',
    '- `coverage-summary.json`: current counts. `selected-local.json.gz`: exact new manifest entries and visual-review receipts.',
    '- `delivery/`: immutable drafts, prepared-file hashes, contact-sheet review decisions and per-file errors. Author images are reused only for the same verified creator and identical reviewed image bytes; captions identify them as author images.',
    '- `standard-ebooks/`: exact edition identity, CC0 cover-design statement, underlying artwork/source evidence and separate territorial/artist-term checks.',
    '- `captures/`: retained source responses with retrieval receipts and SHA-256 hashes. Search results and imported Wikidata claims remain discovery evidence until reviewed.',
    '- `next-article-*` and `search-*`: additional source rounds for unresolved records. A search hit never establishes identity by itself.', '',
    'Images preserve the full supplied frame and are proportionally resized/JPEG-compressed to at most 100,000 bytes. Source originals and backups live under `~/Library/Application Support/Artline/`, outside Documents. Original catalogue dates, statuses, creator links and existing images are not rewritten.', '',
    'New local selections need the normal web/API release before they appear on production. No commit or deployment has been performed by this campaign.']
(p.RUN / 'README.md').write_text('\n'.join(lines) + '\n')
print(json.dumps(summary, ensure_ascii=False))
