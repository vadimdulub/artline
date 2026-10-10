#!/usr/bin/env python3
"""Review a bounded set of existing Government Art Collection identities; apply only pinned holdings."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
from pathlib import Path

spec = importlib.util.spec_from_file_location('h', Path(__file__).with_name('museum-expansion-armenia-holdings-20261007.py'))
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
m = h.m
RUN = m.RUN / 'native/government-art-collection'
IID = '69bdf1c9-b003-5051-a3c6-0e533959c447'
QID = 'Q5588677'
KEY = 'government-art-collection-existing-holdings-001'
SID = m.uid('source/' + KEY)
PLAN = RUN / (KEY + '-plan.json.gz')
REVIEW = RUN / 'editorial-review-001.json'
SELECTED_COUNT = 118


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


def parse_native(raw):
    soup = BeautifulSoup(raw, 'html.parser')
    fields, repeated = {}, {}
    for dt in soup.select('dl dt'):
        dd = dt.find_next_sibling('dd')
        if dd is None:
            continue
        key, value = dt.get_text(' ', strip=True), dd.get_text(' ', strip=True)
        if key in fields:
            repeated.setdefault(key, [fields[key]]).append(value)
        else:
            fields[key] = value
    canonical = soup.select('link[rel="canonical"]')
    return dict(fields=fields, repeated=repeated, headings=[x.get_text(' ', strip=True) for x in soup.find_all('h1')],
                canonical=canonical[0].get('href') if len(canonical)==1 else None,
                creator_links=[dict(label=a.get_text(' ', strip=True), url=a['href']) for dt in soup.select('dl dt')
                  if dt.get_text(' ', strip=True)=='Artist' for a in dt.find_next_sibling('dd').select('a[href]')],
                text=soup.get_text(' ', strip=True))


def native_dates(value):
    text=(value or '').strip()
    for format in ['%d %B %Y','%B %Y']:
        try:
            parsed=datetime.strptime(text,format)
        except ValueError:
            continue
        assert 100<=parsed.year<=1970, 'native creation outside eligible scope'
        return parsed.year,parsed.year,'exact'
    match=re.fullmatch(r'(c\.?)?\s*(\d{4})(?:\s*[-–/]\s*(\d{2}|\d{4}))?',text)
    assert match, 'native date requires review'
    first=int(match[2])
    last=int(match[3]) if match[3] else first
    if match[3] and len(match[3])==2:
        last=(first//100)*100+last
    assert 100<=first<=last<=1970, 'native creation outside eligible scope'
    assert not (match[1] and last==1970), 'circa cutoff requires review'
    precision=('circa' if first==last else 'circa_range') if match[1] else ('exact' if first==last else 'range')
    return first,last,precision


def inventory_namespaces(identity):
    proof=m.load(RUN/'supplementary-identity-comparison-001.json.gz')
    context=m.load(RUN/'inventory-context-001.json.gz')
    decisions=m.load(RUN/'reviewed-text-comparisons-003.json')['inventory_comparisons']
    for collision in identity['inventory_collisions']:
        other=next(r for r in proof['collision_artworks'] if r['id']==collision['id'])
        assert {k:other[k] for k in collision}==collision
        reviewed=[r for r in decisions if r['qid']==identity['qid'] and r['other_artwork']['id']==other['id']]
        assert len(reviewed)==1 and reviewed[0]['decision']=='distinct_objects', 'unreviewed inventory collision'
        decision=reviewed[0]
        links=[r for r in proof['collision_creators'] if r['artwork_id']==other['id']]
        labels=[r['display_name'] for r in links] or [other['unlinked_creator_label']]
        authorities=[r for r in proof['collision_authorities'] if r['entity_id'] in {x['artist_id'] for x in links}]
        target_label=identity['creator_links'][0]['display_name'] if identity['creator_links'] else identity['unlinked_creator']
        assert decision['other_artwork']==other and decision['other_creators']==links and decision['other_labels']==labels and decision['other_authorities']==authorities
        assert decision['target_title']==identity['title'] and decision['target_creator']==target_label
        assert decision['foreign_holding_claims']==[r for r in context['assertions'] if r['artwork_id']==other['id']]
        assert other['current_institution_id']!=IID and m.norm(other['title'])!=m.norm(identity['title'])
        assert all(labels) and m.norm(target_label) not in {m.norm(label) for label in labels}
        assert identity['creator_qid'] not in {r['external_id'] for r in authorities}


def facts(entity, art, identity, native):
    assert art['current_institution_id'] is None and art['status']=='review' and art['published_at'] is None
    assert entity['id']==identity['qid'] and art['id']==identity['artwork_id']==native['artwork_id']
    assert not identity['qid_collisions'], 'duplicate object authority'
    comparisons=m.load(RUN/'reviewed-text-comparisons-003.json')
    assert entity['id'] not in comparisons['holds'], comparisons['holds'].get(entity['id'])
    if identity['same_creator_title_collisions']:
        version=m.load(RUN/'reviewed-text-comparisons-003.json')['versions'].get(entity['id'])
        assert version, 'same-creator/title version lead'
        assert set(version['objects'])=={entity['id'],version['counterpart_qid']}
        other=m.load(RUN/'native-objects-001'/(version['counterpart_qid']+'.json.gz'))
        assert {r['id'] for r in identity['same_creator_title_collisions']}=={other['artwork_id']}
        for object in [native,other]:
            expected=version['objects'][object['qid']]
            assert {k:object['parsed']['fields'][k] for k in expected}==expected
        assert native['inventory']!=other['inventory'] and native['parsed']['fields']['Dimensions']!=other['parsed']['fields']['Dimensions']
    inventory_namespaces(identity)
    assert not one(entity, 'P170').get('qualifiers'), 'qualified Wikidata creator'
    assert val(entity, 'P170')['id']==identity['creator_qid']
    if identity['creator_links']:
        assert identity['creator_match'] and len(identity['creator_links'])==1 and identity['creator_links'][0]['attribution_role']=='primary', 'creator needs reconciliation'
        creator_label=identity['creator_links'][0]['display_name']
    else:
        assert identity['unlinked_creator'] and art['unlinked_creator_label']==identity['unlinked_creator'], 'unlinked creator missing'
        creator_label=identity['unlinked_creator']
    for statement in h.best(entity, 'P18'):
        assert not re.search(r'\b(attributed|after|manner|school|circle|follower|workshop|copy|formerly)\b', h.value(statement).split(' - ')[0], re.I), 'source filename has qualified creator'
    titles=[v['value'] for v in entity.get('labels',{}).values()]+[v['value'] for rows in entity.get('aliases',{}).values() for v in rows]
    assert m.norm(art['title']) in {m.norm(t) for t in titles}, 'changed Wikidata title'
    assert val(entity, 'P31')['id']=='Q3305213' and not one(entity,'P31').get('qualifiers'), 'object type requires review'
    assert not any(h.best(entity,p) for p in ['P518','P361','P1877','P527']), 'component/copy/aggregate lead'
    assert not re.search(r'\b(part of|triptych|diptych|left wing|right wing|predella|recto|verso)\b', art['title'],re.I), 'physical-object review needed'
    collection=one(entity,'P195')
    assert h.value(collection)['id']==QID and not set(collection.get('qualifiers',{}))-{'P580'}, 'collection conflict'
    if collection.get('qualifiers'):
        assert 100<=year(qualifier_value(collection,'P580'))<=2026
    inventory=one(entity,'P217')
    assert set(inventory.get('qualifiers',{}))=={'P195'} and qualifier_value(inventory,'P195')['id']==QID
    assert h.value(inventory)==art['accession_number']==native['inventory']
    dates=creation(one(entity,'P571'))
    assert dates==(art['creation_year_start'],art['creation_year_end'],art['date_precision']), 'Wikidata date differs from catalogue'
    parsed=native['parsed'];f=parsed['fields']
    assert not parsed['repeated'] and parsed['headings']==[f['Title']], 'native field conflict'
    assert native['url']==native['capture']['receipt']['final_url'], 'native redirect mismatch'
    if parsed['canonical']!=native['url']:
        assert comparisons['canonical_aliases'].get(entity['id'])==[native['url'],parsed['canonical']], 'native canonical mismatch'
        alias=m.load(RUN/comparisons['canonical_captures'][entity['id']])['capture']
        raw=gzip.decompress((m.ROOT/alias['body_path']).read_bytes())
        assert alias['receipt']['status']==200 and alias['receipt']['url']==parsed['canonical'] and alias['receipt']['final_url']==native['url']
        assert hashlib.sha256(raw).hexdigest()==alias['receipt']['sha256']==native['capture']['receipt']['sha256']
    assert f['GAC number']==art['accession_number'], 'native object number mismatch'
    assert not re.search(r'\b(after|attributed|manner|school|circle|follower|workshop|copy|formerly|unknown|unidentified)\b',f['Artist'],re.I), 'qualified native creator'
    comparisons=m.load(RUN/'reviewed-text-comparisons-003.json')
    title_pair=[art['title'],f['Title']]
    assert m.norm(title_pair[0])==m.norm(title_pair[1]) or comparisons['titles'].get(entity['id'])==title_pair, 'native title comparison required'
    native_name=re.sub(r'\([^)]*\d{3,4}[^)]*\)','',f['Artist']).strip()
    creator_pair=[creator_label,native_name]
    assert m.norm(creator_pair[0])==m.norm(creator_pair[1]) or comparisons['creators'].get(entity['id'])==creator_pair, 'native creator comparison required'
    native_date=native_dates(f.get('Date'))
    assert f.get('Medium') in ['Oil on canvas','Oil on panel','Oil on board','Oil on plywood','Oil on paper','Oil on hardboard','Oil on canvas board','Oil on canvas on board','Oil on canvas on panel','Oil on cardboard','Verre églomisé (oil on glass)','Oil, crayon and collage on board','Oil on linen on plywood','Tempera on panel','Tempera on board','Egg tempera on canvas laid down on board','Oil on millboard','Oil on card'], 'native medium requires review'
    assert f.get('Dimensions'), 'native dimensions absent'
    assert re.search(r'^(Purchased|Purchasaed|Presented|Transferred|Commissioned|Bequeathed|Acquired)',f.get('Acquisition',''),re.I) or comparisons['unknown_acquisitions'].get(entity['id'])==f.get('Acquisition')=='Origin uncertain', 'collection acquisition requires review'
    assert not re.search(r'\b(loan from|lent by|returned to|restituted|deaccessioned|disposed)\b',f.get('Acquisition',''),re.I), 'custody/ownership ambiguity'
    assert entity['id'] not in comparisons['holds'], comparisons['holds'].get(entity['id'])
    proof=m.load(RUN/'supplementary-identity-comparison-001.json.gz')
    for other in proof['exact_title_lookup']:
        assert other['id']==art['id'] or not other['unlinked_creator_label'] or m.norm(other['unlinked_creator_label'])!=m.norm(creator_label), 'same-title unlinked creator duplicate lead'
    for artist in proof['creator_chronology']:
        if artist['id'] in {r['artist_id'] for r in identity['creator_links']}:
            assert not artist['birth_year'] or native_date[1]>=artist['birth_year'], 'work predates creator'
            assert not artist['death_year'] or native_date[0]<=artist['death_year'], 'work postdates creator'
    return dict(artwork_id=art['id'],qid=entity['id'],title=art['title'],inventory=art['accession_number'],
                creator_qid=identity['creator_qid'],creator_label=creator_label,native_creator=f['Artist'],
                date_display=art['date_display'],first=dates[0],last=dates[1],precision=dates[2],
                native_date_display=f['Date'],native_date=list(native_date),native_title=f['Title'],
                dimensions=f['Dimensions'],acquisition=f['Acquisition'],provenance=f.get('Provenance'),
                source_url=native['url'],wikidata_url='https://www.wikidata.org/wiki/'+entity['id'])


def native_rows():
    result={}
    for path in sorted((RUN/'native-objects-001').glob('*.json.gz')):
        row=m.load(path);cap=row['capture'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes())
        assert cap['receipt']['status']==200 and hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256']
        assert row['parsed']==parse_native(raw)
        assert row['qid'] not in result
        result[row['qid']]=row
    return result


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
    assert len(rows) == 135
    return rows


def evaluate():
    scope = m.load(RUN / 'initial-scope-001.json.gz')
    before = m.load(Path(scope['backup_path']))
    arts = {r['id']: r for r in before['artworks']}
    sources = source_rows()
    natives = native_rows()
    result = []
    for identity in m.load(RUN / 'identity-comparison-001.json.gz')['selected']:
        try:
            assert identity['qid'] in natives, 'native source unavailable'
            parsed = facts(sources[identity['qid']]['entity'], arts[identity['artwork_id']], identity, natives[identity['qid']])
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
    natives = native_rows()
    result = []
    for decision in m.load(REVIEW)['decisions']:
        if decision['decision'] != 'accept_holding':
            continue
        aid = decision['artwork_id']
        source = sources[decision['qid']]
        parsed = facts(source['entity'], arts[aid], identities[aid], natives[decision['qid']])
        assert parsed == decision['facts'] and decision['confidence'] == 0.95
        assert decision['basis'] and decision['limitation'] and decision['version_review']
        result.append(dict(facts=parsed, decision=decision, source=natives[decision['qid']], wikidata=source, holding_id=m.uid(KEY + '/' + aid)))
    assert len(result) == len({r['facts']['artwork_id'] for r in result}) == len({r['facts']['inventory'] for r in result}) == SELECTED_COUNT
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
    proof=m.load(RUN/'supplementary-identity-comparison-001.json.gz')
    queries={
      'collision_artworks': ('SELECT id::text,title,alternate_title,unlinked_creator_label,accession_number,creation_year_start,creation_year_end,date_display,current_institution_id::text FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id',[r['id'] for r in proof['collision_artworks']]),
      'collision_creators': ('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',[r['id'] for r in proof['collision_artworks']]),
      'collision_authorities': ("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,external_id",sorted({r['artist_id'] for r in proof['collision_creators']})),
      'creator_authorities': ("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND external_id=ANY(%s::text[]) ORDER BY external_id,entity_id",sorted({r['creator_qid'] for r in identity['selected']})),
      'creator_chronology': ('SELECT id::text,display_name,birth_year,death_year,birth_precision,death_precision FROM artists WHERE id=ANY(%s::uuid[]) ORDER BY id',identity['artist_ids']),
      'exact_title_lookup': ('SELECT id::text,title,normalized_title,unlinked_creator_label,current_institution_id::text,accession_number FROM artworks WHERE normalized_title=ANY(%s::text[]) ORDER BY id',sorted({m.norm(r['title']) for r in identity['selected']}))}
    for key,(sql,values) in queries.items():
        assert db.execute(sql,(values,)).fetchall()==proof[key], 'Identity comparison changed: '+key
    context=m.load(RUN/'inventory-context-001.json.gz')
    ids=[r['id'] for r in proof['collision_artworks']]
    rows=[r['row'] for r in db.execute('SELECT to_jsonb(x) row FROM artwork_location_assertions x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,id',(ids,))]
    assert rows==context['assertions'], 'Inventory holding context changed'


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
        for key in ['artworks', 'identifiers', 'citations', 'assertions', 'museum', 'artists', 'media']:
            current, previous = before[key], initial[key]
            if isinstance(current, list):
                current = sorted(current, key=lambda row: json.dumps(row,sort_keys=True))
                previous = sorted(previous, key=lambda row: json.dumps(row,sort_keys=True))
            assert current == previous, 'Initial museum scope changed: ' + key
        identity_guard(db)
        assert counts(db) == dict(linked=22, eligible=19)
        for record in selected:
            aid = record['facts']['artwork_id']
            claims = [r for r in before['assertions'] if r['artwork_id'] == aid]
            assert len(claims) == 1
            assert all(r['institution_id'] == IID and r['claim_type'] == 'holding' and r['context'] == 'collection'
                       and r['review_state'] == 'review' and not r['superseded_by'] for r in claims)
    files = [RUN / name for name in ['initial-scope-001.json.gz','identity-comparison-001.json.gz','supplementary-identity-comparison-001.json.gz','inventory-context-001.json.gz','canonical-alias-001.json','canonical-alias-002.json','reviewed-text-comparisons-001.json','reviewed-text-comparisons-002.json','reviewed-text-comparisons-003.json','editorial-review-001.json','native-narrative-review-001.json.gz']]
    files += sorted((RUN/'native-objects-001').glob('*.json.gz'))
    files += sorted((RUN / 'current-entities-001').glob('*.json.gz'))
    files += [Path(__file__).resolve(), Path(h.__file__).resolve(), Path(m.__file__).resolve()]
    plan = dict(at=m.now(), records=selected, before=before, scoped_ids=ids, evidence=[reference(p) for p in files],
                policy='Selected existing holding links in the local catalogue. Preserve all metadata, circa and range qualifiers, unknown fields, images, source evidence and publication states. No new artwork or current-display claim.')
    m.save(PLAN, plan)
    print('Pinned', SELECTED_COUNT, 'holdings', hashlib.sha256(PLAN.read_bytes()).hexdigest(), flush=True)


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
    return decision['basis'] + ' ' + decision['version_review'] + ' Editorial confidence 0.95. ' + decision['limitation'] + ' Plan SHA-256 ' + digest


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
        assert citation['evidence_note'] == note(record, digest) and citation['source_record_id'] == f['inventory']
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
    assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)", (targets,)).fetchone()['n'] == SELECTED_COUNT
    return dict(existing_artworks_linked=SELECTED_COUNT, new_artworks=0, scoped_artwork_metadata_preserved=len(before['artworks']),
                old_citations_preserved=len(before['citations']), artist_links_preserved=len(before['artists']),
                media_links_preserved=len(before['media']), identifiers_preserved=len(before['identifiers']),
                old_assertions_preserved=len(before['assertions']), prior_assertions_superseded=SELECTED_COUNT, new_citations=SELECTED_COUNT,
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
            print('Unchanged replay:', SELECTED_COUNT, 'holdings; zero writes', flush=True)
            return
        assert snapshot(db, plan['scoped_ids']) == plan['before'], 'Baseline changed; re-review required'
        identity_guard(db)
        m.save(m.BACKUP / (KEY + '-preimages.json.gz'), plan)
        db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',
                   (SID, 'museum-expansion-20261006-' + KEY, 'Government Art Collection reviewed existing holdings, 7 October 2026', 'collection_page', 'https://artcollection.dcms.gov.uk/'))
        for record in plan['records']:
            f = record['facts']
            aid = f['artwork_id']
            receipt = record['source']['capture']['receipt']
            db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_holding_reconciliation',%s,%s,%s,%s,%s,%s)",
                       (aid, SID, f['inventory'], f['source_url'], note(record, digest), receipt['retrieved_at'], m.ACTOR))
            db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",
                       (record['holding_id'], aid, IID, SID, f['source_url'], holding_note(record, digest), receipt['retrieved_at']))
            old = next(r for r in plan['before']['assertions'] if r['artwork_id'] == aid)
            db.execute('UPDATE artwork_location_assertions SET superseded_by=%s WHERE id=%s', (record['holding_id'], old['id']))
        result = verify(db, plan, digest)
        assert result['current_counts'] == dict(linked=22+SELECTED_COUNT, eligible=19+SELECTED_COUNT)
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
