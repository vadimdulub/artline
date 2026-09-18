#!/usr/bin/env python3
"""Read-only exact-image duplicate check for the completed follow-up deliveries."""
import argparse
import collections
import importlib.util
import json
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

spec = importlib.util.spec_from_file_location('report', Path(__file__).with_name('report-overnight-images.py'))
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--prior-manifest', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    done = report.delivery.complete_ids(args.run)
    journal = report.journal_state(args.run / 'local-attachments.jsonl')
    assert done <= journal.keys(), 'Completed delivery missing local receipt'
    hashes = {json.loads(Path(journal[aid]['receipt']).read_text())['sha256'] for aid in done}
    prior_hashes = set()
    with args.prior_manifest.open() as source:
        for line in source:
            prior_hashes.add(json.loads(line)['image_sha256'])
    groups = collections.defaultdict(list)
    with psycopg.connect('postgres://localhost/artline', autocommit=True,
                         row_factory=dict_row, options='-c default_transaction_read_only=on') as db:
        for offset in range(0, len(hashes), 500):
            rows = db.execute("""
                SELECT a.id::text, a.title, a.status, m.checksum_sha256, m.storage_path,
                  ARRAY(SELECT p.display_name FROM artwork_artists aa
                    JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id) artists,
                  ARRAY(SELECT e.scheme||':'||e.external_id FROM external_identifiers e
                    WHERE e.entity_type='artwork' AND e.entity_id=a.id) identifiers
                FROM media_assets m JOIN artworks a ON a.primary_media_id=m.id
                WHERE m.checksum_sha256=ANY(%s)
                """, (sorted(hashes)[offset:offset + 500],)).fetchall()
            for row in rows:
                groups[row['checksum_sha256']].append(row)
    result = {
        'at': report.core.now(), 'snapshot_delivered': len(done),
        'unique_current_sha256': len(hashes),
        'shared_with_prior_round_sha256': len(hashes & prior_hashes),
        'groups_with_other_catalogue_primary_images': [
            {'sha256': key, 'records': rows} for key, rows in sorted(groups.items()) if len(rows) > 1
        ],
        'limitation': 'Exact compressed approved-image hashes only; no artwork was deleted or merged. '
                      'Separate physical works require accession and source identity review.',
    }
    report.core.save_new(args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k != 'groups_with_other_catalogue_primary_images'}))
    print('shared groups', len(result['groups_with_other_catalogue_primary_images']))


if __name__ == '__main__':
    main()
