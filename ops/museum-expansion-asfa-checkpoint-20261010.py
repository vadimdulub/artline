"""Wave 130: verify and preserve the ASFA delivery; the nationwide goal stays active."""
import hashlib
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('delivery', Path(__file__).with_name('museum-expansion-asfa-delivery-20261010.py'))
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)
a, c, m, RUN = d.a, d.c, d.m, d.RUN


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    dest = RUN / 'delivery-checkpoint-001.json'
    assert not dest.exists()
    report = m.load(RUN / 'delivery-001.json')
    checks = m.load(RUN / 'checks-001.json')
    public = m.load(RUN / 'public-delivery-001.json')
    assert report['added'] == 248 and report['existing_links'] == 2 and report['new_images'] == 142
    assert checks['readback_passed'] and checks['replay_zero_writes'] and checks['local_unchanged']
    assert public['public_artwork_samples'] == 6 and public['public_image_hashes_matched'] == 142
    plan, digest = a.validate_plan()
    assert digest == d.EXPECTED and c.ref(c.CP)['sha256'] == c.CP_SHA
    prior = m.load(c.CP)
    oldpins = {x['path']: x for x in prior['artifacts']}
    oldext = {x['path']: x for x in prior['external_artifacts']}
    pins, external = dict(oldpins), dict(oldext)

    def add(pin, target):
        assert pin['path'] not in target or target[pin['path']] == pin, pin['path']
        target[pin['path']] = pin

    paths = {c.CP, a.PLAN, Path(__file__).resolve()}
    paths |= {x for x in RUN.rglob('*') if x.is_file()}
    paths |= {x for x in (m.ROOT / 'ops').glob('*asfa*20261010.py')}
    for path in sorted(paths):
        add(c.ref(path), pins)
    for pin in plan['evidence']:
        add(pin, pins)
    for pin in plan['external_evidence']:
        add(pin, external)
    external_paths = {x for x in c.PROOF.rglob('*') if x.is_file()}
    external_paths |= set(m.BACKUP.glob('asfa-production-*.json*'))
    for path in sorted(external_paths):
        add(dict(path=str(path), sha256=sha(path)), external)
    newpins = [x for x in pins.values() if oldpins.get(x['path']) != x]
    newext = [x for x in external.values() if oldext.get(x['path']) != x]
    for pin in newpins:
        c.checked(pin)
    for pin in newext:
        assert sha(pin['path']) == pin['sha256'], pin['path']
    protected = m.load(RUN / 'protected-production-ids-001.json')['ids']
    assert len(protected) == 2277
    assert set(protected) == set(plan['prior_ids']) | {v['artwork_id'] for v in plan['records'] + plan['holdings']}
    queue = m.load(RUN / 'priority-museum-queue-001.json')
    assert len(queue['rows']) == 226 and not any(x['id'] == c.IID for x in queue['rows'])
    assert sum(x['country_code'] == 'GR' for x in queue['rows']) == 66
    assert report['remaining_pending_total'] == 0

    next_work = '''Wave 130 delivered 248 new review works, two existing-work holding links, 142 native images and ten creator links to Athens School of Fine Arts Gallery, IID fe94f502-f226-56ad-89b1-e6a8fa4dd44e. Museum 8 catalogue / 7 numeric / 7 primary images -> 258 catalogue / 251 numeric / 149 primary images. Both 100 and preferred 200 targets reached. Six new dates unresolved, one old unknown preserved. No ready ASFA candidates remain; wider every-museum goal ACTIVE and incomplete. Campaign totals 2253 new works + seven existing-work links across 14 museums. Preserve 2277 IDs = 2260 campaign records + 17 old Kilkis image-only records. Local real database remains unchanged.

Use ops/museum-expansion-asfa-apply-20261010.py directly for validate_plan and verify. Plan asfa-production-001-plan-001.json.gz SHA 7ca6399f36ad79fbc12507719210699ee6b4d1544bb7fbd33dda08e5f1e54986. Seventeen offline checks, live preflight, atomic verification, independent readback, zero-write replay, 142 public image hashes and six public review-artwork API samples passed. Backup 1791651248392 SUCCESSFUL, operation 4beaae78-e218-4f86-acd9-82b300000024, ended 2026-10-10T16:55:39.722Z. All 142 new storage objects uploaded generation-match=0 with receipt/MD5 checks before database application. Preserve 197 old comparator records except the explicitly reviewed two links, one new primary and one alternate; all 2027 prior protected records remain unchanged. No new publication or on-view claims.

Source https://www.searchculture.gr/aggregator/portal/collections/DigASFA?language=en has 4012 entries; separate >9000 physical collection description is not an eligible count. Bounded oldest nine YEAR_ASC pages reviewed 270 index cards, 1883 through 1958. Thirteen administrative documents or books excluded before detail capture. 257 artwork leads include seven old works; one further old comparator yields 258 individual SearchCulture/native pages. 3741 source entries remain outside this index/comparator review. Actual linked native pages https://exhibition.asktdigital.gr/exhibits/{id}/ and image URLs were observed, not guessed. All 258 thumbnails, eleven thumbnail contact sheets, 148 selected native originals, seven original contacts and six prepared contacts inspected. 142 images delivered full-frame JPEG <=99807 bytes, with 141 primaries and one alternate. Native originals 171/172 (1956) were comparison-only; no post-1955 or unresolved-date image was attached.

Native terms state CC BY-NC-ND 4.0 and personal/academic use; SearchCulture item labels separately claim CC BY-SA 4.0. Both preserved. All 142 new images classified restricted under native terms; existing user Greek museum image-workflow approval recorded separately, not as copyright-holder permission. Source native-terms-001 captured. Existing seven ASFA images/rights unchanged. No new provider denial or bypass. One WikiArt webtool internal fetch error resolved using ordinary public HTTP 200, not a denied endpoint.

Identity comparison: 197 artworks, 173 creator links, 278 citations and five artist/alias IDs, with full snapshots and EXPLAIN/timing evidence. Scope: verified creators, informative exact titles, full inventory/source IDs and image hashes. Generic nudes/landscapes/Untitled titles checked inside maker/source/inventory bounds; no claim of exhaustive global duplicate or ten-million-row performance proof. Nine WikiArt images visually compared. Existing source 17, inventory 00680_ZOG885, Mathiopoulos Portait of John Polemis, artwork 6f4e418a-e650-53ba-b654-c0f332ca67e6, date 1924, now linked to ASFA with native framed alternate; old primary a1637d7f-dba3-5c11-8d98-f597fdfd2fcd preserved. Existing source 24, 00678_SXE2, Nikolaou Drawing of a man, artwork a91e096f-7c1b-5313-b336-e3f4dd549d6b, now linked with new native primary. Existing WikiArt-backed 1929 date unchanged despite native 1930 claim, which is recorded in citations. Neither work duplicated or assigned new external identifier.

Print comparisons retained distinct impressions 134/137, 138/139 and 171/172 based on full inventory labels, pencil signatures, margins, abrasions/inking and paper condition, not image hash alone. Portraits 97/98 share a numeric inventory stem but full 00752 and 00752_ZOG727 labels differ, and depict different people/compositions. Classroom same-model studies remain separate makers/views. Greek literal titles/creator labels used for new records; mistranslations such as Argyros -> Silver and kasela -> Cashier retained only as source translation evidence. Orphan/Ορφανό does not become a person. No invented oil/support/dimensions units or artist biographies. One sheet containing two heads remains one object. Religious/decorative studies retain their own 1957/1958 dates rather than ancient prototype/building dates.

Six new numeric dates null: numbers 131,132,133,140,141 are Kefallinos Ten White Lekythoi impressions with source 1953,1954 or 1954-1957 dates. Ministry National Archaeological Museum exhibition confirms portfolio publication 1956; proof versus later impression remains unresolved, so do not invent 1956 or attach images. Source https://www.culture.gov.gr/el/information/SitePages/view.aspx?nID=2455 captured publication-context-001.json. Number 199, Theofilos-attributed Athanasios Diakos, source 1958 after maker death 1934: qualified attribution/creator role, numeric date null, no artist link/image. Number 198 explicitly titled copy preserves 1958 with After Theofilos; copyist unidentified. Do not upgrade either to an original. Yiannis Faitakis number 168 is 1926-2012 authority, not Stelios Faitakis.

Ten new creator links: Mathiopoulos source 7, artist 951faed2-0922-532a-85cc-305f9403a4e0, exact SearchCulture creator authority /persons/-279158142. Moralis sources 33,41,45,46,49,50,55,58,64, artist 3b5fbd54-cae2-5e50-a0b3-f70eabf743cd, authority /persons/-659804591. Existing Nikolaou f6fbb79f-68f7-5abc-8541-f33ae7d091a0 source24 retained, corroborated /persons/-857081719. No painter/alias mutations. Unscoped metadata creator_authorities also contains sitters; only field-qualified creator URLs were used. Luis de Morales/Oleksa Novakivskyi false substring matches not linked.

Research corrections are immutable in research-corrections-001.json: metadata v1 guessed encoding caused one Greek page to decode as Thai; metadata-v2 decoded the same captured bytes strict UTF-8, no overwrite/refetch. Identity v1 first-token/given-name matching hit 863 artists and stopped at its 500 cap before enrichment; identity-v2 used full names and selected surnames, five IDs/197 works, no cap relaxation. No writes resulted from failed research steps. Executed/pinned scripts/artifacts never edited; corrections require new versions.

NEXT National Historical Museum IID 5d1bc5d4-0e01-5e7b-8669-1411c393a158, historical 13 catalogue works; fresh production/local read-only baseline required before research or plan. Collection https://www.searchculture.gr/aggregator/portal/collections/EIM?language=en, 4727 mixed source entries. Discovery already captured as EIM row in previous athens-city-photographs-20261010/next-source-discovery-001.json.gz, HTTP 200, no individual detail/image or ready candidates yet. Native observed https://www.nhmuseum.gr/tmimata/mesa-stis-sylloges-tou-mouseiou and http://www.nhmuseum.gr. First page 1865/1880/1880-1900 photos and pottery 1771-1830, actual CC BY 4.0 links, TIFF native links. Observed GET /aggregator/portal/collections/EIM/search, sort SCORE/YEAR_ASC/YEAR_DESC/TITLE; inspect actual facets before using them. Select paintings, prints, sculpture, decorative art and historic photographic works; do not pad with administrative documents or turn depicted buildings into museum objects. Metadata and duplicate/version checks before selected image download. Creation <=1970, Greek workflow images <=1955; unknown dates explicitly reviewed. Hold all inherited denied/timeout providers without bypass.

Only ASFA register row refreshed. 226 inherited under-100 priority rows remain, 66 Greek; this is a subset, not a fresh global census. ASFA seven unresolved dates retained in research queue. Athens City 208/111 target met, 97 unknown; its photographic medium digital photograph only, archive donation not individual authorship/original-negative proof; 65 of1634 photo items reviewed,1569 remain. Chania192/117 still eight short200 with108unreviewed/14scope holds/native403. Theo215/137 and Zong216/67 met targets; Zong149unknown/63versionholds. Kilkis56/0/53primary,44short100, all65publicobjects reviewed with12holds and oldAEMK2imageconflict. Averoff18/9, nativezografiki403; independentSC71available. All prior provider holds remain in checkpoint chain, no retries via alternative mechanism.

Production proxy 127.0.0.1:55519 PID7614 --gcloud-auth revalidated live; leave it and unrelated55445/55478 alone. Local postgresql://localhost/artline READ ONLY; no fixtures or test databases. Research venv/proofs/backups in Library/Application Support/Artline. No agents, commits or deployments. AGENTS SHA ad0d8067ebf9a99e3198d1d6d0c9853e6acdd8932c5a5a0a9e5bb006416d0241 unchanged. Selected production additions/images authorized; no repeated approval. Inherit full historical archive proof a0480d7954d528917245e1a8158bcc542078d9346d5aae701a4ace2666ba3205; verify new pins and relevant snapshots, not every historical file. Broader goal remains active.'''

    result = dict(prior)
    result.update(
        at=m.now(), wave=130, goal_complete=False, goal_status='active', previous_goal_turn='progress',
        production_only=True, local_unchanged=True, new_additions=248, new_existing_links=2, new_images=142,
        verification=report['verification'], production_museum_before=report['museum_before'],
        production_museum_after=report['museum_after'], production_campaign_totals=report['production_campaign_totals'],
        global_production_counts_refreshed=False, global_production_thresholds_refreshed=False,
        new_tests_passed=17, plan_sha256=digest, plan_reference=c.ref(a.PLAN),
        prior_checkpoint_reference=c.ref(c.CP), artifacts=list(pins.values()), external_artifacts=list(external.values()),
        baseline_reference=c.ref(RUN / 'baseline-verification-001.json'), review_reference=c.ref(a.REVIEW),
        checks_reference=c.ref(RUN / 'checks-001.json'), public_delivery_reference=c.ref(RUN / 'public-delivery-001.json'),
        production_institution_register_reference=c.ref(RUN / 'production-institution-register-001.json.gz'),
        priority_museum_queue_reference=c.ref(RUN / 'priority-museum-queue-001.json'),
        protected_production_ids_reference=c.ref(RUN / 'protected-production-ids-001.json'),
        pending_candidates={}, pending_candidate_total=0,
        global_threshold_summary_note='Only ASFA refreshed: 258 catalogue / 251 numeric-date eligible. Preferred 200 reached; other observations retain timestamps. The 226 priority rows are an inherited subset.',
        source_availability=report['source_access'], remaining_research_reference=c.ref(RUN / 'remaining-research-001.json'),
        next_source_discovery_reference=c.ref(c.PREVIOUS / 'next-source-discovery-001.json.gz'),
        preferred_target_remaining=dict(institution_id=c.IID, catalogue=258, gap_to100=0, gap_to200=0, target_reached=True, numeric_eligible=251),
        public_api_date_scope=public['date_scope_note'], next_work=next_work,
    )
    result.pop('previous_research_checkpoint', None)
    m.save(dest, result)
    m.save(RUN / 'final-checkpoint-verification-001.json', dict(
        at=m.now(), checkpoint=c.ref(dest), verified_new_artifact_pins=len(newpins),
        verified_new_external_pins=len(newext), inherited_unchanged_artifact_pins=len(pins)-len(newpins),
        inherited_unchanged_external_pins=len(external)-len(newext),
        full_historical_proof=prior['initial_full_historical_verification_reference'], plan_sha256=digest,
        goal_complete=False, actual_added=248, actual_existing_links=2, actual_images=142,
        protected_production_ids=2277, pending_candidates=0, local_unchanged=True,
    ))
    print(json.dumps(dict(checkpoint=c.ref(dest), artifacts=len(pins), external=len(external),
        verified_new=len(newpins), verified_external=len(newext), added=248, links=2, images=142, pending=0)), flush=True)


if __name__ == '__main__':
    main()
