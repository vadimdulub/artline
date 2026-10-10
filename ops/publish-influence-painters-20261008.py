#!/usr/bin/env python3
"""Publish the exact painter endpoints subsequently approved by the user.

This is the explicit follow-up approval for the 6,379 imported relationships,
not a catalogue-wide status rewrite. Preserve all factual review states.
"""
import argparse
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('claim_publication', Path(__file__).with_name('publish-painter-influences-20261008.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
d = p.d
OP = d.OP + '-painter-publication'
PLAN = d.RUN / 'production-painter-publication-v1.json.gz'


def endpoints(claims):
    return sorted({r[k] for r in claims for k in ('source_artist_id', 'target_artist_id') if r[k]})


def artist_transition(before, after, ids):
    wanted = set(ids)
    old = {r['id']: r for r in before}
    new = {r['id']: r for r in after}
    assert len(old) == len(before) and len(new) == len(after)
    assert old.keys() == new.keys() and wanted <= old.keys(), 'Painter membership changed'
    for artist_id, previous in old.items():
        current = new[artist_id]
        if artist_id not in wanted:
            assert previous == current, ('Previously published painter changed', artist_id)
            continue
        assert previous['status'] == 'review' and current['status'] == 'published'
        assert current['revision'] == previous['revision'] + 1
        assert current['updated_by'] == d.ACTOR and current['updated_at'] != previous['updated_at']
        assert current['published_at'] == (previous['published_at'] or current['updated_at'])
        allowed = {'status', 'updated_by', 'updated_at', 'published_at', 'revision'}
        assert {k: v for k, v in previous.items() if k not in allowed} == {k: v for k, v in current.items() if k not in allowed}, ('Painter metadata or research review changed', artist_id)


def prepare():
    assert not PLAN.exists(), 'Preserve the existing immutable plan'
    claims_plan, imported, _, claims_digest = p.checked()
    with d.connections.connect('production', readonly=True) as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        target = d.inspect_target(db)
        before = p.snapshot(db, imported)
        last = d.research.load(d.RUN / 'production-publication-v1-verified.json')['verification']['data_sha256']
        for table in ('influence_claims', 'citations'):
            assert p.sha(before[table]) == last[table], ('Published relationship content changed', table)
        selected = [r for r in before['influence_claims'] if r['id'] in set(claims_plan['claim_ids'])]
        assert len(selected) == 6379 and all(r['status'] == 'published' for r in selected)
        artist_ids = endpoints(selected)
        assert artist_ids == imported['artist_ids']
        assert all(r['status'] in ('review', 'published') for r in before['artists'])
        updates = sorted(r['id'] for r in before['artists'] if r['status'] == 'review')
        assert len(updates) == 3723 and len(before['artists']) == 3745
        initial_visibility = p.visibility(db, claims_plan['claim_ids'])
        triggers = {r['tgname'] for r in db.execute("SELECT tgname FROM pg_trigger WHERE tgrelid='artists'::regclass AND tgenabled='O'")}
        assert {'artists_audit', 'catalogue_cache_changed'} <= triggers
    backup = d.BACKUP / 'production-painter-publication-v1-before.json.gz'
    d.save_new(backup, dict(at=d.now(), target=target, before=before))
    plan = dict(operation=OP, at=d.now(), production_only=True,
        authorization='After being told the relationships remained hidden behind painter review status, the user explicitly instructed: "push them I aprrove evertyhing".',
        scope='Publish only the 3,723 reviewed painter endpoints of the 6,379 approved relationships. Preserve factual review flags, uncertain fields, artist metadata, claims, citations and all artworks.',
        policy_context='This explicit follow-up approval authorizes these painter publications; it is separate from the unified-catalogue work, which does not call for a blanket status rewrite.',
        claim_publication_sha256=claims_digest, script_sha256=d.checksum(Path(__file__)),
        claim_ids=claims_plan['claim_ids'], artist_ids=artist_ids, update_ids=updates,
        backup_path=str(backup), backup_sha256=d.checksum(backup), before_sha256=p.sha(before), before_visibility=initial_visibility)
    d.save_new(PLAN, plan)
    print(json.dumps(dict(plan=str(PLAN), sha256=d.checksum(PLAN), painter_publications=len(updates), relationships=len(selected)), indent=2))


def checked(expected_sha=None):
    digest = d.checksum(PLAN)
    assert not expected_sha or expected_sha == digest
    plan = d.research.load(PLAN)
    assert plan['operation'] == OP and plan['production_only']
    assert d.checksum(Path(__file__)) == plan['script_sha256']
    claims_plan, imported, _, claims_digest = p.checked()
    assert claims_digest == plan['claim_publication_sha256']
    assert plan['claim_ids'] == claims_plan['claim_ids']
    backup = Path(plan['backup_path'])
    assert d.checksum(backup) == plan['backup_sha256']
    before = d.research.load(backup)['before']
    assert p.sha(before) == plan['before_sha256']
    assert plan['artist_ids'] == endpoints([r for r in before['influence_claims'] if r['id'] in set(plan['claim_ids'])])
    assert plan['update_ids'] == sorted(r['id'] for r in before['artists'] if r['status'] == 'review')
    return plan, imported, before, digest


def verify(db, plan, imported, before):
    d.inspect_target(db)
    after = p.snapshot(db, imported)
    artist_transition(before['artists'], after['artists'], plan['update_ids'])
    for table in ('influence_claims', 'citations', 'sources', 'identifiers'):
        assert before[table] == after[table], ('Protected content changed', table)
    audited = db.execute("""SELECT count(DISTINCT entity_id) AS n FROM audit_log a
        WHERE entity_type='artist' AND action='update' AND entity_id=ANY(%s::uuid[])
        AND before_json->>'status'='review' AND after_json->>'status'='published'
        AND after_json->>'updated_by'=%s
        AND after_json->>'revision'=(SELECT revision::text FROM artists ar WHERE ar.id=a.entity_id)
        AND after_json->>'updated_at'=(SELECT to_jsonb(ar)->>'updated_at' FROM artists ar WHERE ar.id=a.entity_id)
        """, (plan['update_ids'], d.ACTOR)).fetchone()['n']
    assert audited == len(plan['update_ids'])
    visibility = p.visibility(db, plan['claim_ids'])
    assert visibility == dict(approved=6379, published=6379, publicly_eligible=6379, awaiting_painter_publication=0)
    return dict(painter_publications=len(plan['update_ids']), audited=audited, already_published_painters_preserved=len(plan['artist_ids'])-len(plan['update_ids']),
        visibility=visibility, citations_preserved=7427, all_claims_preserved=len(after['influence_claims']),
        data_sha256={k: p.sha(v) for k, v in after.items()})


def apply(expected_sha):
    plan, imported, before, digest = checked(expected_sha)
    receipt = d.RUN / 'production-painter-publication-v1-applied.json'
    with d.connections.connect('production', readonly=True) as db:
        statuses = {r['status'] for r in db.execute('SELECT DISTINCT status FROM artists WHERE id=ANY(%s::uuid[])', (plan['update_ids'],))}
        if statuses == {'published'}:
            result = verify(db, plan, imported, before)
            if not receipt.exists():
                d.save_new(receipt, dict(at=d.now(), plan_sha256=digest, recovered_committed_operation=True, verification=result))
            print('Verified completed painter publication; zero replay writes.')
            return
        assert statuses == {'review'}, ('Unexpected partial publication', statuses)
    assert not receipt.exists()
    with d.connections.connect('production', readonly=False) as db:
        db.execute("SET LOCAL application_name='artline-influence-painter-publication-20261008'")
        db.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (d.OP,))
        db.execute('LOCK TABLE influence_claims IN SHARE MODE')
        db.execute('LOCK TABLE citations IN SHARE MODE')
        db.execute('SELECT id FROM artists WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE', (plan['artist_ids'],)).fetchall()
        db.execute('SELECT id FROM sources WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE', ([r['id'] for r in before['sources']],)).fetchall()
        assert p.snapshot(db, imported) == before, 'Fresh preimages no longer match'
        rev_before = int(db.execute('SELECT sum(revision) AS n FROM catalogue_cache_revisions').fetchone()['n'])
        changed = db.execute("""UPDATE artists SET status='published',revision=revision+1,
            published_at=coalesce(published_at,now()),updated_at=now(),updated_by=%s
            WHERE id=ANY(%s::uuid[]) AND status='review'""", (d.ACTOR, plan['update_ids'])).rowcount
        assert changed == len(plan['update_ids'])
        result = verify(db, plan, imported, before)
        rev_after = int(db.execute('SELECT sum(revision) AS n FROM catalogue_cache_revisions').fetchone()['n'])
        assert rev_after > rev_before
        result.update(cache_revision_before=rev_before, cache_revision_after=rev_after)
        print('Painter publications, citations, protected metadata and audits verified before commit.', flush=True)
    d.save_new(receipt, dict(at=d.now(), plan_sha256=digest, backup_path=plan['backup_path'], backup_sha256=plan['backup_sha256'], verification=result))
    print('Production painter publication committed.', flush=True)


def verify_only():
    plan, imported, before, digest = checked()
    with d.connections.connect('production', readonly=True) as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        result = verify(db, plan, imported, before)
    receipt = d.RUN / 'production-painter-publication-v1-verified.json'
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
