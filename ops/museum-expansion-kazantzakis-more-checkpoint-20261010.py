"""Wave121: preserve successful delivery and the intervening immutable research."""
import hashlib
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('b',Path(__file__).with_name('museum-expansion-kazantzakis-more-reconciled-20261010.py'))
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
a,m,RUN=b.a,b.m,b.RUN
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
RESEARCH={
    'kazantzakis-more-20261009':'69cf8a71a80abe2efd3e9d94cf6da1cd2d723225aa6ebbe19313a7a5c83178ff',
    'kilkis-review-20261010':'b224245951d11814db9dcc2104b868f2b2600c7f7998c066097b4c6000a07f9e',
    'theocharakis-20261010':'111102ce42532f27023cc3b2c22f580a547efc232896982933b4618b499dc8ba',
    'theocharakis-dated-20261010':'19104950752f9be76c22d8cbf159f569f38ad56ab5c78b24b807ba6e7a5423ec',
    'zongolopoulos-20261010':'32b31e616cf63bd20a1edc62468fe01fb6c23fea9a8474e4b8aa91419402582e',
    'zongolopoulos-paintings-20261010':'b62abdfbe4fa05e5309431b9e78baae7baea6859403f47f9a4d3d58ef060c49c',
    'chania-20261010':'e4b9d345081aed5a1d1167b347d3472087291e2558e1c2fc1fa7f15a8629076a',
    'larissa-20261010':'593f52af993318a98fc5de549d43f9160608de9621ca8e5222cdec2d1e6ea8d1',
}

