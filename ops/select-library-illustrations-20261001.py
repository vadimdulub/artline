#!/usr/bin/env python3
"""Download this bounded, reviewed selection; merge manifests only with --apply.

The indices identify immutable candidates.json entries, not search rankings.
Original selected downloads and transformation receipts are preserved separately.
"""
import argparse
import datetime
import hashlib
import html
import io
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.request
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/research/library-illustrations-20261001'
ORIGINALS = Path('/Users/vadimdulub/Library/Application Support/Artline/source-images/library-illustrations-20261001')
BOOKS = {
    4: 'Title page · 1925', 12: 'Edition cover · 1922',
    15: 'Title page · first part, 1883', 16: 'Opening page · serial edition',
    17: 'Title page · 1874', 18: 'Title page · 1878',
    19: 'Title page · first edition', 21: 'Title page · 1854',
    22: 'Title page · 1850', 28: 'Title page · 1818',
    30: 'Title page · first American edition', 31: 'Title page',
    32: 'Title page · 1776', 40: 'Title page · 1590',
    44: 'Title page · 1556', 81: 'Title-page illustration · Latin edition',
    87: 'Title page · collected edition, 1828',
}
AUTHORS = [95, 96, 99, 101, 102, 103, 105, 107, 110, 112, 115, 116,
           122, 124, 125, 131, 132, 134, 135, 136, 140, 143, 145, 147, 149]
EVENTS = {
    153: "Luther's Ninety-five Theses · historical printed edition",
    156: 'Confrontation at Cajamarca · later engraving by Theodor de Bry',
    157: 'Galileo demonstrating his telescope in Venice · later painting, 1858',
    162: 'The Wounded Cavalier · later painting, 1855',
    163: 'Ratification of the Treaty of Münster · painting, 1648',
    165: 'Presentation of the Declaration of Independence · later painting, 1819',
    167: 'Battle of San Domingo · later painting, 1845',
    173: 'The Nemesis in the First Opium War · print, 1843',
    174: 'Barricade on the Rue Soufflot, June 1848 · painting, 1848–1849',
    176: 'North India during the rebellion · later historical map, 1912',
    178: 'Proclamation of the German Empire · later painting, 1885',
    180: 'Participants at the Berlin Conference · contemporary illustration',
    181: 'Barricades on Arbat Street, Moscow · photograph, December 1905',
    182: 'Nanjing Road, Shanghai, during the Xinhai Revolution · photograph, 1911',
    185: 'March Revolution in Russia · photograph reproduced in a 1921 book',
    186: 'Emergency influenza hospital at Camp Funston · photograph, c. 1918',
}

