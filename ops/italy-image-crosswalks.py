#!/usr/bin/env python3
"""Bounded museum-scoped authority research for existing Italy image gaps."""
import argparse
import collections
import importlib.util
import json
from pathlib import Path
import re
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('campaign', ROOT / 'ops/italy-image-campaign.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
spec = importlib.util.spec_from_file_location('commons_checks', ROOT / 'ops/overnight-commons-images.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
RUN = c.RUN / 'crosswalk-research'
w.core.HOSTS.add('query.wikidata.org')

# Institution authorities cross-checked by name, location and official website.
# The mappings are evidence for image research, never database updates.
MUSEUMS = {
    'pinacoteca-di-brera': ('Q150066', 'https://pinacotecabrera.org/'),
    'gallerie-accademia-venezia': ('Q338330', 'https://www.gallerieaccademia.it/'),
    'galleria-borghese': ('Q841506', 'https://www.collezionegalleriaborghese.it/'),
    'accademia-carrara': ('Q338367', 'https://www.lacarrara.it/'),
    'pinacoteca-ambrosiana': ('Q1085811', 'https://www.ambrosiana.it/'),
    'galleria-arte-moderna-milano': ('Q3757721', 'https://www.gam-milano.com/'),
    'castello-sforzesco-art-collections': ('Q3905124', 'https://www.milanocastello.it/'),
    'accademia-tadini': ('Q3603953', 'https://www.accademiatadini.it/'),
    'museo-poldi-pezzoli': ('Q1190657', 'https://museopoldipezzoli.it/'),
    'musei-civici-monza': ('Q18809784', 'https://museicivicimonza.it/'),
    'musei-civici-arte-storia-brescia': ('Q3388589', 'https://www.bresciamusei.com/'),
    'musei-civici-pavia': ('Q18713219', 'https://museicivici.comune.pv.it/'),
    'museo-scienza-tecnologia-milano': ('Q947082', 'https://www.museoscienza.org/'),
    'accademia-brera-collections': ('Q338472', 'https://www.accademiadibrera.milano.it/'),
    'palazzo-morando-milano': ('Q1228226', 'https://www2.comune.milano.it/web/palazzo-morando'),
}

INSTITUTION_NOTES = {
    'castello-sforzesco-art-collections': {
        'relationship': 'Pinacoteca is a painting subcollection within the broader civic art collections; exact object crosswalk required',
        'source': 'https://www.milanocastello.it/i-musei/pinacoteca/gli-allestimenti'},
    'musei-civici-arte-storia-brescia': {
        'relationship': 'Pinacoteca Tosio Martinengo is within the Brescia civic museum system; exact object crosswalk required',
        'source': 'https://www.bresciamusei.com/biglietti/'},
}


def match_key(value):
    return re.sub(r'[^a-z0-9]', '', w.norm(value or ''))


def discover(slug, cap):
    RUN.mkdir(parents=True, exist_ok=True)
    path = RUN / (slug + '.json')
    if path.exists():
        print('Existing museum discovery retained', slug, flush=True)
        return
    qid, website = MUSEUMS[slug]
    targets = [r for r in c.load(c.RUN / 'eligible-image-gaps.json') if r['institution_slug'] == slug and r['work_type'] == 'painting']
    if not targets:
        print('No targets', slug, flush=True)
        return
    fetcher = w.core.Fetcher(RUN / 'captures')
    museum = w.api(fetcher, 'www.wikidata.org', {'action': 'wbgetentities', 'ids': qid, 'props': 'labels|claims'})['entities'][qid]
    if not {'Q38'} & w.ids(museum, 'P17'):
        raise ValueError('Institution country authority needs review')
    c.save(RUN / (slug + '-institution.json'), {'qid': qid, 'entity': museum, 'official_website': website,
           'basis': 'Reviewed museum name, city and official site; candidate mapping only',
           'relationship_note': INSTITUTION_NOTES.get(slug)})
    creators = sorted({a['qid'] for r in targets for a in r['creators'] if a['qid']})
    query = 'SELECT DISTINCT ?work WHERE { VALUES ?creator { ' + ' '.join('wd:' + q for q in creators) + \
            ' } ?work wdt:P195 wd:' + qid + '; wdt:P170 ?creator; wdt:P31 wd:Q3305213; wdt:P18 ?image. } ORDER BY ?work LIMIT ' + str(cap)
    data = fetcher.metadata('https://query.wikidata.org/sparql?' + urlencode({'query': query, 'format': 'json'}))
    ids = [r['work']['value'].rsplit('/', 1)[-1] for r in data['results']['bindings']]
    entities = {}
    for start in range(0, len(ids), 20):
        entities.update(w.api(fetcher, 'www.wikidata.org', {'action': 'wbgetentities', 'ids': '|'.join(ids[start:start+20]),
              'props': 'labels|aliases|claims', 'languages': 'en|it|fr|de|mul'})['entities'])
        print(slug, 'authority metadata', min(start+20, len(ids)), '/', len(ids), flush=True)
    c.save(path, {'institution': slug, 'institution_qid': qid, 'official_website': website, 'selected_local_gaps': len(targets),
                 'authority_cap': cap, 'cap_reached': len(ids) == cap, 'query': query, 'entities': entities})


def match(slug):
    data = c.load(RUN / (slug + '.json'))
    targets = [r for r in c.load(c.RUN / 'eligible-image-gaps.json') if r['institution_slug'] == slug and r['work_type'] == 'painting']
    matches = []
    held = []
    for target in targets:
        possible = []
        for qid, entity in data['entities'].items():
            names = {w.norm(x['value']) for x in entity.get('labels', {}).values()}
            names.update(w.norm(x['value']) for group in entity.get('aliases', {}).values() for x in group)
            ids = {match_key(x) for x in w.values(entity, 'P217') if isinstance(x, str)}
            title = bool({w.norm(target['title']), w.norm(target.get('alternate_title') or '')} & names)
            accession = bool(target['accession_number'] and match_key(target['accession_number']) in ids)
            serialized = json.dumps(entity, ensure_ascii=False)
            source_refs = [e for e in target['identifiers'] if e['scheme'] != 'wikidata' and
                           (e['url'] and e['url'].rstrip('/') in serialized or re.fullmatch(r'[A-Z]\d{4}-\d{5}', e['id']) and e['id'] in serialized)]
            if not (title or accession or source_refs):
                continue
            if {a['qid'] for a in target['creators']} != w.ids(entity, 'P170'):
                continue
            ident = next((e for e in target['identifiers'] if e['scheme'] != 'wikidata'), None)
            if not ident:
                continue
            record = dict(target, qid=qid, institution_qid=data['institution_qid'], website_url=data['official_website'],
                          provider='night-commons', scheme=ident['scheme'], external_id=ident['id'], page=ident['url'],
                          artist='; '.join(a['name'] for a in target['creators']),
                          crosswalk_basis={'title_match': title, 'accession_match': accession,
                              'exact_source_references': source_refs, 'museum_scoped': True,
                              'source_file': str((RUN / (slug + '.json')).relative_to(ROOT))})
            try:
                filename = w.entity_match(record, entity)
                possible.append({'candidate': record, 'filename': filename, 'entity': entity})
            except ValueError as error:
                held.append({'artwork_id': target['artwork_id'], 'qid': qid, 'reason': str(error), 'candidate': record})
        if len(possible) == 1:
            record = possible[0]
            # Generic titles alone cannot distinguish multiple physical versions,
            # even when only one version happens to be catalogued in Wikidata.
            basis = record['candidate']['crosswalk_basis']
            if not basis['accession_match'] and not basis['exact_source_references']:
                held.append({'artwork_id': target['artwork_id'], 'qid': record['candidate']['qid'],
                    'reason': 'Creator/title/museum lead requires independent inventory or exact museum URL confirmation', **record})
            else:
                matches.append(record)
        elif len(possible) > 1:
            held.append({'artwork_id': target['artwork_id'], 'reason': 'Multiple possible physical objects',
                         'qids': [r['candidate']['qid'] for r in possible]})
    c.save(RUN / (slug + '-matches.json'), {'matches': matches, 'held': held})
    print(slug, 'exact crosswalks', len(matches), 'held', len(held), flush=True)


def select(slug, label):
    data = c.load(RUN / (slug + '-matches.json'))
    select_records([r['candidate'] for r in data['matches']], label)


def select_records(records, label):
    used = {r['artwork_id'] for p in c.RUN.glob('*/candidates.json') for r in c.load(p)['candidates']}
    candidates = [r for r in records if r['artwork_id'] not in used]
    run = c.RUN / label
    run.mkdir(parents=True, exist_ok=True)
    if (run / 'candidates.json').exists():
        return
    local = c.snapshot(candidates, 'postgres://127.0.0.1/artline') if candidates else []
    cloud = c.snapshot(candidates, c.core.cloud_dsn()) if candidates else []
    indexes = []
    for rows in (local, cloud):
        index = collections.defaultdict(list)
        for row in rows: index[row['local_id']].append(row)
        indexes.append(index)
    selected = []
    held = []
    for record in candidates:
        groups = [i[record['artwork_id']] for i in indexes]
        if any(len(g) != 1 for g in groups):
            held.append(dict(record, reason='Cross-database identity missing/ambiguous'))
            continue
        l, r = groups[0][0], groups[1][0]
        if any(x['primary_media_id'] or x['date_scope'] != 'eligible' or not x['selected'] or x['status'] == 'archived' for x in (l, r)):
            held.append(dict(record, reason='Current eligibility/media changed'))
            continue
        if any(l[k] != r[k] or l[k] != record[k] for k in ('slug', 'title', 'creation_year_start', 'creation_year_end', 'work_type')):
            held.append(dict(record, reason='Current metadata differs'))
            continue
        record['target_ids'] = {'local': l['target_id'], 'cloud': r['target_id']}
        selected.append(record)
    c.save(run / 'candidates.json', {'selected_at': c.core.now(), 'candidates': selected,
           'selection': 'Existing Italy museum object with independently corroborated authority crosswalk; no new authority stored in database'})
    c.save(run / 'local-before.json', local)
    c.save(run / 'cloud-before.json', cloud)
    c.save(run / 'selection-held.json', held)
    print(label, 'selected', len(selected), 'held', len(held), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['discover', 'match', 'select'])
    p.add_argument('--museum', required=True, choices=sorted(MUSEUMS))
    p.add_argument('--cap', type=int, default=300)
    p.add_argument('--label', default='round-06-brera')
    a = p.parse_args()
    if a.phase == 'discover': discover(a.museum, a.cap)
    elif a.phase == 'match': match(a.museum)
    else: select(a.museum, a.label)
