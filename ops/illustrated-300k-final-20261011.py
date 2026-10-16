#!/usr/bin/env python3
"""Read-only final coverage and attachment proof after scoped workers stop."""
import collections
import concurrent.futures
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    'images', Path(__file__).with_name('illustrated-300k-20261011.py'))
i = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i)


def main():
    assert all((i.RUN / ('stop-' + mode + '.json')).exists()
               for mode in ['prefetch', 'audit', 'deliver'])
    withdrawn = {r['artwork_id']: r for r in i.m.load(
        i.RUN / 'black-band-withdrawal-0001.json')['withdrawn']}
    expected, samples, receipts = {}, [], []
    by_provider = collections.Counter()
    for folder in sorted((i.RUN / 'batches').iterdir()):
        transactions = list((folder / 'applied').glob('*.json'))
        proof_path = folder / 'verification.json'
        assert not transactions or proof_path.exists(), folder.name
        if not proof_path.exists():
            continue
        proof = i.m.load(proof_path)
        images, _, _ = i.accepted(folder.name)
        ids = [aid for p in transactions for aid in i.m.load(p)['ids']]
        assert set(ids) == {im['artwork_id'] for im in images}
        assert len(ids) == len(set(ids)) == proof['checks'].get('images', 0)
        rows = {r['artwork_id']: r for r in i.selected(folder.name)['rows']}
        active = []
        for im in images:
            aid = im['artwork_id']
            if aid in withdrawn:
                continue
            assert aid not in expected
            upload = i.m.load(folder / 'uploads' / (aid + '.json'))
            assert upload['public_byte_hash_verified'] and upload['sha256'] == im['sha256']
            expected[aid] = (im, rows[aid])
            active.append(im)
            by_provider[folder.name.split('-')[0]] += 1
        if active:
            samples.append(sorted(active, key=lambda im: i.m.sha(im['artwork_id'].encode()))[0])
        receipts.append(dict(batch=folder.name, sha256=i.m.sha(proof_path.read_bytes()),
                             delivered=proof['checks'].get('images', 0), current=len(active)))
    checked = 0
    with i.m.m.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        db.execute("SET LOCAL statement_timeout='60s'")
        coverage = i.coverage(db)
        assert coverage['qualifying_illustrated'] >= i.TARGET, coverage
        for ids in i.m.chunks(list(expected), 1000):
            rows = db.execute('''SELECT a.id::text,a.primary_media_id::text,a.title,
                a.accession_number,a.creation_year_start,a.creation_year_end,a.date_precision,
                a.status,a.current_institution_id::text,
                m.checksum_sha256::text,m.storage_path,m.byte_size,m.mime_type,
                EXISTS(SELECT 1 FROM artwork_media am WHERE am.artwork_id=a.id
                       AND am.media_id=a.primary_media_id) attached,
                EXISTS(SELECT 1 FROM media_rights_evidence e WHERE e.media_id=a.primary_media_id
                       AND e.adapter_version=%s) evidenced,
                EXISTS(SELECT 1 FROM artwork_search_documents s WHERE s.id=a.id
                       AND s.primary_media_id=a.primary_media_id AND s.status=a.status
                       AND s.title=a.title) searchable
                FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id
                WHERE a.id=ANY(%s::uuid[])''', (i.OP, ids)).fetchall()
            assert len(rows) == len(ids)
            for row in rows:
                im, source = expected[row['id']]
                assert row['primary_media_id'] == im['media_id']
                assert row['checksum_sha256'] == im['sha256']
                assert row['storage_path'] == im['storage_path']
                assert row['byte_size'] == im['bytes'] <= 100000
                assert row['mime_type'] == 'image/jpeg' and row['status'] != 'archived'
                assert row['attached'] and row['evidenced'] and row['searchable']
                for field, key in [('title', 'title'), ('accession_number', 'accession_number'),
                                   ('creation_year_start', 'first'), ('creation_year_end', 'last'),
                                   ('date_precision', 'precision')]:
                    assert row[field] == source[key], (row['id'], field)
                assert row['creation_year_end'] <= 1955
                checked += 1
            print('Current attachments verified', checked, flush=True)
        for row in db.execute('SELECT id::text,primary_media_id::text FROM artworks '
                              'WHERE id=ANY(%s::uuid[])', (list(withdrawn),)):
            assert row['primary_media_id'] != withdrawn[row['id']]['media_id']
    with i.m.m.connect(local=True) as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        local = {table: db.execute('SELECT count(*) n FROM ' + table).fetchone()['n']
                 for table in i.baseline()['local_readonly_counts']}
    assert local == i.baseline()['local_readonly_counts']

    def public(im):
        url = 'https://artlines.org' + im['storage_path']
        response = i.session().get(url, timeout=(15, 60))
        response.raise_for_status()
        assert i.m.sha(response.content) == im['sha256']
        route = 'https://artlines.org/api/backend/v1/atlas/artworks/' + im['artwork_id']
        response = i.session().get(route, timeout=(15, 60))
        response.raise_for_status()
        assert im['storage_path'] in response.text
        return dict(artwork_id=im['artwork_id'], image_url=url, route_url=route,
                    sha256=im['sha256'], status=200)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        fresh_public = list(pool.map(public, samples))
    baseline = 180596
    result = dict(at=i.m.now(), target=i.TARGET, target_achieved=True,
                  production=coverage, baseline_illustrated=baseline,
                  total_increase=coverage['qualifying_illustrated']-baseline,
                  campaign_net=checked, campaign_by_provider=dict(by_provider),
                  quality_withdrawals=len(withdrawn),
                  increase_outside_campaign=coverage['qualifying_illustrated']-baseline-checked,
                  current_attachment_checks=checked, upload_public_byte_checks=checked,
                  final_public_samples=fresh_public, verification_receipts=receipts,
                  local_readonly_counts=local, local_baseline_equal=True,
                  count_basis='Distinct active native inventory objects with usable primary images. '
                              'Includes separately accessioned physical print impressions; '
                              'does not claim unique artistic compositions.',
                  review_limit='Every file technically checked. Museum visual review is flagged '
                               'and sampled, with affected cohorts expanded after failures. '
                               'All selected WikiArt images visually reviewed.')
    i.saved(i.RUN / 'final-verification.json', result)
    print({key:value for key,value in result.items()
           if key not in ['final_public_samples','verification_receipts']}, flush=True)


if __name__ == '__main__':
    main()
