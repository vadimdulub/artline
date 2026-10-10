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


def draft(batch, category, min_words):
    directory = p.RUN / 'delivery' / batch
    rows = [r for r in p.load(p.RUN / 'proposals.json.gz') if r['category'] == category and r['identityWordMatches'] >= min_words]
    used = set()
    for path in (p.RUN / 'delivery').glob('*/draft.json.gz'):
        if path.parent != directory:
            used.update((r['category'], r['id']) for r in p.load(path))
    rows = [r for r in rows if (r['category'], r['id']) not in used]
    p.save(directory / 'draft.json.gz', rows)
    p.save(directory / 'draft-pin.json', {'sha256': p.sha((directory / 'draft.json.gz').read_bytes()), 'count': len(rows),
        'status': 'Selected for preparation and review; not accepted for application yet.'})
    print('Draft', batch, len(rows), flush=True)


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
        im = Image.open(p.ROOT / row['path'])
        im.thumbnail((224, 174))
        x, y = (n % 5) * 240, (n // 5) * 240
        canvas.paste(im, (x + (240 - im.width) // 2, y))
        for offset, text in [(177, str(row['index']) + ' ' + row['id']), (192, row['title'][:36]), (207, row['file'][:36]), (222, row['label'][:36])]:
            draw.text((x + 5, y + offset), text, fill='#111111')
    canvas.save(path, 'JPEG', quality=90)
    p.save(path.with_suffix('.json'), [{'index': r['index'], 'id': r['id'], 'sha256': r['sha256'], 'file': r['file']} for r in rows], immutable=False)


def prepare(batch):
    directory = p.RUN / 'delivery' / batch
    pin = p.load(directory / 'draft-pin.json')
    assert p.sha((directory / 'draft.json.gz').read_bytes()) == pin['sha256']
    rows = p.load(directory / 'draft.json.gz')
    ready = []
    for index, row in enumerate(rows):
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
            jpeg, width, height, quality = p.image_core().compress(raw)
            assert len(jpeg) <= 100000
            relative = f"/images/{row['category']}/selected-20261010/{row['id']}.jpg"
            path = p.ROOT / 'apps/web/public' / relative.lstrip('/')
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                assert path.read_bytes() == jpeg, 'Do not overwrite another image'
            else:
                path.write_bytes(jpeg)
            result = {'index': index, 'category': row['category'], 'id': row['id'], 'qid': row['qid'], 'title': row['title'],
                'file': row['file'], 'label': row['proposedLabel'], 'imageUrl': relative, 'path': str(path.relative_to(p.ROOT)),
                'sha256': p.sha(jpeg), 'width': width, 'height': height, 'bytes': len(jpeg), 'quality': quality,
                'original': original, 'sourceMetadata': metadata, 'draftSha256': pin['sha256'],
                'transformation': 'Full supplied frame; EXIF orientation, proportional resizing and JPEG compression. No crop.',
                'visualReview': 'pending'}
            p.save(receipt, result)
            ready.append(result)
        except Exception as error:
            p.save(errorpath, {'index': index, 'id': row['id'], 'file': row['file'], 'error': str(error), 'at': p.now()})
            if any((p.RUN / 'image-host-holds').glob('*.json')):
                print('Image provider access hold; preparation paused', flush=True)
                break
        if len(ready) and len(ready) % 40 == 0:
            sheet(batch, ready[-40:], (len(ready) - 1) // 40)
        if index % 20 == 0:
            print('Prepared', batch, index + 1, '/', len(rows), 'ready', len(ready), flush=True)
    for offset in range(0, len(ready), 40):
        sheet(batch, ready[offset:offset + 40], offset // 40)
    p.save(directory / 'prepared-summary.json', {'draft': len(rows), 'prepared': len(ready), 'errors': len(list((directory / 'errors').glob('*.json'))), 'at': p.now()}, immutable=False)
    print('Preparation finished', batch, len(ready), '/', len(rows), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['draft', 'prepare'])
    parser.add_argument('--batch', required=True)
    parser.add_argument('--category', choices=['books', 'events'])
    parser.add_argument('--min-words', type=int, default=0)
    args = parser.parse_args()
    assert re.fullmatch(r'[a-z0-9-]+', args.batch)
    if args.phase == 'draft':
        assert args.category
        draft(args.batch, args.category, args.min_words)
    else:
        prepare(args.batch)
