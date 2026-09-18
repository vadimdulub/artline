#!/usr/bin/env python3
"""Bounded Commons searches for existing popular-painter painting gaps.

Search terms are discovery leads. Existing artwork authority, museum, creator,
date, original photograph provenance and exact image licence are revalidated.
This command prepares images; existing audited writers deliver them separately.
"""
import argparse
import collections
import fcntl
import importlib.util
import json
import re
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qsl, urlsplit

spec = importlib.util.spec_from_file_location('commons', Path(__file__).with_name('overnight-commons-images.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
core = m.core


def source_key(url):
    parts = urlsplit(url or '')
    host = (parts.hostname or '').removeprefix('www.')
    if parts.scheme not in ('https', 'http'):
        return None
    query = [(k, v) for k, v in parse_qsl(parts.query)
             if not k.startswith('utm_') and not (host == 'marmottan.fr' and k == 'is')]
    return host, parts.path.rstrip('/'), tuple(sorted(query))


def exact_native_file(c, page, text):
    """Require an exact museum object URL, labelled accession and artist.

    The search result, filename and an unqualified museum homepage cannot
    satisfy this route. Object-specific URL parameters remain significant.
    """
    return m.exact_native_file(c, page, text)


def exact_photo(c, page, structured):
    if page.get('ns') != 6 or not page.get('title', '').startswith('File:'):
        raise ValueError('Not a Commons file')
    if re.search(r'\b(detail|détail|collage|montage|verso|reverse|cropped)\b', page['title'], re.I):
        raise ValueError('Partial or composite reproduction needs manual review')
    m.verify_structured_object(c, structured)
    text = page.get('revisions', [{}])[0].get('slots', {}).get('main', {}).get('*', '')
    if re.search(r'\b(annotated|diagram|schema prospettico|perspective analysis|analysis overlay)\b', page['title'] + '\n' + text, re.I):
        raise ValueError('Annotated or diagrammatic reproduction needs manual review')
    categories = ' '.join(re.findall(r'\[\[Category:([^]|]+)', text, re.I))
    if re.search(r'\b(details|works after|copies|replicas|posters|souvenirs)\b', categories, re.I):
        raise ValueError('File category identifies a detail, copy or derivative object')
    if re.search(r'digitally desaturated|black and white reproductions of paintings in colou?r|colou?ri[sz]ed', text, re.I):
        raise ValueError('Artificially altered artwork colour requires review')
    explicit = set(re.findall(r'\|\s*wikidata\s*=\s*(Q\d+)\b', text, re.I))
    if explicit and explicit != {c['qid']}:
        raise ValueError('File artwork template names another physical object')
    if m.ids(structured, 'P6243') != {c['qid']} and explicit != {c['qid']} and not exact_native_file(c, page, text):
        raise ValueError('File lacks an exact artwork template or structured object identity')
    info = page.get('imageinfo', [{}])[0]
    if min(info.get('width', 0), info.get('height', 0)) < 300:
        raise ValueError('Source image too small for this selected pass')


def queries(c):
    title = re.sub(r'["\\\r\n]', ' ', c['title']).strip()[:160]
    artist = re.sub(r'["\\\r\n]', ' ', c['artist']).strip()
    return [f"{c['qid']} OR haswbstatement:P6243={c['qid']}", f'"{title}" "{artist}"']


def extended_queries(c, entity):
    """Bounded source-native categories/titles, always followed by exact matching."""
    clean = lambda value: re.sub(r'["\\\r\n]', ' ', str(value)).strip()[:160]
    result = []
    for category in m.values(entity, 'P373'):
        if isinstance(category, str) and category.strip():
            result.append('incategory:"' + clean(category) + '"')
    artist = clean(c['artist'])
    titles = [c.get('alternate_title')]
    titles.extend(entity.get('labels', {}).get(language, {}).get('value') for language in ('ru', 'de', 'fr', 'it', 'nl'))
    seen = {m.norm(c['title'])}
    for title in titles:
        if title and m.norm(title) not in seen:
            seen.add(m.norm(title))
            result.append(f'"{clean(title)}" "{artist}"')
    return list(dict.fromkeys(result))[:4]


def accession_queries(c, entity):
    """Exact inventory and native creator names are discovery only, never proof."""
    clean = lambda value: re.sub(r'["\\\r\n]', ' ', str(value)).strip()[:160]
    result = []
    if c.get('accession_number'):
        query = '"' + clean(c['accession_number']) + '"'
        if re.fullmatch(r'[\d ._-]+', c['accession_number']) and c.get('artist'):
            query += ' "' + clean(c['artist']) + '"'
        result.append(query)
    native = entity.get('labels', {}).get('ru', {}).get('value')
    if native:
        result.append('"' + clean(native) + '"')
    return result


def candidate_image(c, entity, page, structured, rendered, discovery):
    exact_photo(c, page, structured)
    info, credit, label, uri, status, url, original = m.rights_and_identity(c, entity, page, structured, rendered)
    im = dict(c, page=info['descriptionurl'], source_image_url=url, policy_url=uri,
              rights_status=status, license_label=label, checked_at=core.now(),
              raw={'wikidata': entity, 'commons': page, 'structured_data': structured,
                   'independent_photo_discovery': discovery}, creator_credit=credit,
              source_name='Wikimedia Commons', source_record_url=info['descriptionurl'],
              image_url=url, image_license=label, image_license_url=uri,
              rights_statement=label, creator=c['artist'], creation_date=c['date_display'],
              source_object_id=c['qid'], rights_verified_at=core.now())
    if rendered:
        im['rendered_licence_evidence'] = rendered
    if original:
        im['commons_original_sha1'] = info['sha1']
    im['attribution_text'] = (f"{c['artist']}. {c['title']}. Image credit: {credit}. "
                              f"{info['descriptionurl']}. {label} ({uri}). "
                              'Full-frame proportional resize and JPEG compression; applicable ShareAlike terms retained.')
    return im


def rendered_photo_rights(fetch, c, page, structured):
    """Keep the strict file-revision proof for separately licensed photos."""
    try:
        return m.rendered_rights_uri(fetch, page)
    except ValueError as exc:
        if str(exc) != 'Explicit rendered image licence absent or conflicting':
            raise
        if m.origin.verify(c, page) != 'independent_photographer':
            raise ValueError('Separate photo licence requires independent original photography')
        spec = importlib.util.spec_from_file_location('photo_licence', Path(__file__).with_name('commons-photograph-licence.py'))
        split = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(split)
        return split.resolve(fetch, c, page, m, structured)


def verify_original_photograph(c, page):
    """A transferring or retouching account is not the original photographer."""
    if m.origin.verify(c, page) != 'independent_photographer':
        raise ValueError('Independent original photographer required')
    meta = page.get('imageinfo', [{}])[0].get('extmetadata', {})
    source = m.plain(' '.join(meta.get(k, {}).get('value', '') for k in ('Credit', 'Attribution')))
    if not re.search(r'own work|own photo|self-photographed|photographie personnelle', source, re.I):
        raise ValueError('Explicit original-photograph statement required')
    if re.search(r'scann?ed|original uploader|book|DVD|digital processing|retouch|modifications made|colou?rs? adjusted', source, re.I):
        raise ValueError('Scan, transfer or image-editor attribution requires review')
    if not m.photographic_credits(c, page):
        raise ValueError('Original photographer credit required')


def research(c, entity, fetch, run, require_primary_image=False, independent_photographers_only=False, extended_search=False):
    primary = m.entity_match(c, entity, require_primary_image=require_primary_image)
    rejected_path = run / 'prior-rejected-commons-files.json'
    if not rejected_path.exists():
        rejected_path = run.parent / 'prior-rejected-commons-files.json'
    rejected = set(json.loads(rejected_path.read_text())['titles']) if rejected_path.exists() else set()
    seen, held, searches = set(), [], []
    search_queries = queries(c) + (extended_queries(c, entity) + accession_queries(c, entity) if extended_search else [])
    for stage, query in enumerate(search_queries):
        result = m.api(fetch, 'commons.wikimedia.org', {
            'action': 'query', 'list': 'search', 'srsearch': query,
            'srnamespace': 6, 'srlimit': 25, 'srprop': ''})
        searches.append({'query': query, 'response': result, 'retrieved_at': core.now()})
        titles = [x['title'] for x in result.get('query', {}).get('search', [])]
        if stage == 0 and primary:
            titles.insert(0, 'File:' + primary)
        titles = list(dict.fromkeys(t for t in titles if t not in seen))
        seen.update(titles)
        for title in titles:
            if title.replace('_', ' ') in rejected:
                held.append({'title': title, 'reason': 'Previously rejected file retained on hold; a different source image is required'})
        titles = [t for t in titles if t.replace('_', ' ') not in rejected]
        for start in range(0, len(titles), 10):
            part = titles[start:start + 10]
            data = m.api(fetch, 'commons.wikimedia.org', {
                'action': 'query', 'titles': '|'.join(part), 'prop': 'imageinfo|revisions',
                'iiprop': 'url|extmetadata|sha1|size|mime', 'iiurlwidth': 960,
                'rvprop': 'ids|content', 'rvslots': 'main'})
            pages = [p for p in data.get('query', {}).get('pages', {}).values() if p.get('imageinfo')]
            mids = ['M' + str(p['pageid']) for p in pages]
            structured = m.api(fetch, 'commons.wikimedia.org', {
                'action': 'wbgetentities', 'ids': '|'.join(mids), 'props': 'claims'})['entities'] if mids else {}
            for page in pages:
                try:
                    sdc = structured.get('M' + str(page['pageid']), {})
                    exact_photo(c, page, sdc)
                    rendered = rendered_photo_rights(fetch, c, page, sdc)
                    im = candidate_image(c, entity, page, sdc, rendered,
                                         {'method': 'Exact artwork authority and title searches', 'searches': searches})
                    if independent_photographers_only:
                        verify_original_photograph(c, page)
                    im['raw']['independent_photo_discovery']['independent_photographers_only'] = independent_photographers_only
                    core.save_new(run / 'discovery' / (c['artwork_id'] + '.json'), {
                        'at': core.now(), 'artwork_id': c['artwork_id'], 'files_considered': len(seen),
                        'held': held, 'selected': im['page']})
                    return im
                except (ValueError, KeyError) as exc:
                    held.append({'pageid': page['pageid'], 'title': page['title'], 'reason': str(exc)})
    core.save_new(run / 'discovery' / (c['artwork_id'] + '.json'), {
        'at': core.now(), 'artwork_id': c['artwork_id'], 'files_considered': len(seen),
        'held': held, 'selected': None})
    raise ValueError('No exact, independently sourced and rights-cleared full painting photograph')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--limit', type=int, default=30)
    p.add_argument('--deadline', type=float, required=True)
    p.add_argument('--independent-photographers-only', action='store_true',
                   help='Skip museum-origin reproductions unless researched separately under exact native rights')
    p.add_argument('--extended-search', action='store_true', help='Also search authoritative Commons categories and source-native titles')
    a = p.parse_args()
    lock = (a.run / 'worker.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert (a.run.parent / 'backups.json').exists()
    all_rows = json.loads((a.run / 'candidates.json').read_text())['candidates']
    assert all(c['popular'] and c['work_type'] == 'painting' for c in all_rows)
    done = {k for k, v in core.latest_events(a.run).items()
            if v['outcome'] in ('prepared', 'complete', 'manual_review', 'failed')}
    rows = sorted((c for c in all_rows if c['artwork_id'] not in done),
                  key=lambda c: (c['artist'] != 'Claude Monet', c['artist'], c['title']))[:a.limit]
    fetch = core.Fetcher(a.run / 'metadata')
    for start in range(0, len(rows), 25):
        if time.time() >= a.deadline:
            break
        group = rows[start:start + 25]
        entities = m.api(fetch, 'www.wikidata.org', {
            'action': 'wbgetentities', 'ids': '|'.join(c['qid'] for c in group),
            'props': 'claims|labels|aliases', 'languages': 'en|mul|fr|it|nl|de|ru|el|sv|da|fi|es|pt|nb|pl'})['entities']
        for c in group:
            if time.time() >= a.deadline:
                break
            path = a.run / 'selected/night-commons' / (c['artwork_id'] + '.json')
            try:
                if not path.exists():
                    im = research(c, entities.get(c['qid'], {}), fetch, a.run,
                                  independent_photographers_only=a.independent_photographers_only,
                                  extended_search=a.extended_search)
                    core.save_new(path, im)
                core.worker('night-commons', [c], SimpleNamespace(run=a.run, prepare_only=True), None)
            except (ValueError, KeyError) as exc:
                core.event(a.run, {'provider': 'night-commons', 'artwork_id': c['artwork_id'],
                                  'external_id': c['qid'], 'outcome': 'manual_review', 'reason': str(exc)})
            counts = collections.Counter(x['outcome'] for x in core.latest_events(a.run).values())
            print(core.now(), 'Popular painting photographs', sum(counts.values()),
                  'source outcomes', dict(counts), flush=True)


if __name__ == '__main__':
    main()
