"""Apply and verify the105 pinned selections, then publish a separate delivery record."""
import argparse
import contextlib
import csv
import importlib.util
import io
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-kazantzakis-more-resume-20261010.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
a,m,RUN=r.a,r.m,r.RUN
EXPECTED='6e43e487b4c4fa63455b230f53a64bb83d123c7c30ff8854c9ffac2a330386fd'

def table(name,rows):
    assert rows
    with(RUN/name).open('x',encoding='utf-8-sig',newline='')as out:
        writer=csv.DictWriter(out,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def apply():
    assert not(RUN/'apply-command-001.json').exists()
    completed=m.load(RUN/'cloud-backup-completed-001.json');a.checked(completed['backup_reference'])
    assert completed['plan_reference']==a.reference(a.PLAN)
    output=io.StringIO()
    with contextlib.redirect_stdout(output):a.apply(EXPECTED)
    receipt=m.load(a.RUN/(a.KEY+'-applied.json'))
    assert receipt['plan_sha256']==EXPECTED and receipt['created']==105 and receipt['local_unchanged']
    m.save(RUN/'apply-command-001.json',dict(at=m.now(),plan_sha256=EXPECTED,stdout=output.getvalue(),completed=True,
        applied_reference=a.reference(a.RUN/(a.KEY+'-applied.json')),script_reference=a.reference(Path(__file__).resolve())))
    print(output.getvalue(),end='',flush=True)

def verify():
    assert not(RUN/'checks-001.json').exists();applied=m.load(RUN/'apply-command-001.json');assert applied['completed'];a.checked(applied['applied_reference'])
    p,digest=a.validate_plan();assert digest==EXPECTED
    with a.i.prod.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');result=a.verify(db,p,digest)
    with m.connect()as db:
        initial=m.load(a.RUN/'initial-scope-001.json.gz');assert a.snapshot(db,initial['scoped_ids'])==initial['snapshot']and a.counts(db)==initial['counts']
    replay=io.StringIO()
    with contextlib.redirect_stdout(replay):a.apply(digest)
    assert replay.getvalue().strip()=='Unchanged replay: zero writes'
    tests=m.load(RUN/'offline-test-observation-001.json');assert tests['exit_code']==0 and tests['tests_passed']==20
    m.save(RUN/'readback-001.json',dict(at=m.now(),verification=result,plan_sha256=digest,local_unchanged=True,read_only=True))
    m.save(RUN/'replay-001.json',dict(at=m.now(),stdout=replay.getvalue(),zero_writes=True,plan_sha256=digest))
    m.save(RUN/'checks-001.json',dict(at=m.now(),offline_tests_passed=20,offline_test_reference=a.reference(RUN/'offline-test-observation-001.json'),
        atomic_verification_passed=True,readback_passed=True,replay_zero_writes=True,local_unchanged=True,protected_existing=128,protected_prior=921,
        actual_added=105,actual_existing_links=0,new_images=0,new_artist_links=0,new_published=0,new_display_claims=0,
        plan_reference=a.reference(a.PLAN),apply_reference=a.reference(RUN/'apply-command-001.json'),readback_reference=a.reference(RUN/'readback-001.json'),replay_reference=a.reference(RUN/'replay-001.json'),
        backup_reference=a.reference(a.RUN/'cloud-backup-001.json'),script_reference=a.reference(Path(__file__).resolve())))
    print(json.dumps(dict(verified_new=105,museum_counts=result['current_counts'],replay_zero_writes=True,local_unchanged=True)),flush=True)

def report():
    checks=m.load(RUN/'checks-001.json');assert checks['readback_passed']and checks['replay_zero_writes']and checks['actual_added']==105
    p,digest=a.validate_plan();assert digest==EXPECTED;readback=m.load(RUN/'readback-001.json');verified=readback['verification'];prior=m.load(a.CHECKPOINT)
    assert verified['current_counts']=={a.IID:dict(linked=223,eligible=217)}
    at=m.now();rr=prior['production_institution_register_reference'];register=m.load(a.checked(rr))['rows'];target=next(v for v in register if v['id']==a.IID)
    assert target['verified_production_works']==118 and target['verified_production_eligible_works']==112
    target.update(production_catalogue_count_to_200=223,production_date_eligible_count_to_200=217,production_catalogue_count_state='exact',production_date_eligible_count_state='exact',
        verified_production_works=223,verified_production_eligible_works=217,production_catalogue_count_at=readback['at'],production_date_eligible_count_at=readback['at'])
    m.save(RUN/'production-institution-register-001.json.gz',dict(at=at,rows=register,previous_register_reference=rr,read_only=True,updated_institutions=[a.IID],
        global_exact_counts_refreshed=False,global_thresholds_refreshed=False,policy='Only Kazantzakis refreshed to223 catalogue/217 numeric date-eligible works. Preferred200 target reached; other observations retain timestamps.'))
    table('production-institution-register-001.csv',register)
    qr=prior['priority_museum_queue_reference'];queue=m.load(a.checked(qr));assert not any(v['id']==a.IID for v in queue['rows'])
    queue.setdefault('preferred_target_reached',[]).append(dict(id=a.IID,at=readback['at'],catalogue=223,date_eligible=217))
    queue.update(at=at,previous_queue_reference=qr,policy='Kazantzakis now exceeds200 and remains outside the under100 priority subset. Queue rows are inherited observations, not a fresh global all-museum count.')
    m.save(RUN/'priority-museum-queue-001.json',queue)
    added=[]
    for v in p['records']:
        f=v['facts'];added.append(dict(artwork_id=v['artwork_id'],institution_id=a.IID,source_id=f['source_id'],title=f['title'],creator_label=f['creator_label'],
            date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],inventory=f['inventory'],source_url=f['source_url'],status='review'))
    table('added-production-artworks-001.csv',added)
    protected=sorted(set(p['prior_ids'])|{v['artwork_id']for v in p['records']});assert len(protected)==1026
    m.save(RUN/'protected-production-ids-001.json',dict(at=at,ids=protected,previous_protected_records=921,new_records=105,
        composition=dict(campaign_new_artworks=1025,campaign_existing_link=1),plan_reference=a.reference(a.PLAN)))
    backup=m.load(a.RUN/'cloud-backup-001.json');remaining=dict(kilkis=26,theocharakis=197,zongolopoulos=199,chania=174,larissa=187);assert sum(remaining.values())==783
    m.save(RUN/'delivery-001.json',dict(at=at,goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=105,existing_links=0,date_eligible_added=105,
        verification=verified,museum_before=dict(works=118,eligible_works=112),museum_after=dict(works=223,eligible_works=217),preferred_200_target_reached=True,
        production_campaign_totals=dict(new_artworks=1025,existing_links=1,museums=7),historical_local_totals_unchanged=prior['historical_local_campaign_totals'],cross_database_totals_combined=False,
        source_records_reviewed=110,reproduction_holds=4,source_identity_holds=1,reference_images_seen=110,new_images=0,remaining_pending_candidates=remaining,remaining_pending_total=783,
        global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,backup_id=backup['id'],
        next_work='Deliver remaining reviewed selections with fresh scoped/global identity checks. Larissa187 and prepared205 images can reach205 catalogue; Theocharakis197 and Zongolopoulos199 also approach/exceed200 after reconciliation. Chania174 and Kilkis26 remain selected candidates. Continue Averoff/Athens City public research afterward; Averoff SearchCulture currently exposes71 records, not enough alone to promise100 eligible works.',
        source_access='All inherited provider access holds persist. Google CLI access and task proxy recovered without alternate identity; an unrelated backup was observed to completion before the selected backup.'))
    (RUN/'README.md').write_text(f'''# Nikos Kazantzakis Museum — continuation delivered, 10 October 2026

Added **105 production review artworks**, taking the museum from **118 to 223 catalogue works** and **112 to 217 numerically date-eligible works**. Kazantzakis now exceeds the preferred 200-work target. The real local catalogue remains unchanged.

- [105 added artworks](added-production-artworks-001.csv)
- [Readback and preservation checks](checks-001.json)
- [Delivery record](delivery-001.json)
- [Original source review](../kazantzakis-more-20261009/README.md)

These are 104 drawings and one mixed-technique scenery detail with an unresolved physical type, dated by the source to 1940–1941. The source's unknown creator label remains distinct from EKT's Anemoyannis enrichment. Corrected titles retain the original corrupted strings and same-page evidence. Qualified production context, unknown dimensions and accessions remain explicit. Holdings establish neither current display nor legal ownership.

The original 110-source review retains four reproduction holds (35035, 35036, 35037, 35032) and one image/description identity hold (35062). Original/copy versions, distinct preparatory supports, multiple panels and reverse sketches were reconciled before selection. No held source was added to meet the target. No new image, artist-authority link, publication or display claim was added by this metadata delivery.

Google token refresh recovered. The expected local proxy on port 55519 was absent, so a new loopback listener was started using the same gcloud identity; the two unrelated existing proxies were not touched. A concurrent Cloud SQL backup initially caused a 409 response. That specific operation was observed to completion before this batch's backup was requested. Successful backup **{backup['id']}** preceded atomic application.

Twenty offline tests passed. Fresh production checks preserved **128 existing comparison records** and **921 prior campaign records**. The exact plan SHA-256 is `{digest}`. Independent readback verified every new record, source identifier, citation and accepted holding. A repeat application completed with **zero writes**. Existing dates, creator links, images, statuses and museum records remained unchanged. Local queries stayed read-only; no local fixtures, test databases, commits or deployments were created.

The selected production phase now totals **1,025 new artworks and one existing-work museum link across seven museums**. Its 1,026 protected artwork IDs include the previously linked Rhodes work. Only Kazantzakis's register counts were refreshed; the inherited 232-row priority subset is not a fresh global census. Historical local-delivery totals remain separate.

**783 reviewed candidates across five museums remain pending live reconciliation and delivery:** Kilkis 26, Theocharakis 197, Zongolopoulos 199, Chania 174 and Larissa 187. Larissa also has 205 prepared image files. These are candidate counts, not confirmed additional production identities. Continue those deliveries, then Averoff and Athens City research. Averoff's 71 SearchCulture source records are a starting point, not sufficient evidence that it can meet 100 under the creation cutoff.

The earlier pending files and research checkpoints remain immutable historical evidence. This delivery record supersedes their undelivered state for these 105 Kazantzakis candidates only. The every-museum goal is still active and incomplete.
''',encoding='utf-8')
    print(json.dumps(dict(added=105,counts=verified['current_counts'],production_campaign_new=1025,protected_ids=1026,pending_candidates=783,queue=len(queue['rows']))),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['apply','verify','report']);args=parser.parse_args()
    {'apply':apply,'verify':verify,'report':report}[args.command]()
