#!/usr/bin/env python3
"""Selected alternate photographs for existing French national catalogue works.

Require the exact Joconde identifier before searching. Images retain the native
database key and use the existing audited Joconde attachment adapter.
"""
import argparse
import datetime
import fcntl
import hashlib
import importlib.util
import json
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


photo = load('photo', 'research-popular-painting-photos.py')
joconde = load('joconde', 'overnight-joconde-images.py')
core = joconde.core


def verify_native_source(c, entity):
    if c['external_id'] not in photo.m.values(entity, 'P347'):
        raise ValueError('Exact national catalogue identifier differs')
    photo.m.entity_match(c, entity, require_primary_image=False)


def verified_cached_authority(qid, paths, root=core.ROOT):
    """Reuse a recent, intact public API capture during a source outage.

    Only artwork metadata is cached here. Photograph identity and rights still
    use the separate Commons requests and exact file-revision checks.
    """
    for relative in paths:
        path = (root / relative).resolve()
        if not path.is_relative_to((root / 'docs/research').resolve()):
            raise ValueError('Authority capture outside research evidence')
        capture = json.loads(path.read_text())
        receipt = capture['receipt']
        url = urlsplit(receipt['url'])
        params = parse_qs(url.query)
        if (url.scheme, url.hostname, url.path) != ('https', 'www.wikidata.org', '/w/api.php') or params.get('action') != ['wbgetentities'] or qid not in params.get('ids', [''])[0].split('|'):
            raise ValueError('Authority capture source or requested identity differs')
        retrieved = datetime.datetime.fromisoformat(receipt['retrieved_at'].replace('Z', '+00:00'))
        age = (datetime.datetime.now(datetime.timezone.utc) - retrieved).total_seconds()
        if not 0 <= age <= 48 * 3600:
            continue
        key = hashlib.sha256(receipt['url'].encode()).hexdigest()
        original = path.parent.parent / 'wikidata-evidence' / (key + '.json')
        content = original.read_bytes()
        if hashlib.sha256(content).hexdigest() != receipt['sha256'] or len(content) != receipt['bytes']:
            raise ValueError('Authority response checksum or byte size differs')
        entity = json.loads(content).get('entities', {}).get(qid)
        if not entity or entity != capture['entity'] or entity.get('id') != qid:
            raise ValueError('Authority extraction differs from the original response')
        return entity, receipt
    raise ValueError('No intact authority capture within 48 hours; defer source research')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--deadline', required=True, type=float)
    parser.add_argument('--authority-cache-index', type=Path,
                        help='Explicit fallback to intact artwork-only API captures less than 48 hours old')
    args = parser.parse_args()
    lock = (args.run / 'worker.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert (args.run.parent / 'backups.json').exists()
    rows = json.loads((args.run / 'candidates.json').read_text())['candidates']
    done = core.latest_events(args.run)
    fetch = core.Fetcher(args.run / 'metadata')
    index = json.loads(args.authority_cache_index.read_text()) if args.authority_cache_index else None
    for start in range(0, len(rows), 25):
        group = [c for c in rows[start:start + 25] if c['artwork_id'] not in done]
        if not group or time.time() >= args.deadline:
            continue
        entities = {} if index is not None else photo.m.api(fetch, 'www.wikidata.org', {
            'action': 'wbgetentities', 'ids': '|'.join(c['qid'] for c in group),
            'props': 'claims|labels|aliases', 'languages': 'en|mul|fr|de|it|nl|ru'})['entities']
        for c in group:
            if time.time() >= args.deadline:
                break
            try:
                entity, authority_receipt = (verified_cached_authority(c['qid'], index.get(c['qid'], []))
                                             if index is not None else (entities[c['qid']], None))
                verify_native_source(c, entity)
                image = photo.research(c, entity, fetch, args.run,
                                       independent_photographers_only=True, extended_search=True)
                image.update(provider='night-joconde', source_name=core.PROVIDERS['night-joconde'],
                             source_record_url='https://pop.culture.gouv.fr/notice/joconde/' + c['external_id'],
                             source_object_id=c['external_id'])
                if authority_receipt:
                    image['raw']['reused_artwork_authority_receipt'] = authority_receipt
                core.save_new(args.run / 'selected/night-joconde' / (c['artwork_id'] + '.json'), image)
                core.worker('night-joconde', [c], SimpleNamespace(run=args.run, prepare_only=True), None)
            except (ValueError, KeyError) as exc:
                core.event(args.run, {'provider': 'night-joconde', 'artwork_id': c['artwork_id'],
                                     'outcome': 'manual_review', 'reason': str(exc)})
            print(core.now(), 'National catalogue photograph outcomes',
                  len(core.latest_events(args.run)), 'of', len(rows), flush=True)


if __name__ == '__main__':
    main()
