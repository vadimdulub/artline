#!/usr/bin/env python3
"""Corroborate selected YCBA object identities using its current official LIDO service."""
import argparse
import collections
import concurrent.futures
import importlib.util
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET

s = importlib.util.spec_from_file_location('m', Path(__file__).with_name('research-artwork-location-secondary-20261004.py'))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
p, r = m.p, m.r
NS = {'l': 'http://www.lido-schema.org', 'o': 'http://www.openarchives.org/OAI/2.0/'}
L = '{http://www.lido-schema.org}'
ENDPOINT = 'https://harvester-bl.britishart.yale.edu/oaicatmuseum/OAIHandler'


def selection():
    result = []
    # Historical filename retained; the actual museum QID is explicitly validated.
    for value in r.load(r.RUN / 'rmg-armenia-selected-20261005b.json.gz'):
        if value['museum_qid'] != 'Q6352575':
            continue
        ids = {m.value(v) for v in m.current_statements(value['entity'], 'P9789')}
        if len(ids) == 1 and re.fullmatch(r'\d+', str(next(iter(ids)))):
            result.append({**value, 'object_id': str(next(iter(ids)))})
    return result


def texts(node, path):
    return [e.text.strip() for e in node.findall(path, NS) if e.text and e.text.strip()]


def parse(raw, oid):
    root = ET.fromstring(raw)
    assert not root.findall('o:error', NS), 'OAI record unavailable'
    assert texts(root, './/o:header/o:identifier') == ['oai:tms.ycba.yale.edu:' + oid]
    header = root.find('.//o:header', NS)
    assert header is not None and header.get('status') != 'deleted'
    assert texts(root, './/l:recordWrap/l:recordID') == [oid]
    repositories = root.findall('.//l:repositorySet', NS)
    current = [v for v in repositories if v.get(L + 'type') == 'current']
    assert len(current) == 1, 'No unique current repository'
    repository = current[0]
    museums = texts(repository, 'l:repositoryName/l:legalBodyName/l:appellationValue')
    assert museums == ['Yale Center for British Art'], 'Current repository conflict'
    inventory = texts(repository, 'l:workID[@l:type="inventory number"]')
    assert len(inventory) == 1
    actors, dates = [], []
    for event in root.findall('.//l:event', NS):
        if 'production' not in texts(event, 'l:eventType/l:term'):
            continue
        dates.extend(texts(event, 'l:eventDate/l:displayDate'))
        for actor in event.findall('l:eventActor', NS):
            actors.append({'names': texts(actor, './/l:nameActorSet/l:appellationValue'),
                           'qualified_display': texts(actor, 'l:displayActorInRole'),
                           'qualifiers': texts(actor, './/l:attributionQualifierActor'),
                           'roles': texts(actor, './/l:roleActor/l:term'),
                           'identifiers': texts(actor, './/l:actorID')})
    links = texts(root, './/l:recordInfoLink')
    url = 'https://collections.britishart.yale.edu/catalog/tms:' + oid
    assert url in links
    return {'object_id': oid, 'titles': texts(root, './/l:titleSet/l:appellationValue'), 'inventory': inventory[0],
            'object_wikidata': texts(repository, 'l:workID[@l:type="Object Wikidata"]'), 'current_repository': museums[0],
            'repository_location_text': texts(repository, './/l:repositoryLocation//l:appellationValue'),
            'actors': actors, 'dates': dates, 'credits': texts(root, './/l:rightsWorkSet/l:creditLine'),
            'catalogue_updated': texts(root, './/o:header/o:datestamp'), 'human_url': url}


def capture_one(oid):
    path = r.RUN / 'ycba-objects-20261005b' / (oid + '.json.gz')
    if path.exists():
        return
    for attempt in range(3):
        try:
            raw, receipt = r.capture(ENDPOINT, {'verb': 'GetRecord', 'metadataPrefix': 'lido', 'identifier': 'oai:tms.ycba.yale.edu:' + oid}, tag='ycba-current-objects-20261005b' + (('-retry' + str(attempt)) if attempt else ''), timeout=40)
            assert receipt['status'] == 200
            try:
                obj = parse(raw, oid)
                value = {'object': obj, 'source_receipt': receipt}
            except AssertionError as exc:
                value = {'reason': str(exc), 'source_receipt': receipt}
            r.save_gz(path, value)
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))
    time.sleep(0.35)


def capture():
    ids = sorted({v['object_id'] for v in selection()})
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n, _ in enumerate(pool.map(capture_one, ids), 1):
            if n % 100 == 0:
                print('YCBA selected current objects', n, '/', len(ids), flush=True)
    r.save(r.RUN / 'ycba-capture-complete-20261005b.json', {'at': r.now(), 'objects': len(ids)})


