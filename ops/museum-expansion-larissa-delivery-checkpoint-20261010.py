"""Wave122 immutable production checkpoint; preserve inherited research pins."""
import hashlib
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-larissa-delivery-20261010.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
a,c,m,RUN=d.a,d.c,d.m,d.RUN
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    dest=RUN/'delivery-checkpoint-001.json';assert not dest.exists()
    report=m.load(RUN/'delivery-001.json');checks=m.load(RUN/'checks-001.json');public=m.load(RUN/'public-delivery-001.json')
    assert report['added']==184 and report['existing_links']==3 and checks['readback_passed'] and checks['replay_zero_writes'] and public['public_image_hashes_matched']==205
    plan,digest=a.validate_plan();assert digest==d.EXPECTED and c.ref(c.CP)['sha256']==c.CP_SHA
    prior=m.load(c.CP);oldpins={v['path']:v for v in prior['artifacts']};oldext={v['path']:v for v in prior['external_artifacts']}
    pins=dict(oldpins);external=dict(oldext)
    def add(pin,target):
        assert pin['path'] not in target or target[pin['path']]==pin,pin['path']
        target[pin['path']]=pin
    paths={c.CP,c.RESEARCH_CP,a.PLAN,Path(__file__).resolve()}
    paths|={v for v in RUN.rglob('*') if v.is_file()};paths|={v for v in (m.ROOT/'ops').glob('*larissa*20261010.py')}
    for path in sorted(paths):add(c.ref(path),pins)
    for pin in plan['evidence']:add(pin,pins)
    for pin in plan['external_evidence']:add(pin,external)
    for path in sorted(m.BACKUP.glob('larissa-production-*.json*')):add(dict(path=str(path),sha256=sha(path)),external)
    add(dict(path=plan['backup_path'],sha256=plan['backup_sha256']),external)
    newpins=[v for v in pins.values() if oldpins.get(v['path'])!=v];newext=[v for v in external.values() if oldext.get(v['path'])!=v]
    for pin in newpins:c.checked(pin)
    for pin in newext:assert sha(pin['path'])==pin['sha256'],pin['path']
    protected=m.load(RUN/'protected-production-ids-001.json')['ids'];assert len(protected)==1213
    assert set(protected)==set(plan['prior_ids'])|{v['artwork_id'] for v in plan['records']+plan['holdings']}
    pending=report['remaining_pending_candidates'];assert sum(pending.values())==596
    next_work='''Wave122 made verified production progress: Larissa184new review artworks+3existing-work museum links+205authentic image attachments. Actual museum18/15 to205catalogue/193numeric-date eligible,194primary-image works. Catalogue preferred200 reached; numeric eligible remains193. Campaign1209new+4existing links across8museums,1213protectedIDs. Real local catalogue unchanged. Goal ACTIVE and incomplete.

Use this checkpoint and its dated register/231-row priority subset as the current production baseline. Only Larissa refreshed; no fresh global census. Immutable plan larissa-delivery-20261010/larissa-production-001-plan-001.json.gz SHA145286e3507a7cb58c4eddfda1e560057e8cfcb96a59041c7898916b093dffd4. Import ops/museum-expansion-larissa-reconciled-20261010.py and use its .a for validation/verification. Original apply remains immutable. The first preflight stopped before writes because8unrelated comparison records gained primary images. No identity metadata,5250creator links or12026citations changed. production-identity-refresh-001 and adapter retain strict exact live guards, without changing the184+3selection.71focused/current records and1026previous campaign IDs preserved. Backup1791639050008SUCCESSFUL.17offline tests, atomic verification, independent readback, zero-write replay and205public image SHA checks passed;4public API artwork samples returned review holdings without display claims.

Three existing links: MaleasLavrio3f1bb857-c5c5-5568-860a-9c059a9d71c1, TriantafyllidisGirlWithTurkeys314c82c5-1883-5907-bd7c-94fe90f40b51, MoralisNudeStanding4802adb0-4c1e-5872-984b-e3d0fe094bda. FormerLavrio primary and12old museum primaries unchanged. Other2existing unknown dates retained; source dates evidence only. New184types120painting8drawing39print17watercolor.177numeric7null; no authority links added, literal/qualified creators preserved. Album176Kanas1946one unit with12plates. Distinct Giallinas watercolours, Galanis impressions and Vassiliou handwritten versions checked in full official frames.181primary+24alternate attachments;5new unillustrated32/46/67/92/168. Actual restricted CC BY-NC4 labels separate from Greek pre1955 approval.205explicit SC HTTPSpreview URLs yielded identical bytes to nativeHTTP originals; no scheme invention/schema changes. One nativeHTTPSimage7 ConnectTimeout was not retried. Prior native46/67/92missing and date/imageholds persist.

Next deliver remaining596reviewed candidates using NEW delivery scripts/run and fresh production identity reconciliation: Chania174, Zongolopoulos199, Theocharakis197, Kilkis26. Research CPs W114–120 inherited. Chania is next strongest prepared-image batch: runchania-20261010 CP SHAe4b9d345081aed5a1d1167b347d3472087291e2558e1c2fc1fa7f15a8629076a.174candidate units;188prepared images; canonical editorial/physicalunit002. CauldronM825A–ΣΤ six views oneobject, M763A/B onepair. Image identityholds38/110/161 and date-imageholds67/78/99/187 persist. Candidate count is not guaranteed new IDs. Larissa revealed3existing identities despite initialsource-ID misses; repeat global translated-title/creator/version/image checks before additions.

Zongolopoulos199=49dated+150further; two-sided supports countonce, explicit physical unknowns;19imagesprepared. Theocharakis197=138+59,125numeric72unknown. Kilkis26selected6holds; review earlier overly broad NC/ND imagehold under actual Greek source policy. After pending deliveries, Averoff nativecatalogue advertises>700works; SearchCulture71. Prior discovery stored under kazantzakis-more-delivery-20261010/next-source-discovery-001.json.gz, normal links /zografiki /glyptiki /haraktiki /shedio /fotografia /nea-mesa-ekfrasis at https://www.averoffmuseum.gr/. IIDea977842-2f6e-5020-a853-d300b507aca0 last18/9.700nativecollectionclaim is not eligible count; shop reproductions not originalobjects. AthensCityIIDf575847e-47eb-59e4-b558-32d8723bc3c9, SearchCultureDigAthensMuseum,last18/16 follows.

Taskproxy port55519 PID7614 --gcloud-auth (startedW121session93421) remains live; inspect authoritative state before recovery, leave unrelated55445/55478 and other cloud operations untouched. Existing gcloudidentity works. Never print credentials. Retain inherited provider403/429/timeout holds; no bypass. Inherit fullhistorical archive verification, verifyonlynew pins/relevant snapshots; do not rehash43kfiles eachwave. Executed writers and pinned artifacts immutable; create versions for corrections. Production selected additions/images authorized, no repeatpermissions, subagents, localwrites, fixtures, commits or deployment.'''
    result=dict(prior)
    result.update(at=m.now(),wave=122,goal_complete=False,goal_status='active',previous_goal_turn='progress',production_only=True,local_unchanged=True,new_additions=184,new_existing_links=3,new_images=205,verification=report['verification'],production_museum_before=report['museum_before'],production_museum_after=report['museum_after'],production_campaign_totals=report['production_campaign_totals'],global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,new_tests_passed=17,plan_sha256=digest,plan_reference=c.ref(a.PLAN),prior_checkpoint_reference=c.ref(c.CP),previous_research_checkpoint=c.ref(c.RESEARCH_CP),artifacts=list(pins.values()),external_artifacts=list(external.values()),baseline_reference=c.ref(RUN/'baseline-verification-001.json'),review_reference=c.ref(a.REVIEW),checks_reference=c.ref(RUN/'checks-001.json'),public_delivery_reference=c.ref(RUN/'public-delivery-001.json'),production_institution_register_reference=c.ref(RUN/'production-institution-register-001.json.gz'),priority_museum_queue_reference=c.ref(RUN/'priority-museum-queue-001.json'),protected_production_ids_reference=c.ref(RUN/'protected-production-ids-001.json'),pending_candidates=pending,pending_candidate_total=596,global_threshold_summary_note='Only Larissa refreshed to205/193. Other observations retain historical timestamps;231priority rows are a subset.',source_availability=report['source_access'],next_work=next_work)
    # This batch has no superseded plan; retain the earlier policy change solely in history.
    result.pop('superseded_plan_reference',None)
    m.save(dest,result)
    m.save(RUN/'final-checkpoint-verification-001.json',dict(at=m.now(),checkpoint=c.ref(dest),verified_new_artifact_pins=len(newpins),verified_new_external_pins=len(newext),inherited_unchanged_artifact_pins=len(pins)-len(newpins),inherited_unchanged_external_pins=len(external)-len(newext),full_historical_proof=prior['initial_full_historical_verification_reference'],plan_sha256=digest,goal_complete=False,actual_added=184,actual_existing_links=3,actual_images=205,protected_production_ids=1213,pending_candidates=596,local_unchanged=True))
    print(json.dumps(dict(checkpoint=c.ref(dest),artifacts=len(pins),external=len(external),verified_new=len(newpins),verified_external=len(newext),added=184,linked=3,images=205,pending=596)),flush=True)

if __name__=='__main__':main()
