#!/usr/bin/env python3
"""Consolidate two primary museum notices for Moreau's single Cat. 284 drawing.

Museum, maker, inventory, dating, provenance and independently inspected images
agree. The 3.5/35 cm source discrepancy remains in the archived source evidence.
"""
import argparse, importlib.util, json
from pathlib import Path

s = importlib.util.spec_from_file_location('p', Path(__file__).with_name('consolidate-overnight-pop-objects.py'))
p = importlib.util.module_from_spec(s); s.loader.exec_module(p)
m = p.m; CORE = p.CORE
p.RUN = m.x.BASE / 'duplicates/moreau-cat284-consolidation'
p.BACK = m.BACKUPS / 'moreau-cat284-consolidation'
p.SOURCE = 'overnight-moreau-cat284-physical-identity-20260913'

def plan():
    if (p.RUN / 'plan.json').exists(): return
    evidence_dir = m.x.BASE / 'duplicates/moreau-cat284-primary'
    notices = []
    for oid in ('50410000324', '50410004508'):
        f = evidence_dir / 'captures' / (oid + '.json')
        evidence = json.loads(f.read_text())
        assert CORE.sha(f.with_suffix('.html').read_bytes()) == evidence['receipt']['sha256']
        assert m.m.accession_key(evidence['fields']["Numéro d'inventaire"]) == 'CAT.284'
        assert 'Moreau Gustave' in evidence['fields']['Auteur']
        notices.append(evidence)
    image_receipt = json.loads((evidence_dir / 'image-inspection-receipt.json').read_text())
    assert len(image_receipt['images']) == 2
    entry = dict(key='moreau-cat284', canonical_slug='europe-joconde-m5041-8b9caa33544e-jacob-et-l-ange',
                 old_slug='europe-joconde-m5041-03f7cac65ce3-jacob-et-l-ange',
                 primary={**notices[0], 'alternate_primary_notice': notices[1], 'image_comparison': image_receipt},
                 institution_context='Two distinct POP notices describe the same Moreau museum Cat. 284 watercolour, circa 1878, signed lower right, same legacy and relationship to the Fogg painting. Actual side-by-side image inspection confirms identical composition and paper pigment marks. Alternate source height 3.5 cm versus 35 cm is preserved, not silently validated. The related Fogg painting is a different object. No museum photograph is published by this merge.', targets={})
    snapshots = {}
    for target in ('local', 'production'):
        with m.m.r.base.connect(target == 'production') as db, db.transaction():
            db.execute('SET TRANSACTION READ ONLY'); p.a.ensure_schema(db)
            rows = {r['slug']: r['id'] for r in db.execute('SELECT id::text,slug FROM artworks WHERE slug=ANY(%s)', ([entry['old_slug'], entry['canonical_slug']],))}
            assert len(rows) == 2
            old, keep = rows[entry['old_slug']], rows[entry['canonical_slug']]
            snap = p.a.snapshot(db, [old, keep]); works = {r['id']: r for r in snap['artworks']}
            assert all(w['status'] == 'review' and w['published_at'] is None for w in works.values())
            assert works[old]['current_institution_id'] == works[keep]['current_institution_id']
            assert all(m.m.accession_key(w['accession_number']) == 'CAT.284' for w in works.values())
            creators = lambda aid: {(r['artist_id'], r['attribution_role']) for r in snap['artwork_artists'] if r['artwork_id'] == aid}
            assert creators(old) == creators(keep) and creators(keep)
            assert not works[old]['primary_media_id']
            for table in ('artwork_places', 'curated_collection_items', 'artwork_media'):
                assert not any(r['artwork_id'] == old for r in snap[table]), table
            for aid, oid in ((keep, '50410000324'), (old, '50410004508')):
                assert any(r['entity_id'] == aid and (r['source_url'] or '').rstrip('/').endswith('/' + oid) for r in snap['citations'])
            assert any(r['artwork_id'] == keep and r['claim_type'] == 'holding' and r['review_state'] == 'accepted' and not r['superseded_by'] for r in snap['artwork_location_assertions'])
            common = {r['scheme'] for r in snap['external_identifiers'] if r['entity_id'] == old} & {r['scheme'] for r in snap['external_identifiers'] if r['entity_id'] == keep}
            entry['targets'][target] = dict(old_id=old, canonical_id=keep, preserve_archived_schemes=sorted(common), issues=[])
            snapshots[target] = {'moreau-cat284': snap}
    fields = ('slug', 'title', 'creation_year_start', 'creation_year_end', 'date_precision', 'status', 'accession_number', 'work_type')
    comparable = lambda target: [{k: w[k] for k in fields} for w in sorted(snapshots[target]['moreau-cat284']['artworks'], key=lambda w: w['slug'])]
    assert comparable('local') == comparable('production')
    for target, snap in snapshots.items(): CORE.save_new(p.BACK / (target + '-preimages.json'), snap)
    CORE.save_new(p.RUN / 'plan.json', [entry])
    CORE.save_new(p.RUN / 'manifest.json', dict(at=CORE.now(), plan_sha256=CORE.sha((p.RUN / 'plan.json').read_bytes()), pairs=1))
    print('Moreau Cat. 284 one physical-object merge planned for both databases', flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('command', choices=['plan', 'apply', 'verify'])
    command = parser.parse_args().command
    (plan if command == 'plan' else getattr(p, command))()
