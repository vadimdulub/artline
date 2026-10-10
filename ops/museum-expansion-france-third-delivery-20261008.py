"""Record completed checks and update progress with a retained README preimage."""
import hashlib,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-third-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    report=m.load(m.RUN/'verification-after-wave-58.json');assert report['verified_new_artworks']==5959 and not report['unrelated_coverage_changes_since_prior_report']
    logdir=Path('/Users/vadimdulub/Library/Logs');prefix='artline-france-third-'
    assert 'Ran 22 tests' in (logdir/(prefix+'tests-20261008.log')).read_text() and (logdir/(prefix+'tests-20261008.log')).read_text().rstrip().endswith('OK')
    assert (logdir/(prefix+'replay-20261008.log')).read_text().strip()=='Unchanged replay: zero writes'
    logs={p.name.removeprefix(prefix).removesuffix('-20261008.log'):dict(path=str(p),sha256=sha(p)) for p in sorted(logdir.glob(prefix+'*-20261008.log'))}
    assert not (a.RUN/'checks-001.json').exists()
    m.save(a.RUN/'checks-001.json',dict(at=m.now(),new_offline_tests_passed=22,historical_tests_passed=904,cumulative_verified_tests=926,historical_tests_rerun=False,replay_zero_writes=True,all_workers_completed=True,new_selected_sources=123,captured_review_holds=50,unique_unselected_or_index_held=1275,identity_version='002;001 preserved but superseded to expand former labels and creator aliases',logs=logs,other_job_totals_separate=True))
    rows=report['france_third_museum_changes'];table='| Museum | Added | Linked before → after | Eligible before → after |\n| --- | ---: | ---: | ---: |\n'+'\n'.join('| '+v['name']+' | '+str(v['new'])+' | '+str(v['linked_before'])+' → '+str(v['linked_after'])+' | '+str(v['eligible_before'])+' → '+str(v['eligible_after'])+' |' for v in rows)
    path=a.RUN/'README.md';assert not path.exists();path.write_text('''# Third French museum pass — 8 October 2026

Added **73 real local artwork records**, all in review: 50 drawings, 13 prints, six paintings and four sculptures. Évreux and Tournus now exceed 100 eligible records. The other three museums still need evidence-backed additions.

'''+table+'''

The verified September Joconde snapshot contained 1,796 rows for these museums, including 1,398 new source identities. Two bounded queues selected 123 complete current records, all returned with HTTP 200. Individual review approved 73 and held 50. Another 1,275 unique leads remain held or outside this selection. The supplemental 55 records supersede their initial exclusions; they are not counted twice.

Official Museofile context explicitly identifies Tournus's short museum name. Montargis's official operator supports its intercommunal public owner. These narrow parser adaptations preserve original location, legal labels and source fields. Deposit and missing-object exclusions remain in force. Optional Flers context capture ended with an incomplete-response transport error; it was not used to approve records, and the dependent optional Carpentras context capture was not reached.

The identity scope includes 36,894 existing artworks and 77,629 citations, with former Nevelson/Berliawsky and Janssens/Dietrich labels plus Schidone/Schedoni, Hondecoeter/Hondecooter and Del Marle variants. All 123 source facts and comparisons were recomputed against the final scope. Two Évreux Joconde references describe one Rome painting with an existing counterpart; neither became another artwork. An inventory shared across different museums is retained as a false-positive lead, not a match. Grouped and uncertain versions remain held. Girodet recto/verso drawings, multi-figure sheets and individually inventoried print impressions each count as one physical unit.

Creator labels and qualifications stay literal, including anonymous ancient sculpture and the Mayo/Milliarakis and Puni/Pougny aliases. The 1970 Alechinsky drawing is eligible. Represented historical years and sitter life dates do not replace creation dates. Current Maury chronology, a Leroy print mentioning Greuze's 1805 death despite eighteenth-century dating, books, casting dates, source medium conflicts and unresolved physical counterparts remain research holds. Missing dimensions, unknown lower date bounds and source dating differences remain explicit. Holdings do not establish current display.

The [plan](france-third-additions-001-plan.json.gz), [individual decisions](editorial-reviewed-001.json.gz), [application receipt](france-third-additions-001-applied.json) and [wave58 verification](../../verification-after-wave-58.json) document the additions. Readback verifies every new row, identifier, citation and holding assertion, preserving 3,046 scoped existing records and all 6,671 prior campaign records with associated data. The import uses the local loopback database only. No images, painter authorities, publication changes or display claims were added.

Twenty-two fresh offline checks passed; 904 historical checks remain pinned, for 926 cumulative verified checks. Historical tests were not all rerun; these checks are not a load-performance benchmark. Replay wrote nothing. Backups and execution logs are in Library, not scattered across Documents. The [delivery checkpoint](delivery-checkpoint-001.json) pins the evidence and the explicit root README supersession.

Campaign totals: **5,959 additions and 785 existing-record links across 169 expanded institutions**. Tournus and Montargis are newly expanded. All five museums were already included in source-pass totals, which remain 350 museums plus Barnes. A fresh audit has **1,184 canonical museum entries below 100 linked records** and **1,288 below 200**, with no unrelated coverage changes. The overall goal remains active. The separate minimum-100 job is terminal, unchanged and counted separately.
''')
    root=m.RUN/'README.md';backup=m.BACKUP/'france-third-root-readme-before-001.json.gz';assert not backup.exists();old=root.read_text();cp=m.load(a.CHECKPOINT);pin=next(v for v in cp['artifacts'] if v['path']==str(root.relative_to(m.ROOT)));assert sha(root)==pin['sha256'];m.save(backup,dict(at=m.now(),path=str(root.relative_to(m.ROOT)),sha256=sha(root),text=old))
    # Earlier dated sections remain historical. Only the current introduction,
    # deliverable links and source table are advanced, with an appended section.
    split=old.index('\n## Added works');intro=old[:split].replace('5,886','5,959').replace('164 local museums','166 local museums').replace('167 institutions','169 institutions').replace('1,186','1,184').replace('after-wave-57','after-wave-58');rest=old[split:]
    line='| Joconde — second five-museum selections, current official records | 132 | 5 continuations |'
    # Locate the existing final Joconde source-table line by its exact amount.
    lines=rest.splitlines();ix=next(i for i,v in enumerate(lines) if v.startswith('| Joconde') and '| 132 |' in v);lines.insert(ix+1,'| Joconde — third five-museum selections, current official records | 73 | 5 continuations |');rest='\n'.join(lines)+'\n'
    section='''

## Third five-museum pass — 8 October continuation

The [third five-museum pass](native/france-third-minimum-20261008/README.md) added **73 review records**: 50 drawings, 13 prints, six paintings and four sculptures. Current official Joconde responses covered 123 selected records; 73 passed individual review and 50 remain held. Another 1,275 unique new source leads remain held or outside the bounded selection.

'''+table+'''

Tournus's short museum name and Montargis's public intercommunal owner are supported by official context while original labels remain unchanged. The final identity scope includes former and variant creator names. Two references to one Évreux painting were held with their existing counterpart; recto/verso and multi-figure sheets count once. Anonymous sculpture, qualified makers, unknown dimensions and literal date evidence are preserved. Conflicting chronology, books, casting dates and unresolved physical versions remain held. Holding evidence does not establish display.

The [wave58 verification](verification-after-wave-58.json) confirms all 73 additions, preserving 3,046 scoped existing records plus 6,671 prior campaign objects and their associated data. Fresh identity preflight covered 36,894 artworks and 77,629 citations. All 123 literal source records and final comparisons were recomputed. Twenty-two fresh tests passed and replay wrote nothing. The 904 historical checks remain pinned, for 926 cumulative verified checks; they were not all rerun.

Campaign totals are **5,959 additions and 785 existing-record links across 169 expanded institutions**. Évreux and Tournus now exceed 100 eligible works; Flers, Montargis and Carpentras still need additions. Tournus and Montargis are newly expanded, while source-pass totals remain 350 museums plus Barnes. The fresh audit has **1,184 canonical museum entries below 100** and **1,288 below 200**, with no unrelated coverage changes. The [wave58 checkpoint](native/france-third-minimum-20261008/delivery-checkpoint-001.json) preserves the evidence chain and README preimage. The overall goal remains active, and the separate minimum-100 job and its totals remain unchanged.
'''
    root.write_text(intro+rest+section)
    print('Checks and documentation prepared; README preimage retained in Library',flush=True)
if __name__=='__main__':main()
