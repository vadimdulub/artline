#!/usr/bin/env python3
"""Publish exactly the imported influence claims approved by the user.

Keep the original import plan/receipts immutable. Back up fresh preimages,
change only status and update attribution, and verify evidence preservation.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('influence_import', Path(__file__).with_name('apply-painter-influences-20261008.py'))
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)
OP = d.OP + '-publication'
PLAN = d.RUN / 'production-publication-v1.json.gz'


def sha(value):
    return hashlib.sha256(d.encoded(value)).hexdigest()


def snapshot(db, imported):
    claims = d.rows(db, 'influence_claims')
    citations = d.rows(db, 'citations', "entity_type='influence' AND entity_id=ANY(%s::uuid[])", ([r['id'] for r in claims],))
    return dict(
        influence_claims=claims, citations=citations,
        artists=d.rows(db, 'artists', 'id=ANY(%s::uuid[])', (imported['artist_ids'],)),
        identifiers=d.rows(db, 'external_identifiers', "entity_type='artist' AND entity_id=ANY(%s::uuid[])", (imported['artist_ids'],)),
        sources=d.rows(db, 'sources', 'id=ANY(%s::uuid[])', (sorted({r['source_id'] for r in citations}),)),
    )


def publication_transition(before, after, claim_ids):
    """Reject missing/extra claims, collateral changes or evidence upgrades."""
    wanted = set(claim_ids)
    old = {r['id']: r for r in before}
    new = {r['id']: r for r in after}
    assert len(old) == len(before) and len(new) == len(after)
    assert old.keys() == new.keys() and wanted <= old.keys(), 'Claim membership changed'
    for claim_id, previous in old.items():
        current = new[claim_id]
        if claim_id not in wanted:
            assert previous == current, ('Unapproved claim changed', claim_id)
            continue
        assert previous['status'] == 'review' and current['status'] == 'published'
        assert current['updated_by'] == d.ACTOR and current['updated_at'] != previous['updated_at']
        allowed = {'status', 'updated_by', 'updated_at'}
        assert {k: v for k, v in previous.items() if k not in allowed} == {k: v for k, v in current.items() if k not in allowed}, ('Claim evidence or identity changed', claim_id)


def visibility(db, ids):
    return db.execute("""SELECT count(*) AS approved,
        count(*) FILTER (WHERE i.status='published') AS published,
        count(*) FILTER (WHERE i.status='published' AND t.status='published'
            AND (s.id IS NULL OR s.status='published') AND EXISTS (
                SELECT 1 FROM citations c JOIN sources src ON src.id=c.source_id
                WHERE c.entity_type='influence' AND c.entity_id=i.id AND src.is_active)) AS publicly_eligible,
        count(*) FILTER (WHERE t.status<>'published' OR (s.id IS NOT NULL AND s.status<>'published')) AS awaiting_painter_publication
        FROM influence_claims i JOIN artists t ON t.id=i.target_artist_id
        LEFT JOIN artists s ON s.id=i.source_artist_id WHERE i.id=ANY(%s::uuid[])""", (ids,)).fetchone()


def prepare():
    assert not PLAN.exists(), 'Preserve the immutable publication plan'
    imported, import_sha = d.checked_plan(d.DEFAULT_PLAN)
    with d.connections.connect('production', readonly=True) as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        target = d.inspect_target(db)
        verified = d.verify(db, imported)
        receipt = d.research.load(d.RUN / 'production-plan-v1-verified.json')
        assert verified['data_sha256'] == receipt['verification']['data_sha256'], 'Imported content drifted'
        before = snapshot(db, imported)
        ids = sorted(r['id'] for r in imported['inserts']['influence_claims'])
        assert len(ids) == len(set(ids)) == 6379
        eligible = visibility(db, ids)
    backup = d.BACKUP / 'production-publication-v1-before.json.gz'
    d.save_new(backup, dict(at=d.now(), target=target, before=before))
    plan = dict(operation=OP, at=d.now(), production_only=True,
        authorization='User: "just push them I appove them", explicitly approving publication of the imported relationships.',
        policy='Publish imported influence claims; preserve confidence, evidence, citations, artist profiles and all other claims.',
        import_plan_sha256=import_sha, script_sha256=d.checksum(Path(__file__)),
        claim_ids=ids, backup_path=str(backup), backup_sha256=d.checksum(backup), before_sha256=sha(before),
        before_visibility=eligible, claim_types=dict(Counter(r['relationship_type'] for r in imported['inserts']['influence_claims'])))
    d.save_new(PLAN, plan)
    print(json.dumps(dict(plan=str(PLAN), sha256=d.checksum(PLAN), claims=len(ids), before_visibility=eligible), indent=2))


def checked(expected_sha=None):
    digest = d.checksum(PLAN)
    assert not expected_sha or digest == expected_sha, 'Publication plan changed'
    plan = d.research.load(PLAN)
    assert plan['operation'] == OP and plan['production_only']
    assert plan['script_sha256'] == d.checksum(Path(__file__)), 'Publication script changed'
    imported, import_sha = d.checked_plan(d.DEFAULT_PLAN)
    assert plan['import_plan_sha256'] == import_sha
    assert plan['claim_ids'] == sorted(r['id'] for r in imported['inserts']['influence_claims'])
    backup = Path(plan['backup_path'])
    assert d.checksum(backup) == plan['backup_sha256']
    before = d.research.load(backup)['before']
    assert sha(before) == plan['before_sha256']
    return plan, imported, before, digest


def verify(db, plan, imported, before):
    d.inspect_target(db)
    after = snapshot(db, imported)
    publication_transition(before['influence_claims'], after['influence_claims'], plan['claim_ids'])
    for name in ('citations', 'artists', 'identifiers', 'sources'):
        assert before[name] == after[name], ('Protected rows changed', name)
    audited = db.execute("""SELECT count(DISTINCT entity_id) AS n FROM audit_log
        WHERE entity_type='influence' AND action='update' AND entity_id=ANY(%s::uuid[])
        AND before_json->>'status'='review' AND after_json->>'status'='published'
        AND after_json->>'updated_by'=%s
        AND after_json->>'updated_at'=(SELECT to_jsonb(i)->>'updated_at' FROM influence_claims i WHERE i.id=audit_log.entity_id)
        """, (plan['claim_ids'], d.ACTOR)).fetchone()['n']
    assert audited == len(plan['claim_ids']), ('Missing publication audit', audited)
    counts = visibility(db, plan['claim_ids'])
    assert counts['published'] == counts['approved'] == len(plan['claim_ids'])
    ids = set(plan['claim_ids'])
    imported_citations = [r for r in after['citations'] if r['entity_id'] in ids]
    assert len(imported_citations) == 7427
    return dict(visibility=counts, audited=audited, citations_preserved=len(imported_citations),
        prior_claims_preserved=len(after['influence_claims'])-len(ids), painter_rows_preserved=len(after['artists']),
        claim_types=plan['claim_types'], data_sha256={k: sha(v) for k, v in after.items()})


def apply(expected_sha):
    plan, imported, before, digest = checked(expected_sha)
    receipt = d.RUN / 'production-publication-v1-applied.json'
    with d.connections.connect('production', readonly=True) as db:
        statuses = {r['status'] for r in db.execute('SELECT DISTINCT status FROM influence_claims WHERE id=ANY(%s::uuid[])', (plan['claim_ids'],))}
        if statuses == {'published'}:
            result = verify(db, plan, imported, before)
            if not receipt.exists():
                d.save_new(receipt, dict(at=d.now(), plan_sha256=digest, recovered_committed_operation=True, verification=result))
            print('Verified completed publication; zero replay writes.')
            return
        assert statuses == {'review'}, ('Unexpected partial publication', statuses)
    assert not receipt.exists()
    with d.connections.connect('production', readonly=False) as db:
        db.execute("SET LOCAL application_name='artline-painter-influence-publication-20261008'")
        db.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (d.OP,))
        db.execute('LOCK TABLE influence_claims IN SHARE ROW EXCLUSIVE MODE')
        db.execute('LOCK TABLE citations IN SHARE MODE')
        db.execute('SELECT id FROM artists WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE', (imported['artist_ids'],)).fetchall()
        db.execute('SELECT id FROM sources WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE', ([r['id'] for r in before['sources']],)).fetchall()
        d.inspect_target(db)
        assert snapshot(db, imported) == before, 'Fresh preimages no longer match'
        revision_before = int(db.execute('SELECT sum(revision) AS n FROM catalogue_cache_revisions').fetchone()['n'])
        changed = db.execute("""UPDATE influence_claims SET status='published', updated_by=%s, updated_at=now()
            WHERE id=ANY(%s::uuid[]) AND status='review'""", (d.ACTOR, plan['claim_ids'])).rowcount
        assert changed == len(plan['claim_ids'])
        result = verify(db, plan, imported, before)
        revision_after = int(db.execute('SELECT sum(revision) AS n FROM catalogue_cache_revisions').fetchone()['n'])
        assert revision_after > revision_before
        result.update(cache_revision_before=revision_before, cache_revision_after=revision_after)
        print('All approved status transitions, protected data and audits verified before commit.', flush=True)
    d.save_new(receipt, dict(at=d.now(), plan_sha256=digest, backup_path=plan['backup_path'], backup_sha256=plan['backup_sha256'], verification=result))
    print('Production publication committed.', flush=True)


def verify_only():
    plan, imported, before, digest = checked()
    with d.connections.connect('production', readonly=True) as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        result = verify(db, plan, imported, before)
    receipt = d.RUN / 'production-publication-v1-verified.json'
    if not receipt.exists():
        d.save_new(receipt, dict(at=d.now(), plan_sha256=digest, read_only=True, verification=result))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'apply', 'verify'])
    parser.add_argument('--plan-sha256')
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare()
    elif args.command == 'apply':
        assert args.plan_sha256, '--plan-sha256 required'
        apply(args.plan_sha256)
    else:
        verify_only()
