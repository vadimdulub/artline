#!/usr/bin/env python3
"""Read-only selected-record research and museum guide snapshots."""
import argparse
import collections
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('r', Path(__file__).with_name('research-artwork-locations-20261004.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
GUIDES = r.ROOT / 'docs/research/museum-guides-20261005'


def baseline():
    dest = r.RUN / 'museum-guides-baseline-20261005e.json.gz'
    if dest.exists():
        data = r.load(dest)
    else:
        with r.connect() as db:
            missing = db.execute("SELECT id::text,slug,title,status,primary_media_id::text FROM artworks WHERE status<>'archived' AND current_institution_id IS NULL ORDER BY id").fetchall()
            museums = db.execute("""SELECT to_jsonb(i) institution,count(*) works,
                count(a.primary_media_id) images,
                count(*) FILTER(WHERE h.id IS NOT NULL) accepted_holdings
                FROM institutions i JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived'
                LEFT JOIN artwork_location_assertions h ON h.artwork_id=a.id AND h.claim_type='holding'
                AND h.review_state='accepted' AND h.superseded_by IS NULL
                GROUP BY i.id ORDER BY count(*) DESC,i.id""").fetchall()
            totals = db.execute("SELECT count(*) works,count(primary_media_id) images,count(current_institution_id) institutions FROM artworks WHERE status<>'archived'").fetchone()
        data = {'at': r.now(), 'missing': missing, 'museums': museums, 'totals': totals}
        r.save_gz(dest, data)
    ids = {x['id'] for x in data['missing']}
    rows = [v for v in r.load(r.RUN / 'missing-locations.json.gz') if v['artwork']['id'] in ids]
    supplied = collections.Counter(c[3] for v in rows for c in v['supplied'] or [])
    providers = {}
    for path in sorted((r.RUN / 'primary-plans').glob('*.json.gz')):
        plan = r.load(path)
        claims = [v for v in plan['claims'] if v['artwork_id'] in ids]
        holds = [v for v in plan['holds'] if v.get('artwork_id') in ids]
        providers[path.name] = {'claims': len(claims), 'states': dict(collections.Counter(v.get('review_state', 'accepted') for v in claims)), 'holds': len(holds), 'reasons': dict(collections.Counter(v['reason'] for v in holds))}
    summary = {'at':data['at'], 'totals':data['totals'], 'missing':len(ids), 'museums':len(data['museums']),
        'top_museums':[{'name':v['institution']['name'], 'works':v['works'], 'images':v['images'], 'accepted_holdings':v['accepted_holdings']} for v in data['museums'][:30]],
        'top_remaining_supplied':supplied.most_common(65), 'providers':providers}
    r.save(r.RUN/'museum-guides-distribution-20261005e.json', summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='providers'},ensure_ascii=False),flush=True)
    for name, counts in providers.items():
        if counts['claims'] + counts['holds'] >= 100:
            print(name, json.dumps(counts,ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['baseline'])
    globals()[parser.parse_args().command]()
