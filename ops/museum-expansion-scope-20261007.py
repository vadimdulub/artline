#!/usr/bin/env python3
"""Preserve one bounded, read-only museum association scope and its real preimages."""
import argparse
import importlib.util
import json
import re
import uuid
from pathlib import Path

spec = importlib.util.spec_from_file_location('campaign', Path(__file__).with_name('museum-expansion-20261006.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def audit(iid, key):
    assert str(uuid.UUID(iid)) == iid and re.fullmatch(r'[a-z][a-z0-9-]+', key)
    destination = m.RUN / 'native' / key / 'initial-scope-001.json.gz'
    backup = m.BACKUP / (key + '-001-existing-records.json.gz')
    assert not destination.exists() and not backup.exists(), 'Preserve prior scope evidence'
    with m.connect() as db:
        museum = db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s', (iid,)).fetchone()['row']
        ids = [r['id'] for r in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=%s ORDER BY id LIMIT 1001', (iid, iid))]
        assert len(ids) <= 1000, 'Use bounded keyset pages for a larger museum scope'
        queries = {
            'artworks': 'SELECT to_jsonb(x) row FROM artworks x WHERE id=ANY(%s::uuid[]) ORDER BY id',
            'citations': "SELECT to_jsonb(x) row FROM citations x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",
            'assertions': 'SELECT to_jsonb(x) row FROM artwork_location_assertions x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,id',
            'identifiers': "SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",
            'artists': 'SELECT to_jsonb(x) row FROM artwork_artists x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,artist_id,attribution_role',
            'media': 'SELECT to_jsonb(x) row FROM artwork_media x WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,media_id',
        }
        before = {key: [r['row'] for r in db.execute(sql, (ids,))] for key, sql in queries.items()}
        before.update(at=m.now(), museum=museum)
        links = db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,a.display_name,a.normalized_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id', (ids,)).fetchall()
        artist_ids = sorted({r['artist_id'] for r in links})
        authorities = db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,scheme,external_id", (artist_ids,)).fetchall()
        before.update(creator_links=links, creator_authorities=authorities)
        eligibility = db.execute('SELECT id::text,title,date_display,accession_number,current_institution_id::text,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id', (ids,)).fetchall()
        counts = db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'", (iid,)).fetchone()
    m.save(backup, before)
    m.save(destination, dict(at=m.now(), museum=museum, scoped_ids=ids, eligibility=eligibility,
        identifiers=before['identifiers'], creator_links=links, creator_authorities=authorities, counts=counts,
        backup_path=str(backup), policy='Read-only initial museum association audit; pending assertions are discovery leads, not approved assignments. Refresh source/physical-object identity, creator qualifications and eligible creation dates before selected writes. No fixtures or new database rows.'))
    print(json.dumps(dict(museum=museum['name'], scoped_artworks=len(ids), existing_counts=counts,
        eligible_unlinked=sum(r['scope'] == 'eligible' and r['current_institution_id'] is None for r in eligibility),
        records_currently_at_other_institutions=sum(r['current_institution_id'] not in [None, iid] for r in eligibility))), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--institution-id', required=True)
    parser.add_argument('--key', required=True)
    args = parser.parse_args()
    audit(args.institution_id, args.key)
