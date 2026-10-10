#!/usr/bin/env python3
"""Build the third-round report from committed, verified evidence; database reads only."""
from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('round3', Path(__file__).with_name('apply-painter-influences-round3-20261009.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def main():
    p, digest = m.checked(m.PLAN)
    applied = m.r.load(m.RUN / 'production-plan-v1-applied.json')
    verified = m.r.load(m.RUN / 'production-plan-v1-verified.json')
    public = m.r.load(m.RUN / 'public-api-verification-passed.json')
    assert all(v['plan_sha256'] == digest for v in (applied, verified, public))
    assert not public['failures']
    claims = p['inserts']['influence_claims']
    citations = p['inserts']['citations']
    assert public['verified_new_relationships'] == len(claims)
    artists = {v['id']: v for v in p['before']['artists']}
    incoming = defaultdict(list)
    urls = defaultdict(set)
    for v in claims:
        incoming[v['target_artist_id']].append(v)
    for v in citations:
        urls[v['entity_id']].add(v['source_url'])
    assert set(incoming) == {v['target_id'] for v in public['results']}
    targets = {v['target_artist_id'] for v in claims if v['relationship_type'] == 'influenced'}
    old_targets = {v['target_artist_id'] for v in p['before']['influence_claims']
                   if v['relationship_type'] == 'influenced' and v['status'] != 'archived'}
    with m.d.connections.connect('production', readonly=True) as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        counts = db.execute('SELECT relationship_type,status,count(*) AS n FROM influence_claims GROUP BY 1,2 ORDER BY 1,2').fetchall()
        total_citations = db.execute("SELECT count(*) AS n FROM citations WHERE entity_type='influence'").fetchone()['n']
    expected = Counter((v['relationship_type'], v['status']) for v in p['before']['influence_claims'] + claims)
    assert {(v['relationship_type'], v['status']): v['n'] for v in counts} == dict(expected)
    assert total_citations == len(p['before']['citations']) + len(citations)
    leads = m.r.load(m.RUN / 'candidate-passages.json.gz')
    assert leads == m.r.load(m.PREVIOUS / 'candidate-passages.json.gz')
    current_indices = {json.loads(line)['i'] for line in (m.RUN / 'reviews.jsonl').read_text().splitlines()}
    previous_indices = {json.loads(line)['i'] for line in (m.PREVIOUS / 'reviews.jsonl').read_text().splitlines()}
    assert not current_indices & previous_indices
    assert current_indices == set(range(141, 291))
    remaining = [dict(queue_index=i, **lead) for i, lead in enumerate(leads) if i not in current_indices | previous_indices]
    assert len(remaining) == 1339
    first_ids = {v['lead_id'] for v in m.r.load(m.r.RUN / 'reviewed-biography-decisions.json')}
    assert not first_ids & {v['id'] for v in remaining}
    (m.RUN / 'remaining-candidate-passages.jsonl').write_text(''.join(json.dumps(v, ensure_ascii=False, sort_keys=True) + '\n' for v in remaining))
    summary = dict(at=m.d.now(), operation=m.OP, plan_sha256=digest, completed=True,
        **p['summary'], total_production_claims=sum(v['n'] for v in counts),
        total_production_influence_citations=total_citations, production_claim_counts=counts,
        artistic_influence_target_painters=len(targets), first_artistic_influence_target_profiles=len(targets - old_targets),
        new_claims_with_unlinked_named_sources=sum(v['source_artist_id'] is None for v in claims),
        primary_assertion_source_pages=len({v['evidence']['source_url'] for v in m.r.load(m.RUN / 'primary-decisions.json')}),
        remaining_selected_passages=len(remaining), original_discovered_passages_remaining=20568 - 407 - 141 - 150,
        public_target_pages=public['target_pages'], publicly_verified_new_relationships=public['verified_new_relationships'],
        retried_public_target_pages=public.get('retried_target_pages', 0),
        public_failures=len(public['failures']), database_verification=verified['verification'],
        backup_path=p['backup_path'], applied_at=applied['at'], painter_statuses_preserved=True, local_database_modified=False)
    m.d.save_new(m.RUN / 'summary.json', summary)
    labels = {'influenced': 'Influence', 'teacher_of': 'Teacher', 'documented_admiration': 'Admired painter'}
    lines = ['# Third-round additions by painter', '',
        'Direction: **library painter ← inspiring painter, teacher or admired painter**. Every listed relationship was added to production and checked through the public API. Teaching and admiration are separate types. The evidence notes retain period, medium and uncertainty qualifications.', '']
    for aid, values in sorted(incoming.items(), key=lambda item: (artists[item[0]]['display_name'].casefold(), item[0])):
        a = artists[aid]
        lines += [f"## [{a['display_name']}](https://artlines.org/artists/{a['slug']})", '']
        for v in sorted(values, key=lambda v: (v['relationship_type'], v['source_label'].casefold())):
            source_links = ' '.join(f'[source {i + 1}]({url})' for i, url in enumerate(sorted(urls[v['id']])))
            lines += [f"- **{labels[v['relationship_type']]}: {v['source_label']}** — {v['evidence_level']} / {v['confidence']}. {v['evidence_note']} {source_links}"]
        lines.append('')
    (m.RUN / 'additions-by-painter.md').write_text('\n'.join(lines))
    v = verified['verification']
    report = f"""# Painter influences — third research round

Completed 9 October 2026. This round added **324 relationships and 326 citations across 137 painter profiles** to production. All 324 were verified through the public API. The catalogue now contains **{summary['total_production_claims']:,} relationships and {total_citations:,} influence citations**.

| New relationship type | Count |
|---|---:|
| Artistic influence | 264 |
| Teaching | 56 |
| Documented admiration | 4 |

The artistic influences concern **{len(targets)} target painters**; **{len(targets - old_targets)} target profiles gained their first recorded artistic influence**. These are profile-level counts, not deduplicated historical-person counts. Teaching and admiration do not automatically establish artistic influence. See [additions by painter](additions-by-painter.md) for every addition, evidence note and source.

**18 relationships are documented by museum sources; 306 retain medium-confidence editorial-inference labels.** The latter are explicit assertions in individually read secondary-source passages whose underlying historical references were not independently checked. Publication preserves these qualifications. No new low-confidence Wikidata-only assertions were imported.

## Research and source decisions

This pass reviewed **150 additional biography passages** (queue indices 141–290), yielding 326 assertions, and **30 assertions from 12 museum source pages**. None of the 150 passages overlap with the first round's 407 or second round's 141 reviewed passages. The 356 interpreted assertions produced 348 eligible canonical pairs after consolidation and two held assertions. **24 existing pairs were skipped**, preserving their existing evidence and history.

Selected museum evidence comes from the National Gallery in London and the National Gallery in Athens. Newly added examples include Monet and Renoir → Manet, Bellini and Raphael → Lotto, Caravaggio and Ludovico Carracci → Guercino, and Lazzarini → Tiepolo as a teacher. Each claim preserves the source's period or medium limits.

The [Moralis interview catalogue](https://www.nationalgallery.gr/wp-content/uploads/2021/10/moralis_both.pdf) was read as text and visually checked on PDF pages 20–21 (printed pages 19–20). It supports De Chirico's influence on a specific Cavafy woodcut, a temporary phase shaped by Kontoglou's methods through Tsarouchis, and Moralis's expressed admiration for El Greco. These are qualified individually; admiration and named comparisons were not automatically converted into influence.

Kontoglou's existing profile was reconciled for research using its native National Gallery identifier and the [museum biography](https://www.nationalgallery.gr/en/artist/kontoglou-fotis/). The museum's 1896 birth year and the authority's 1895 remain documented variants. This research-only binding changed no database identity, date or biography. Its evidence is in [supplemental-identity-bindings.json](supplemental-identity-bindings.json).

Seven new claims retain authority-checked named sources without linked painter profiles; no placeholder painter records were created. Two proposed targets, Kumashiro Yūhi and Kishi Ganku, lacked an unambiguous library identity and were held. Other held readings include speculative training, group-level claims, impossible early chronology, mere resemblance, explicit dislikes and names that are fellow students rather than teachers. See [reviews.jsonl](reviews.jsonl), [supplementary resolutions](supplementary-review-resolutions.json) and [primary holds](primary-holds.json).

Fresh primary-source receipts record 19 requests, including the additional identity biography: 18 HTTP 200 responses and one 404. A retrieved page is not automatically accepted relationship evidence. The 30 selected assertions use 12 sources. Museum HTML/PDF captures remain private under `/Users/vadimdulub/Library/Application Support/Artline/research/painter-influences-round3-20261009/primary/`.

Wikipedia passages were retrieved on 8 October in the first pass and individually reviewed in this round; they are not represented as fresh fetches. Citations preserve revision URLs, original-wikitext paragraph hashes, retrieval/review timestamps and attribution to Wikipedia contributors under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Used primary captures and every reviewed biography context were checked against their recorded hashes.

This completes another selected research pass, not every painter's historical research. **1,339 passages remain in the selected queue**, and **19,870 of the original 20,568 discovered passages remain individually unreviewed**. The [remaining queue](remaining-candidate-passages.jsonl) excludes all first/second/third-pass reviewed leads represented in it. These are research leads, not accepted relationships.

## Production delivery and verification

The [immutable production plan](production-plan-v1.json.gz) has SHA-256 `{digest}`. The [application receipt](production-plan-v1-applied.json) records the completed atomic transaction at `{applied['at']}`. Its scoped backup is:

`{p['backup_path']}`

The transaction inserted 324 published relationships and 326 citations, reusing existing source registries. It preserved all **{v['existing_claims_preserved']:,} prior claims, {v['existing_citations_preserved']:,} prior influence citations and {v['painter_rows_and_statuses_preserved']:,} checked painter rows**, including statuses and identifiers. No artworks, images, biographies, dates or review flags changed. The real local database remained read-only. No deployment or Git commit was performed in this round.

The user's earlier publication approval applies to the new claims. The unified catalogue already exposes active records regardless of historical status, so no painter-status rewrite was needed.

Six pure policy checks passed without database fixtures. Before commit, the transaction checked exact new rows, protected preimages, audit inserts and active citations. Catalogue cache revision advanced from {applied['verification']['cache_revision_before']} to {applied['verification']['cache_revision_after']}. A [fresh read-only database verification](production-plan-v1-verified.json) then passed. The maximum incoming relationship count among affected painters was {v['max_target_incoming_links']}, within the API's 40-row bound.

The [public API verification](public-api-verification-passed.json) checked **all 137 target pages and all 324 new relationships**, including direction, type, evidence label, note and citation URLs, with zero outstanding failures. One endpoint initially returned HTTP 503; only that page was retried and it passed. The [initial receipt](public-api-verification-failed.json) is preserved, and the final receipt retains each page's actual verification time. A separate final read-only query verified total claims by type/status and the influence citation count. Machine-readable results are in [summary.json](summary.json).

Scripts: [delivery](../../../ops/apply-painter-influences-round3-20261009.py), [public verification](../../../ops/verify-painter-influences-round3-api-20261009.py), [report generation](../../../ops/finalize-painter-influences-round3-20261009.py). Earlier evidence remains in the [first round](../painter-influences-20261008/README.md) and [second round](../painter-influences-round2-20261008/README.md).
"""
    (m.RUN / 'README.md').write_text(report)
    print(json.dumps({k: summary[k] for k in ('new_claims', 'new_citations', 'new_target_painters', 'total_production_claims', 'total_production_influence_citations', 'public_failures')}, indent=2))


if __name__ == '__main__':
    main()
