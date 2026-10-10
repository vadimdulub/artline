#!/usr/bin/env python3
"""Add missing, locally reviewed holding evidence while preserving existing rows."""
import argparse
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('alignment', Path(__file__).with_name('align-catalogues-20261008.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def make_plan():
    pre = m.load(m.BACKUP / 'remaining-holdings-preflight.json.gz')
    citations = m.load(m.BACKUP / 'remaining-holdings-citation-plan.json.gz')
    assert len(pre['classifications']) == 297
    assert all(r['classification'] == 'missing' for r in pre['classifications'])
    assert len({r['production_id'] for r in pre['classifications']}) == 297
    assert all(r['current_institution_id'] is None and r['status'] == 'review' for r in pre['production_artworks'])
    assert all(r['claim_type'] == 'holding' and r['review_state'] == 'accepted' and r['display_state'] is None and r['venue_id'] is None and r['source_url'].startswith('https://') and r['evidence_note'] for r in pre['local_holdings'])
    rows = [dict(r, artwork_id=pre['maps']['artworks'].get(r['artwork_id'], r['artwork_id']), source_id=pre['maps']['sources'].get(r['source_id'], r['source_id']), institution_id=pre['maps']['institutions'].get(r['institution_id'], r['institution_id'])) for r in pre['local_holdings']]
    assert len(rows) == len(citations['new']) == 297
    assert {r['artwork_id'] for r in rows} == {r['entity_id'] for r in citations['new']}
    assert not {r['id'] for r in rows} & {r['id'] for r in pre['production_holdings']}
    plan = dict(at=m.now(), inserts={'citations': citations['new'], 'artwork_location_assertions': rows},
        before_artworks=pre['production_artworks'], before_citations=citations['existing'],
        before_holdings=pre['production_holdings'], before_institutions=pre['institutions'],
        source_holdings=pre['local_holdings'], source_citations=pre['local_citations'],
        policy='Previously reviewed source-backed local holdings; add missing evidence and fill NULL holding only. Keep original source limitations, confidence, pending assertions, images, dates, catalogue fields and review/publication states.')
    path = m.BACKUP / 'remaining-holdings-plan.json.gz'
    m.save(path, plan)
    m.save(m.RUN / 'remaining-holdings-plan-pin.json', dict(path=str(path), sha256=m.digest(path), counts={t:len(v) for t,v in plan['inserts'].items()}))
    print('Pinned 297 holding additions and their 297 citations', flush=True)


def by_id(rows):
    return {r['id']: r for r in rows}


def verify(db, plan):
    for table, rows in plan['inserts'].items():
        assert by_id(m.select_rows(db, table, 'id', list(by_id(rows)))) == by_id(rows), table
    holding = {r['artwork_id']: r['institution_id'] for r in plan['inserts']['artwork_location_assertions']}
    expected = [dict(r, current_institution_id=holding[r['id']]) for r in plan['before_artworks']]
    assert by_id(m.select_rows(db, 'artworks', 'id', list(by_id(expected)))) == by_id(expected), 'Existing artwork metadata changed'
    for table, key in [('citations', 'before_citations'), ('artwork_location_assertions', 'before_holdings'), ('institutions', 'before_institutions')]:
        rows = plan[key]
        assert by_id(m.select_rows(db, table, 'id', list(by_id(rows)))) == by_id(rows), ('Existing rows changed', table)
    return dict(at=m.now(), added_holdings=297, added_citations=297, existing_artwork_holding_fills=297,
        original_assertions_preserved=len(plan['before_holdings']), existing_metadata_overwrites=0,
        publication_changes=0, display_claims=0, image_changes=0, local_database_writes=0)


def execute(apply=False):
    pin = m.load(m.RUN / 'remaining-holdings-plan-pin.json')
    assert m.digest(Path(pin['path'])) == pin['sha256']
    plan = m.load(Path(pin['path']))
    if apply:
        assert not (m.RUN / 'remaining-holdings-applied.json').exists()
        with m.connect('local') as db:
            for table, key in [('artwork_location_assertions','source_holdings'), ('citations','source_citations')]:
                rows = plan[key]
                assert by_id(m.select_rows(db,table,'id',list(by_id(rows)))) == by_id(rows), 'Local source changed'
        with m.connect('production', readonly=False) as db:
            db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
            assert by_id(m.select_rows(db,'artworks','id',list(by_id(plan['before_artworks'])))) == by_id(plan['before_artworks']), 'Production artwork changed'
            for table, rows in plan['inserts'].items():
                assert not m.select_rows(db,table,'id',list(by_id(rows))), 'Target ID appeared'
            assert not m.select_rows(db,'artwork_location_assertions','artwork_id',list(by_id(plan['before_artworks'])), "AND review_state='accepted' AND superseded_by IS NULL AND claim_type='holding'")
            current = m.select_rows(db,'citations','entity_id',list(by_id(plan['before_artworks'])), "AND entity_type='artwork'")
            keys={(r['entity_id'],r['field_name'],r['source_url']) for r in current}
            assert not any((r['entity_id'],r['field_name'],r['source_url']) in keys for r in plan['inserts']['citations']), 'Source evidence appeared'
            m.save(m.BACKUP/'remaining-holdings-locked.json.gz',dict(at=m.now(),before_artworks=plan['before_artworks'],before_holdings=plan['before_holdings'],plan_sha256=pin['sha256']))
            meta=m.load(m.RUN/'inventory/production-schema.json')['tables']
            for table in ['citations','artwork_location_assertions']:
                m.insert(db,table,plan['inserts'][table],meta[table])
            result=verify(db,plan)
        m.save(m.RUN/'remaining-holdings-applied.json',dict(result,plan_sha256=pin['sha256'],backup_id=m.load(m.RUN/'cloud-backup.json')['id']))
        print('Committed missing holding evidence',result,flush=True)
    else:
        with m.connect('production') as db:
            result=verify(db,plan)
        m.save(m.RUN/'remaining-holdings-verification.json',dict(result,plan_sha256=pin['sha256']))
        print('Independent holding verification passed',result,flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['prepare','apply','verify'])
    args=parser.parse_args()
    if args.phase=='prepare':
        make_plan()
    else:
        execute(args.phase=='apply')
