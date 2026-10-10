#!/usr/bin/env python3
"""Prepare source-cleared library images; merge only explicit visual selections."""
import argparse
import collections
import gzip
import importlib.util
import io
import json
from pathlib import Path
import re
import time
import urllib.parse

from PIL import Image, ImageDraw, ImageOps

spec = importlib.util.spec_from_file_location('pictures', Path(__file__).with_name('library-pictures-20261010.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
SHEETS = Path('/tmp/artline-library-picture-review-20261010')
STAGED = p.DATA / 'prepared-images/library-pictures-20261010'


def staged_path(prepared):
    relative = Path(prepared['path']).relative_to('apps/web/public')
    assert relative.parts[0] == 'images' and relative.parts[1] in ['books', 'events']
    assert relative.parts[2].startswith('selected-20261010')
    return STAGED / relative


def asset_path(prepared):
    public = p.ROOT / prepared['path']
    return public if public.exists() else staged_path(prepared)


def stage_unselected():
    """Keep campaign files outside public delivery until actually selected."""
    selected = {r['imageUrl'] for manifest in p.MANIFESTS.values() for r in p.load(manifest)}
    moved = []
    for receipt in (p.RUN / 'delivery').glob('*/prepared/*.json'):
        prepared = p.load(receipt)
        public = p.ROOT / prepared['path']
        if prepared['imageUrl'] in selected or not public.exists():
            continue
        raw = public.read_bytes()
        assert p.sha(raw) == prepared['sha256']
        target = staged_path(prepared)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.read_bytes() == raw
        else:
            target.write_bytes(raw)
        public.unlink()
        moved.append({'id': prepared['id'], 'from': prepared['path'], 'to': str(target), 'sha256': prepared['sha256']})
    p.save(p.RUN / 'delivery-staging' / (p.now().replace(':', '-') + '.json'), {'at': p.now(), 'moved': moved})
    print('Unselected campaign assets moved to private staging:', len(moved), flush=True)


def draft(batch, category, min_words, kind='all', promote_authors=False):
    directory = p.RUN / 'delivery' / batch
    rows = [r for r in p.load(p.RUN / 'proposals.json.gz') if r['category'] == category and r['identityWordMatches'] >= min_words]
    if kind != 'all':
        rows = [r for r in rows if (r.get('property') == 'author-portrait') == (kind == 'author')]
    used = set()
    for path in (p.RUN / 'delivery').glob('*/draft.json.gz'):
        if path.parent != directory:
            used.update((r['category'], r['id']) for r in p.load(path) if not (promote_authors and r.get('property') == 'author-portrait'))
    rows = [r for r in rows if (r['category'], r['id']) not in used]
    p.save(directory / 'draft.json.gz', rows)
    p.save(directory / 'draft-pin.json', {'sha256': p.sha((directory / 'draft.json.gz').read_bytes()), 'count': len(rows),
        'status': 'Selected for preparation and review; not accepted for application yet.'})
    print('Draft', batch, len(rows), flush=True)


def publisher_draft(batch, promote_authors=False):
    directory = p.RUN / 'delivery' / batch
    used = set()
    for path in (p.RUN / 'delivery').glob('*/draft.json.gz'):
        if path.parent != directory:
            used.update(r['id'] for r in p.load(path) if not (promote_authors and r.get('property') == 'author-portrait'))
    rows = []
    qualified = p.RUN / 'standard-ebooks/publisher-qualified.json.gz'
    sourcepath = qualified if qualified.exists() else p.RUN / 'standard-ebooks/rights-selected.json.gz'
    for source in p.load(sourcepath):
        if source['id'] in used:
            continue
        edition = source['edition']
        artist = source.get('coverArtist') or source.get('artworkEvidence', {}).get('metadata', {}).get('Artist', '').split('(', 1)[0].strip()
        assert artist, 'Publisher artwork credit is required'
        rows.append(source | {'file': edition['title'] + ' — Standard Ebooks cover', 'property': 'publisher-edition-cover',
            'proposedLabel': 'Modern edition cover · Standard Ebooks', 'identityWordMatches': 1,
            'reviewed': {'sourceImageUrl': edition['imageUrl'], 'sourceUrl': edition['url'], 'license': 'CC0',
                'licenseUrl': 'https://creativecommons.org/publicdomain/zero/1.0/', 'date': '',
                'credit': 'Cover design: Standard Ebooks; artwork: ' + artist,
                'description': edition['title'] + ' by ' + edition['author'],
                'rightsBasis': source['rightsBasis'], 'rightsStatement': source['rightsStatement']}})
    p.save(directory / 'draft.json.gz', rows)
    p.save(directory / 'draft-pin.json', {'sha256': p.sha((directory / 'draft.json.gz').read_bytes()), 'count': len(rows),
        'status': 'Publisher identity and design/source artwork rights checked; pending visual review.'})
    print('Publisher draft', batch, len(rows), flush=True)


def search_draft(batch, category, limit):
    """Select promising search leads for actual visual identity review only."""
    directory = p.RUN / 'delivery' / batch
    used = set()
    for path in (p.RUN / 'delivery').glob('*/draft.json.gz'):
        if path.parent != directory:
            used.update(r['id'] for r in p.load(path) if r.get('property') != 'author-portrait')
    metadata = p.load(p.RUN / 'search-commons-index.json.gz')
    grouped = collections.defaultdict(list)
    for row in p.load(p.RUN / 'search-candidates.json.gz'):
        if row['category'] != category or row['id'] in used:
            continue
        reviewed, reason = p.source_review(row, metadata.get(row['file'], {}))
        if not reviewed:
            continue
        name = p.words(row['title'])
        text = p.words(row['file'] + ' ' + reviewed['description'])
        common = len(name & text)
        if common < 2 or common / max(1, len(name)) < .7:
            continue
        cover = bool(re.search(r'cover|title.?page|frontispiece|titelblatt|обложк|титульн', row['file'] + ' ' + reviewed['description'], re.I))
        grouped[row['id']].append(row | {'reviewed': reviewed, 'metadataProvider': 'search',
            'identityWordMatches': common, 'rankScore': common + 4 * cover,
            'identityBasis': 'Commons search lead; retained catalogue title, source description and displayed cover/page or historical image compared during visual review. Search ranking alone is not identity evidence.',
            'proposedLabel': 'Search lead · identity review required', 'visualReview': 'pending'})
    rows = [max(group, key=lambda r:r['rankScore']) for group in grouped.values()][:limit]
    p.save(directory / 'draft.json.gz', rows)
    p.save(directory / 'draft-pin.json', {'sha256': p.sha((directory / 'draft.json.gz').read_bytes()), 'count': len(rows),
        'status': 'Search leads selected for preparation only; identity and visual acceptance still required.'})
    print('Search draft', batch, len(rows), flush=True)


def author_search_draft(batch, limit):
    """Prepare alternative creator images only where no usable image is reserved."""
    directory = p.RUN / 'delivery' / batch
    selected = {r['id'] for r in p.load(p.RUN / 'selected-local.json.gz')}
    links = {(r['book_id'], r['creator_id']): r for r in p.load(p.RUN / 'creator-links.json.gz') if r['position'] == 0}
    metadata = p.load(p.RUN / 'author-search-commons-index.json.gz')
    commons = p.load(p.RUN / 'commons-index.json.gz')
    rejected_files, prior = set(), []
    for path in (p.RUN / 'delivery').glob('*/draft.json.gz'):
        rows = p.load(path)
        prior.extend(rows)
        for review in (path.parent / 'visual-reviews').glob('*.json'):
            for item in p.load(review)['rejected']:
                row = rows[item['index']]
                if row.get('property') == 'author-portrait':
                    rejected_files.add((row['creatorId'], row['file']))
    reserved = set(selected)
    for row in prior:
        if row.get('property') != 'author-portrait':
            continue
        if (row['creatorId'], row['file']) in rejected_files:
            continue
        source = metadata if row.get('metadataProvider') == 'author-search' else commons
        if p.source_review(row, source.get(row['file'], {}))[0]:
            reserved.add(row['id'])
    grouped = collections.defaultdict(list)
    for row in p.load(p.RUN / 'author-search-candidates.json.gz'):
        if row['id'] in reserved or (row['creatorId'], row['file']) in rejected_files:
            continue
        link = links.get((row['id'], row['creatorId']))
        if not link:
            continue
        reviewed, reason = p.source_review(row, metadata.get(row['file'], {}))
        if not reviewed:
            continue
        names = p.words(row['creatorName'])
        text = p.words(row['file'] + ' ' + reviewed['description'])
        common = len(names & text)
        if common < min(2, len(names)) or common / max(1, len(names)) < .6:
            continue
        portrait = bool(re.search(r'portrait|porträt|портрет|bust|retratu|ritratto', row['file'] + ' ' + reviewed['description'], re.I))
        grouped[row['id']].append(row | {'reviewed': reviewed, 'metadataProvider': 'author-search',
            'creatorLink': link, 'identityWordMatches': common, 'rankScore': common + 3 * portrait,
            'proposedLabel': 'Author image search lead: ' + row['creatorName'], 'visualReview': 'pending'})
    rows = [max(group, key=lambda r: r['rankScore']) for group in grouped.values()][:limit]
    p.save(directory / 'draft.json.gz', rows)
    p.save(directory / 'draft-pin.json', {'sha256': p.sha((directory / 'draft.json.gz').read_bytes()), 'count': len(rows),
        'status': 'Alternative author images await visual identity and reuse review; existing selections are excluded.'})
    print('Author search draft', batch, len(rows), flush=True)


def picture(url):
    core = p.image_core()
    key = p.sha(url.encode())
    original = p.ORIGINALS / (key + '.source')
    receipt = original.with_suffix('.json')
    host = urllib.parse.urlsplit(url).hostname
    assert host in ['upload.wikimedia.org', 'thumb.wikimedia.org', 'standardebooks.org']
    if original.exists():
        evidence = p.load(receipt)
        assert evidence['url'] == url and p.sha(original.read_bytes()) == evidence['sha256']
        return original.read_bytes(), evidence
    hold = p.RUN / 'image-host-holds' / (host + '.json')
    if hold.exists():
        raise RuntimeError('Image host held: ' + host)
    core.provider_rate_slot(host)
    with p.SESSION.get(url, stream=True, timeout=(15, 45)) as response:
        if response.status_code in [401, 403, 429]:
            p.save(hold, {'url': url, 'status': response.status_code, 'at': p.now(), 'retryAfter': response.headers.get('Retry-After')})
            if response.status_code == 429:
                core.provider_rate_slot(host, cooldown=core.retry_delay(response.headers.get('Retry-After')))
        response.raise_for_status()
        assert urllib.parse.urlsplit(response.url).hostname in ['upload.wikimedia.org', 'thumb.wikimedia.org', 'standardebooks.org']
        buffer = bytearray()
        for chunk in response.iter_content(65536):
            buffer.extend(chunk)
            assert len(buffer) <= 20_000_000, 'Source image exceeds selected preview budget'
        raw = bytes(buffer)
        assert response.headers.get('Content-Type', '').startswith('image/')
    image = Image.open(io.BytesIO(raw))
    assert image.width * image.height <= 40_000_000 and image.width >= 80 and image.height >= 80
    image.verify()
    evidence = {'url': url, 'finalUrl': response.url, 'sha256': p.sha(raw), 'bytes': len(raw), 'at': p.now(), 'path': str(original)}
    original.parent.mkdir(parents=True, exist_ok=True)
    original.write_bytes(raw)
    p.save(receipt, evidence)
    return raw, evidence


def sheet(batch, rows, number):
    path = SHEETS / batch / (f'{number:04d}.jpg')
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas = Image.new('RGB', (1200, ((len(rows) + 4) // 5) * 240), '#eeeeea')
    draw = ImageDraw.Draw(canvas)
    for n, row in enumerate(rows):
        im = Image.open(asset_path(row))
        im.thumbnail((224, 174))
        x, y = (n % 5) * 240, (n // 5) * 240
        canvas.paste(im, (x + (240 - im.width) // 2, y))
        for offset, text in [(177, str(row['index']) + ' ' + row['id']), (192, row['title'][:36]), (207, row['file'][:36]), (222, row['label'][:36])]:
            draw.text((x + 5, y + offset), text, fill='#111111')
    canvas.save(path, 'JPEG', quality=90)
    p.save(path.with_suffix('.json'), [{'index': r['index'], 'id': r['id'], 'sha256': r['sha256'], 'file': r['file']} for r in rows], immutable=False)


def has_transparency(raw):
    with Image.open(io.BytesIO(raw)) as im:
        if im.mode not in ['RGBA', 'LA'] and 'transparency' not in im.info:
            return False
        return im.convert('RGBA').getchannel('A').getextrema()[0] < 255


def compress_picture(raw):
    transparent = has_transparency(raw)
    if transparent:
        with Image.open(io.BytesIO(raw)) as opened:
            im = ImageOps.exif_transpose(opened).convert('RGBA')
            background = Image.new('RGBA', im.size, 'white')
            background.alpha_composite(im)
            buffer = io.BytesIO()
            background.convert('RGB').save(buffer, 'PNG')
            raw = buffer.getvalue()
    return (*p.image_core().compress(raw), transparent)


def prepare(batch):
    directory = p.RUN / 'delivery' / batch
    pin = p.load(directory / 'draft-pin.json')
    assert p.sha((directory / 'draft.json.gz').read_bytes()) == pin['sha256']
    rows = p.load(directory / 'draft.json.gz')
    ready = []
    author_batch = bool(rows) and all(r.get('property') == 'author-portrait' for r in rows)
    def review_rows():
        if not author_batch:
            return ready
        unique = {}
        for prepared in ready:
            source = rows[prepared['index']]
            unique.setdefault((source['creatorId'], prepared['sha256']), prepared)
        return list(unique.values())
    rendered_count = 0
    for index, row in enumerate(rows):
        if re.search(r'child sexual abuse|erotic activities involving children|sexual exploitation of children', row.get('reviewed', {}).get('categories', ''), re.I):
            continue
        receipt = directory / 'prepared' / (row['id'] + '.json')
        if receipt.exists():
            ready.append(p.load(receipt))
            continue
        errorpath = directory / 'errors' / (row['id'] + '.json')
        if errorpath.exists():
            continue
        try:
            metadata = row['reviewed']
            raw, original = picture(metadata['sourceImageUrl'])
            jpeg, width, height, quality, transparent = compress_picture(raw)
            assert len(jpeg) <= 100000
            relative = f"/images/{row['category']}/selected-20261010-{batch}/{row['id']}.jpg"
            publicpath = p.ROOT / 'apps/web/public' / relative.lstrip('/')
            path = STAGED / relative.lstrip('/')
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                assert path.read_bytes() == jpeg, 'Do not overwrite another image'
            else:
                path.write_bytes(jpeg)
            result = {'index': index, 'category': row['category'], 'id': row['id'], 'qid': row['qid'], 'title': row['title'],
                'file': row['file'], 'label': row['proposedLabel'], 'imageUrl': relative, 'path': str(publicpath.relative_to(p.ROOT)),
                'sha256': p.sha(jpeg), 'width': width, 'height': height, 'bytes': len(jpeg), 'quality': quality,
                'original': original, 'sourceMetadata': metadata, 'draftSha256': pin['sha256'],
                'transformation': 'Full supplied frame; EXIF orientation, proportional resizing and JPEG compression. No crop.' + (' Transparent pixels composited on white.' if transparent else ''),
                'transparentPixelsCompositedOnWhite': transparent,
                'visualReview': 'pending'}
            p.save(receipt, result)
            ready.append(result)
        except Exception as error:
            p.save(errorpath, {'index': index, 'id': row['id'], 'file': row['file'], 'error': str(error), 'at': p.now()})
            if any((p.RUN / 'image-host-holds').glob('*.json')):
                print('Image provider access hold; preparation paused', flush=True)
                break
        reviewable = review_rows()
        if len(reviewable) and len(reviewable) % 40 == 0 and len(reviewable) > rendered_count:
            sheet(batch, reviewable[-40:], (len(reviewable) - 1) // 40)
            rendered_count = len(reviewable)
        if index % 20 == 0:
            print('Prepared', batch, index + 1, '/', len(rows), 'ready', len(ready), flush=True)
    reviewable = review_rows()
    for offset in range(0, len(reviewable), 40):
        sheet(batch, reviewable[offset:offset + 40], offset // 40)
    p.save(directory / 'prepared-summary.json', {'draft': len(rows), 'prepared': len(ready), 'errors': len(list((directory / 'errors').glob('*.json'))), 'at': p.now()}, immutable=False)
    print('Preparation finished', batch, len(ready), '/', len(rows), flush=True)


def review_sheet(batch, number, kinds, held=None, overrides=None):
    """Persist the operator's actual contact-sheet inspection, never auto-approve.

    One manually supplied image-kind code per displayed image. Ambiguous identity
    and composite-rights cases must be held; captions may be explicitly refined.
    """
    held, overrides = held or {}, overrides or {}
    path = SHEETS / batch / (f'{number:04d}.jpg')
    displayed = p.load(path.with_suffix('.json'))
    kinds = ''.join(kinds.split())
    assert len(kinds) == len(displayed), (len(kinds), len(displayed))
    directory = p.RUN / 'delivery' / batch
    draft = p.load(directory / 'draft.json.gz')
    inventory = {(r['category'], r['id']): r for r in p.load(p.RUN / 'inventory.json.gz')}
    descriptions = {'M': 'Map associated with the event', 'S': 'Later view of the associated site',
        'A': 'Associated artifact · museum photograph', 'L': 'Movement emblem', 'D': 'Historical document',
        'P': 'Photograph associated with the event', 'T': 'Painted depiction', 'E': 'Printed depiction',
        'H': 'Historical photograph', 'R': 'Portrait of an associated person', 'G': 'Diagram illustrating the topic',
        'F': 'Flag or emblem', 'V': 'Later view of a related building or monument',
        'B': 'Edition cover', 'J': 'Title page', 'I': 'Illustration associated with the book',
        'W': 'Manuscript or printed page', 'X': 'Held for further review'}
    accepted, rejected = [], []
    for item, kind in zip(displayed, kinds):
        assert kind in descriptions
        index = item['index']
        row = draft[index]
        assert row['id'] == item['id']
        prepared = p.load(directory / 'prepared' / (row['id'] + '.json'))
        assert item['sha256'] == prepared['sha256'] == p.sha(asset_path(prepared).read_bytes())
        if index in held or kind == 'X':
            rejected.append(item | {'reason': held.get(index, 'Identity or reuse terms require further review.')})
            continue
        label = descriptions[kind]
        # Commons dates can describe a photograph/upload, rather than the
        # depicted artwork. Only explicit reviewed captions add chronology.
        if row.get('property') == 'author-portrait':
            assert kind in ['R', 'H', 'P', 'T', 'E']
            label = 'Author portrait: ' + row['creatorName']
        if row.get('property') == 'publisher-edition-cover':
            assert kind == 'B'
            label = 'Modern edition cover · Standard Ebooks'
        label = overrides.get(index, label)
        identity_basis = row.get('identityBasis')
        if row.get('property') == 'curated-event-context':
            identity_basis = 'Curated event context from the retained event record and source article; subject, period and image relationship checked during visual review. The image is labelled as contextual where it is not a direct depiction.'
        accepted.append(item | {'label': label, 'visualKind': kind,
            'identityBasis': identity_basis or 'Exact retained work/event image claim or identity-checked source article, plus file description, inspected against the rendered image. Image type is labelled without changing catalogue dates.'})
    p.save(directory / 'visual-reviews' / (f'{number:04d}.json'), {'sheet': str(path), 'sheetSha256': p.sha(path.read_bytes()),
        'at': p.now(), 'reviewer': 'Codex', 'accepted': accepted, 'rejected': rejected})
    print(batch, number, len(accepted), 'accepted', len(rejected), 'held', flush=True)


def canonical_license(metadata):
    name, url = metadata['license'], metadata['licenseUrl']
    if name == 'Public domain':
        return 'https://creativecommons.org/publicdomain/mark/1.0/'
    if name == 'CC0':
        return 'https://creativecommons.org/publicdomain/zero/1.0/'
    match = re.fullmatch(r'CC (BY(?:-SA)?) ([1-4]\.0|2\.5)(?: ([a-z]{2,3}))?', name)
    assert match, name
    path = '/licenses/' + match[1].lower() + '/' + match[2] + '/'
    if match[3]:
        path += match[3] + '/'
    parsed = urllib.parse.urlsplit(url)
    assert parsed.scheme == 'https' and parsed.netloc == 'creativecommons.org' and not parsed.query and not parsed.fragment
    assert parsed.path.rstrip('/') == path.rstrip('/') or re.fullmatch(re.escape(path) + r'(?:deed(?:\.[a-z-]+)?|legalcode(?:\.[a-z-]+)?)', parsed.path)
    return 'https://creativecommons.org' + path


def author_bindings(batch):
    """Reuse an inspected author image only for the same verified creator link.

    Each derivative must have the identical hash. This records image reuse; it
    does not claim a second visual inspection or represent a portrait as a cover.
    """
    directory = p.RUN / 'delivery' / batch
    draft_rows = p.load(directory / 'draft.json.gz')
    assert all(r.get('property') == 'author-portrait' for r in draft_rows)
    inspected, existing, rejected = {}, set(), set()
    for path in (directory / 'visual-reviews').glob('*.json'):
        review = p.load(path)
        for checked in review['accepted']:
            row = draft_rows[checked['index']]
            inspected[(row['creatorId'], row['file'], checked['sha256'])] = (checked, path)
            existing.add(row['id'])
        rejected.update(r['id'] for r in review['rejected'])
    bindings = []
    for index, row in enumerate(draft_rows):
        receipt = directory / 'prepared' / (row['id'] + '.json')
        if row['id'] in existing or row['id'] in rejected or not receipt.exists():
            continue
        prepared = p.load(receipt)
        reference = inspected.get((row['creatorId'], row['file'], prepared['sha256']))
        if not reference:
            continue
        checked, reviewpath = reference
        assert row['creatorLink']['creator_id'] == row['creatorId'] and row['creatorLink']['book_id'] == row['id'] and row['creatorLink']['position'] == 0
        bindings.append({'index': index, 'id': row['id'], 'file': row['file'], 'sha256': prepared['sha256'],
            'label': checked['label'], 'visualKind': checked['visualKind'],
            'visualRepresentative': checked['id'], 'representativeReview': str(reviewpath.relative_to(p.ROOT)),
            'identityBasis': 'Identical reviewed image bytes and source file for the same named primary creator; book-to-creator relationship retained from the read-only catalogue export. This is a labelled author image, not a cover.'})
    p.save(directory / 'author-bindings.json', bindings, immutable=False)
    print('Author image bindings', batch, len(bindings), flush=True)


def merge():
    """Attach only individually inspected, hash-pinned images to local manifests.

    No database writes, publication, commits or deployment. An existing entry is
    never overwritten. All candidates and unresolved rights remain evidence.
    """
    commons = p.load(p.RUN / 'commons-index.json.gz')
    searchpath = p.RUN / 'search-commons-index.json.gz'
    search_commons = p.load(searchpath) if searchpath.exists() else {}
    authorpath = p.RUN / 'author-search-commons-index.json.gz'
    author_commons = p.load(authorpath) if authorpath.exists() else {}
    qualified_path = p.RUN / 'standard-ebooks/publisher-qualified.json.gz'
    publisher_qualified = {r['id']: r for r in p.load(qualified_path)} if qualified_path.exists() else {}
    previous_path = p.RUN / 'selected-local.json.gz'
    previous = {r['id']: r for r in p.load(previous_path)} if previous_path.exists() else {}
    selected, holds, caption_history = [], [], set()
    holdpath = p.RUN / 'review-holds.json'
    review_holds = p.load(holdpath) if holdpath.exists() else {}
    for directory in sorted((p.RUN / 'delivery').iterdir()):
        if not directory.is_dir() or not (directory / 'draft.json.gz').exists():
            continue
        pin = p.load(directory / 'draft-pin.json')
        assert p.sha((directory / 'draft.json.gz').read_bytes()) == pin['sha256']
        draft_rows = p.load(directory / 'draft.json.gz')
        for archived in (directory / 'review-amendments').glob('*.json'):
            caption_history.update((directory.name, r['id'], r['sha256'], r['label']) for r in p.load(archived).get('accepted', []))
        reviewpaths = sorted((directory / 'visual-reviews').glob('*.json'))
        if (directory / 'author-bindings.json').exists():
            reviewpaths.append(directory / 'author-bindings.json')
        for reviewpath in reviewpaths:
            review = p.load(reviewpath)
            if isinstance(review, list):
                for binding in review:
                    original_review = p.load(p.ROOT / binding['representativeReview'])
                    assert any(r['id'] == binding['visualRepresentative'] and r['sha256'] == binding['sha256'] and r['label'] == binding['label'] for r in original_review['accepted'])
                review = {'accepted': review}
            else:
                sheetpath = Path(review['sheet'])
                if not sheetpath.is_absolute():
                    sheetpath = SHEETS / directory.name / sheetpath
                assert p.sha(sheetpath.read_bytes()) == review['sheetSha256']
            for checked in review['accepted']:
                row = draft_rows[checked['index']]
                assert row['id'] == checked['id']
                later_hold = review_holds.get(directory.name + ':' + str(checked['index']))
                if later_hold:
                    holds.append({'id': row['id'], 'batch': directory.name, 'reason': later_hold['reason']})
                    continue
                prepared = p.load(directory / 'prepared' / (row['id'] + '.json'))
                imagepath = asset_path(prepared)
                assert checked['sha256'] == prepared['sha256'] == p.sha(imagepath.read_bytes())
                assert imagepath.stat().st_size <= 100000 and prepared['draftSha256'] == pin['sha256']
                if not prepared.get('transparentPixelsCompositedOnWhite') and has_transparency(Path(prepared['original']['path']).read_bytes()):
                    holds.append({'id': row['id'], 'batch': directory.name, 'reason': 'transparent-source-needs-white-background-and-repeat-visual-review'})
                    continue
                if row.get('property') == 'publisher-edition-cover':
                    qualified = publisher_qualified.get(row['id'])
                    if not qualified or qualified['edition']['url'] != prepared['sourceMetadata']['sourceUrl']:
                        holds.append({'id': row['id'], 'batch': directory.name, 'reason': 'publisher-native-artwork-provenance-pending-or-held'})
                        continue
                else:
                    metadata_index = {'search': search_commons, 'author-search': author_commons}.get(row.get('metadataProvider'), commons)
                    reviewed, reason = p.source_review(row, metadata_index.get(row['file'], {}))
                    if reviewed is None:
                        holds.append({'id': row['id'], 'batch': directory.name, 'reason': reason})
                        continue
                    assert reviewed['fileSha1'] == prepared['sourceMetadata']['fileSha1'], 'Source file changed after review'
                metadata = prepared['sourceMetadata']
                if row.get('property') != 'publisher-edition-cover' and 'mw-parser-output' in metadata['credit']:
                    metadata = metadata | {'credit': reviewed['credit']}
                try:
                    license_url = canonical_license(metadata)
                except AssertionError:
                    holds.append({'id': row['id'], 'batch': directory.name, 'reason': 'licence-label-url-mismatch'})
                    continue
                key = 'bookId' if row['category'] == 'books' else 'eventId'
                entry = {key: row['id'], 'sourceId': row['qid'], 'imageUrl': prepared['imageUrl'],
                    'sourceUrl': metadata['sourceUrl'], 'label': checked['label'],
                    'credit': metadata['credit'] + ' · Resized and JPEG-compressed; full supplied frame.',
                    'license': metadata['license'], 'licenseUrl': license_url, 'checkedAt': '2026-10-10'}
                selected.append({'category': row['category'], 'id': row['id'], 'entry': entry, 'property': row.get('property'),
                    'visualKind': checked.get('visualKind'), 'batch': directory.name,
                    'imageSha256': prepared['sha256'], 'review': str(reviewpath.relative_to(p.ROOT))})
                if row.get('correctionEvidence'):
                    selected[-1]['correctionEvidence'] = row['correctionEvidence']
    byidentity = {}
    for row in selected:
        key = row['category'], row['id']
        prior = byidentity.get(key)
        if prior:
            assert (prior['property'] == 'author-portrait') != (row['property'] == 'author-portrait'), 'Conflicting work-specific selections'
            if row['property'] == 'author-portrait':
                continue
        byidentity[key] = row
    selected = list(byidentity.values())
    for selected_row in selected:
        prepared = p.load(p.RUN / 'delivery' / selected_row['batch'] / 'prepared' / (selected_row['id'] + '.json'))
        source = asset_path(prepared)
        public = p.ROOT / prepared['path']
        if source != public:
            raw = source.read_bytes()
            assert p.sha(raw) == selected_row['imageSha256']
            public.parent.mkdir(parents=True, exist_ok=True)
            public.write_bytes(raw)
    for category, path in p.MANIFESTS.items():
        current = p.load(path)
        key = 'bookId' if category == 'books' else 'eventId'
        byid = {r[key]: r for r in current}
        before = {r[key]: r for r in p.load(p.RUN / ('before-' + category + '.json'))}
        assert all(byid.get(k) == v for k, v in before.items()), 'Original manifest entries changed'
        accepted_ids = {r['id'] for r in selected if r['category'] == category}
        held_ids = {r['id'] for r in holds if r['reason'] != 'publisher-native-artwork-provenance-pending-or-held'}
        for id, prior in previous.items():
            if prior['category'] == category and id not in before and id not in accepted_ids and id in held_ids:
                assert byid.get(id) == prior['entry'], 'Do not withdraw an unrelated change'
                p.save(p.RUN / 'withdrawn-local-selections' / (id + '-' + prior['imageSha256'] + '.json'), {
                    'previous': prior, 'reasons': [r for r in holds if r['id'] == id],
                    'decision': 'Withdraw this campaign’s local image selection after a stricter evidence check; preserve original catalogue and image evidence.'})
                del byid[id]
        for selected_row in selected:
            if selected_row['category'] != category:
                continue
            entry = selected_row['entry']
            if selected_row['id'] in byid:
                if byid[selected_row['id']] != entry:
                    prior = previous.get(selected_row['id'])
                    author_upgrade = prior and prior['property'] == 'author-portrait' and selected_row['property'] != 'author-portrait'
                    alpha_repair = prior and selected_row.get('correctionEvidence', {}).get('previousImageSha256') == prior['imageSha256']
                    caption_fix = False
                    if prior and prior['imageSha256'] == selected_row['imageSha256'] and (prior['entry'] | {'label': entry['label']}) == entry:
                        caption_fix = (selected_row['batch'], prior['id'], prior['imageSha256'], prior['entry']['label']) in caption_history
                    assert selected_row['id'] not in before and prior and prior['entry'] == byid[selected_row['id']] and (author_upgrade or alpha_repair or caption_fix), 'Do not overwrite an existing selected picture'
                    audit = 'caption-corrections' if caption_fix else ('repaired-transparent-images' if alpha_repair else 'superseded-author-images')
                    reason = 'Caption corrected with prior review preserved; image and source unchanged.' if caption_fix else ('Reviewed replacement preserves transparent source content on white.' if alpha_repair else 'A reviewed work-specific image takes priority over this campaign’s labelled author fallback.')
                    p.save(p.RUN / audit / (selected_row['id'] + '-' + p.sha(json.dumps(entry, sort_keys=True).encode()) + '.json'), {'previous': prior, 'replacement': selected_row, 'reason': reason})
                    byid[selected_row['id']] = entry
                continue
            byid[selected_row['id']] = entry
        raw = path.read_bytes()
        backup = p.BACKUP / (category + '-' + p.sha(raw) + '.json')
        backup.parent.mkdir(parents=True, exist_ok=True)
        if backup.exists():
            assert backup.read_bytes() == raw
        else:
            backup.write_bytes(raw)
        final = sorted(byid.values(), key=lambda r: r[key])
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(final, ensure_ascii=False, indent=2) + '\n')
        temporary.replace(path)
    p.save(p.RUN / 'selected-local.json.gz', selected, immutable=False)
    p.save(p.RUN / 'post-review-holds.json', holds, immutable=False)
    print('Locally attached', dict(collections.Counter(r['category'] for r in selected)), 'post-review holds', len(holds), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['draft', 'search-draft', 'author-search-draft', 'prepare', 'publisher', 'merge', 'author-bindings', 'stage-unselected'])
    parser.add_argument('--batch', required=True)
    parser.add_argument('--category', choices=['books', 'events'])
    parser.add_argument('--min-words', type=int, default=0)
    parser.add_argument('--kind', choices=['all', 'work', 'author'], default='all')
    parser.add_argument('--promote-authors', action='store_true')
    parser.add_argument('--limit', type=int, default=200)
    args = parser.parse_args()
    assert re.fullmatch(r'[a-z0-9-]+', args.batch)
    if args.phase == 'stage-unselected':
        stage_unselected()
    elif args.phase == 'author-bindings':
        author_bindings(args.batch)
    elif args.phase == 'merge':
        merge()
    elif args.phase == 'draft':
        assert args.category
        draft(args.batch, args.category, args.min_words, args.kind, args.promote_authors)
    elif args.phase == 'publisher':
        publisher_draft(args.batch, args.promote_authors)
    elif args.phase == 'search-draft':
        assert args.category
        search_draft(args.batch, args.category, args.limit)
    elif args.phase == 'author-search-draft':
        author_search_draft(args.batch, args.limit)
    else:
        prepare(args.batch)
