#!/usr/bin/env python3
"""Read-only preimage backup for a pinned research plan; complements a full backup."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('common', Path(__file__).with_name('reconcile-artwork-creators.py'))
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)


def main(directory, output):
    assert not output.exists(), 'Preserve existing recovery evidence'
    manifest = json.loads((directory / 'manifest.json').read_text())
    raw = (directory / 'plan.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == manifest['sha256']
    plan = json.loads(raw)
    inputs = [{'rid': r['rid'], 'work_slug': r['slug'], 'artist_slug': r['artist']['slug']} for r in plan]
    literal = "'" + json.dumps(inputs).replace("'", "''") + "'::jsonb"
    sql = """WITH input AS (
      SELECT * FROM jsonb_to_recordset(""" + literal + """) AS i(rid text,work_slug text,artist_slug text)
    ), w AS (SELECT a.* FROM artworks a JOIN input i ON i.work_slug=a.slug),
    a AS (SELECT DISTINCT p.* FROM artists p JOIN input i ON i.artist_slug=p.slug),
    entities AS (SELECT 'artwork'::text typ,id FROM w UNION ALL SELECT 'artist',id FROM a)
    SELECT json_build_object(
      'captured_at',now(),'database',current_database(),
      'artworks',(SELECT coalesce(jsonb_agg(to_jsonb(w)),'[]') FROM w),
      'artists',(SELECT coalesce(jsonb_agg(to_jsonb(a)),'[]') FROM a),
      'artwork_artists',(SELECT coalesce(jsonb_agg(to_jsonb(x)),'[]') FROM artwork_artists x JOIN w ON w.id=x.artwork_id),
      'external_identifiers',(SELECT coalesce(jsonb_agg(to_jsonb(x)),'[]') FROM external_identifiers x JOIN entities e ON e.typ=x.entity_type AND e.id=x.entity_id),
      'citations',(SELECT coalesce(jsonb_agg(to_jsonb(x)),'[]') FROM citations x JOIN entities e ON e.typ=x.entity_type AND e.id=x.entity_id),
      'audit_log',(SELECT coalesce(jsonb_agg(to_jsonb(x)),'[]') FROM audit_log x JOIN entities e ON e.typ=x.entity_type AND e.id=x.entity_id),
      'research_artwork_enrichments',(SELECT coalesce(jsonb_agg(to_jsonb(x)),'[]') FROM research_artwork_enrichments x JOIN input i ON i.rid=x.research_record_id),
      'research_artwork_links',(SELECT coalesce(jsonb_agg(to_jsonb(x)),'[]') FROM research_artwork_links x JOIN input i ON i.rid=x.research_record_id),
      'research_source',(SELECT coalesce(jsonb_agg(to_jsonb(x)),'[]') FROM sources x WHERE slug='expanded-round2-research')
    )"""
    data = common.query(sql)[0]
    assert data['database'] == 'artline'
    assert len(data['artworks']) == manifest['links']
    assert {r['slug'] for r in data['artworks']} == {r['slug'] for r in plan}
    assert not data['artwork_artists'] and not data['research_artwork_enrichments']
    assert all(r['status'] == 'review' and r['research_candidate'] for r in data['artworks'])
    assert {r['slug'] for r in data['artists']} == {r['artist']['slug'] for r in plan if not r['artist']['new']}
    data.update(plan_sha256=manifest['sha256'], planned_artist_slugs=sorted({r['artist']['slug'] for r in plan}),
                scope='Complete preimages of every row the research writer updates, plus existing related attribution, identity, citation, audit and ledger rows. Complements the retained managed full backup; not a full database dump.')
    common.save(output, data)
    assert json.loads(output.read_text()) == data
    receipt = {'kind': 'scoped-research-preimage', 'plan_sha256': manifest['sha256'],
               'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'bytes': output.stat().st_size,
               'captured_at': data['captured_at'], 'artworks': len(data['artworks']),
               'existing_artists': len(data['artists']), 'all_planned_preimages_verified': True}
    common.save(output.with_name('production-scoped-receipt.json'), receipt)
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    main(args.dir, args.output)
