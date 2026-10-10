"""Document 291 verified additions while retaining the remaining research queue."""
import collections,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-fifteenth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    report=m.load(m.RUN/'verification-after-wave-70.json');assert report['verified_new_artworks']==9337 and report['institutions_with_new_records_or_reconciled_holdings']==200
    growth=m.load(a.RUN/'coverage-registry-growth-001.json');a.checked(report['external_registry_growth_reference']);assert len(report['newly_observed_institutions'])==108 and report['newly_observed_institutions']==growth['added_institutions'];assert len(report['unrelated_coverage_changes_since_prior_report'])==1
    p,digest=a.validate_plan()
    with m.connect() as db:verified=a.verify(db,p,digest)
    logsroot=Path('/Users/vadimdulub/Library/Logs');prefix='artline-france-fifteenth-'
    tests=(logsroot/(prefix+'release-tests-20261008.log')).read_text();assert 'Ran 9 tests' in tests and tests.rstrip().endswith('OK')
    assert (logsroot/(prefix+'replay-20261008.log')).read_text().strip()=='Unchanged replay: zero writes'
    cp=m.load(a.RUN/'review-progress-checkpoint-004.json');assert cp['tests_passed']==34
    logs={v.name:dict(path=str(v),sha256=sha(v)) for v in sorted(logsroot.glob(prefix+'*-20261008.log')) if v.name not in [prefix+'delivery-20261008.log',prefix+'checkpoint-20261008.log']}
    ds=m.load(a.REVIEW)['decisions'];assert collections.Counter(d['state'] for d in ds)=={'approved_review_only_addition':291,'editorial_hold':58,'deferred_identity_review':301}
    assert not (a.RUN/'checks-001.json').exists()
    m.save(a.RUN/'checks-001.json',dict(at=m.now(),new_offline_tests_passed=43,new_release_tests_passed=9,prior_wave70_tests_passed=34,historical_tests_passed=1356,cumulative_verified_tests=1399,historical_tests_rerun=False,replay_zero_writes=True,all_workers_completed=True,selected_current_sources=650,added=291,captured_review_holds=58,deferred_identity_candidates=301,logs=logs,other_job_totals_separate=True,policy='10 date +19 selection +5 identity +9 release checks, counted once. Initial selection log includes date checks and is not counted twice. Research and source snapshots preserved. Remaining candidates are not approved by quota.'))
    rows=report['france_fifteenth_museum_changes'];table='| Museum | Added | Linked before → after | Eligible before → after |\n| --- | ---: | ---: | ---: |\n'+'\n'.join('| '+v['name']+' | '+str(v['new'])+' | '+str(v['linked_before'])+' → '+str(v['linked_after'])+' | '+str(v['eligible_before'])+' → '+str(v['eligible_after'])+' |' for v in rows)
    types=collections.Counter(v['facts']['work_type'] for v in p['records']);kindtext=', '.join(str(v)+' '+k for k,v in sorted(types.items()))
    changes=[]
    def replace_with_backup(path,text,key,expected=None):
        before=sha(path)
        if expected:assert before==expected
        backup=m.BACKUP/(key+'.json.gz');assert not backup.exists();m.save(backup,dict(at=m.now(),path=str(path.relative_to(m.ROOT)),sha256=before,text=path.read_text()))
        path.write_text(text);changes.append(dict(path=str(path.relative_to(m.ROOT)),before_sha256=before,after_sha256=sha(path),backup_path=str(backup),backup_sha256=sha(backup)))
    detail='''# Fifteenth French museum pass — first release

Added **291 real local artwork records**, all in review. Estève, Avelines and Dobrée now each exceed 100 eligible works. The broader all-museum 100–200 goal remains active.

'''+table+'''

Types: '''+kindtext+'''. This release uses the fully resolved portion of a 650-notice research selection. **58 notices remain editorial holds and 301 remain deferred for identity review.** Cognacq-Jay and Écouen received no additions in this release; their captured records and all research decisions remain available for continuation. Deferred work is not reported as completed or rejected.

All 650 current Joconde notices were individually first-reviewed. Supplemental review is documented for every released object, including title translations, other creator labels, old inventories and related works. The three additional generic pools for candidates 212, 220 and 254 were inspected in full. The unresolved generic portrait pools, same-plate print impressions, sparse comparator identities, source conflicts and old Louvre aliases remain outside the release.

The read-only identity scope contains 67,824 artworks and 148,704 citations. All 650 literal source facts and supplemental comparisons were independently recomputed. The preserved comparison bundle contains 2,475 national primary records. Selected paper prints are distinguished from their painted prototypes, printing matrices, supports and publication packaging. Separate impressions require physical evidence; duplicate notices, shared sheets and unresolved casts are held. Five object-level creator labels explicitly qualify Hans Sebald Beham’s copies after Barthel and the Galle attributions. Original national maker labels remain in each citation. No artist authority was changed.

The Estève portfolio format evidence and municipal ownership, Avelines object marks and collection provenance, and Dobrée departmental ownership are preserved. Unknown fields, original dates, before-date lower bounds and source rights labels remain literal. Museum holdings do not imply current display. No images were downloaded or attached.

The [review decisions](editorial-reviewed-001.json.gz), [comparison coverage](supplemental-review-001.json.gz), [frozen notes](working-notes-release-three-museums-001.py), [transaction plan](france-fifteenth-additions-001-plan.json.gz), [application receipt](france-fifteenth-additions-001-applied.json), [wave 70 verification](../../verification-after-wave-70.json) and [delivery checkpoint](delivery-checkpoint-001.json) preserve the release and its limits.

Exact readback verified 291 artworks, source identifiers, citations and accepted holding assertions. All 279 initial target-museum records, 3,206 protected comparison records and 9,831 prior campaign records remain unchanged. Replay wrote nothing. No existing dates, images, publication states, artist links or display claims were changed. Backups and completed logs are under Artline’s Library directories.

**43 unique offline checks passed**: 10 date, 19 selection, 5 identity and 9 release checks. The 1,356 pinned historical checks were not rerun; the cumulative evidence record is 1,399 checks. These checks do not establish ten-million-row performance.

Campaign totals: **9,337 new artworks and 785 existing-record holding links across 200 expanded institutions**. **1,257 canonical museums remain below 100 linked records and 1,390 below 200.** Eligible dates, linked counts, physical object identity, images and publication remain separate measures.

## Continuation

Continue the 301 deferred candidates, particularly Cognacq-Jay and Écouen, then the wider museum register. Candidate 458 still has unreviewed supplemental generic portrait leads. All other newly displayed supplemental ranges are recorded in the frozen notes; that coverage does not resolve remaining initial generic-title and specific pending questions. The 25 deferred candidates in the first three museums remain open as well. Do not rerun a fresh-import preflight against the pre-release museum counts; the delivery checkpoint and exact replay are now the continuation baseline.

The coverage snapshot also records 108 institutions added outside this batch (107 museums and one foundation), plus changed South African National Gallery counts. The full register now contains 1,599 institution rows and 1,555 canonical museum entries. Those external artworks are not counted among this campaign’s additions. New registry rows use their first-observed counts as the explicit coverage baseline, not an invented historical count.

The separate minimum-100 job remains terminal and separately counted. Baltimore, Orsay Coubertin, the prior Hugo timeout and the denied Bourges city article remain access holds without retry or bypass. Earlier wave 69 delivery files remain unchanged.
'''
    replace_with_backup(a.RUN/'README.md',detail,'france-fifteenth-preparation-readme-before-001')
    root=m.RUN/'README.md';prior=m.load(a.CHECKPOINT);pin=next(v for v in prior['artifacts'] if v['path']==str(root.relative_to(m.ROOT)))
    old=root.read_text();split=old.index('\n## Added works');intro=old[:split].replace('9,046','9,337').replace('196 local museums','197 local museums').replace('expand 199 institutions','expand 200 institutions').replace('1,152','1,257').replace('1,448','1,555').replace('after-wave-69','after-wave-70')
    lines=old[split:].splitlines();ix=next(i for i,v in enumerate(lines) if v.startswith('| Joconde — fourteenth five-museum'));lines.insert(ix+1,'| Joconde — fifteenth pass, resolved Estève/Avelines/Dobrée objects | 291 | 3 museums, 1 newly expanded |')
    ix=next(i for i,v in enumerate(lines) if v.startswith('| Distinct new-record campaign total |'));lines[ix]='| Distinct new-record campaign total | **9,337** | **198 collections** |'
    section='''

## Fifteenth pass — three-museum release

The [fifteenth review](native/france-fifteenth-minimum-20261008/README.md) added **291 review records**. Estève, Avelines and Dobrée each now exceed 100 eligible works. The 58 held and 301 deferred notices remain in the five-museum research queue; Cognacq-Jay and Écouen have not yet received additions from this pass.

'''+table+'''

All released records have source-backed physical-object decisions and complete relevant comparison coverage. Forty-three unique offline checks passed, exact readback succeeded, and replay wrote nothing. Existing catalogue metadata and all prior campaign records were preserved.

The [wave 70 verification](verification-after-wave-70.json) confirms **9,337 additions and 785 existing-record holding links across 200 expanded institutions**. **1,257 canonical museums remain below 100 linked records and 1,390 below 200.** The broader goal remains active. The expanded register includes 108 newly observed institutions from outside this batch; their works are separately tracked and not credited to this campaign.
'''
    replace_with_backup(root,intro+'\n'.join(lines)+'\n'+section,'france-fifteenth-root-readme-before-001',pin['sha256'])
    m.save(a.RUN/'readme-supersessions-001.json',dict(at=m.now(),changes=changes,policy='Wave70 documentation supersedes only the campaign README and its own preparation README. Both originals preserved in Library. Prior delivered evidence, scripts and reports unchanged.'))
    print('Wave70: 291 additions documented; 301 deferred and 58 held notices preserved; previous READMEs backed up.',flush=True)
if __name__=='__main__':main()
