#!/usr/bin/env python3
"""Review a bounded set of existing Manchester identities; apply only pinned holdings."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import re
from pathlib import Path

spec = importlib.util.spec_from_file_location('h', Path(__file__).with_name('museum-expansion-armenia-holdings-20261007.py'))
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
m = h.m
RUN = m.RUN / 'native/manchester'
IID = 'bc21f807-a431-50d1-9a35-4744f5e7c24e'
QID = 'Q2638817'
KEY = 'manchester-existing-holdings-001'
SID = m.uid('source/' + KEY)
PLAN = RUN / (KEY + '-plan.json.gz')
REVIEW = RUN / 'editorial-review-001.json'


def reference(path):
    return dict(path=str(path.relative_to(m.ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def checked_reference(ref):
    path = m.ROOT / ref['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == ref['sha256'], ref['path']


def one(entity, prop):
    # Do not let a preferred claim conceal another non-deprecated identity.
    rows = [r for r in entity.get('claims', {}).get(prop, []) if r['rank'] != 'deprecated']
    assert len(rows) == 1, 'non-unique ' + prop
    assert rows[0]['mainsnak']['snaktype'] == 'value', 'unknown ' + prop
    return rows[0]


def val(entity, prop):
    return h.value(one(entity, prop))


def qualifier_value(statement, prop):
    rows = statement.get('qualifiers', {}).get(prop, [])
    assert len(rows) == 1 and rows[0]['snaktype'] == 'value', 'non-unique qualifier ' + prop
    return rows[0]['datavalue']['value']


def year(value):
    assert value['calendarmodel'] == 'http://www.wikidata.org/entity/Q1985727'
    assert value['precision'] >= 9 and value['before'] == value['after'] == 0
    assert re.fullmatch(r'\+\d{4}-\d\d-\d\dT00:00:00Z', value['time'])
    return int(value['time'][1:5])


def creation(statement):
    qualifiers = set(statement.get('qualifiers', {}))
    assert not qualifiers - {'P1319', 'P1326', 'P1480'}, 'unreviewed creation qualifier'
    circa = 'P1480' in qualifiers
    if circa:
        assert qualifier_value(statement, 'P1480')['id'] == 'Q5727902', 'non-circa qualification'
    if qualifiers & {'P1319', 'P1326'}:
        assert {'P1319', 'P1326'} <= qualifiers, 'incomplete source range'
        first = year(qualifier_value(statement, 'P1319'))
        last = year(qualifier_value(statement, 'P1326'))
        precision = 'circa_range' if circa else 'range'
    else:
        first = last = year(h.value(statement))
        precision = 'circa' if circa else 'exact'
    assert 100 <= first <= last <= 1970, 'ineligible source date'
    return first, last, precision


def inventory_namespaces(identity):
    """Year.number accessions are museum-scoped, not globally unique identities."""
    proof = m.load(RUN / 'inventory-and-authority-comparison-001.json.gz')
    arts = {r['id']: r for r in proof['collision_artworks']}
    for collision in identity['inventory_collisions']:
        other = arts[collision['id']]
        assert {k: other[k] for k in collision} == collision
        assert other['current_institution_id'] not in [None, IID], 'unresolved inventory namespace'
        assert m.norm(other['title']) != m.norm(identity['title']), 'same-title inventory collision'
        links = [r for r in proof['collision_creators'] if r['artwork_id'] == other['id']]
        assert links and all(r['attribution_role'] == 'primary' for r in links), 'unresolved collision creator'
        authorities = {r['external_id'] for r in proof['collision_authorities'] if r['entity_id'] in {x['artist_id'] for x in links}}
        assert authorities and identity['creator_qid'] not in authorities, 'same or unknown collision creator'


def facts(entity, art, identity):
    assert art['current_institution_id'] is None and art['status'] == 'review' and art['published_at'] is None
    assert identity['creator_match'] and len(identity['creator_links']) == 1, 'creator needs reconciliation'
    assert identity['creator_links'][0]['attribution_role'] == 'primary'
    assert entity['id'] == identity['qid']
    assert not any(identity[k] for k in ['qid_collisions', 'same_creator_title_collisions']), 'unresolved duplicate/version lead'
    inventory_namespaces(identity)
    assert not one(entity, 'P170').get('qualifiers'), 'qualified creator'
    assert val(entity, 'P170')['id'] == identity['creator_qid']
    for statement in h.best(entity, 'P18'):
        filename = h.value(statement)
        assert isinstance(filename, str)
        creator_part = filename.split(' - ')[0]
        assert not re.search(r'\b(attributed|after|manner|school|circle|follower|workshop|copy|formerly)\b', creator_part, re.I), 'source filename preserves a qualified creator'
    titles = [v['value'] for v in entity.get('labels', {}).values()]
    titles += [v['value'] for rows in entity.get('aliases', {}).values() for v in rows]
    assert m.norm(art['title']) in {m.norm(t) for t in titles}, 'changed source title'
    assert val(entity, 'P31')['id'] == 'Q3305213' and not one(entity, 'P31').get('qualifiers')
    assert not any(h.best(entity, p) for p in ['P518', 'P361', 'P1877', 'P527']), 'component/copy/aggregate lead'
    assert not re.search(r'\b(part of|triptych|diptych|left wing|right wing|predella|recto|verso)\b', art['title'], re.I), 'component or face title needs physical-object review'
    collection = one(entity, 'P195')
    assert h.value(collection)['id'] == QID
    assert not set(collection.get('qualifiers', {})) - {'P580'}, 'qualified or historical collection'
    if collection.get('qualifiers'):
        assert 100 <= year(qualifier_value(collection, 'P580')) <= 2026
    for prop in ['P276', 'P127']:
        if entity.get('claims', {}).get(prop):
            statement = one(entity, prop)
            assert h.value(statement)['id'] == QID and not statement.get('qualifiers'), 'conflicting location/owner'
    inventory = one(entity, 'P217')
    assert set(inventory.get('qualifiers', {})) == {'P195'}
    assert qualifier_value(inventory, 'P195')['id'] == QID
    assert h.value(inventory) == art['accession_number']
    assert re.fullmatch(r'\d{4}\.\d+', art['accession_number']), 'compound or unfamiliar inventory'
    dates = creation(one(entity, 'P571'))
    assert dates == (art['creation_year_start'], art['creation_year_end'], art['date_precision']), 'source/catalogue creation conflict'
    artuk = val(entity, 'P1679')
    assert re.fullmatch(r'[a-z0-9-]+-\d+', artuk)
    artuk_statement = one(entity, 'P1679')
    assert not set(artuk_statement.get('qualifiers', {})) - {'P407', 'P813'}
    if 'P407' in artuk_statement.get('qualifiers', {}):
        assert qualifier_value(artuk_statement, 'P407')['id'] == 'Q1860'
    if 'P813' in artuk_statement.get('qualifiers', {}):
        assert 2000 <= year(qualifier_value(artuk_statement, 'P813')) <= 2026
    refs = [snak['datavalue']['value'] for ref in collection.get('references', [])
            for snak in ref.get('snaks', {}).get('P1679', []) if snak.get('snaktype') == 'value']
    assert refs and set(refs) == {artuk}, 'collection lacks exact Art UK object reference'
    return dict(artwork_id=art['id'], qid=entity['id'], title=art['title'], inventory=art['accession_number'],
                creator_qid=identity['creator_qid'], creator_label=identity['creator_links'][0]['display_name'],
                date_display=art['date_display'], first=dates[0], last=dates[1], precision=dates[2],
                source_url='https://www.wikidata.org/wiki/' + entity['id'], artuk_url='https://artuk.org/discover/artworks/' + artuk)


def source_rows():
    rows = {}
    for path in sorted((RUN / 'current-entities-001').glob('*.json.gz')):
        batch = m.load(path)
        cap = batch['capture']
        raw = gzip.decompress((m.ROOT / cap['body_path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == cap['receipt']['sha256'] and cap['receipt']['status'] == 200
        assert cap['receipt']['url'] == cap['receipt']['final_url']
        assert cap['receipt']['url'].startswith('https://www.wikidata.org/w/api.php?')
        assert json.loads(raw)['entities'] == batch['entities'] and set(batch['entities']) == set(batch['ids'])
        for qid, entity in batch['entities'].items():
            assert qid not in rows
            rows[qid] = dict(entity=entity, capture=cap)
    assert len(rows) == 259
    return rows


def evaluate():
    scope = m.load(RUN / 'initial-scope-001.json.gz')
    before = m.load(Path(scope['backup_path']))
    arts = {r['id']: r for r in before['artworks']}
    sources = source_rows()
    result = []
    for identity in m.load(RUN / 'identity-comparison-001.json.gz')['selected']:
        try:
            parsed = facts(sources[identity['qid']]['entity'], arts[identity['artwork_id']], identity)
        except AssertionError as error:
            result.append(dict(artwork_id=identity['artwork_id'], qid=identity['qid'], title=identity['title'], decision='hold', reason=str(error)))
        else:
            result.append(dict(artwork_id=identity['artwork_id'], qid=identity['qid'], title=identity['title'], decision='candidate', facts=parsed))
    return result


def records():
    scope = m.load(RUN / 'initial-scope-001.json.gz')
    arts = {r['id']: r for r in m.load(Path(scope['backup_path']))['artworks']}
    identities = {r['artwork_id']: r for r in m.load(RUN / 'identity-comparison-001.json.gz')['selected']}
    sources = source_rows()
    result = []
    for decision in m.load(REVIEW)['decisions']:
        if decision['decision'] != 'accept_holding':
            continue
        aid = decision['artwork_id']
        source = sources[decision['qid']]
        parsed = facts(source['entity'], arts[aid], identities[aid])
        assert parsed == decision['facts'] and decision['confidence'] == 0.8
        assert decision['basis'] and decision['limitation'] and decision['version_review']
        result.append(dict(facts=parsed, decision=decision, source=source, holding_id=m.uid(KEY + '/' + aid)))
    assert len(result) == len({r['facts']['artwork_id'] for r in result}) == len({r['facts']['inventory'] for r in result}) == 200
    return result


def snapshot(db, ids):
    queries = {
        'artworks': 'SELECT to_jsonb(x) row FROM artworks x WHERE id=ANY(%s::uuid[]) ORDER BY id',
        'artists': 'SELECT to_jsonb(x) row FROM artwork_artists x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,artist_id,attribution_role',
        'media': 'SELECT to_jsonb(x) row FROM artwork_media x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,media_id',
        'identifiers': "SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",
        'citations': "SELECT to_jsonb(x) row FROM citations x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",
        'assertions': 'SELECT to_jsonb(x) row FROM artwork_location_assertions x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,id',
    }
    result = {key: [r['row'] for r in db.execute(sql, (ids,))] for key, sql in queries.items()}
    result['museum'] = db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s', (IID,)).fetchone()['row']
    return result


def identity_guard(db):
    identity = m.load(RUN / 'identity-comparison-001.json.gz')
    rows = db.execute('''SELECT a.id::text,a.title,a.normalized_title,a.alternate_title,a.accession_number,a.creation_year_start,a.creation_year_end,a.date_display,a.dimensions_text,a.current_institution_id::text,aa.artist_id::text
        FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) ORDER BY a.id,aa.artist_id''', (identity['artist_ids'],)).fetchall()
    assert rows == identity['artist_artworks'], 'Creator-scoped comparison changed'
    rows = db.execute('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE accession_number=ANY(%s::text[]) ORDER BY id',
                      (sorted({r['inventory'] for r in identity['selected'] if r['inventory']}),)).fetchall()
    assert rows == identity['inventory_lookup'], 'Inventory comparison changed'
    rows = db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=ANY(%s::text[]) ORDER BY entity_id",
                      ([r['qid'] for r in identity['selected']],)).fetchall()
    assert rows == identity['qid_lookup'], 'Object authority comparison changed'
    authorities = m.load(RUN / 'creator-authority-check-001.json')['rows']
    rows = db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND external_id=ANY(%s::text[]) ORDER BY external_id,entity_id",
                      (sorted({r['external_id'] for r in authorities}),)).fetchall()
    assert rows == authorities, 'Creator authority comparison changed'
    previous = m.load(RUN / 'additional-identity-review-002.json.gz')['exact_title_lookup']
    titles = sorted({m.norm(r['facts']['title']) for r in evaluate() if r['decision'] == 'candidate'})
    rows = db.execute('SELECT id::text,title,normalized_title,unlinked_creator_label,current_institution_id::text,accession_number FROM artworks WHERE normalized_title=ANY(%s::text[]) ORDER BY id', (titles,)).fetchall()
    assert rows == previous, 'Exact-title comparison changed'
    proof = m.load(RUN / 'inventory-and-authority-comparison-001.json.gz')
    collision_ids = [r['id'] for r in proof['collision_artworks']]
    rows = db.execute('SELECT id::text,title,alternate_title,unlinked_creator_label,accession_number,creation_year_start,creation_year_end,date_display,current_institution_id::text FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id', (collision_ids,)).fetchall()
    assert rows == proof['collision_artworks'], 'Cross-museum inventory identities changed'
    rows = db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id', (collision_ids,)).fetchall()
    assert rows == proof['collision_creators'], 'Cross-museum creators changed'
    rows = db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,external_id", (sorted({r['artist_id'] for r in proof['collision_creators']}),)).fetchall()
    assert rows == proof['collision_authorities'], 'Cross-museum creator authorities changed'
    previous = m.load(RUN / 'creator-date-sanity-001.json')
    assert not previous['conflicts']
    rows = db.execute('SELECT id::text,display_name,birth_year,death_year,birth_precision,death_precision FROM artists WHERE id=ANY(%s::uuid[]) ORDER BY id', (identity['artist_ids'],)).fetchall()
    assert rows == previous['artists'], 'Creator chronology changed'


def counts(db):
    return db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'", (IID,)).fetchone()


def prepare():
    assert not PLAN.exists()
    selected = records()
    scope = m.load(RUN / 'initial-scope-001.json.gz')
    initial = m.load(Path(scope['backup_path']))
    ids = scope['scoped_ids']
    with m.connect() as db:
        before = snapshot(db, ids)
        for key in ['artworks', 'identifiers', 'citations', 'assertions', 'museum']:
            current, previous = before[key], initial[key]
            if isinstance(current, list):
                current = sorted(current, key=lambda row: row['id'])
                previous = sorted(previous, key=lambda row: row['id'])
            assert current == previous, 'Initial museum scope changed: ' + key
        identity_guard(db)
        assert counts(db) == dict(linked=0, eligible=0)
        for record in selected:
            aid = record['facts']['artwork_id']
            claims = [r for r in before['assertions'] if r['artwork_id'] == aid]
            assert len(claims) == 1
            assert all(r['institution_id'] == IID and r['claim_type'] == 'holding' and r['context'] == 'collection'
                       and r['review_state'] == 'review' and not r['superseded_by'] for r in claims)
            creator = record['decision']['facts']['creator_qid']
            old_links = [r for r in before['artists'] if r['artwork_id'] == aid]
            original = [r for r in scope['creator_links'] if r['artwork_id'] == aid]
            assert len(old_links) == len(original) == 1 and old_links[0]['artist_id'] == original[0]['artist_id']
            assert old_links[0]['attribution_role'] == 'primary'
            assert any(r['entity_id'] == original[0]['artist_id'] and r['external_id'] == creator and r['scheme'] == 'wikidata' for r in scope['creator_authorities'])
    files = [RUN / name for name in ['initial-scope-001.json.gz', 'identity-comparison-001.json.gz', 'additional-identity-review-002.json.gz', 'creator-authority-check-001.json', 'inventory-and-authority-comparison-001.json.gz', 'creator-date-sanity-001.json', 'unlinked-label-comparison-001.json', 'editorial-review-001.json']]
    files += sorted((RUN / 'current-entities-001').glob('*.json.gz'))
    files += [Path(__file__).resolve(), Path(h.__file__).resolve(), Path(m.__file__).resolve()]
    plan = dict(at=m.now(), records=selected, before=before, scoped_ids=ids, evidence=[reference(p) for p in files],
                policy='200 selected existing holding links in the local catalogue. Preserve all metadata, circa and range qualifiers, unknown fields, images, source evidence and publication states. No new artwork or current-display claim.')
    m.save(PLAN, plan)
    print('Pinned 200 holdings', hashlib.sha256(PLAN.read_bytes()).hexdigest(), flush=True)


def validate_plan():
    plan = m.load(PLAN)
    for ref in plan['evidence']:
        checked_reference(ref)
    assert plan['records'] == records()
    return plan, hashlib.sha256(PLAN.read_bytes()).hexdigest()


def note(record, digest):
    return json.dumps(dict(plan_sha256=digest, evidence=record, policy='Holding only. Preserve catalogue metadata, dates, creators, images and review/publication states.'), ensure_ascii=False)


def holding_note(record, digest):
    decision = record['decision']
    return decision['basis'] + ' ' + decision['version_review'] + ' Editorial confidence 0.8. ' + decision['limitation'] + ' Plan SHA-256 ' + digest


def assert_delta(before, after, records, digest):
    targets = {r['facts']['artwork_id'] for r in records}
    byid = {r['id']: r for r in after['artworks']}
    assert set(byid) == {r['id'] for r in before['artworks']}
    for old in before['artworks']:
        new = byid[old['id']]
        ignored = {'current_institution_id', 'updated_at'} if old['id'] in targets else set()
        assert {k: v for k, v in old.items() if k not in ignored} == {k: v for k, v in new.items() if k not in ignored}
        if old['id'] in targets:
            assert new['current_institution_id'] == IID
    for key in ['artists', 'media', 'identifiers', 'museum']:
        assert after[key] == before[key], key
    assert [r for r in after['citations'] if r['source_id'] != SID] == before['citations']
    newc = {r['entity_id']: r for r in after['citations'] if r['source_id'] == SID}
    newh = {r['artwork_id']: r for r in after['assertions'] if r['source_id'] == SID}
    assert set(newc) == set(newh) == targets
    assert len(after['citations']) == len(before['citations']) + len(records)
    assert len(after['assertions']) == len(before['assertions']) + len(records)
    for record in records:
        f = record['facts']
        citation, assertion = newc[f['artwork_id']], newh[f['artwork_id']]
        assert citation['evidence_note'] == note(record, digest) and citation['source_record_id'] == f['qid']
        assert citation['source_url'] == f['source_url'] and citation['field_name'] == 'museum_expansion_holding_reconciliation'
        assert assertion['id'] == record['holding_id'] and assertion['claim_type'] == 'holding'
        assert assertion['institution_id'] == IID and assertion['review_state'] == 'accepted' and assertion['context'] == 'collection'
        assert not assertion['superseded_by'] and assertion['source_url'] == f['source_url'] and assertion['evidence_note'] == holding_note(record, digest)
        assert not any(assertion.get(key) for key in ['display_state', 'gallery', 'venue_id', 'effective_from', 'effective_to'])
    expected = [dict(r, superseded_by=newh[r['artwork_id']]['id']) if r['artwork_id'] in targets else r for r in before['assertions']]
    assert [r for r in after['assertions'] if r['source_id'] != SID] == expected


def verify(db, plan, digest):
    after = snapshot(db, plan['scoped_ids'])
    before = plan['before']
    assert_delta(before, after, plan['records'], digest)
    targets = [r['facts']['artwork_id'] for r in plan['records']]
    assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)", (targets,)).fetchone()['n'] == 200
    return dict(existing_artworks_linked=200, new_artworks=0, scoped_artwork_metadata_preserved=len(before['artworks']),
                old_citations_preserved=len(before['citations']), artist_links_preserved=len(before['artists']),
                media_links_preserved=len(before['media']), identifiers_preserved=len(before['identifiers']),
                old_assertions_preserved=len(before['assertions']), prior_assertions_superseded=200, new_citations=200,
                current_counts=counts(db), new_images=0, new_publications=0, new_display_claims=0)


def apply(digest):
    plan, actual = validate_plan()
    assert actual == digest
    ids = [r['facts']['artwork_id'] for r in plan['records']]
    with m.psycopg.connect('postgresql://localhost/artline', autocommit=True, row_factory=m.dict_row, options='-c timezone=UTC -c statement_timeout=180000') as db, db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        target = db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone()
        assert target['db'] == 'artline' and target['addr'] in [None, '127.0.0.1', '::1'] and target['port'] in [None, 5432]
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE', (ids,)).fetchall()
        if db.execute('SELECT 1 FROM sources WHERE id=%s', (SID,)).fetchone():
            verify(db, plan, digest)
            print('Unchanged replay: 200 holdings; zero writes', flush=True)
            return
        assert snapshot(db, plan['scoped_ids']) == plan['before'], 'Baseline changed; re-review required'
        identity_guard(db)
        m.save(m.BACKUP / (KEY + '-preimages.json.gz'), plan)
        db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',
                   (SID, 'museum-expansion-20261006-' + KEY, 'Manchester Art Gallery reviewed existing holdings, 7 October 2026', 'authority_data', 'https://www.wikidata.org/'))
        for record in plan['records']:
            f = record['facts']
            aid = f['artwork_id']
            receipt = record['source']['capture']['receipt']
            db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_holding_reconciliation',%s,%s,%s,%s,%s,%s)",
                       (aid, SID, f['qid'], f['source_url'], note(record, digest), receipt['retrieved_at'], m.ACTOR))
            db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",
                       (record['holding_id'], aid, IID, SID, f['source_url'], holding_note(record, digest), receipt['retrieved_at']))
            old = next(r for r in plan['before']['assertions'] if r['artwork_id'] == aid)
            db.execute('UPDATE artwork_location_assertions SET superseded_by=%s WHERE id=%s', (record['holding_id'], old['id']))
        result = verify(db, plan, digest)
        assert result['current_counts'] == dict(linked=200, eligible=200)
    m.save(RUN / (KEY + '-applied.json'), dict(at=m.now(), plan_sha256=digest, local_only=True, verification=result))
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['evaluate', 'prepare', 'apply', 'verify'])
    parser.add_argument('--plan-sha')
    args = parser.parse_args()
    if args.command == 'evaluate':
        print(json.dumps(evaluate(), ensure_ascii=False, indent=2))
    elif args.command == 'prepare':
        prepare()
    elif args.command == 'apply':
        assert args.plan_sha
        apply(args.plan_sha)
    else:
        plan, digest = validate_plan()
        with m.connect() as db:
            print(json.dumps(verify(db, plan, digest)), flush=True)
