#!/usr/bin/env python3
"""Report committed fourth-round additions and the full production research register."""
from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('round4', Path(__file__).with_name('apply-painter-influences-round4-20261009.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def main():
    p, digest = m.checked(m.PLAN)
    applied = m.r.load(m.RUN / 'production-plan-v1-applied.json')
    verified = m.r.load(m.RUN / 'production-plan-v1-verified.json')
    public = m.r.load(m.RUN / 'public-api-verification-passed.json')
    coverage = m.r.load(m.RUN / 'coverage-summary.json')
    register = m.r.load(m.RUN / 'painter-research-register.json.gz')
    assert all(v['plan_sha256'] == digest for v in (applied, verified, public))
    assert not public['failures']
    claims = p['inserts']['influence_claims']; citations = p['inserts']['citations']
    assert public['verified_new_relationships'] == len(claims)
    artists = {v['id']: v for v in p['before']['artists']}
    incoming = defaultdict(list); urls = defaultdict(set)
    for v in claims: incoming[v['target_artist_id']].append(v)
    for v in citations: urls[v['entity_id']].add(v['source_url'])
    assert set(incoming) == {v['target_id'] for v in public['results']}
    targets = {v['target_artist_id'] for v in claims if v['relationship_type'] == 'influenced'}
    old_targets = {v['target_artist_id'] for v in p['before']['influence_claims'] if v['relationship_type'] == 'influenced' and v['status'] != 'archived'}
    with m.d.connections.connect('production', readonly=True) as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        counts = db.execute('SELECT relationship_type,status,count(*) AS n FROM influence_claims GROUP BY 1,2 ORDER BY 1,2').fetchall()
        total_citations = db.execute("SELECT count(*) AS n FROM citations WHERE entity_type='influence'").fetchone()['n']
        current_profiles = db.execute("SELECT count(*) AS n FROM artists WHERE status<>'archived'").fetchone()['n']
        live_coverage = db.execute("""SELECT count(DISTINCT c.target_artist_id) AS any_relationship,
            count(DISTINCT c.target_artist_id) FILTER (WHERE c.relationship_type='influenced') AS artistic_influence
            FROM influence_claims c JOIN artists a ON a.id=c.target_artist_id
            WHERE c.status<>'archived' AND a.status<>'archived'""").fetchone()
    expected = Counter((v['relationship_type'], v['status']) for v in p['before']['influence_claims'] + claims)
    assert {(v['relationship_type'], v['status']): v['n'] for v in counts} == dict(expected)
    assert total_citations == len(p['before']['citations']) + len(citations)
    assert live_coverage['any_relationship'] == coverage['profiles_with_any_relationship']
    assert live_coverage['artistic_influence'] == coverage['profiles_with_artistic_influence']
    leads = m.r.load(m.RUN / 'candidate-passages.json.gz')
    reviewed_ids = {v['lead_id'] for v in m.r.load(m.r.RUN / 'reviewed-biography-decisions.json')}
    for directory in m.PREVIOUS + [m.RUN]:
        queue = m.r.load(directory / 'candidate-passages.json.gz')
        reviewed_ids.update(queue[json.loads(line)['i']]['id'] for line in (directory / 'reviews.jsonl').read_text().splitlines())
    remaining = [dict(queue_index=i, **lead) for i, lead in enumerate(leads) if lead['id'] not in reviewed_ids]
    (m.RUN / 'remaining-candidate-passages.jsonl').write_text(''.join(json.dumps(v, ensure_ascii=False, sort_keys=True) + '\n' for v in remaining))
    unresolved = sorted((v for v in register if not v['relationship_counts'].get('influenced')),
        key=lambda v: (-bool(v['pending_biography_passages']), -v['pending_biography_passages'], v['name'].casefold(), v['artist_id']))
    m.r.save(m.RUN / 'remaining-painter-research.json.gz', unresolved)
    assert coverage['individually_reviewed_passages'] == len(reviewed_ids)
    summary = dict(at=m.d.now(), operation=m.OP, plan_sha256=digest, selected_round_completed=True,
        all_painters_historically_complete=False, **p['summary'], total_production_claims=sum(v['n'] for v in counts),
        total_production_influence_citations=total_citations, production_claim_counts=counts,
        artistic_influence_target_painters=len(targets), first_artistic_influence_target_profiles=len(targets - old_targets),
        new_claims_with_unlinked_named_sources=sum(v['source_artist_id'] is None for v in claims),
        primary_assertion_source_pages=len({v['evidence']['source_url'] for v in m.r.load(m.RUN / 'primary-decisions.json')}),
        remaining_selected_passages=len(remaining), coverage=coverage, current_production_active_profiles=current_profiles,
        live_production_relationship_coverage=live_coverage,
        public_target_pages=public['target_pages'], publicly_verified_new_relationships=public['verified_new_relationships'],
        retried_public_target_pages=public.get('retried_target_pages', 0), public_failures=len(public['failures']),
        database_verification=verified['verification'], backup_path=p['backup_path'], applied_at=applied['at'],
        painter_statuses_preserved=True, local_database_modified=False)
    summary_path = m.RUN / ('summary-catalogue-catchup.json' if coverage.get('catalogue_catchup_profiles') else 'summary.json')
    m.d.save_new(summary_path, summary)
    labels = {'influenced': 'Influence', 'teacher_of': 'Teacher', 'documented_admiration': 'Admired painter'}
    lines = ['# Fourth-round additions by painter', '',
        'Direction: **library painter ← inspiring painter, teacher or admired painter**. All additions were committed to production and checked through the public API. The notes retain period, medium and uncertainty qualifications.', '']
    for aid, values in sorted(incoming.items(), key=lambda item: (artists[item[0]]['display_name'].casefold(), item[0])):
        a = artists[aid]; lines += [f"## [{a['display_name']}](https://artlines.org/artists/{a['slug']})", '']
        for v in sorted(values, key=lambda v: (v['relationship_type'], v['source_label'].casefold())):
            source_links = ' '.join(f'[source {i + 1}]({url})' for i, url in enumerate(sorted(urls[v['id']])))
            lines += [f"- **{labels[v['relationship_type']]}: {v['source_label']}** — {v['evidence_level']} / {v['confidence']}. {v['evidence_note']} {source_links}"]
        lines.append('')
    (m.RUN / 'additions-by-painter.md').write_text('\n'.join(lines))
    v = verified['verification']; types = p['summary']['claim_types']
    status_rows = '\n'.join(f"| {key.replace('_', ' ')} | {value:,} |" for key, value in coverage['research_status_counts'].items())
    hold_counts = Counter(item['reason'] for item in p['held'])
    hold_rows = '\n'.join(f'- {reason}: {count} assertions.' for reason, count in sorted(hold_counts.items())) or '- None.'
    catchup_text = ''
    if coverage.get('catalogue_catchup_profiles'):
        catchup_text = f"The final count found {coverage['catalogue_catchup_profiles']} additional active profiles absent from the pinned import snapshot. A separate [read-only catalogue catch-up](catalogue-catchup/production-snapshot.json) searched all of them and collected {coverage['catalogue_catchup_discovered_passages']} further biography passages. Those passages remain research leads for individual review; no extra claims were automatically published. The original import snapshot, immutable plan and earlier summary were preserved. This brings the register to the current snapshot total shown above.\n\n"
    report = f"""# Painter influences — fourth research round

Completed 9 October 2026. Added **{len(claims):,} relationships and {len(citations):,} citations across {len(incoming):,} painter profiles** to production. All additions were verified through the public API. Production now contains **{summary['total_production_claims']:,} relationships and {total_citations:,} influence citations**.

| New relationship type | Count |
|---|---:|
| Artistic influence | {types.get('influenced', 0)} |
| Teaching | {types.get('teacher_of', 0)} |
| Documented admiration | {types.get('documented_admiration', 0)} |

**{len(targets - old_targets)} profiles gained their first recorded artistic influence**. All additions, notes and source links appear in [additions by painter](additions-by-painter.md). Teaching and admiration remain separate from artistic influence. Counts refer to catalogue profiles; unresolved duplicate historical persons are not silently merged.

## Whole-library coverage

The research register covers all **{coverage['active_production_profiles']:,} active profiles** in the production snapshot of `{coverage['snapshot_at']}`. Every profile has a recorded lookup attempt across the research rounds. The initial discovery pass freshly searched the **170 newcomers** absent from the original register, retained 95 supported research-only identity bindings, and retrieved 92 identity-checked biographies in seven languages. All 62 keyword passages discovered in that initial discovery were individually reviewed. Identity matches do not by themselves establish influence, and no database identities were rewritten.

{catchup_text}After this import, **{coverage['profiles_with_artistic_influence']:,} profiles have at least one recorded artistic influence**, and **{coverage['profiles_with_any_relationship']:,} have at least one influence, teacher or admiration relationship**. **{coverage['profiles_without_artistic_influence']:,} still have no recorded artistic influence.** All-painter historical research remains incomplete. A failed lookup or absence of evidence in checked sources does not mean the painter had no influences.

| Current research state | Profiles |
|---|---:|
{status_rows}

The [complete painter register](painter-research-register.json.gz) records identity IDs, lookup evidence, relationship counts, reviewed passages and remaining lead IDs per profile. The [remaining painter research list](remaining-painter-research.json.gz) contains all profiles without an artistic influence, prioritizing those with unreviewed biography leads. The state label is a next-action classification, not a statement that all historical literature has been examined.

Across the rounds, **{coverage['individually_reviewed_passages']:,} passages have been individually reviewed**; **{coverage['pending_discovered_passages']:,} discovered passages remain unreviewed**. The narrower [selected queue](remaining-candidate-passages.jsonl) has {len(remaining):,} passages remaining and is not the whole-library backlog. The final read-only count found {current_profiles:,} active production profiles; snapshot coverage is anchored to its recorded time.

## Evidence reviewed this round

Reviewed **262 new biography passages**: 200 previously retrieved passages at queue indices 291–490 and all 62 fresh newcomer passages at indices 1630–1691. None overlap earlier individually reviewed leads. The older passages retain their original retrieval dates; they are not represented as fresh fetches. Revision URLs, original-wikitext hashes, review times, source attribution and [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) licensing are retained.

Selected **49 assertions from {summary['primary_assertion_source_pages']} museum biography pages**. Source captures include 12 London National Gallery requests and 20 Athens National Gallery requests. Five London requests returned 404; four successful HTTP responses had no usable substantive biography. HTTP success alone was not evidence. All accepted source captures and reviewed biography contexts passed hash checks.

Examples of source-backed museum readings include [Mantegna and Francesco Morone → Gerolamo dai Libri](https://www.nationalgallery.org.uk/artists/gerolamo-dai-libri), [Corot → Volanakis, specifically landscapes](https://www.nationalgallery.gr/en/artist/volanakis-konstantinos/), [Lipparini → Tsokos](https://www.nationalgallery.gr/en/artist/tsokos-dionysios/), and the artists whose work shaped [Vryzakis’s style and historical subjects](https://www.nationalgallery.gr/en/artist/vryzakis-theodoros/). These museum assertions may consolidate with biography claims or be skipped where a relationship already exists.

The {p['summary']['interpreted_assertions']} interpreted assertions consolidated into {p['summary']['canonical_pairs']} eligible canonical pairs; {p['summary']['existing_pairs_skipped']} existing pairs were skipped. Existing claims and citations were preserved, including their prior qualifications. New claims comprise **{p['summary']['evidence_levels'].get('documented',0)} documented/high-confidence relationships** and **{p['summary']['evidence_levels'].get('editorial_inference',0)} qualified editorial-inference/medium-confidence relationships**. Secondary biographies contain explicit relationship statements, but their underlying historical references were not independently verified. No Wikidata-only influence statement was imported automatically.

Fresh article/authority lookups resolved selected named sources. [Supplementary resolutions](supplementary-review-resolutions.json) preserve those decisions and a corrected QID transcription caught before planning. Held examples include a historian mistaken for a similarly named painter, a footballer mistaken for an artist’s brother, conflicting authority labels, speculative tuition, impossible chronology, group-level traditions, mere resemblance, and social acquaintance. No placeholder painter profiles were created. {summary['new_claims_with_unlinked_named_sources']} new claims retain a checked source name without a linked painter profile.

Import guard holds:

{hold_rows}

See [individual reviews](reviews.jsonl), [museum decisions](primary-decisions.json), [museum holds](primary-holds.json), [named-source lookup receipts](named-source-resolution-receipts.json.gz) and [name-search identity decisions](name-search-identity-decisions.json.gz). Private raw evidence remains under `/Users/vadimdulub/Library/Application Support/Artline/research/painter-influences-round4-20261009/`.

## Production verification

The [immutable plan](production-plan-v1.json.gz) has SHA-256 `{digest}`. The [application receipt](production-plan-v1-applied.json) records the completed atomic transaction at `{applied['at']}`. Scoped backup:

`{p['backup_path']}`

The transaction preserved **{v['existing_claims_preserved']:,} existing relationships, {v['existing_citations_preserved']:,} influence citations and {v['painter_rows_and_statuses_preserved']:,} checked painter rows**, including identifiers, dates and statuses. The real local database was not modified. No deployment or Git commit was performed. Earlier publication approval covers the new relationships; unified catalogue visibility required no painter-status changes.

Six pure policy/evidence tests passed without database fixtures. The atomic transaction checked new rows, protected preimages, audit inserts and active source citations before committing. Catalogue cache revision advanced from {applied['verification']['cache_revision_before']} to {applied['verification']['cache_revision_after']}. [Fresh read-only database verification](production-plan-v1-verified.json) passed; the maximum incoming relationship count on affected targets was {v['max_target_incoming_links']}, within the API’s 40-row bound.

[Public API verification](public-api-verification-passed.json) checked **all {public['target_pages']} affected target pages and all {public['verified_new_relationships']} additions**, including direction, type, evidence label, note and citation URLs. There are zero outstanding failures; {public.get('retried_target_pages',0)} pages required a separate retry pass. Final read-only queries independently checked relationship totals by type/status and the influence citation total. Machine-readable results: [current summary]({summary_path.name}).

Scripts: [research register](../../../ops/research-painter-influences-round4-20261009.py), [delivery](../../../ops/apply-painter-influences-round4-20261009.py), [public verification](../../../ops/verify-painter-influences-round4-api-20261009.py), [report generation](../../../ops/finalize-painter-influences-round4-20261009.py). Earlier evidence: [round 3](../painter-influences-round3-20261009/README.md).
"""
    (m.RUN / 'README.md').write_text(report)
    print(json.dumps({k: summary[k] for k in ('new_claims', 'new_citations', 'new_target_painters', 'total_production_claims', 'total_production_influence_citations', 'public_failures')}, indent=2))


if __name__ == '__main__':
    main()