def maker_names(row, actors, authorities):
    names = [n for actor in actors for n in actor['names']]
    proofs = []
    for actor in actors:
        source_qids = {match.group(1) for url in actor['identifiers'] if (match := re.fullmatch(r'https?://www\.wikidata\.org/wiki/(Q[1-9]\d*)', url))}
        for local in row['artists']:
            common = authorities.get(local['id'], set()) & source_qids
            if common:
                names.append(local['name'])
                proofs.append({'local_artist_id': local['id'], 'local_name': local['name'], 'primary_names': actor['names'], 'shared_wikidata_ids': sorted(common), 'qualifiers': actor['qualifiers']})
    return names, proofs


def plan():
    assert (r.RUN / 'ycba-capture-complete-20261005b.json').exists()
    index = p.Index()
    museum = index.institution('wikimedia-museum-q6352575')
    authority = r.load(r.RUN / 'ycba-data-authority-20261005b.json')['receipt']
    artist_authorities = collections.defaultdict(set)
    for identifier in r.load(r.RUN / 'ycba-local-artist-authorities-20261005b.json')['identifiers']:
        artist_authorities[identifier['entity_id']].add(identifier['external_id'])
    claims, holds = [], []
    direct_qualifiers = {'', 'print made by', 'by', 'painted by', 'drawn by', 'sculpted by', 'engraved by', 'artist'}
    for value in selection():
        aid, qid, oid = value['artwork_id'], value['qid'], value['object_id']
        row = index.by_id[aid]
        captured = r.load(r.RUN / 'ycba-objects-20261005b' / (oid + '.json.gz'))
        obj = captured.get('object')
        if not obj:
            holds.append({'artwork_id': aid, 'reason': captured['reason'], 'source_receipt': captured['source_receipt']})
            continue
        flags = []
        if 'https://www.wikidata.org/wiki/' + qid not in obj['object_wikidata']:
            flags.append('primary_record_reverse_object_id_not_confirmed')
        direct = [v for v in obj['actors'] if {r.norm(x) for x in v['qualifiers']} <= direct_qualifiers]
        direct_names, creator_proofs = maker_names(row, direct, artist_authorities)
        comparison_titles = obj['titles']
        local_title_matches = {p.titlekey(row['artwork'].get(k)) for k in ['title', 'alternate_title'] if row['artwork'].get(k)} & {p.titlekey(t) for t in obj['titles']}
        if not local_title_matches and not flags and row['artwork'].get('accession_number') and p.acckey(row['artwork']['accession_number']) == p.acckey(obj['inventory']):
            # Two exact object identifiers permit retaining a changed-title
            # candidate in review, never accepting that mismatch automatically.
            comparison_titles = [*obj['titles'], row['artwork']['title']]
            flags.append('source_title_wording_changed')
        basis = index.match(row, 'wikidata', qid, comparison_titles, direct_names, obj['inventory'], obj['dates'])
        if not basis.startswith(('existing_', 'unique_')):
            all_names, all_proofs = maker_names(row, obj['actors'], artist_authorities)
            other_basis = index.match(row, 'wikidata', qid, comparison_titles, all_names, obj['inventory'], obj['dates'])
            if not other_basis.startswith(('existing_', 'unique_')):
                holds.append({'artwork_id': aid, 'reason': 'current_primary_identity_not_reconciled', 'detail': basis, 'source_receipt': captured['source_receipt'], 'source_url': obj['human_url']})
                continue
            basis = other_basis
            creator_proofs = all_proofs
            flags.append('creator_relationship_qualified')
        date = row['artwork'].get('date_display')
        if date and obj['dates'] and p.datekey(date) not in {p.datekey(v) for v in obj['dates']}:
            flags.append('source_date_wording_changed')
        if re.search(r'\b(loan|lent|returned|deaccession|lost|stolen)\b', r.norm(' '.join(obj['credits'] + obj['repository_location_text']))):
            flags.append('custody_qualification')
        evidence = {'current_lido_record': obj, 'identity_selection': value, 'museum_data_service_authority_receipt': authority, 'creator_authority_reconciliation': creator_proofs, 'qualifications': flags}
        c = p.claim(row, 'ycba-object', oid, museum, captured['source_receipt'], obj['human_url'], evidence, basis + '; exact museum inventory, primary reverse Wikidata identifier, current repository and maker checked')
        if flags:
            c['review_state'] = 'review'
            c['limitation'] = 'Current primary museum candidate retained in review: ' + ', '.join(flags) + '. No new creator attribution, physical presence or current display asserted.'
        claims.append(c)
    p.output('ycba-20261005b', claims, holds)
    print('Claim states', collections.Counter(c.get('review_state', 'accepted') for c in claims), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['capture', 'plan'])
    globals()[parser.parse_args().command]()
