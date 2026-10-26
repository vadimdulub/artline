"""Finite Rouen image preparation. No database connection or Storage write.

Prepared files remain candidates until actual visual review and a fresh,
locked production preflight. Existing object metadata is never changed here.
"""
import argparse
import collections
import gzip
import io
import json
import re
import shutil
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlsplit

import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
from bs4 import BeautifulSoup
import exhibitions_common as c

NAME = 'catalogue-deduplication-20261026'
E = c.ROOT / 'docs/research' / NAME
D = Path.home() / 'Library/Application Support/Artline/source-metadata' / NAME
O = Path.home() / 'Library/Application Support/Artline/source-images' / NAME
RESERVE = 15 * 1024**3
BUDGET = 1024**3
UA = 'ArtlineResearch/1.0 (+https://artlines.org; finite exact Rouen collection research)'


def field(soup, label):
    node = soup.find(string=label)
    return node.parent.find_next_sibling().get_text(' ', strip=True) if node and node.parent.find_next_sibling() else None


def select():
    crosswalk = c.load(D / 'rouen-native-identity-map-v2.json.gz')
    eligible = c.load(D / 'rouen-native-scope-screen.json.gz')['eligible']
    selected, held = [], []
    for row in eligible:
        native = row['native_id']
        ids = crosswalk['native_to_active_ids'].get(native, [])
        notice_path = D / 'rouen-notices' / (native + '.json.gz')
        if len(ids) != 1 or not notice_path.exists():
            continue
        artwork = crosswalk['works'][ids[0]]
        if artwork['primary_media_id']:
            continue
        notice = c.load(notice_path)
        if notice['state'] != 'published_images':
            continue
        soup = BeautifulSoup(gzip.decompress(Path(notice['receipt']['body_path']).read_bytes()), 'html.parser')
        facts = dict(notice['fields'])
        facts['Millésime de création'] = field(soup, 'Millésime de création')
        facts["Précisions sur l'auteur"] = field(soup, "Précisions sur l'auteur")
        reasons = []
        if c.norm(facts.get('Titre') or '') != c.norm(row['facts']['title']):
            reasons.append('Current source title differs from pinned native catalogue.')
        if c.norm(artwork['title']) != c.norm(facts.get('Titre') or ''):
            reasons.append('Existing work title requires individual multilingual identity review.')
        inventory = facts.get("Numéro d'inventaire") or ''
        if c.norm(inventory) != c.norm(row['facts']['accession']):
            reasons.append('Current source inventory differs from pinned native catalogue.')
        if artwork.get('accession_number') and c.norm(artwork['accession_number']) != c.norm(inventory):
            reasons.append('Existing accession requires individual review.')
        if 'rouen' not in c.norm(facts.get('Lieu de conservation') or ''):
            reasons.append('Current conservation location does not confirm Rouen.')
        if any(int(y) > 1989 for y in re.findall(r'\b[12]\d{3}\b', facts.get('Millésime de création') or '')):
            reasons.append('Current creation text includes a date outside the authorized scope.')
        value = dict(native_id=native, artwork_id=artwork['id'], title=artwork['title'],
                     pinned_artwork=artwork, source_facts=row['facts'], notice_fields=facts,
                     notice_receipt=notice['receipt'], images=notice['images'],
                     exact_native_identity_basis='Unique active work linked by exact Joconde research object key or native identifier; current title and inventory checked.',
                     actual_visual_review_required=True)
        if reasons:
            held.append(dict(value, reasons=reasons))
        else:
            selected.append(value)
    value = dict(at=c.now(), selected=selected, held=held,
                 images_do_not_rewrite_metadata_creators_or_holdings=True,
                 preimage_is_historical_fresh_production_preflight_required=True)
    path = D / ('rouen-image-selection-' + str(len(selected)) + '.json.gz')
    c.save(path, value)
    print(json.dumps(dict(selection=str(path), selected=len(selected), held=len(held))), flush=True)
    return path


def used():
    return sum(p.stat().st_size for root in [D, O] for p in root.rglob('*') if p.is_file())


