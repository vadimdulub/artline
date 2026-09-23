#!/usr/bin/env python3
"""Download selected Met CC0 images for review without mutating catalogues."""
import argparse
import importlib.util
import io
import json
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image
import requests

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('core', ROOT/'ops/enrich-artwork-images.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
REFERENCE = ROOT/'docs/research/open-access-image-gaps-20260919-met-pd'
OBJECTS = ('341074', '735290', '45092', '717624', '45090',
           '717616', '48892', '717617', '45074', '52009')
CC0 = 'https://creativecommons.org/publicdomain/zero/1.0/'
SOURCE_ROOT = Path('/Users/vadimdulub/Library/Application Support/Artline/source-images')


def validate(obj, oid):
    if str(obj.get('objectID')) != oid:
        raise ValueError('Object identity differs')
    if obj.get('isPublicDomain') is not True or obj.get('rightsAndReproduction'):
        raise ValueError('No explicit current Open Access image designation')
    lo, hi = obj.get('objectBeginDate'), obj.get('objectEndDate')
    if type(lo) is not int or type(hi) is not int or not 1000 <= lo <= hi <= 1955 or not obj.get('objectDate'):
        raise ValueError('Creation interval does not establish age over 70 years')
    image = obj.get('primaryImage')
    if urlparse(image or '').scheme != 'https' or urlparse(image).hostname != 'images.metmuseum.org':
        raise ValueError('No official primary image')
    core.validate_source_image_identity({'provider': 'met', 'external_id': oid,
                                         'source_image_url': obj.get('primaryImageSmall')})
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    args.run.mkdir(parents=True, exist_ok=True)
    fetch = core.Fetcher(args.run/'metadata')
    fetch.defer_long_cooldowns = True
    leads = {c['external_id']: c for c in json.loads((REFERENCE/'candidates.json').read_text())['candidates']}
    old = core.latest_events(REFERENCE)
    selected, held = [], []
    # Finish bounded metadata selection before fetching any image bytes.
    for oid in OBJECTS:
        try:
            url = 'https://collectionapi.metmuseum.org/public/collection/v1/objects/'+oid
            obj = fetch.metadata(url)
            image = validate(obj, oid)
            lead = leads[oid]
            selected.append({'object_id': oid, 'title': obj['title'], 'artist': obj['artistDisplayName'],
                             'date': obj['objectDate'], 'source_image_url': image,
                             'source_page_url': obj['objectURL'], 'license_url': CC0,
                             'catalogue_artwork_id': lead['artwork_id'],
                             'catalogue_hold': old.get(lead['artwork_id'], {}).get('error'),
                             'metadata_sha256': core.sha(core.encode(obj)), 'object': obj})
            print('Current Open Access verified', oid, obj['title'], flush=True)
        except Exception as error:
            held.append({'object_id': oid, 'reason': str(error)[:400]})
            if isinstance(error, core.SourceCooldown) or isinstance(error, requests.HTTPError) and error.response.status_code in (403, 429):
                print('Source access/cooldown pause; no alternative access route attempted', flush=True)
                break
    core.save_new(args.run/'selection.json', {'selected': selected, 'held': held,
        'policy': 'Exact current Met CC0 and official image URLs; source creation intervals end by 1955. Local review download only; catalogue mismatches remain unresolved. No age-based rights inference.'})
    complete, failures = [], []
    for entry in selected:
        oid = entry['object_id']
        try:
            receipt_path = args.run/'receipts'/(oid+'.json')
            if receipt_path.exists():
                receipt = json.loads(receipt_path.read_text())
                assert core.sha(Path(receipt['source_file']).read_bytes()) == receipt['source_sha256']
                assert core.sha(Path(receipt['review_file']).read_bytes()) == receipt['review_sha256']
                complete.append(receipt)
                continue
            data, headers = fetch.get(entry['source_image_url'], limit=20_000_000)
            with Image.open(io.BytesIO(data)) as original:
                if original.format != 'JPEG':
                    raise ValueError('Expected original JPEG')
                width, height = original.size
                original.verify()
            compressed, w, h, quality = core.compress(data)
            source = SOURCE_ROOT/args.run.name/(oid+'-'+core.sha(data)[:16]+'.jpg')
            review = args.run/'images'/(oid+'-'+core.sha(compressed)[:16]+'.jpg')
            core.save_new(source, data)
            core.save_new(review, compressed)
            receipt = {k: v for k, v in entry.items() if k != 'object'}
            receipt.update(retrieved_at=core.now(), source_file=str(source), source_sha256=core.sha(data),
                           source_bytes=len(data), source_width=width, source_height=height,
                           review_file=str(review.resolve()), review_sha256=core.sha(compressed),
                           review_bytes=len(compressed), review_width=w, review_height=h, headers=headers,
                           attachment_status='not_attached_pending_catalogue_reconciliation')
            core.save_new(receipt_path, receipt)
            complete.append(receipt)
            print('Downloaded', oid, len(data), 'bytes; retained separately for review', flush=True)
        except Exception as error:
            failures.append({'object_id': oid, 'reason': str(error)[:400]})
            if isinstance(error, core.SourceCooldown) or isinstance(error, requests.HTTPError) and error.response.status_code in (403, 429):
                break
    report = {'at': core.now(), 'requested_objects': len(OBJECTS), 'rights_cleared_selected': len(selected),
              'downloaded': len(complete), 'original_bytes': sum(r['source_bytes'] for r in complete),
              'review_bytes': sum(r['review_bytes'] for r in complete), 'held': held, 'failures': failures,
              'catalogue_mutations': 0, 'cloud_uploads': 0, 'records': complete}
    core.save_new(args.run/'download-report.json', report)
    print(json.dumps({k: v for k, v in report.items() if k != 'records'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
