#!/usr/bin/env python3
"""Revalidate selected Commons file leads using explicit artwork identities.

Discovery tags do not confirm identity. The existing exact artwork-template or
digital-representation checks, original-photo checks and licence checks must all
pass. This command only prepares files; visual review and delivery are separate.
"""
import argparse
import fcntl
import importlib.util
import json
import re
import time
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('photo', Path(__file__).with_name('research-popular-painting-photos.py'))
photo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(photo)
m = photo.m
core = m.core


def verify_photo_origin(c, page):
    photo.verify_original_photograph(c, page)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--deadline', required=True, type=float)
    args = parser.parse_args()
    lock = (args.run / 'worker.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert (args.run.parent / 'backups.json').exists()
    rows = json.loads((args.run / 'candidates.json').read_text())['candidates']
    fetch = core.Fetcher(args.run / 'metadata')
    done = core.latest_events(args.run)
    for c in rows:
        if time.time() >= args.deadline:
            break
        if c['artwork_id'] in done:
            continue
        try:
            entity = m.api(fetch, 'www.wikidata.org', {
                'action': 'wbgetentities', 'ids': c['qid'], 'props': 'claims|labels|aliases',
                'languages': 'en|mul|fr|de|it|nl|ru'})['entities'][c['qid']]
            m.entity_match(c, entity, require_primary_image=False)
            response = m.api(fetch, 'commons.wikimedia.org', {
                'action': 'query', 'titles': c['discovery_file_title'],
                'prop': 'imageinfo|revisions', 'iiprop': 'url|extmetadata|sha1|size|mime',
                'iiurlwidth': 960, 'rvprop': 'ids|content', 'rvslots': 'main'})
            page = m.page_for_filename(response, c['discovery_file_title'].removeprefix('File:'))
            mid = 'M' + str(page['pageid'])
            structured = m.api(fetch, 'commons.wikimedia.org', {
                'action': 'wbgetentities', 'ids': mid, 'props': 'claims'})['entities'][mid]
            photo.exact_photo(c, page, structured)
            verify_photo_origin(c, page)
            try:
                rendered = m.rendered_rights_uri(fetch, page)
            except ValueError as exc:
                if str(exc) != 'Explicit rendered image licence absent or conflicting':
                    raise
                spec = importlib.util.spec_from_file_location('split', Path(__file__).with_name('commons-photograph-licence.py'))
                split = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(split)
                rendered = split.resolve(fetch, c, page, m, structured)
            image = photo.candidate_image(c, entity, page, structured, rendered, {
                'method': 'Fresh exact-file and explicit physical-artwork identity verification',
                'independent_photographers_only': True})
            core.save_new(args.run / 'selected/night-commons' / (c['artwork_id'] + '.json'), image)
            core.worker('night-commons', [c], SimpleNamespace(run=args.run, prepare_only=True), None)
        except (ValueError, KeyError) as exc:
            core.event(args.run, {'provider': 'night-commons', 'artwork_id': c['artwork_id'],
                                 'outcome': 'manual_review', 'reason': str(exc)})
        print(core.now(), 'Exact-file sources examined', len(core.latest_events(args.run)),
              'of', len(rows), flush=True)


if __name__ == '__main__':
    main()
