#!/usr/bin/env python3
"""Read-only fourth-round discovery and complete production-profile coverage register."""
import argparse
from collections import Counter, defaultdict
import importlib.util
import json
import hashlib
from pathlib import Path
import requests

spec = importlib.util.spec_from_file_location('original_research', Path(__file__).with_name('research-painter-influences-20261008.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
ORIGINAL = r.RUN
RUN = r.ROOT / 'docs/research/painter-influences-round4-20261009'
CACHE = Path.home() / 'Library/Application Support/Artline/research/painter-influences-round4-20261009'
PRIOR = [r.ROOT / 'docs/research' / name for name in ('painter-influences-round2-20261008', 'painter-influences-round3-20261009')]


def prior_register():
    return {b['id']: v for v in r.load(ORIGINAL / 'painter-research-register.json.gz')
            for b in v['catalogue_bindings'] if b['catalogue'] == 'production'}


def newcomers():
    old = prior_register()
    return [v for v in r.load(RUN / 'production-artists.json.gz') if v['id'] not in old]


def fetch_new():
    fresh = newcomers()
    r.save(RUN / 'newcomer-profiles.json.gz', fresh)
    original_authorities = r.authority_index()
    authority_reader = r.authority_index
    r.RUN, r.CACHE, r._bindings = RUN, CACHE, None
    r.roster = lambda: fresh
    r.authority_index = lambda: {**original_authorities, **authority_reader()}
    print('Fresh lookup targets', len(fresh), flush=True)
    r.identity_search()
    r.wikidata()
    r.authorities()
    r.resolve_names()
    r._bindings = None
    r.wikidata()
    r.authorities()
    r.wikipedia()
    r.native_articles()
    r.wikipedia_native()
    r.biography_leads()


def resolve_named():
    grouped = defaultdict(list)
    for v in r.load(RUN / 'named-source-titles.json'):
        grouped[v['language']].append(v['title'])
    receipts = []
    qids = set()
    batches = [(language, titles[i:i + 40]) for language, titles in grouped.items() for i in range(0, len(titles), 40)]
    for language, titles in batches:
        response = requests.get('https://' + language + '.wikipedia.org/w/api.php', params=dict(
            action='query', format='json', formatversion=2, titles='|'.join(titles),
            prop='pageprops|info', inprop='url', redirects=1), headers={'User-Agent': r.UA}, timeout=40)
        response.raise_for_status()
        data = response.json()
        assert 'error' not in data
        for v in data.get('query', {}).get('pages', []):
            props = v.get('pageprops', {})
            if props.get('wikibase_item') and 'disambiguation' not in props:
                qids.add(props['wikibase_item'])
        receipts.append(dict(at=r.now(), language=language, requested_titles=titles, url=response.url, data=data))
    receipt_path = RUN / 'named-source-resolution-receipts.json.gz'
    if receipt_path.exists():
        archive = RUN / 'named-source-resolution-history' / (hashlib.sha256(receipt_path.read_bytes()).hexdigest() + '.json.gz')
        if not archive.exists():
            r.save(archive, r.load(receipt_path))
    r.save(receipt_path, receipts)
    r.RUN = RUN
    for offset in range(0, len(qids), 100):
        batch = sorted(qids)[offset:offset + 100]
        query = '''SELECT ?artist ?artistLabel ?birth ?death ?occupation ?occupationLabel ?wikiart ?article WHERE {
          VALUES ?artist { ''' + ' '.join('wd:' + q for q in batch) + ''' }
          OPTIONAL {?artist wdt:P569 ?birth} OPTIONAL {?artist wdt:P570 ?death}
          OPTIONAL {?artist wdt:P106 ?occupation} OPTIONAL {?artist wdt:P6002 ?wikiart}
          OPTIONAL {?article schema:about ?artist; schema:isPartOf <https://en.wikipedia.org/>}
          SERVICE wikibase:label {bd:serviceParam wikibase:language "en,mul,fr,de,ru,el"}
        }'''
        assert r.sparql(query, 'wikidata-authorities', hashlib.sha256(query.encode()).hexdigest())
    print('Resolved title authorities', len(qids), flush=True)


def coverage():
    if (RUN / 'summary-catalogue-catchup.json').exists():
        raise RuntimeError('The register now includes later catalogue arrivals. Preserve it; use the catch-up workflow with a new snapshot instead of overwriting it from the earlier import roster.')
    artists = r.load(RUN / 'production-artists.json.gz')
    old = prior_register()
    snapshot = r.load(RUN / 'production-snapshot.json')
    claims = snapshot['existing_influences']
    plan_path = RUN / 'production-plan-v1.json.gz'
    if (RUN / 'production-plan-v1-verified.json').exists():
        claims += r.load(plan_path)['inserts']['influence_claims']
    incoming = defaultdict(Counter)
    for c in claims:
        if c['status'] != 'archived':
            incoming[c['target_artist_id']][c['relationship_type']] += 1
    leads = r.load(ORIGINAL / 'biography-leads.json.gz')
    fresh_leads = r.load(RUN / 'biography-leads.json.gz') if (RUN / 'biography-leads.json.gz').exists() else []
    all_leads = {v['id']: v for v in leads + fresh_leads}
    reviewed = {v['lead_id'] for v in r.load(ORIGINAL / 'reviewed-biography-decisions.json')}
    for directory in PRIOR + [RUN]:
        path = directory / 'reviews.jsonl'
        if path.exists():
            candidates = r.load(directory / 'candidate-passages.json.gz')
            reviewed.update(candidates[json.loads(line)['i']]['id'] for line in path.read_text().splitlines())
    extra_reviews = RUN / 'newcomer-reviews.jsonl'
    if extra_reviews.exists():
        reviewed.update(json.loads(line)['lead_id'] for line in extra_reviews.read_text().splitlines())
    by_q = defaultdict(list)
    for v in all_leads.values():
        by_q[v['subject_qid']].append(v)
    bindings = {}
    for name in ('supplemental-identity-bindings.json', 'research-identity-bindings.json'):
        if (RUN / name).exists():
            bindings.update({v['artist_id']: v['qid'] for v in r.load(RUN / name) if v['decision'] == 'supported_research_identity'})
    statement_qids = set()
    if (RUN / 'wikidata-statement-coverage.json').exists():
        statement_qids = {q for v in r.load(RUN / 'wikidata-statement-coverage.json')['results'] if v['ok'] for q in v['qids']}
    records = []
    for a in artists:
        previous = old.get(a['id'])
        qs = {v['external_id'] for v in a['identifiers'] if v['scheme'] == 'wikidata'}
        if previous:
            qs.update(previous['wikidata_ids'])
        if a['id'] in bindings:
            qs.add(bindings[a['id']])
        passages = {v['id']: v for q in qs for v in by_q[q]}
        pending = sorted(set(passages) - reviewed)
        search_path = RUN / 'identity-search' / (a['id'] + '.json')
        search = r.load(search_path) if search_path.exists() else None
        count = incoming[a['id']]
        attempted = bool((previous and previous['research_attempted']) or search or qs & statement_qids)
        status = ('artistic_influence_recorded' if count['influenced'] else
                  'teaching_or_admiration_only' if count else
                  'biography_passages_require_review' if pending else
                  'identity_unresolved_after_lookup' if len(qs) != 1 and attempted else
                  'no_relationship_in_checked_sources' if attempted else 'lookup_not_completed')
        records.append(dict(artist_id=a['id'], name=a['display_name'], slug=a['slug'], entity_type=a['entity_type'],
            historical_status=a['status'], wikidata_ids=sorted(qs), research_attempted=attempted,
            previous_register_artist_id=previous['artist_id'] if previous else None,
            previous_research_status=previous['research_status'] if previous else None,
            newcomer_search=dict(at=search['at'], url=search.get('url'),
                status='error' if 'error' in search else 'candidates_found' if search.get('data', {}).get('search') else 'no_candidate_found') if search else None,
            fresh_wikidata_statement_check=bool(qs & statement_qids),
            relationship_counts=dict(count), reviewed_biography_passages=len(set(passages) & reviewed),
            pending_biography_passages=len(pending), pending_lead_ids=pending, research_status=status,
            limitation='Lookup coverage is not historical completeness. Missing evidence does not mean the painter had no influences.'))
    assert len(records) == len(artists) == len({v['artist_id'] for v in records})
    r.save(RUN / 'painter-research-register.json.gz', records)
    r.save(RUN / 'coverage-summary.json', dict(at=r.now(), active_production_profiles=len(records),
        newcomer_profiles=len(newcomers()), lookup_attempted_profiles=sum(v['research_attempted'] for v in records),
        profiles_with_artistic_influence=sum(v['relationship_counts'].get('influenced', 0) > 0 for v in records),
        profiles_with_any_relationship=sum(bool(v['relationship_counts']) for v in records),
        profiles_without_artistic_influence=sum(not v['relationship_counts'].get('influenced', 0) for v in records),
        research_status_counts=dict(Counter(v['research_status'] for v in records)),
        individually_reviewed_passages=len(reviewed), pending_discovered_passages=len(set(all_leads) - reviewed),
        complete_historical_review=False, snapshot_at=snapshot['at']))
    r.save(RUN / 'initial-production-influence-coverage.json.gz', dict(at=snapshot['at'], read_only=True,
        counts=[dict(relationship_type=k[0], status=k[1], n=n) for k, n in Counter((v['relationship_type'], v['status']) for v in snapshot['existing_influences']).items()],
        painters=[dict(id=a['id'], slug=a['slug'], display_name=a['display_name'], influences=incoming[a['id']]['influenced']) for a in artists])) if not (RUN / 'initial-production-influence-coverage.json.gz').exists() else None
    print(json.dumps(r.load(RUN / 'coverage-summary.json'), indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['fetch-new', 'coverage', 'resolve-named'])
    args = parser.parse_args()
    {'fetch-new': fetch_new, 'coverage': coverage, 'resolve-named': resolve_named}[args.command]()