def prepare(selection):
    queue = c.load(Path(selection))['selected']
    O.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers['User-Agent'] = UA
    holds = c.load(c.ROOT / 'docs/research/low-image-painters-100-wave2-20261026/source-holds-preflight.json')['denied_hosts']
    assert not (E / 'rouen-source-image-access-hold.json').exists()
    robots = {}
    for row in queue:
        # Every published view is preserved for review. No automatic primary
        # assignment, selection of the largest view, or detail/verso inference.
        for number, image in enumerate(row['images']):
            key = row['native_id'] + '-' + str(number)
            dest = E / 'image-preparation' / (key + '.json')
            if dest.exists():
                prior = c.load(dest)
                if prior['state'] == 'held' and prior.get('reason') == 'AssertionError()' and not prior.get('original_path'):
                    # Some published S3 images use application/octet-stream.
                    # Preserve the first failed MIME check and inspect their
                    # bytes with Pillow, without treating a MIME label as proof.
                    dest = dest.with_name(key + '-mime-v2.json')
                    if dest.exists():
                        continue
                else:
                    continue
            url = image['url']
            host = urlsplit(url).hostname
            assert host not in holds, ('Inherited source hold', host)
            assert '/joconde/' + row['native_id'] + '/' in url
            origin = 'https://' + urlsplit(url).netloc
            if origin not in robots:
                receipt_path = E / ('image-robots-' + host + '.json')
                if receipt_path.exists():
                    receipt = c.load(receipt_path)
                    raw = gzip.decompress(Path(receipt['body_path']).read_bytes())
                else:
                    response = session.get(origin + '/robots.txt', timeout=(8, 25), allow_redirects=False)
                    raw = response.content
                    body = D / ('image-robots-' + host + '.body.gz')
                    body.write_bytes(gzip.compress(raw, mtime=0))
                    receipt = dict(at=c.now(), url=response.url, status=response.status_code,
                                   bytes=len(raw), sha256=c.sha(raw), body_path=str(body))
                    c.save(receipt_path, receipt)
                if receipt['status'] in [401, 402, 403, 429]:
                    c.save(E / 'rouen-source-image-access-hold.json', receipt)
                    raise RuntimeError('Image source access hold; stopped without alternate retrieval')
                assert receipt['status'] in [200, 404], receipt
                robot = urllib.robotparser.RobotFileParser()
                robot.parse(raw.decode(errors='replace').splitlines() if receipt['status'] == 200 else [])
                robots[origin] = robot
            assert robots[origin].can_fetch('ArtlineResearch', url), ('Robots restriction', url)
            assert shutil.disk_usage(O).free >= RESERVE + 16 * 1024**2
            assert used() + 16 * 1024**2 <= BUDGET, 'Finite combined metadata/image budget hold'
            out = dict(at=c.now(), artwork_id=row['artwork_id'], native_id=row['native_id'],
                       candidate=number, title=row['title'], source_page=row['notice_receipt']['url'],
                       source_page_receipt=row['notice_receipt'], image_url=url,
                       credit=row['notice_fields'].get('Crédits photographiques'),
                       source_fields=row['notice_fields'], state='held')
            began = time.monotonic()
            try:
                with session.get(url, stream=True, timeout=(8, 30), allow_redirects=False) as response:
                    if response.status_code in [401, 402, 403, 429]:
                        hold = dict(at=c.now(), url=url, status=response.status_code)
                        c.save(E / 'rouen-source-image-access-hold.json', hold)
                        raise RuntimeError('SOURCE_ACCESS_HOLD')
                    assert response.status_code == 200, ('Image HTTP', response.status_code)
                    content_type = response.headers.get('Content-Type', '').split(';')[0].strip().lower()
                    assert content_type.startswith('image/') or content_type in ['', 'application/octet-stream'], ('Unexpected source MIME', content_type)
                    assert int(response.headers.get('Content-Length', '0')) <= 12_000_000, 'Native Content-Length exceeds finite cap'
                    chunks, size = [], 0
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        assert size <= 12_000_000, 'Native image exceeds finite source-byte cap'
                        chunks.append(chunk)
                    raw = b''.join(chunks)
                    rc = dict(url=url, status=200, at=c.now(), bytes=len(raw), sha256=c.sha(raw),
                              content_type=response.headers.get('Content-Type'))
                original = O / 'originals' / (key + '.source')
                original.parent.mkdir(exist_ok=True)
                original.write_bytes(raw)
                with Image.open(io.BytesIO(raw)) as opened:
                    assert opened.width * opened.height <= 36_000_000, 'Source exceeds finite pixel cap'
                    opened.load()
                    oriented = ImageOps.exif_transpose(opened)
                    alpha = oriented.mode in ['RGBA', 'LA'] or 'transparency' in oriented.info
                    if alpha:
                        rgba = oriented.convert('RGBA')
                        full = Image.new('RGB', rgba.size, 'white')
                        full.paste(rgba, mask=rgba.getchannel('A'))
                    else:
                        full = oriented.convert('RGB')
                assert min(full.size) >= 150 and max(full.size) >= 400, ('Small source view', full.size)
                for edge in [1400, 1200, 1050, 900, 800, 700, 600]:
                    resized = full.copy()
                    resized.thumbnail((edge, edge), Image.Resampling.LANCZOS)
                    for quality in [88, 82, 76, 70, 64, 58]:
                        output = io.BytesIO()
                        resized.save(output, 'JPEG', quality=quality, optimize=True)
                        if len(output.getvalue()) <= 100000:
                            break
                    if len(output.getvalue()) <= 100000:
                        break
                binary = output.getvalue()
                assert 1000 < len(binary) <= 100000
                path = O / 'derivatives' / (key + '.jpg')
                path.parent.mkdir(exist_ok=True)
                path.write_bytes(binary)
                out.update(state='prepared_pending_visual_review', path=str(path), original_path=str(original),
                           source_receipt=rc, source_dimensions=full.size, width=resized.width, height=resized.height,
                           bytes=len(binary), sha256=c.sha(binary), rights_status='unknown',
                           rights_basis='Source photographic credit retained. Etalab metadata licence is not an image licence; no CC/public-domain image claim inferred.',
                           transformation='Complete supplied frame retained; EXIF orientation, proportional reduction and JPEG compression only.' + (' Transparent pixels composited on white.' if alpha else ''))
            except Exception as error:
                out.update(reason=repr(error))
                if 'SOURCE_ACCESS_HOLD' in str(error):
                    raise
            c.save(dest, out)
            print(key, out['state'], out.get('bytes', out.get('reason')), flush=True)
            time.sleep(max(0, 1.1 - (time.monotonic() - began)))