def plain(value):
    return ' '.join(html.unescape(re.sub(r'<[^>]*>', ' ', str(value))).split())

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def main(apply=False):
    candidate_bytes = (OUT / 'candidates.json').read_bytes()
    assert hashlib.sha256(candidate_bytes).hexdigest() == '2fbe8b7ae839c1c02e34a0f0b7be1518e17e8f222bb39734aebd870fa78ae0f9', 'Preserve this reviewed campaign; use a new campaign for new research.'
    candidates = json.loads(candidate_bytes)
    manifests = {'books': [], 'authors': [], 'events': []}
    receipts = []
    choices = BOOKS | {i: 'Portrait of ' + candidates[i]['name'] for i in AUTHORS} | EVENTS
    ORIGINALS.mkdir(parents=True, exist_ok=True)
    for index, label in choices.items():
        row = candidates[index]
        info = row['page']['imageinfo'][0]
        meta = info['extmetadata']
        val = lambda k: plain(meta.get(k, {}).get('value', ''))
        assert val('LicenseShortName') == 'Public domain' and not val('Restrictions')
        assert not re.search(r'copyright claims|disputed copyright|deletion request|missing permission|possibly unfree', val('Categories') + val('Credit'), re.I)
        assert val('Credit') and info['mime'].startswith('image/')
        proof = ROOT / row['evidenceFile']
        assert hashlib.sha256(proof.read_bytes()).hexdigest() == row['evidenceSha256']
        category, identity = row['category'], row['id']
        relative = f'/images/{category}/selected-20261001/{identity}.jpg'
        target = ROOT / 'apps/web/public' / relative.lstrip('/')
        source = ORIGINALS / f'{category}-{identity}.source'
        url = (info.get('thumburl') or info['url']).split('?')[0]
        if not source.exists():
            for attempt in range(4):
                try:
                    request = urllib.request.Request(url, headers={'User-Agent': 'ArtlineSelectedImages/1.0 (https://artlines.org/about)'})
                    with urllib.request.urlopen(request, timeout=60) as response:
                        raw = response.read(12 * 1024 * 1024 + 1)
                    assert len(raw) <= 12 * 1024 * 1024
                    source.write_bytes(raw)
                    time.sleep(3)
                    break
                except urllib.error.HTTPError as error:
                    if error.code not in (429, 503) or attempt == 3:
                        raise
                    time.sleep(min(60, int(error.headers.get('Retry-After', '30'))))
        raw = source.read_bytes()
        picture = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert('RGB')
        picture.thumbnail((720, 720))
        for size in (720, 640, 560, 480):
            picture.thumbnail((size, size))
            for quality in (88, 82, 75, 65, 55, 45):
                data = io.BytesIO()
                picture.save(data, 'JPEG', quality=quality, optimize=True)
                if len(data.getvalue()) <= 100000:
                    break
            if len(data.getvalue()) <= 100000: break
        assert len(data.getvalue()) <= 100000
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data.getvalue())
        credit = val('Attribution') or val('Artist') or 'Creator not identified in the source'
        credit = re.sub(r'(Unknown (?:author|illustrator)\s*)+', 'Creator not identified in the source ', credit).strip()
        common = dict(imageUrl=relative, sourceUrl=info['descriptionurl'], label=label,
                      credit=credit, license='Public domain',
                      licenseUrl='https://creativecommons.org/publicdomain/mark/1.0/', checkedAt='2026-10-01')
        keys = {'books': dict(bookId=identity, sourceId=row['qid']),
                'authors': dict(creatorId=identity, creatorSourceUrl=row['source_url']),
                'events': dict(eventId=identity, sourceId=row['qid'])}[category]
        manifests[category].append(keys | common)
        receipts.append(dict(index=index, category=category, id=identity, name=row['name'], file=row['file'],
            label=label, claimId=row['claimId'], evidenceFile=row['evidenceFile'], evidenceSha256=row['evidenceSha256'],
            sourceImageURL=url, sourcePage=info['descriptionurl'], origin=val('Credit'),
            rights=val('Categories'), sourcePath=str(source), sourceSHA256=hashlib.sha256(raw).hexdigest(),
            path=str(target.relative_to(ROOT)), bytes=target.stat().st_size, sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            width=picture.width, height=picture.height,
            transformation='Full supplied composition; EXIF orientation, proportional resize and JPEG compression; no cropping.',
            identityReview='Matched work/person/event P18 claim and file description; edition and later-depiction labels reviewed separately from catalogue dates.'))
        print(category, identity, target.stat().st_size, flush=True)
    save(OUT / 'selected-images.json', receipts)
    save(OUT / 'prepared-manifests.json', manifests)
    for category, rows in manifests.items():
        items = [r for r in receipts if r['category'] == category]
        sheet = Image.new('RGB', (1000, ((len(items)+4)//5)*230), '#eee8dc')
        draw = ImageDraw.Draw(sheet)
        for n, item in enumerate(items):
            pic = Image.open(ROOT / item['path']);pic.thumbnail((180,180))
            x, y = (n%5)*200, (n//5)*230
            sheet.paste(pic, (x+(200-pic.width)//2,y))
            draw.text((x+5,y+183), str(item['index'])+' '+item['name'][:26], fill='#13120f')
            draw.text((x+5,y+201), item['label'][:29], fill='#13120f')
        sheet.save(f'/tmp/artline-{category}-20261001.jpg')
    if apply:
        paths = {'books': ('apps/server/internal/books/cover-selection.json','bookId'),
                 'authors': ('apps/server/internal/books/portrait-selection.json','creatorId'),
                 'events': ('apps/server/internal/events/image-selection.json','eventId')}
        for category, (relative, key) in paths.items():
            path = ROOT / relative
            before = json.loads(path.read_text()) if path.exists() else []
            merged = {row[key]: row for row in before}
            for row in manifests[category]:
                assert row[key] not in merged or merged[row[key]] == row, 'Never replace an existing selection silently'
                merged[row[key]] = row
            save(path, sorted(merged.values(), key=lambda row: row[key]))
        save(OUT/'selection-summary.json', {'added': {k:len(v) for k,v in manifests.items()}, 'maximumBytes':max(r['bytes'] for r in receipts), 'databaseWrites':0})

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    main(parser.parse_args().apply)
