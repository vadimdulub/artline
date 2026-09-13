#!/usr/bin/env python3
"""Recover selected retired Met IDs from exact museum-donated Commons files.

Uses saved Commons API responses with current file-level CC0 and original
museum XML identifying the exact existing object. No catalogue ID remapping.
"""
import argparse
import html
import importlib.util
import json
from pathlib import Path
import re
from types import SimpleNamespace
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location('enrichment', Path(__file__).with_name('enrich-artwork-images.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def identity_and_rights(candidate, response):
    pages = list(response.get('query', {}).get('pages', {}).values())
    if len(pages) != 1 or pages[0].get('ns') != 6:
        raise ValueError('Expected one Commons file')
    page = pages[0]
    info = page['imageinfo'][0]
    meta = info['extmetadata']
    value = lambda key: meta.get(key, {}).get('value', '')
    if (value('License') != 'cc0' or value('LicenseShortName') != 'CC0' or
        value('LicenseUrl') not in ('http://creativecommons.org/publicdomain/zero/1.0/deed.en',
                                   'https://creativecommons.org/publicdomain/zero/1.0/deed.en') or
        value('Restrictions')):
        raise ValueError('Current file does not have unrestricted CC0 evidence')
    text = page['revisions'][0]['slots']['main']['*']
    match = re.search(r'<metadata_raw>\s*(.*?)\s*</metadata_raw>', text, re.S)
    if not match:
        raise ValueError('Missing original museum metadata')
    museum = ET.fromstring(html.unescape(match[1]))
    field = lambda key: (museum.findtext(key) or '').strip()
    expected_url = '/art/collection/search/' + candidate['external_id']
    link = urlparse(field('Link_Resource'))
    if (field('Object_ID') != candidate['external_id'] or
        link.hostname != 'www.metmuseum.org' or link.path != expected_url):
        raise ValueError('Donated museum object identity mismatch')
    normalize = lambda text: ''.join(c for c in text.casefold() if c.isalnum())
    if (normalize(field('Title')) != normalize(candidate['title']) or
        normalize(field('Artist_Display_Name')) != normalize(candidate['artist'])):
        raise ValueError('Donated title or artist differs from selected artwork')
    if field('Is_Public_Domain') != 'True' or field('Rights_and_Reproduction'):
        raise ValueError('Original museum image rights conflict')
    if normalize(page['title']) != normalize('File:' + field('Filename') + '.jpg'):
        raise ValueError('Donated metadata names a different image file')
    start, end = int(field('Object_Begin_Date')), int(field('Object_End_Date'))
    if not start or not end or start > end or end > 1970:
        raise ValueError('Donated museum dates need review')
    source = urlparse(field('Image_Url'))
    if source.hostname != 'images.metmuseum.org' or not source.path.lower().endswith('.jpg'):
        raise ValueError('Unexpected donated museum image URL')
    upload = urlparse(info['url'])
    if upload.scheme != 'https' or upload.hostname != 'upload.wikimedia.org' or info['mime'] != 'image/jpeg':
        raise ValueError('Unexpected Commons image URL or MIME type')
    if info['size'] > 8_000_000:
        raise ValueError('Donated image exceeds source byte budget')
    return {**candidate, 'provider':'met-commons', 'page':info['descriptionurl'],
            'source_image_url':info['url'], 'raw':response, 'rights_status':'cc0',
            'license_label':'CC0 1.0', 'policy_url':'https://creativecommons.org/publicdomain/zero/1.0/',
            'checked_at':module.now(), 'commons_revision':page['revisions'][0]['revid'],
            'commons_original_sha1':info['sha1'], 'donor_object_id':field('Object_ID'),
            'donor_image_url':field('Image_Url'), 'donor_creation_start':start,
            'donor_creation_end':end,
            'identity_basis':'Exact Object_ID and Link_Resource in original museum-donated XML; title and artist match; current Commons file CC0'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    latest = {}
    for line in (args.after / 'events.jsonl').read_text().splitlines():
        event = json.loads(line)
        if event.get('artwork_id'):
            latest[event['artwork_id']] = event
    rows = json.loads((args.after / 'candidates.json').read_bytes())['candidates']
    selected = []
    for candidate in rows:
        metadata = args.run / 'metadata' / (candidate['external_id'] + '.json')
        if candidate['provider'] != 'met' or not metadata.exists():
            continue
        event = latest.get(candidate['artwork_id'], {})
        if event.get('outcome') != 'failed' or '404 Client Error' not in event.get('error', ''):
            raise ValueError('Recovery requires a confirmed failed retired Met ID')
        path = args.run / 'selected/met-commons' / (candidate['artwork_id'] + '.json')
        if path.exists():
            image = json.loads(path.read_bytes())
        else:
            data = metadata.read_bytes()
            capture = json.loads(metadata.with_suffix('.receipt.json').read_bytes())
            if module.sha(data) != capture['sha256']:
                raise ValueError('Saved Commons metadata checksum mismatch')
            image = identity_and_rights(candidate, json.loads(data))
            image['commons_capture'] = capture
            module.save_new(path, image)
        selected.append({**candidate, 'provider':'met-commons'})
    if not selected:
        raise ValueError('No exact recoverable museum files')
    module.save_new(args.run / 'candidates.json', {'candidates':selected, 'after':str(args.after),
                    'selection':'Only failed existing Met IDs with exact donated Commons metadata'})
    completed = set()
    if (args.run / 'events.jsonl').exists():
        for line in (args.run / 'events.jsonl').read_text().splitlines():
            event = json.loads(line)
            if event.get('outcome') == 'complete':
                completed.add(event['artwork_id'])
    pending = [c for c in selected if c['artwork_id'] not in completed]
    module.worker('met-commons', pending, SimpleNamespace(run=args.run), module.cloud_dsn())


if __name__ == '__main__':
    main()