def sheets():
    ready = [c.load(path) for path in sorted((E / 'image-preparation').glob('*.json'))]
    ready = [row for row in ready if row['state'] == 'prepared_pending_visual_review']
    assert len({(r['native_id'], r['candidate']) for r in ready}) == len(ready)
    already = {(r['native_id'], r['candidate'], r['image_sha256'])
               for path in E.glob('actual-image-review-*.json')
               for r in c.load(path)['decisions']}
    ready = [r for r in ready if (r['native_id'], r['candidate'], r['sha256']) not in already]
    folder = O / ('review-unreviewed-' + str(len(ready)))
    folder.mkdir(exist_ok=True)
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 16)
    index = []
    for offset in range(0, len(ready), 9):
        rows = ready[offset:offset + 9]
        canvas = Image.new('RGB', (1650, 1740), '#e8e6e2')
        draw = ImageDraw.Draw(canvas)
        for i, row in enumerate(rows):
            x, y = i % 3 * 550, i // 3 * 580
            with Image.open(row['path']) as photo:
                photo.thumbnail((530, 460), Image.Resampling.LANCZOS)
                canvas.paste(photo, (x + (550 - photo.width) // 2, y + (460 - photo.height) // 2))
            lines = [str(offset + i + 1) + ' ' + row['native_id'] + ' view ' + str(row['candidate']),
                     row['title'][:64], (row['source_fields'].get('Auteur') or 'Unknown source maker')[:64],
                     'Inventory: ' + (row['source_fields'].get("Numéro d'inventaire") or '')[:54]]
            for j, line in enumerate(lines):
                draw.text((x + 8, y + 468 + j * 24), line, font=font, fill='black')
        path = folder / ('review-sheet-' + str(offset // 9 + 1).zfill(3) + '.jpg')
        canvas.save(path, quality=93)
        index.append(dict(path=str(path), sha256=c.sha(path.read_bytes()),
                          candidates=[dict(native_id=r['native_id'], candidate=r['candidate'], artwork_id=r['artwork_id']) for r in rows]))
    c.save(E / ('unreviewed-image-contact-sheets-' + str(len(ready)) + '.json'), dict(at=c.now(), prepared=len(ready), sheets=index,
           actual_visual_review_complete=False, production_writes=0))
    print(json.dumps(dict(prepared=len(ready), sheets=len(index))), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['select', 'prepare', 'sheets'])
    parser.add_argument('--selection')
    args = parser.parse_args()
    if args.phase == 'prepare':
        assert args.selection
        prepare(args.selection)
    else:
        globals()[args.phase]()
