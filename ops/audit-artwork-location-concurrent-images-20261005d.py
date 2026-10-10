#!/usr/bin/env python3
"""Account for a separate, exactly pinned 19-record image attachment operation."""
from pathlib import Path

PIN = '7a3cc2b8c045b31324a0b40b5a92a844a9998e96b7acba4c00f69d1cb70de92b'


def load(r):
    path = r.ROOT / 'docs/research/louvre-image-coverage-20261005/repair-plan.json.gz'
    assert r.sha(path.read_bytes()) == PIN
    data = r.load(path)
    assert data['operation'] == 'louvre-image-links-20261005' and len(data['claims']) == 19
    backup = Path.home() / 'Library/Application Support/Artline/backups/louvre-image-links-20261005'
    maps, evidence = {}, {'operation': data['operation'], 'plan_path': str(path), 'plan_sha256': PIN, 'targets': {}}
    for target, info in data['targets'].items():
        before_path, after_path = backup / (target + '-preimages.json.gz'), backup / (target + '-after.json.gz')
        before, after = r.load(before_path), r.load(after_path)
        assert before['plan_sha256'] == after['plan_sha256'] == PIN
        assert before['preimages'] == info['preimages']
        maps[target] = {}
        ids = [info['id_map'][c['target_id']] for c in data['claims']]
        with r.connect(target) as db:
            logs = db.execute("SELECT id::text,entity_id::text,created_at,before_json,after_json FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND created_at>=%s::timestamptz ORDER BY created_at,id", (ids, '2026-10-05T17:31:55Z')).fetchall()
            citations = db.execute("SELECT entity_id::text,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='image_identity'", (ids,)).fetchall()
        for c in data['claims']:
            aid, sid = info['id_map'][c['target_id']], info['id_map'][c['source_id']]
            old, new = before['preimages'][aid], after['records'][aid]
            allowed = {'primary_media_id', 'revision', 'updated_at', 'updated_by'}
            assert {k:v for k,v in old['artwork'].items() if k not in allowed} == {k:v for k,v in new['artwork'].items() if k not in allowed}
            assert old['artwork']['primary_media_id'] is None and new['artwork']['primary_media_id'] == c['media_id']
            assert new['artwork']['revision'] == old['artwork']['revision'] + 1
            assert old['creators'] == new['creators']
            assert after['records'][sid] == before['preimages'][sid]
            assert new['media'] == before['preimages'][sid]['media'] and new['rights'] == before['preimages'][sid]['rights']
            expected_media = old['attachments'] + [{'artwork_id': aid, 'media_id': c['media_id'], 'sort_order': 0, 'view_label': 'Full composition'}]
            assert sorted(new['attachments'], key=lambda v:v['media_id']) == sorted(expected_media, key=lambda v:v['media_id'])
            matching = [v for v in logs if v['entity_id'] == aid and v['before_json'] == old['artwork'] and v['after_json'] == new['artwork']]
            assert len(matching) == 1, (target, aid, 'concurrent image change must have exact database audit preimage and postimage')
            assert any(v['entity_id'] == aid and v['source_url'] == c['source_url'] and PIN in v['evidence_note'] for v in citations)
            maps[target][aid] = {'primary_media_id': c['media_id'], 'attachments': new['attachments'], 'audit_id': matching[0]['id'], 'audit_at': str(matching[0]['created_at'])}
        evidence['targets'][target] = {'affected_artworks': len(maps[target]), 'before_path': str(before_path), 'before_sha256': r.sha(before_path.read_bytes()), 'after_path': str(after_path), 'after_sha256': r.sha(after_path.read_bytes()), 'verified_changes': maps[target]}
    return maps, evidence