def main():
    dest=RUN/'delivery-checkpoint-001.json';assert not dest.exists()
    report=m.load(RUN/'delivery-001.json');checks=m.load(RUN/'checks-001.json')
    assert report['added']==checks['actual_added']==105 and checks['readback_passed'] and checks['replay_zero_writes'] and checks['local_unchanged']
    plan,digest=a.validate_plan();assert digest=='0a6042ef210b44166f4a8044871acb7236937aa5dd835e130a2d35d35fbc244b'
    assert a.reference(a.CHECKPOINT)['sha256']=='21973a04eb7411fec1875f49baa8f0ac9f426e5de3effd5da24ca028b22b891a'
    prior=m.load(a.CHECKPOINT)
    oldpins={v['path']:v for v in prior['artifacts']};oldext={v['path']:v for v in prior['external_artifacts']}
    pins=dict(oldpins);external=dict(oldext);research=[]
    # Only the documented access-policy edit supersedes an existing path.
    current_policy=a.reference(m.ROOT/'AGENTS.md')
    assert current_policy['sha256']==b.NEW_POLICY
    assert pins['AGENTS.md']['sha256']==b.OLD_POLICY
    pins['AGENTS.md']=current_policy
    def add(pin,target):
        assert pin['path'] not in target or target[pin['path']]==pin,pin['path']
        target[pin['path']]=pin
    for name,expected in RESEARCH.items():
        path=m.RUN/'native'/name/'research-checkpoint-001.json';assert sha(path)==expected
        cp=m.load(path);research.append(a.reference(path));add(a.reference(path),pins)
        for pin in cp['artifacts']:add(pin,pins)
        for pin in cp['external_artifacts']:add(pin,external)
    paths={a.CHECKPOINT,a.PLAN,b.ORIGINAL,Path(__file__).resolve()}
    paths|={v for v in RUN.rglob('*') if v.is_file()}
    paths|={v for v in a.RUN.rglob('*') if v.is_file()}
    paths|={v for v in (m.ROOT/'ops').glob('*kazantzakis-more*20261010.py')}
    paths.add(m.ROOT/'ops/museum-expansion-averoff-discovery-20261010.py')
    for path in sorted(paths):add(a.reference(path),pins)
    for pin in plan['evidence']:add(pin,pins)
    for pin in plan['external_evidence']:add(pin,external)
    for path in sorted(m.BACKUP.glob('kazantzakis-more-*.json*')):
        add(dict(path=str(path),sha256=sha(path)),external)
    add(dict(path=plan['backup_path'],sha256=plan['backup_sha256']),external)
    newpins=[v for v in pins.values() if oldpins.get(v['path'])!=v]
    newext=[v for v in external.values() if oldext.get(v['path'])!=v]
    for pin in newpins:a.checked(pin)
    for pin in newext:assert sha(Path(pin['path']))==pin['sha256'],pin['path']
    ids=m.load(RUN/'protected-production-ids-001.json')['ids']
    assert len(ids)==1026 and set(ids)==set(plan['prior_ids'])|{v['artwork_id'] for v in plan['records']}
    pending=report['remaining_pending_candidates'];assert sum(pending.values())==783
    next_work='''Wave121 made verified production progress: 105 new Kazantzakis review artworks; museum118/112 to223 catalogue/217 numeric date eligible. Preferred200 target reached. Selected production campaign1025new+1existing-work link across7museums,1026 protected artwork IDs including the Rhodes existing-work link. Local historical totals remain separate and the real local catalogue remains unchanged. Every-museum goal ACTIVE and incomplete.

Use this delivery checkpoint and its register/queue as the next production baseline. The new immutable plan is kazantzakis-more-20261009/kazantzakis-more-production-001-plan-002.json.gz, SHA0a6042ef210b44166f4a8044871acb7236937aa5dd835e130a2d35d35fbc244b. Import the reconciled adapter to validate it: the original apply module defaults to superseded PLAN001 and must not be used unadapted for post-delivery validation. The member/bookmarks paragraph added to AGENTS was proven to be the only edit; original hash rejection occurred before any database connection/write. New plan repeats all source, identity, before-state and prior-state checks. Successful CloudSQL backup1791630924075 preceded the105 additions. Twenty offline tests, atomic verification, independent readback and zero-write replay passed.128 comparator records and921 previous campaign records preserved. No images, artist links, publication or display claims added.

Google CLI access recovered under the existing identity. Expected port55519 listener was absent and a task proxy was started using --gcloud-auth (initial execsession93421,PID7614). Check authoritative listener/process state before any recovery; leave unrelated55445/55478 proxies and other cloud operations untouched. No secret values printed. An unrelated backup caused409; it was observed to completion, then this batch's backup succeeded. All inherited source access holds persist, without retries/bypass.

Next deliver the783 reviewed candidates using NEW delivery run/scripts and fresh scoped production and global source/title identity reconciliation: Larissa187, Chania174, Zongolopoulos199, Theocharakis197, Kilkis26. These are candidates, not guaranteed new IDs. Their immutable research checkpoints W114–120 and all source/image pins are inherited here. Previous pending counts for Kazantzakis105 are superseded only by this actual delivery. Preserve archived exclusions, review state, literal/qualified creators and all unknown/conflicting dates; no filler works.

Larissa is the strongest next delivery: IID d843489b-7a33-5cbb-916a-4eecb0dac8b8, research run larissa-20261010, CP120SHA593f52af993318a98fc5de549d43f9160608de9621ca8e5222cdec2d1e6ea8d1. Last observed18catalogue/15eligible;187 physical candidates (180numeric7null) could reach205/195 if live identities remain distinct. Canonical editorial/physical-unit/CSV001.205 full-frame JPEGs prepared <=99820bytes:182new works+12existing+11extra album views; no uploads yet. One1946Kanas album is one physical unit despite12source plates;18Vassiliou bifolios each one. Native source date conflicts51/54/102 remain nullnumeric; all claims pre1955. Image40446/67/92 metadata retained, no URL guessing; public-image date holds32/168/211–216. Actual CC BY-NC4 labels retained separately from Greek pre1955 user authorization. Do not infer accessions from filenames or artist authority from names alone.604of820 source index records remain outside completed selection.

Chania174 includes cauldronM825A–ΣΤ six views counted once, M763A/B one pair, canonical editorial/physicalunit002.188preparedimages. Image identity holds38/110/161 and date-imageholds67/78/99/187 remain. Zongolopoulos199 includes49dated+150further; two-sided supports once, explicit unknownphysicaldates; only19imagesprepared. Theocharakis197 includes138+59;125numeric72unknown. Kilkis26 selected,6holds; reconsider the old overly broad NC/ND image hold under actual Greek policy when preparing images.

After pending deliveries continue Averoff. Fresh public capture next-source-discovery-001.json.gz in this run shows SearchCulture71 records but the museum native site advertises over700works. Observed normal catalogue links /zografiki /glyptiki /haraktiki /shedio /fotografia /nea-mesa-ekfrasis on https://www.averoffmuseum.gr/; no individual objects reviewed this wave. TargetIID ea977842-2f6e-5020-a853-d300b507aca0, last18/9. Native700 is a collection claim, not700 eligible selectable works or current display evidence. Shop reproductions are not original objects. AthensCity follows, IIDf575847e-47eb-59e4-b558-32d8723bc3c9, SearchCulture DigAthensMuseum, last18/16.

Only Kazantzakis counts refreshed;232-row priority list is a subset, not a new global census. Preserve all earlier research and executed writers; do not edit pinned files or rerun writers over existing artifacts. New versions for corrections. Inherit full historical archive verification; validate only new pins and relevant snapshots, not38k archived files again. Production selected additions authorized; no repeated permissions, subagents, local writes, fixtures, commits or deployments.'''
    result=dict(prior)
    result.update(at=m.now(),wave=121,goal_complete=False,goal_status='active',previous_goal_turn='progress',production_only=True,local_unchanged=True,
        new_additions=105,new_existing_links=0,verification=report['verification'],production_museum_before=report['museum_before'],production_museum_after=report['museum_after'],
        production_campaign_totals=report['production_campaign_totals'],global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,
        new_tests_passed=20,plan_sha256=digest,plan_reference=a.reference(a.PLAN),superseded_plan_reference=a.reference(b.ORIGINAL),
        prior_checkpoint_reference=a.reference(a.CHECKPOINT),previous_research_checkpoint=research[-1],intervening_research_checkpoints=research,
        artifacts=list(pins.values()),external_artifacts=list(external.values()),baseline_reference=a.reference(a.RUN/'baseline-verification-001.json'),
        intentional_supersessions=[dict(path='AGENTS.md',before_sha256=b.OLD_POLICY,after_sha256=b.NEW_POLICY,proof_reference=a.reference(RUN/'policy-reconciliation-001.json'))],
        review_reference=a.reference(a.REVIEW),remaining_research_reference=research[-1],checks_reference=a.reference(RUN/'checks-001.json'),
        production_institution_register_reference=a.reference(RUN/'production-institution-register-001.json.gz'),priority_museum_queue_reference=a.reference(RUN/'priority-museum-queue-001.json'),
        protected_production_ids_reference=a.reference(RUN/'protected-production-ids-001.json'),pending_candidates=pending,pending_candidate_total=783,
        global_threshold_summary_note='Only Kazantzakis refreshed to223/217. Other museum and threshold observations remain dated historical counts.',
        source_availability=report['source_access'],next_source_discovery_reference=a.reference(RUN/'next-source-discovery-001.json.gz'),next_work=next_work)
    m.save(dest,result)
    m.save(RUN/'final-checkpoint-verification-001.json',dict(at=m.now(),checkpoint=a.reference(dest),verified_new_or_superseded_artifact_pins=len(newpins),verified_new_external_pins=len(newext),
        inherited_unchanged_artifact_pins=len(pins)-len(newpins),inherited_unchanged_external_pins=len(external)-len(newext),full_historical_proof=prior['initial_full_historical_verification_reference'],
        plan_sha256=digest,goal_complete=False,actual_added=105,protected_production_ids=1026,pending_candidates=783,local_unchanged=True))
    print(json.dumps(dict(checkpoint=a.reference(dest),artifacts=len(pins),external=len(external),verified_new=len(newpins),verified_external=len(newext),added=105,pending=783)),flush=True)

if __name__=='__main__':main()
