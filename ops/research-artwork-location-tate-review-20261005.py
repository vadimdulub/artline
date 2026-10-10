#!/usr/bin/env python3
"""Exact Tate metadata matches, explicitly historical and review-only."""
import csv
import importlib.util
import io
import json
from pathlib import Path

s = importlib.util.spec_from_file_location('primary', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r
BASE = 'https://raw.githubusercontent.com/tategallery/collection/master/'


def main():
    index = p.Index()
    raw, receipt = r.capture(BASE + 'artwork_data.csv', tag='tate-review-20261005')
    commits_raw, commits_receipt = r.capture('https://api.github.com/repos/tategallery/collection/commits?path=artwork_data.csv&per_page=1', tag='tate-review-20261005')
    readme, readme_receipt = r.capture(BASE + 'README.md', tag='tate-review-20261005')
    assert receipt['status'] == commits_receipt['status'] == readme_receipt['status'] == 200
    commit = json.loads(commits_raw)[0]
    source_date = commit['commit']['committer']['date']
    assert source_date.startswith('2014-10-27') and b'owns or jointly owns' in readme and b'last updated in October 2014' in readme
    claims, holds = [], []
    for obj in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
        for row in index.find('tate-object', obj['id'], [obj['title']], [obj['artist']], ['Tate']):
            assert all(c[4] == 'United Kingdom' for c in row['supplied'] or [] if c[3] == 'Tate')
            basis = index.match(row, 'tate-object', obj['id'], [obj['title']], [obj['artist']], obj['accession_number'], [obj['dateText']])
            if not basis.startswith(('existing_', 'unique_')):
                holds.append({'artwork_id': row['artwork']['id'], 'object_id': obj['id'], 'reason': basis})
                continue
            url = obj['url'].replace('http://www.tate.org.uk/', 'https://www.tate.org.uk/')
            assert url.startswith('https://www.tate.org.uk/art/artworks/')
            evidence = {k: obj[k] for k in ['id', 'accession_number', 'artist', 'artistId', 'artistRole', 'title', 'dateText', 'creditLine', 'year', 'dimensions', 'url']}
            evidence.update(dataset_commit_sha=commit['sha'], source_snapshot_date=source_date, dataset_history_receipt=commits_receipt, dataset_documentation_receipt=readme_receipt)
            claim = p.claim(row, 'tate-object', obj['id'], index.institution('tate'), receipt, url, evidence, basis)
            claim['review_state'] = 'review'
            claim['source_class'] = 'historical_primary_museum_open_dataset'
            claim['limitation'] = 'Exact catalogue identity matches Tate’s official open dataset last updated on 27 October 2014. Fresh retrieval does not make the underlying catalogue current. Tate or joint ARTIST ROOMS collection association requires current verification; no present institution, legal ownership, physical location, branch, gallery or public display is accepted. Existing creation dates and attribution are unchanged.'
            claims.append(claim)
    p.output('tate-review-20261005', claims, holds)


if __name__ == '__main__':
    main()
