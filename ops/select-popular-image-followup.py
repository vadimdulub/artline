#!/usr/bin/env python3
"""Read-only, bounded popular-painter image selection with recoverable preimages."""
import argparse
import collections
import importlib.util
import json
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

spec = importlib.util.spec_from_file_location('common', Path(__file__).with_name('overnight-commons-images.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
core = m.core


def connect(dsn):
    return psycopg.connect(dsn, autocommit=True, row_factory=dict_row,
                          options='-c default_transaction_read_only=on -c statement_timeout=90000')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--limit', type=int, default=200)
    parser.add_argument('--discovery-mode', choices=('fresh', 'depicts'), default='fresh')
    parser.add_argument('--previous-run', type=Path, action='append', default=[])
    parser.add_argument('--max-per-artist', type=int, default=0)
    parser.add_argument('--direct-per-provider', type=int, default=30)
    parser.add_argument('--local-only', action='store_true',
                        help='Prepare a local selection while cloud access is unavailable; production must be revalidated before delivery')
    args = parser.parse_args()
    root = args.run
    root.mkdir(parents=True, exist_ok=True)
    prior = core.ROOT / 'docs/research/popular-painting-images-20260916'
    searched = set()
    for pattern in ('commons-fulltext/discovery/*.json', 'commons-native-links*/discovery/*.json'):
        for path in prior.glob(pattern):
            searched.add(path.stem)
    austria = core.ROOT / 'docs/research/austrian-museums-20260916/alternate-images/discovery'
    searched.update(path.stem for path in austria.glob('*.json'))
    if args.discovery_mode == 'depicts':
        # This route asks a different, corroborated structured-data query.
        # Skip paintings already attempted through that same route.
        searched = set()
    direct_searched = set()
    for previous in args.previous_run:
        for path in previous.glob('*/events.jsonl'):
            is_depicts = 'depicts' in path.parent.name
            for line in path.read_text().splitlines():
                event = json.loads(line)
                aid = event.get('artwork_id')
                if aid and ((args.discovery_mode == 'depicts' and is_depicts) or
                            (args.discovery_mode == 'fresh' and not is_depicts)):
                    searched.add(aid)
                if aid and path.parent.name == 'direct-museums':
                    direct_searched.add(aid)
    blocked = set()
    for history in [prior, *args.previous_run]:
        for filename in ('prior-rejected-commons-files.json', 'newly-rejected-commons-files.json'):
            path = history / filename
            if path.exists():
                blocked.update(json.loads(path.read_text())['titles'])
    core.save_new(root / 'prior-rejected-commons-files.json', {'titles': sorted(blocked)})
    with connect('postgres://localhost/artline') as db:
        rows = db.execute("""WITH popular AS MATERIALIZED (
          SELECT DISTINCT aa.artwork_id FROM artist_discovery_selection d
          JOIN artists ar ON ar.id=d.artist_id AND ar.status<>'archived'
          JOIN artwork_artists aa ON aa.artist_id=d.artist_id WHERE d.is_popular)
          SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,a.accession_number,
          a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,
          i.id::text institution_id,i.slug institution_slug,i.name museum,i.wikidata_id institution_qid,
          i.website_url,p.country_code,
          ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id) roles,
          (SELECT jsonb_agg(jsonb_build_object('qid',e.external_id,'name',ar.display_name,'death',ar.death_year)
           ORDER BY ar.id) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id
           LEFT JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=ar.id AND e.scheme='wikidata'
           WHERE aa.artwork_id=a.id) creators,
          (SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'external_id',e.external_id,'url',e.canonical_url)
           ORDER BY e.scheme,e.external_id) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) identifiers
          FROM popular pw JOIN artworks a ON a.id=pw.artwork_id JOIN institutions i ON i.id=a.current_institution_id
          LEFT JOIN places p ON p.id=i.place_id
          WHERE a.status='review' AND a.primary_media_id IS NULL AND a.work_type='painting'
          AND a.creation_year_start>=1000 AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
          AND artline_has_selection_evidence(a.id) ORDER BY a.slug""").fetchall()
    core.save_new(root / 'eligible-popular-painting-gaps.json', {'at': core.now(), 'records': rows})
    fresh, direct, held = [], [], []
    schemes = {'european-met-the-met-object': 'met', 'met-object': 'met',
               'european-chicago-art-institute-of-chicago-object': 'chicago', 'aic-object': 'chicago',
               'european-cleveland-cleveland-museum-of-art-object': 'cleveland', 'cleveland-object': 'cleveland',
               'european-smk-statens-museum-for-kunst-object': 'smk'}
    for row in rows:
        c = dict(row, popular=True)
        c['artist'] = '; '.join(x['name'] for x in c['creators'] or [])
        c['native_identifiers'] = [e for e in c['identifiers'] or [] if e['scheme'] != 'wikidata']
        qids = [e['external_id'] for e in c['identifiers'] or [] if e['scheme'] == 'wikidata']
        if len(qids) == 1 and c['institution_qid'] and c['roles'] == ['primary'] and len(c['creators'] or []) == 1 and c['creators'][0]['qid']:
            if c['artwork_id'] not in searched:
                fresh.append(dict(c, qid=qids[0], external_id=qids[0], scheme='wikidata', provider='night-commons'))
        for identifier in c['native_identifiers']:
            if identifier['scheme'] in schemes:
                direct.append(dict(c, provider=schemes[identifier['scheme']], scheme=identifier['scheme'],
                                   external_id=identifier['external_id'], page=identifier['url']))
                break
    fresh.sort(key=lambda c: (c['artist'], c['title']))
    if args.max_per_artist:
        per_artist = collections.Counter()
        diversified = []
        for c in fresh:
            if per_artist[c['artist']] < args.max_per_artist:
                diversified.append(c)
                per_artist[c['artist']] += 1
        fresh = diversified
    fresh = fresh[:args.limit]
    # A different direct museum image may succeed after a Commons hold. Limit
    # this pass to 30 records per source; candidates still need fresh rights.
    per = collections.Counter()
    bounded_direct = []
    for c in direct:
        if per[c['provider']] < args.direct_per_provider and c['artwork_id'] not in direct_searched and c['artwork_id'] not in {x['artwork_id'] for x in fresh}:
            bounded_direct.append(c)
            per[c['provider']] += 1
    dsn = None if args.local_only else core.cloud_dsn()
    accepted = {'commons-photos': [], 'direct-museums': []}
    all_rows = fresh + bounded_direct
    if args.local_only:
        for c in all_rows:
            c['target_ids'] = {'local': c['artwork_id']}
            accepted['commons-photos' if c['provider'] == 'night-commons' else 'direct-museums'].append(c)
    else:
        with connect(dsn) as db:
            remote = db.execute("""SELECT a.id::text,a.slug,a.title,a.creation_year_start,a.creation_year_end,
              a.work_type,a.primary_media_id::text,a.status,e.scheme,e.external_id,
              artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope,
              artline_has_selection_evidence(a.id) supported
              FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id
              WHERE e.scheme=ANY(%s) AND e.external_id=ANY(%s)""",
              (list({c['scheme'] for c in all_rows}), list({c['external_id'] for c in all_rows}))).fetchall()
            index = collections.defaultdict(list)
            for row in remote:
                index[(row['scheme'], row['external_id'])].append(row)
            for c in all_rows:
                hits = index[(c['scheme'], c['external_id'])]
                if len(hits) != 1 or any(hits[0][k] != c[k] for k in ('slug','title','creation_year_start','creation_year_end','work_type')) or hits[0]['status'] != 'review' or hits[0]['scope'] != 'eligible' or not hits[0]['supported']:
                    held.append({'artwork_id': c['artwork_id'], 'reason': 'Production identity or eligibility differs'})
                    continue
                if hits[0]['primary_media_id']:
                    continue
                c['target_ids'] = {'local': c['artwork_id'], 'cloud': hits[0]['id']}
                accepted['commons-photos' if c['provider'] == 'night-commons' else 'direct-museums'].append(c)
    backup = Path.home() / 'Library/Application Support/Artline/backups' / root.name
    backup.mkdir(parents=True, exist_ok=True)
    manifest = {'scope': 'Fresh selected artwork, creator and source-identity preimages; image associations only, no replacement or publication.', 'targets': {}}
    chosen = sum(accepted.values(), [])
    targets = [('local','postgres://localhost/artline')] + ([] if args.local_only else [('cloud',dsn)])
    for target, conn in targets:
        with connect(conn) as db:
            preimage = db.execute("""SELECT to_jsonb(a) artwork,
              (SELECT jsonb_agg(to_jsonb(aa)) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creators,
              (SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) identifiers
              FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id""", ([c['target_ids'][target] for c in chosen],)).fetchall()
        path = backup / (target + '-selected-before.json')
        core.save_new(path, preimage)
        manifest['targets'][target] = {'path': str(path), 'rows': len(preimage), 'sha256': core.sha(path.read_bytes())}
    core.save_new(root / 'backups.json', manifest)
    for folder, group in accepted.items():
        core.save_new(root / folder / 'candidates.json', {'at': core.now(), 'candidates': group})
        core.save_new(root / folder / 'backups.json', manifest)
    core.save_new(root / 'selection-report.json', {'at': core.now(), 'local_only': args.local_only, 'eligible_local_gaps': len(rows),
      'prior_alternate_searches_excluded': len(searched), 'selected': {k: len(v) for k,v in accepted.items()},
      'direct_providers': dict(collections.Counter(c['provider'] for c in accepted['direct-museums'])), 'held': held})
    print(json.dumps({'eligible_local_gaps': len(rows), 'selected': {k:len(v) for k,v in accepted.items()}, 'held': len(held)}), flush=True)


if __name__ == '__main__':
    main()
