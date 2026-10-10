#!/usr/bin/env python3
"""Export the real catalogue and an evidence-backed, delivery-aware research ledger.

Read-only database access; immutable, timestamped outputs. Production delivery
is derived from committed batch receipts and separate verification receipts.
An unfinished upload is never represented as a verified production write.
"""
import collections
import csv
import gzip
import importlib.util
import json
from pathlib import Path
import shutil

spec = importlib.util.spec_from_file_location('delivery', Path(__file__).with_name('apply-artwork-locations-20261004.py'))
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)
r = d.r
WAVES = ['primary-02', 'walters-01', 'france-03', 'followup-01', 'walters-02', 'curated-01', 'final-local-01']
PROVIDERS = ['moma', 'fng', 'mia', 'lombardia', 'walters-current', 'joconde-final', 'mia-followup', 'smk-followup', 'walters-followup-v2', 'saam-followup-v2', 'agsa', 'curated', 'wikidata-review']


def csv_output(path, rows, fields):
    assert not path.exists()
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fields, extrasaction='raise')
        writer.writeheader()
        writer.writerows(rows)


def main():
    at = r.now()
    dest = r.RUN / ('report-' + at.replace('-', '').replace(':', ''))
    dest.mkdir()
    baseline = r.load(r.RUN / 'local-baseline.json')
    rows = r.load(r.RUN / 'missing-locations.json.gz')
    original = {v['artwork']['id']: v for v in rows}
    delivered, wave_stats, source_receipts = {}, [], {}
    outcomes = collections.defaultdict(set)
    paths = collections.defaultdict(set)
    candidate_names = collections.defaultdict(set)
    candidate_urls = collections.defaultdict(set)
    for provider in PROVIDERS:
        path = r.RUN / 'primary-plans' / (provider + '.json.gz')
        data = r.load(path)
        for claim in data['claims']:
            aid = claim['artwork_id']
            outcomes[aid].add(provider + ':candidate_' + claim.get('review_state', 'accepted'))
            paths[aid].add(str(path.relative_to(r.ROOT)))
            candidate_names[aid].add(claim['institution']['name'])
            candidate_urls[aid].add(claim['source_url'])
        for hold in data['holds']:
            aid = hold.get('artwork_id')
            if aid in original:
                outcomes[aid].add(provider + ':' + hold['reason'])
                paths[aid].add(str(path.relative_to(r.ROOT)))
    for wave in WAVES:
        data, digest = d.pinned(wave)
        folder = r.RUN / 'delivery' / wave
        verified = {}
        for path in folder.glob('verification*.json'):
            receipt = r.load(path)
            assert receipt['plan_sha256'] == digest and not receipt['errors']
            verified.update(receipt['targets'])
        receipts = {}
        for target in ['local', 'production']:
            receipts[target] = set()
            for path in (folder / target).glob('*.json'):
                receipt = r.load(path)
                assert receipt['plan_sha256'] == digest
                assert not receipts[target].intersection(receipt['artwork_ids'])
                receipts[target].update(receipt['artwork_ids'])
        stats = {'wave': wave, 'planned': len(data['claims']), 'committed': {}, 'verified': verified}
        for target in receipts:
            stats['committed'][target] = dict(collections.Counter(c.get('review_state', 'accepted') for c in data['claims'] if c['target_ids'].get(target) in receipts[target]))
        wave_stats.append(stats)
        for c in data['claims']:
            aid = c['artwork_id']
            assert aid not in delivered, ('duplicate final local claim', aid)
            assert c['target_ids']['local'] in receipts['local']
            assert verified.get('local') == len(data['claims'])
            production_id = c['target_ids'].get('production')
            production_status = 'pending_authentication_and_preflight'
            if production_id:
                production_status = 'pending_upload_authentication'
                if production_id in receipts['production']:
                    production_status = 'committed_and_verified' if verified.get('production') == len(data['claims']) else 'committed_full_verification_pending'
            delivered[aid] = {**c, 'wave': wave, 'production_id': production_id, 'production_status': production_status}
            receipt = c['source_receipt']
            if receipt['body_path'] in source_receipts:
                assert source_receipts[receipt['body_path']]['sha256'] == receipt['sha256']
            source_receipts[receipt['body_path']] = receipt
        for hold in data['held']:
            aid = hold['artwork_id']
            outcomes[aid].add('preflight:' + hold['reason'])
            paths[aid].add(str((folder / 'plan.json.gz').relative_to(r.ROOT)))

    wikiart = {}
    for path in sorted((r.RUN / 'wikiart-leads').glob('*.json')):
        lead = r.load(path)
        aid = lead['artwork_id']
        wikiart[aid] = lead
        outcomes[aid].add('wikiart:' + lead['outcome'])
        paths[aid].add(str(path.relative_to(r.ROOT)))
        if lead['outcome'] == 'museum_lead_requires_corroboration':
            candidate_names[aid].add(lead['fields']['Location'])
            candidate_urls[aid].add(lead['source_url'])

    # A full bounded-column export is an offline audit, never a browser/API payload.
    current = {}
    with r.connect() as db:
        totals = db.execute('SELECT status,count(*) artworks,count(current_institution_id) with_institution FROM artworks GROUP BY status ORDER BY status').fetchall()
        assertions = db.execute('SELECT claim_type,review_state,count(*) FROM artwork_location_assertions GROUP BY 1,2 ORDER BY 1,2').fetchall()
        with (dest / 'catalogue-location-coverage-after.csv').open('wb') as file:
            with db.cursor().copy("COPY (SELECT a.id,a.slug,a.title,a.status,a.current_institution_id,i.name institution,a.current_location_text,a.current_location_unknown_reason,a.location_checked_at FROM artworks a LEFT JOIN institutions i ON i.id=a.current_institution_id WHERE a.status<>'archived' ORDER BY a.id) TO STDOUT WITH CSV HEADER") as cp:
                for chunk in cp:
                    file.write(chunk)
        france = [c for c in delivered.values() if c['wave'] == 'france-03'][:500]
        schemes = [v['scheme'] for v in db.execute("SELECT DISTINCT scheme FROM external_identifiers WHERE entity_type='artwork'").fetchall() if d.scheme_family(v['scheme']) == 'joconde']
        urls = sorted({c['source_url'] for c in france} | {c['source_url'].replace('https://pop.culture.gouv.fr/', 'https://www.pop.culture.gouv.fr/') for c in france})
        plan = db.execute("""EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) WITH selected AS MATERIALIZED (
          SELECT entity_id,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=ANY(%s)
          UNION SELECT entity_id,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)
        ) SELECT e.entity_id::text,e.scheme,e.external_id,e.canonical_url,a.status FROM selected e JOIN artworks a ON a.id=e.entity_id WHERE a.status<>'archived'""", (schemes, sorted({c['external_id'] for c in france}), urls)).fetchone()
        r.save(dest / 'local-500-object-identity-query-plan.json', {'at': r.now(), 'selected_objects': len(france), 'plan': plan, 'limitation': 'Read-only actual-plan audit against the real local catalogue; no fixtures inserted. This is not evidence of 10-million-row performance. Representative disposable load testing remains outstanding outside Documents.'})
    with (dest / 'catalogue-location-coverage-after.csv').open(newline='') as file:
        current = {v['id']: v for v in csv.DictReader(file)}
    with (r.RUN / 'catalogue-location-coverage.csv').open(newline='') as file:
        before = {v['id']: v for v in csv.DictReader(file)}
    assert current.keys() == before.keys()
    assert {v['status']: v['artworks'] for v in totals} == {v['status']: v['artworks'] for v in baseline['totals']}
    unrelated_changes = []
    for aid, old in before.items():
        new = current[aid]
        assert all(new[k] == old[k] for k in ['id', 'slug', 'title', 'status'])
        if aid in delivered:
            c = delivered[aid]
            if c.get('review_state', 'accepted') == 'accepted':
                assert not old['current_institution_id'] and new['current_institution_id'] == c['target_institutions']['local']['id']
            else:
                assert old == new
        elif old != new:
            unrelated_changes.append({'artwork_id': aid, 'changed_fields': [k for k in old if old[k] != new[k]]})
    assert not unrelated_changes, unrelated_changes[:10]

    fields = ['local_artwork_id', 'production_artwork_id', 'slug', 'title', 'creators', 'museum', 'location_text', 'claim_type', 'review_state', 'source_url', 'checked_at', 'identity_basis', 'limitation', 'source_body_sha256', 'source_body_path', 'wave', 'local_delivery', 'production_delivery']
    accepted_rows, review_rows = [], []
    for aid, c in sorted(delivered.items()):
        old = original[aid]
        row = {'local_artwork_id': aid, 'production_artwork_id': c['production_id'], 'slug': old['artwork']['slug'], 'title': old['artwork']['title'], 'creators': '; '.join(v['name'] for v in old['artists']) or old['artwork'].get('unlinked_creator_label'), 'museum': c['institution']['name'], 'location_text': c['location_text'], 'claim_type': 'holding', 'review_state': c.get('review_state', 'accepted'), 'source_url': c['source_url'], 'checked_at': c['checked_at'], 'identity_basis': c['identity_basis'], 'limitation': c['limitation'], 'source_body_sha256': c['source_receipt']['sha256'], 'source_body_path': c['source_receipt']['body_path'], 'wave': c['wave'], 'local_delivery': 'committed_and_verified', 'production_delivery': c['production_status']}
        (accepted_rows if row['review_state'] == 'accepted' else review_rows).append(row)
    csv_output(dest / 'supported-museum-links.csv', accepted_rows, fields)
    csv_output(dest / 'museum-leads-for-review.csv', review_rows, fields)

    ledger, counts = [], collections.Counter()
    for aid, old in sorted(original.items()):
        c = delivered.get(aid)
        if c:
            status = 'accepted_museum_holding' if c.get('review_state', 'accepted') == 'accepted' else 'museum_candidate_in_review'
        elif any(x.startswith('preflight:') for x in outcomes[aid]):
            status = 'identity_or_location_held'
        elif wikiart.get(aid, {}).get('outcome') == 'museum_lead_requires_corroboration':
            status = 'museum_candidate_uncorroborated'
        elif outcomes[aid]:
            status = 'researched_candidate_unresolved'
        else:
            status = 'not_researched_this_pass'
        counts[status] += 1
        ledger.append({'artwork_id': aid, 'slug': old['artwork']['slug'], 'title': old['artwork']['title'], 'creators': '; '.join(v['name'] for v in old['artists']) or old['artwork'].get('unlinked_creator_label'), 'publication_status': current[aid]['status'], 'research_status': status, 'current_local_museum': current[aid]['institution'], 'candidate_museums_not_current_location_proof': ' | '.join(sorted(candidate_names[aid])), 'candidate_source_urls': ' | '.join(sorted(candidate_urls[aid])), 'research_outcomes': ' | '.join(sorted(outcomes[aid])), 'evidence_paths': ' | '.join(sorted(paths[aid])), 'local_delivery': 'committed_and_verified' if c else 'no_new_assertion', 'production_delivery': c['production_status'] if c else 'no_new_assertion'})
    csv_output(dest / 'research-ledger.csv', ledger, list(ledger[0]))
    unresolved = [v for v in ledger if not current[v['artwork_id']]['current_institution_id']]
    csv_output(dest / 'unresolved-artworks.csv', unresolved, list(ledger[0]))

    display_plan = r.load(r.RUN / 'delivery/dated-display-02/plan.json.gz')
    display_rows = []
    for c in display_plan['targets']['local']:
        source_receipts[c['source_receipt']['body_path']] = c['source_receipt']
        display_rows.append({'artwork_id': c['artwork_id'], 'title': c['before']['artwork']['title'], 'holding_museum': current[c['artwork_id']]['institution'], 'observed_institution': c['institution']['name'], 'venue': (c.get('venue') or {}).get('name'), 'display_state': c['display_state'], 'source_url': c['source_url'], 'checked_at': c['source_receipt']['retrieved_at'], 'source_updated_at': c['source_updated_at'], 'note': c['note'], 'local_delivery': 'committed_and_verified', 'production_delivery': 'pending_upload_authentication'})
    csv_output(dest / 'dated-display-observations.csv', display_rows, list(display_rows[0]))

    bytes_verified = 0
    for path, receipt in source_receipts.items():
        raw = gzip.decompress((r.ROOT / path).read_bytes())
        assert r.sha(raw) == receipt['sha256'], path
        bytes_verified += len(raw)
    r.save(dest / 'source-integrity.json', {'at': r.now(), 'distinct_response_bodies_verified': len(source_receipts), 'uncompressed_bytes_verified': bytes_verified, 'all_sha256_match': True, 'scope': 'Every source response cited by the delivered local holding and display assertions.'})

    production_committed = [c for c in delivered.values() if c['production_status'].startswith('committed')]
    production_verified = [c for c in production_committed if c['production_status'] == 'committed_and_verified']
    summary = {'generated_at': at, 'status': 'local_complete_for_this_research_pass; production_partial_authentication_expired; research_incomplete_for_entire_catalogue', 'scope': 'Existing catalogue gaps only. Previously assigned museum links were inventoried, not all freshly re-researched. Supported museum holdings do not prove current physical location or public display.', 'local_baseline': baseline, 'local_after': {'totals': totals, 'assertions': assertions, 'new_accepted_holdings': len(accepted_rows), 'new_review_holdings': len(review_rows), 'new_dated_display_observations': len(display_rows), 'remaining_missing_museum': len(unresolved)}, 'production': {'new_committed_by_review_state': dict(collections.Counter(c.get('review_state', 'accepted') for c in production_committed)), 'fully_verified_by_review_state': dict(collections.Counter(c.get('review_state', 'accepted') for c in production_verified)), 'pending_holdings_by_review_state': dict(collections.Counter(c.get('review_state', 'accepted') for c in delivered.values() if not c['production_status'].startswith('committed'))), 'pending_dated_display_observations': 3, 'blocker': 'Google Cloud: Reauthentication failed; cannot prompt during non-interactive execution. Awaiting gcloud auth login by the user. Production-only candidates still require fresh preflight.', 'receipt_limit': 'Committed counts are durable transaction receipts; France partial batches still need full post-write verification.'}, 'research_ledger_counts': dict(counts), 'wikiart': r.load(r.RUN / 'wikiart-summary.json'), 'research_limitations': ['Not every artwork was individually researched. The ledger separates unresearched rows, unsuccessful candidates, review leads and accepted holdings.', 'Source access challenges, HTTP errors, timeouts, missing metadata, ambiguous object identity, deposits and museum/physical-location conflicts remain explicitly unresolved.', 'Secondary-source candidates were kept in review; no artwork publication state, dates, creators, existing media or prior assertions were changed.', 'The run spans wall-clock interruptions; no claim of continuous active research duration is made.', '10-million-artwork performance remains untested; the attached query plan measures a scoped 500-object lookup on the real local catalogue.'], 'waves': wave_stats, 'all_local_wave_verifications_passed': True, 'all_original_active_ids_titles_slugs_and_statuses_preserved': True, 'unrelated_location_changes': unrelated_changes, 'backups': r.load(r.RUN / 'backups.json'), 'production_resume_commands_after_user_login': ['/tmp/artline-museum-research-20261004-venv/bin/python ops/apply-artwork-locations-20261004.py apply --wave france-03 --target production', '/tmp/artline-museum-research-20261004-venv/bin/python ops/apply-artwork-locations-20261004.py verify --wave france-03', '/tmp/artline-museum-research-20261004-venv/bin/python ops/apply-artwork-locations-20261004.py plan --wave final-production-01 --providers saam-followup-v2 agsa wikidata-review --targets production', '/tmp/artline-museum-research-20261004-venv/bin/python ops/apply-artwork-locations-20261004.py apply --wave final-production-01 --target production', '/tmp/artline-museum-research-20261004-venv/bin/python ops/apply-artwork-locations-20261004.py verify --wave final-production-01', '/tmp/artline-museum-research-20261004-venv/bin/python ops/apply-artwork-display-research-20261004.py apply --target production', '/tmp/artline-museum-research-20261004-venv/bin/python ops/apply-artwork-display-research-20261004.py verify']}
    r.save(dest / 'summary.json', summary)
    manifest = []
    archive = r.BACKUP / dest.name / 'scripts'
    archive.mkdir(parents=True)
    scripts = sorted(r.ROOT.joinpath('ops').glob('*artwork*20261004.py'))
    for path in scripts:
        shutil.copy2(path, archive / path.name)
        manifest.append({'path': str(path.relative_to(r.ROOT)), 'sha256': r.sha(path.read_bytes()), 'backup_path': str(archive / path.name)})
    r.save(dest / 'script-manifest.json', manifest)
    r.save(dest / 'report-files.json', [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': r.sha(p.read_bytes())} for p in sorted(dest.iterdir()) if p.is_file()])
    print(json.dumps({'report': str(dest), 'local_accepted': len(accepted_rows), 'local_review': len(review_rows), 'unresolved': len(unresolved), 'research_ledger_counts': counts, 'production': summary['production'], 'source_bodies_verified': len(source_receipts)}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
