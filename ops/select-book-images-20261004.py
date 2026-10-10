#!/usr/bin/env python3
"""Prepare explicit reviewed reproductions; merge manifests only after visual QA."""
import argparse
import hashlib
import html
import io
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.request
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/research/books-5000bce-1850-20261004'
ORIGINALS = Path('/Users/vadimdulub/Library/Application Support/Artline/source-images/books-5000bce-1850-20261004')


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def plain(value):
    return ' '.join(html.unescape(re.sub('<[^>]*>', ' ', str(value))).split())


def prepare():
    assert not (OUT / 'image-apply-receipt.json').exists(), 'Preserve completed image evidence.'
    choices = json.loads((OUT / 'image-choices.json').read_text())
    manifests, receipts = {'books': [], 'authors': []}, []
    ORIGINALS.mkdir(parents=True, exist_ok=True)
    for choice in choices:
        raw = (OUT / choice['candidateFile']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == choice['candidateSha256']
        row = json.loads(raw)[choice['index']]
        assert row['id'] == choice['id'] and row['file'] == choice['file']
        proof = row['source']
        assert hashlib.sha256((ROOT / proof['path']).read_bytes()).hexdigest() == proof['sha256']
        info = row['page']['imageinfo'][0]
        meta = info['extmetadata']; val = lambda k: plain(meta.get(k, {}).get('value', ''))
        license_name = val('LicenseShortName')
        assert license_name in (['Public domain', 'CC0'] if row['category'] == 'books' else ['Public domain']) and not val('Restrictions')
        assert val('Credit') and not re.search(r'copyright claims|disputed copyright|deletion request|missing permission|possibly unfree', val('Categories') + val('Credit'), re.I)
        if choice.get('previewPage'):
            assert row['category'] == 'books' and info['mime'] == 'image/vnd.djvu'
            assert 1 <= choice['previewPage'] <= info['pagecount'] and info.get('thumburl')
        else:
            assert info['mime'] in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        category, identity = row['category'], row['id']
        url = (info.get('thumburl') or info['url']).split('?')[0]
        if choice.get('previewPage'):
            assert '/page1-' in url
            url = url.replace('/page1-', '/page' + str(choice['previewPage']) + '-')
        source = ORIGINALS / (category + '-' + identity + '.source')
        source_receipt = source.with_suffix('.json')
        if source.exists():
            assert json.loads(source_receipt.read_text())['url'] == url, 'Never silently replace a prior source.'
        else:
            for attempt in range(4):
                try:
                    request = urllib.request.Request(url, headers={'User-Agent': 'ArtlineSelectedImages/1.0 (https://artlines.org/about)'})
                    with urllib.request.urlopen(request, timeout=45) as response:
                        raw = response.read(16 * 1024 * 1024 + 1)
                    assert len(raw) <= 16 * 1024 * 1024
                    source.write_bytes(raw)
                    save(source_receipt, {'url': url, 'sha256': hashlib.sha256(raw).hexdigest()})
                    time.sleep(2)
                    break
                except urllib.error.HTTPError as error:
                    if error.code not in (429, 503) or attempt == 3:
                        raise
                    delay = int(error.headers.get('Retry-After', '30'))
                    time.sleep(min(60, max(15, delay)))
        picture = ImageOps.exif_transpose(Image.open(source)).convert('RGB')
        picture.thumbnail((720, 720))
        for size in (720, 640, 560, 480):
            picture.thumbnail((size, size))
            for quality in (88, 82, 75, 65, 55, 45):
                data = io.BytesIO(); picture.save(data, 'JPEG', quality=quality, optimize=True)
                if len(data.getvalue()) <= 100000:
                    break
            if len(data.getvalue()) <= 100000:
                break
        assert len(data.getvalue()) <= 100000
        relative = f'/images/{category}/selected-20261004/{identity}.jpg'
        target = ROOT / 'apps/web/public' / relative.lstrip('/')
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data.getvalue())
        credit = choice.get('credit') or val('Attribution') or val('Artist') or 'Image creator not identified in the source'
        credit = re.sub(r'(Unknown author\s*)+', 'Image creator not identified in the source ', credit).strip()
        license_url = 'https://creativecommons.org/publicdomain/zero/1.0/' if license_name == 'CC0' else 'https://creativecommons.org/publicdomain/mark/1.0/'
        common = {'imageUrl': relative, 'sourceUrl': info['descriptionurl'], 'label': choice['label'], 'credit': credit, 'license': license_name, 'licenseUrl': license_url, 'checkedAt': '2026-10-04'}
        keys = {'bookId': identity, 'sourceId': row['qid']} if category == 'books' else {'creatorId': identity, 'creatorSourceUrl': 'https://www.wikidata.org/wiki/' + row['qid']}
        manifests[category].append(keys | common)
        receipts.append({'category': category, 'id': identity, 'name': row['name'], 'file': row['file'], 'label': choice['label'], 'source': proof, 'sourceImageUrl': url, 'sourcePath': str(source), 'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'path': str(target.relative_to(ROOT)), 'bytes': target.stat().st_size, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'width': picture.width, 'height': picture.height, 'rightsCategories': val('Categories'), 'origin': val('Credit'), 'identityReview': choice['identityReview'], 'transformation': 'Full supplied frame, EXIF orientation, proportional resizing and JPEG compression; no new crop.'})
        print(category, identity, target.stat().st_size, flush=True)
    save(OUT / 'prepared-image-manifests.json', manifests)
    save(OUT / 'selected-images.json', receipts)
    for category in manifests:
        items = [r for r in receipts if r['category'] == category]
        sheet = Image.new('RGB', (1000, ((len(items)+4)//5)*245), '#eee8dc'); draw = ImageDraw.Draw(sheet)
        for i, item in enumerate(items):
            pic = Image.open(ROOT / item['path']); pic.thumbnail((185, 190))
            x,y = (i%5)*200, (i//5)*245
            sheet.paste(pic, (x+(200-pic.width)//2, y))
            draw.text((x+5, y+193), item['id'], fill='#111111')
            draw.text((x+5, y+209), item['name'][:27], fill='#111111')
            draw.text((x+5, y+225), item['label'][:28], fill='#111111')
        sheet.save('/tmp/artline-selected-' + category + '-20261004.jpg')


def apply(pin):
    path = OUT / 'prepared-image-manifests.json'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == pin
    review = json.loads((OUT / 'image-visual-review.json').read_text())
    assert review['manifestSha256'] == pin and review['approved']
    manifests = json.loads(path.read_text())
    for image in json.loads((OUT / 'selected-images.json').read_text()):
        assert hashlib.sha256((ROOT / image['path']).read_bytes()).hexdigest() == image['sha256']
    for category, filename, key in [('books', 'cover-selection.json', 'bookId'), ('authors', 'portrait-selection.json', 'creatorId')]:
        path = ROOT / 'apps/server/internal/books' / filename
        before = json.loads(path.read_text()); merged = {r[key]: r for r in before}
        save(OUT / ('before-' + filename), before)
        for row in manifests[category]:
            assert row[key] not in merged, 'Do not replace an existing selection.'
            merged[row[key]] = row
        save(path, sorted(merged.values(), key=lambda r: r[key]))
    save(OUT / 'image-apply-receipt.json', {'manifestSha256': pin, 'added': {c: len(v) for c,v in manifests.items()}, 'existingSelectionsPreserved': True})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'apply'])
    parser.add_argument('--sha256')
    args = parser.parse_args()
    prepare() if args.stage == 'prepare' else apply(args.sha256)
