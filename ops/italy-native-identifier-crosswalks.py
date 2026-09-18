#!/usr/bin/env python3
"""Find artwork authorities by exact SIRBeC identifiers in a bounded gap cohort."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import re
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('crosswalks', ROOT / 'ops/italy-image-crosswalks.py')
x = importlib.util.module_from_spec(spec)
spec.loader.exec_module(x)
c, w = x.c, x.w
OUT = c.RUN / 'native-identifier-crosswalks'


def discover(limit, lowercase_only=False):
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for record in c.load(c.RUN / 'eligible-image-gaps.json'):
        if record['work_type'] != 'painting' or record['scope_basis'] != 'Italian museum identity':
            continue
        pattern = r'[A-Za-z0-9]{5}-[0-9]{5}' if lowercase_only else r'[A-Z0-9]{5}-[0-9]{5}'
        ids = [i for i in record['identifiers'] if re.fullmatch(pattern, i['id'])
               and i.get('url') and 'lombardiabeniculturali.it/opere-arte/' in i['url']]
        if lowercase_only:
            ids = [i for i in ids if re.search(r'[a-z]', i['id'])]
        if len(ids) == 1:
            rows.append(dict(record, native_identifier=ids[0]))
    rows = sorted(rows, key=lambda r: (r['institution_slug'], r['artwork_id']))[:limit]
    c.save(OUT / 'selected-gap-cohort.json', {'limit': limit, 'rows': rows,
           'scope': 'Only existing eligible selected painting gaps in Italian museum identities; metadata queries only'})
    fetcher = w.core.Fetcher(OUT / 'captures')
    for start in range(0, len(rows), 40):
        path = OUT / ('batch-' + str(start).zfill(4) + '.json')
        if path.exists():
            continue
        subset = rows[start:start+40]
        source_ids = sorted({r['native_identifier']['id'] for r in subset})
        query = 'SELECT DISTINCT ?source ?work WHERE { VALUES ?source { ' + \
                ' '.join(json.dumps(v) for v in source_ids) + ' } ?work wdt:P3855 ?source. } LIMIT 100'
        data = fetcher.metadata('https://query.wikidata.org/sparql?' + urlencode({'query': query, 'format': 'json'}))
        bindings = data['results']['bindings']
        if len(bindings) >= 100:
            raise ValueError('Exact-ID authority result cap reached; split and review')
        qids = sorted({r['work']['value'].rsplit('/', 1)[-1] for r in bindings})
        entities = {}
        for offset in range(0, len(qids), 20):
            entities.update(w.api(fetcher, 'www.wikidata.org', {'action': 'wbgetentities',
                'ids': '|'.join(qids[offset:offset+20]), 'props': 'labels|aliases|claims',
                'languages': 'it|en|mul|fr|de'})['entities'])
        c.save(path, {'query': query, 'source_ids': source_ids, 'bindings': bindings, 'entities': entities})
        print('Exact native IDs researched', min(start+40, len(rows)), '/', len(rows), 'authorities', len(entities), flush=True)


def select(label, independent_images=False):
    rows = c.load(OUT / 'selected-gap-cohort.json')['rows']
    by_source = {}
    for path in OUT.glob('batch-*.json'):
        data = c.load(path)
        for e in data['entities'].values():
            for sid in w.values(e, 'P3855'):
                by_source.setdefault(sid, {})[e['id']] = (e, str(path.relative_to(ROOT)))
    accepted, held = [], []
    for original in rows:
        identity = original['native_identifier']
        hits = by_source.get(identity['id'], {})
        if len(hits) != 1:
            held.append({'artwork_id': original['artwork_id'], 'source_id': identity['id'],
                'reason': 'No exact authority' if not hits else 'Multiple authorities for native identifier'})
            continue
        entity, capture = next(iter(hits.values()))
        mapping = x.MUSEUMS.get(original['institution_slug'])
        institution_qid = original.get('institution_qid') or (mapping[0] if mapping else None)
        # Both the civic system and its painting gallery are independently
        # documented. Use only the authority actually stated for this object.
        if original['institution_slug'] == 'musei-civici-arte-storia-brescia' and 'Q18751939' in w.ids(entity, 'P195'):
            institution_qid = 'Q18751939'
        if not institution_qid:
            held.append({'artwork_id': original['artwork_id'], 'qid': entity['id'],
                'reason': 'Institution authority mapping needs independent review', 'capture': capture})
            continue
        record = dict(copy.deepcopy(original), qid=entity['id'], institution_qid=institution_qid,
            website_url=mapping[1] if mapping else original['website_url'],
            provider='night-commons', scheme=identity['scheme'], external_id=identity['id'], page=identity['url'],
            artist='; '.join(a['name'] for a in original['creators']))
        labels = entity.get('labels', {})
        source_title = next((labels[lang]['value'] for lang in ('it','en','mul','fr','de') if lang in labels), None)
        if source_title:
            record['catalogue_alternate_title_before_research'] = record.get('alternate_title')
            record['alternate_title'] = source_title
        record['crosswalk_resolution'] = {'method': 'Exact native SIRBeC identifier P3855',
            'native_identifier': identity, 'authority_capture': capture,
            'authority_title_for_image_matching_only': source_title, 'catalogue_metadata_write': False}
        try:
            w.entity_match(record, entity, require_primary_image=not independent_images)
            if independent_images:
                record['prior_reason'] = 'Exact native authority established; independently identify a licensed full-work file'
            accepted.append(record)
        except ValueError as error:
            held.append({'artwork_id': original['artwork_id'], 'qid': entity['id'],
                         'reason': str(error), 'capture': capture, 'candidate': record})
    c.save(OUT / (label + '-matches.json'), {'accepted': accepted, 'held': held})
    x.select_records(accepted, label)
    print('Native authority matches', len(accepted), 'held', len(held), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['discover','select'])
    p.add_argument('--limit', type=int, default=650)
    p.add_argument('--label', default='round-16-native-identifiers')
    p.add_argument('--independent-images', action='store_true')
    p.add_argument('--lowercase-cohort', action='store_true')
    a = p.parse_args()
    if a.lowercase_cohort:
        OUT = c.RUN / 'native-lowercase-identifier-crosswalks'
    discover(a.limit, a.lowercase_cohort) if a.phase == 'discover' else select(a.label, a.independent_images)
