#!/usr/bin/env python3
"""Copy the concurrent, source-reviewed Africa additions without replacing prod data."""
import argparse
import copy
import importlib.util
from pathlib import Path

from psycopg import sql
from psycopg.types.json import Jsonb

spec = importlib.util.spec_from_file_location('alignment', Path(__file__).with_name('align-catalogues-20261008.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
BASE_RUN, BASE_BACKUP = m.RUN, m.BACKUP
m.RUN, m.BACKUP = m.RUN / 'supplemental', m.BACKUP / 'supplemental'
AFRICA = m.ROOT / 'docs/research/morocco-africa-20261008/application-plan.json.gz'
CALDECOTT = '05a8efd8-5531-50a9-953b-0e9d1c7c9bb3'
ORDER = ['countries', 'places', 'sources', 'institutions', 'institution_venues',
         'artworks', 'artwork_artists', 'citations', 'external_identifiers', 'artwork_location_assertions']


def prepare():
    africa = m.load(AFRICA)
    # Revalidate the original editorial decisions and every retained source body.
    spec = importlib.util.spec_from_file_location('africa', Path(__file__).with_name('morocco-africa-apply-20261008.py'))
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    original.validate(africa)
    diff = m.load(m.RUN / 'presence-comparison.json')['tables']
    old = m.load(Path(m.load(BASE_RUN / 'delivery-plan-pin.json')['path']))
    known = {r['local_id'] for r in old['existing']}
    absent = lambda t: {m.json.loads(pk)[0] for values in diff[t]['missing_from_production'].values() for pk in values}
    new_ids = absent('artworks') - known
    assert new_ids == {r['id'] for r in africa['artworks'] if not r['existing_id']}
    assert absent('institutions') == {r['id'] for r in africa['institutions'] if not r['existing']}
    assert absent('places') == {r['id'] for r in africa['places']}
    assert absent('institution_venues') == {r['id'] for r in africa['venues']}
    assert not m.load(BASE_BACKUP / 'supplemental-production-preflight.json.gz')['native']
    assert not m.load(BASE_BACKUP / 'supplemental-production-preflight.json.gz')['url_matches']
    assert not m.load(BASE_BACKUP / 'supplemental-production-preflight.json.gz')['title_inventory_candidates']
    assert not m.load(BASE_BACKUP / 'supplemental-production-preflight.json.gz')['place_matches']
    review = m.load(m.RUN / 'title-review-decisions.json')
    leads = m.load(m.RUN / 'title-review.json')
    assert len(review) == len(leads) and all(r['decision'] == 'already_present' for r in review)
    reuse = {r['local_id']: r['production_id'] for r in review}
    artwork_ids = sorted(new_ids | {CALDECOTT})
    with m.connect('local') as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        data = {t: m.select_rows(db, t, 'id', sorted(absent(t))) for t in ['artworks', 'institutions', 'places', 'sources', 'institution_venues']}
        data['artworks'] = [r for r in data['artworks'] if r['id'] in new_ids]
        data['artwork_artists'] = m.select_rows(db, 'artwork_artists', 'artwork_id', sorted(new_ids))
        data['citations'] = m.select_rows(db, 'citations', 'entity_id', artwork_ids + [r['id'] for r in africa['institutions']], "AND field_name='morocco_africa_research_20261008'")
        data['external_identifiers'] = m.select_rows(db, 'external_identifiers', 'entity_id', artwork_ids, "AND scheme='morocco-africa-object-20261008'")
        data['artwork_location_assertions'] = m.select_rows(db, 'artwork_location_assertions', 'artwork_id', artwork_ids, "AND source_id=ANY(ARRAY[" + ','.join(sql.Literal(r['id']).as_string() for r in africa['sources']) + "]::uuid[])")
        data['countries'] = [r['v'] for r in db.execute('SELECT to_jsonb(c) v FROM countries c WHERE code=ANY(%s)', ([r['code'] for r in africa['countries']],))]
        local_existing = m.select_rows(db, 'artworks', 'id', [CALDECOTT])[0]
        local_institution = m.select_rows(db, 'institutions', 'id', [local_existing['current_institution_id']])[0]
    assert len(data['artworks']) == 97 and len(data['institutions']) == 108
    assert len(data['citations']) == 207 and len(data['external_identifiers']) == len(data['artwork_location_assertions']) == 98
    assert all(r['status'] == 'review' and r['published_at'] is None and r['primary_media_id'] is None and r['research_candidate'] and (r['creation_year_end'] is None or r['creation_year_end'] <= 1970) for r in data['artworks'])
    assert sum(r['creation_year_end'] is None for r in data['artworks']) == 17
    assert all(r['claim_type'] == 'holding' and r['review_state'] == 'accepted' and r['display_state'] is None and r['superseded_by'] is None for r in data['artwork_location_assertions'])
    assert all(r['status'] == 'review' for r in data['institutions'] + data['institution_venues'])
    source = m.BACKUP / 'source.json.gz'
    m.save(source, dict(tables=data, africa_plan_sha256=m.digest(AFRICA)))
    # Existing WikiArt records retain their images, dates and dimension labels.
    # Only the new native museum evidence and missing holdings are transferred.
    data['artworks'] = [r for r in data['artworks'] if r['id'] not in reuse]
    data['artwork_artists'] = [r for r in data['artwork_artists'] if r['artwork_id'] not in reuse]
    for table, column in [('citations', 'entity_id'), ('external_identifiers', 'entity_id'), ('artwork_location_assertions', 'artwork_id')]:
        for row in data[table]:
            row[column] = reuse.get(row[column], row[column])
    maps = m.identity_maps()
    for r in data['artwork_artists']:
        r['artist_id'] = maps['artists'][r['artist_id']]
    with m.connect('production') as db:
        existing = m.select_rows(db, 'artworks', 'id', [CALDECOTT] + list(reuse.values()))
        institution = m.select_rows(db, 'institutions', 'id', [local_existing['current_institution_id']])[0]
        assert all(r['current_institution_id'] is None for r in existing)
        assert not m.select_rows(db, 'artwork_location_assertions', 'artwork_id', [r['id'] for r in existing], "AND review_state='accepted' AND superseded_by IS NULL")
        assert institution['place_id'] in (None, local_institution['place_id'])
        assert not db.execute('SELECT code FROM countries WHERE code=ANY(%s)', ([r['code'] for r in data['countries']],)).fetchall()
        # All other foreign references must already exist or be in this package.
        meta = m.load(m.RUN / 'inventory/production-schema.json')
        for f in meta['foreign']:
            if f['child'] not in data or f['parent_column'] != 'id':
                continue
            ids = {r.get(f['column']) for r in data[f['child']]} - {None}
            ids -= {r['id'] for r in data.get(f['parent'], []) if 'id' in r}
            if ids:
                assert {r['id'] for r in m.select_rows(db, f['parent'], 'id', sorted(ids))} == ids, f
    plan = dict(at=m.now(), inserts=data, source_path=str(source), source_sha256=m.digest(source),
                existing_artworks=existing, existing_institution=institution, reused_artworks=reuse,
                institution_place_fill=local_institution['place_id'] if institution['place_id'] is None else None,
                existing_artwork_holding_fills={r['artwork_id']: r['institution_id'] for r in data['artwork_location_assertions'] if r['artwork_id'] in {a['id'] for a in existing}},
                policy='Insert missing source-backed local catalogue data; fill only verified empty geography/holding fields; preserve every conflicting production value, image and publication state.')
    path = m.BACKUP / 'delivery-plan.json.gz'
    m.save(path, plan)
    m.save(m.RUN / 'delivery-plan-pin.json', dict(path=str(path), sha256=m.digest(path), counts={t: len(rows) for t, rows in data.items()}, existing_artwork_holding_fills=len(existing), existing_institution_place_fills=int(bool(plan['institution_place_fill']))))
    print('Prepared supplemental delivery', {t: len(v) for t, v in data.items()}, flush=True)


def validate_absences(db, plan):
    data = plan['inserts']
    for table, rows in data.items():
        if table == 'artwork_artists':
            assert not m.select_rows(db, table, 'artwork_id', [r['artwork_id'] for r in rows])
        elif table == 'countries':
            assert not db.execute('SELECT code FROM countries WHERE code=ANY(%s)', ([r['code'] for r in rows],)).fetchall()
        else:
            assert not m.select_rows(db, table, 'id', [r['id'] for r in rows]), table
        if rows and 'slug' in rows[0]:
            assert not db.execute(sql.SQL('SELECT slug FROM {} WHERE slug=ANY(%s)').format(sql.Identifier(table)), ([r['slug'] for r in rows],)).fetchall(), table
    identifiers = data['external_identifiers']
    assert not db.execute('SELECT e.id FROM jsonb_to_recordset(%s) x(scheme text,external_id text) JOIN external_identifiers e USING(scheme,external_id)', (Jsonb(identifiers),)).fetchall()
    assert not db.execute("SELECT id FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)", ([r['canonical_url'] for r in identifiers],)).fetchall()
    assert {r['id']: r for r in m.select_rows(db, 'artworks', 'id', [r['id'] for r in plan['existing_artworks']])} == {r['id']: r for r in plan['existing_artworks']}
    assert m.select_rows(db, 'institutions', 'id', [plan['existing_institution']['id']])[0] == plan['existing_institution']


def verify(db, plan):
    meta = m.load(m.RUN / 'inventory/production-schema.json')['tables']
    for table, rows in plan['inserts'].items():
        if table == 'countries':
            actual = [r['v'] for r in db.execute('SELECT to_jsonb(c) v FROM countries c WHERE code=ANY(%s)', ([r['code'] for r in rows],))]
        else:
            column = 'artwork_id' if table == 'artwork_artists' else 'id'
            actual = m.select_rows(db, table, column, [r[column] for r in rows])
        generated = {c['column_name'] for c in meta[table]['columns'] if c['is_generated'] != 'NEVER'}
        canon = lambda values: sorted(m.json.dumps({k: v for k, v in r.items() if k not in generated}, sort_keys=True) for r in values)
        assert canon(actual) == canon(rows), ('Full supplemental row verification', table)
    for row in plan['existing_artworks']:
        expected = dict(row, current_institution_id=plan['existing_artwork_holding_fills'][row['id']])
        assert m.select_rows(db, 'artworks', 'id', [row['id']])[0] == expected
    expected = copy.deepcopy(plan['existing_institution'])
    if plan['institution_place_fill']:
        expected['place_id'] = plan['institution_place_fill']
    assert m.select_rows(db, 'institutions', 'id', [expected['id']])[0] == expected
    scope = db.execute('SELECT artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,count(*) n,bool_and(artline_has_selection_evidence(id)) evidence FROM artworks WHERE id=ANY(%s::uuid[]) GROUP BY 1', ([r['id'] for r in plan['inserts']['artworks']],)).fetchall()
    assert {r['scope']: r['n'] for r in scope} == {'eligible': 80, 'review': 15}
    assert all(r['evidence'] for r in scope)
    return dict(at=m.now(), counts={t: len(v) for t, v in plan['inserts'].items()}, scope=scope,
                existing_artwork_holding_fills=len(plan['existing_artworks']), existing_institution_place_fills=int(bool(plan['institution_place_fill'])),
                local_database_writes=0, existing_content_overwrites=0, publication_changes=0, image_changes=0)


def execute(apply=False):
    pin = m.load(m.RUN / 'delivery-plan-pin.json')
    assert m.digest(Path(pin['path'])) == pin['sha256']
    plan = m.load(Path(pin['path']))
    if apply:
        assert not (m.RUN / 'delivery-applied.json').exists()
        assert m.digest(Path(plan['source_path'])) == plan['source_sha256']
        backup = m.load(BASE_RUN / 'cloud-backup.json')
        assert m.cloud('sql', 'backups', 'describe', str(backup['id']), '--instance=artline-postgres')['status'] == 'SUCCESSFUL'
        with m.connect('local') as db:
            # Review source rows cannot drift between pinning and the production transaction.
            source = m.load(Path(plan['source_path']))['tables']
            for table in ['artworks', 'institutions', 'sources', 'places', 'institution_venues', 'citations', 'external_identifiers', 'artwork_location_assertions']:
                rows = source[table]
                assert {r['id']: r for r in m.select_rows(db, table, 'id', [r['id'] for r in rows])} == {r['id']: r for r in rows}, table
        with m.connect('production', readonly=False) as db:
            db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
            validate_absences(db, plan)
            m.save(m.BACKUP / 'locked-preimages.json.gz', dict(at=m.now(), artworks=plan['existing_artworks'], institution=plan['existing_institution'], absent={t: len(v) for t, v in plan['inserts'].items()}))
            meta = m.load(m.RUN / 'inventory/production-schema.json')['tables']
            for table in ORDER:
                m.insert(db, table, plan['inserts'][table], meta[table])
            if plan['institution_place_fill']:
                assert db.execute('UPDATE institutions SET place_id=%s WHERE id=%s AND place_id IS NULL', (plan['institution_place_fill'], plan['existing_institution']['id'])).rowcount == 1
            result = verify(db, plan)
        m.save(m.RUN / 'delivery-applied.json', dict(result, plan_sha256=pin['sha256'], backup_id=backup['id']))
        print('Committed supplemental catalogue', result, flush=True)
    else:
        with m.connect('production') as db:
            result = verify(db, plan)
        m.save(m.RUN / 'delivery-verification.json', dict(result, plan_sha256=pin['sha256']))
        print('Independent supplemental verification passed', result, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['prepare', 'apply', 'verify'])
    args = parser.parse_args()
    if args.phase == 'prepare':
        prepare()
    else:
        execute(args.phase == 'apply')
