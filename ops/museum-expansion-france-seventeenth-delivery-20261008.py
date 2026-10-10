"""Document the verified Cognacq-Jay release, preserving superseded README."""
import collections,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-seventeenth-apply-v2-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report=m.load(m.RUN/'verification-after-wave-72.json');assert report['verified_new_artworks']==9583
 plan,digest=a.validate_plan()
 with m.connect() as db:verified=a.verify(db,plan,digest)
 logsroot=Path('/Users/vadimdulub/Library/Logs');prefix='artline-france-seventeenth-'
 testlog=(logsroot/(prefix+'release-tests-20261008.log')).read_text();assert 'Ran 10 tests' in testlog and testlog.rstrip().endswith('OK')
 rebase_tests=(logsroot/(prefix+'rebase-tests-20261008.log')).read_text();assert 'Ran 3 tests' in rebase_tests and rebase_tests.rstrip().endswith('OK')
 assert (logsroot/(prefix+'replay-20261008.log')).read_text().strip()=='Unchanged replay: zero writes'
 states=collections.Counter(d['state'] for d in m.load(a.REVIEW)['decisions']);assert states=={'approved_review_only_addition':125,'editorial_hold':60,'deferred_identity_review':53}
 logs={p.name:dict(path=str(p),sha256=sha(p)) for p in sorted(logsroot.glob(prefix+'*-20261008.log')) if p.name not in [prefix+'delivery-20261008.log',prefix+'checkpoint-20261008.log']}
 m.save(a.RUN/'checks-001.json',dict(at=m.now(),new_offline_tests_passed=13,historical_tests_passed=1408,cumulative_verified_tests=1421,historical_tests_rerun=False,replay_zero_writes=True,source_facts_reparsed=238,comparisons_recomputed=True,date_only_proposals_physically_reviewed=212,added=125,editorial_holds=60,deferred_identity_candidates=53,logs=logs,other_job_totals_separate=True))
 changes=report['france_seventeenth_museum_changes'];changed=[v for v in changes if v['new']];assert len(changed)==1
 c=changed[0];assert (c['linked_before'],c['linked_after'],c['eligible_before'],c['eligible_after'])==(81,206,3,128)
 table='| Museum | Added | Linked before → after | Eligible before → after |\n| --- | ---: | ---: | ---: |\n'+'| '+c['name']+' | 125 | 81 → 206 | 3 → 128 |'
 types=collections.Counter(v['facts']['work_type'] for v in plan['records']);after=report['after']
 text='''# Seventeenth French museum pass — Cognacq-Jay

Added **125 real local artwork records**, all in review. Cognacq-Jay now has **206 linked records, including 128 with eligible creation dates and selection evidence**. It exceeds the 100-work minimum; the preference for 200 eligible works remains open. Linked counts do not by themselves establish date eligibility.

'''+table+'\n\nTypes: '+', '.join(str(v)+' '+k for k,v in sorted(types.items()))+'''. Each sculpture, painting, miniature and paper sheet is a physical catalogue unit. Frames, depicted artworks, prototypes and obsolete titles are not extra entries.

National Joconde records and all selected native Paris Musées pages were checked against matching inventory numbers. Native executing makers, model authors, attributed workshops, alternative and former attributions are preserved in qualified object labels; literal national exports remain in citations. No painter authority was invented or linked. Unknown fields remain unknown. Before-date lower bounds remain null; nineteenth-century copies retain their manufacture periods, and a circa1900 miniature is not redated from its forged1787 signature. Sources distinguish acquisitions from manufacture.

The initial fresh identity scope covers **44,129 existing artworks and 94,866 citations**. All238 remaining candidate facts, comparisons and within-batch groups were recomputed. The physical comparison bundle retains primary fields and individual reasons. The212 date-only triage proposals affecting selected works were checked for physical form, support, composition, scale, inscriptions and acquisition; differing dates alone do not establish different objects. Historical F21/D73 overlaps were resolved through distinct documented compositions, physical formats and current inventories. Related NGA1960.6.12 is an oil model, not the selected gouache.

The first application stopped before writes because another workflow attached an image/citation to a Dijon Lignier painting. The preserved [rebase capture](concurrent-state-rebase-001.json.gz) also records eight unrelated new artworks. The revised plan preserves these external changes. Inside the final transaction, all selected identity-hit classes are recomputed against current data; unrelated creator-pool growth alone cannot block the release, but any new or changed relevant comparison still does. The original failed attempt and both plans are retained.

**60 holds and53 deferred identities remain** in the five-museum queue. These include ambiguous Greuze versions, sparse same-era portraits, the Poncet and Lejeune physical-version questions, and the Louvre/Écouen historicalCL22278 conflict. The17 Cognacq-Jay deferred cases have explicit follow-up questions; six earlier Cognacq-Jay holds persist. No access hold was retried or bypassed. Met429, Baltimore429, OrsayCoubertin403, prior Hugo timeout and Bourges city403 remain recorded. An independent Grenoble Faure La Source page surfaced as a follow-up lead; it was not used to approve the deferred comparator.

The [editorial review](editorial-reviewed-001.json.gz), [comparison coverage](supplemental-review-001.json.gz), [physical date audit](physical-date-audit-001.json.gz), [transaction plan](france-seventeenth-additions-001-plan-002.json.gz), [application receipt](france-seventeenth-additions-001-applied.json) and [wave72 verification](../../verification-after-wave-72.json) preserve the evidence. Exact readback verified125 artworks, identifiers, citations and accepted holding assertions. All691 initial target records, '''+str(verified['protected_existing_records'])+''' scoped existing comparison records and10,243 prior campaign records were preserved. Thirteen offline release checks passed;1,408 historical checks remain pinned and were not rerun. Replaying the transaction wrote nothing. No new images, publication, current-display claims or deployments.

Campaign totals are **9,583 new artworks and785 reconciled holding links across202 institutions**. The current registry still has **'''+format(after['museums_below_100'],',')+''' canonical museums below100 linked works** and '''+format(after['museums_below_200'],',')+''' below200. The global goal remains active. The separate minimum100 job stays terminal and separately counted. Continue the113 held/deferred notices as evidence permits, then the broader museum queue; do not repeat this delivered125-record batch.
'''
 target=a.RUN/'README.md';assert not target.exists();target.write_text(text)
 root=m.RUN/'README.md';cp=m.load(a.CHECKPOINT);pin=next(v for v in cp['artifacts'] if v['path']==str(root.relative_to(m.ROOT)));assert sha(root)==pin['sha256'];before=root.read_text()
 backup=m.BACKUP/'france-seventeenth-root-readme-before-001.json.gz';assert not backup.exists();m.save(backup,dict(at=m.now(),path=str(root.relative_to(m.ROOT)),sha256=sha(root),text=before))
 split=before.index('\n## Added works');intro=before[:split].replace('9,458','9,583').replace('1,256',format(after['museums_below_100'],',')).replace('after-wave-71','after-wave-72')
 lines=before[split:].splitlines();ix=next(i for i,v in enumerate(lines) if v.startswith('| Joconde — sixteenth pass'));lines.insert(ix+1,'| Joconde — seventeenth pass, Cognacq-Jay | 125 | 1 museum, continuation |')
 ix=next(i for i,v in enumerate(lines) if v.startswith('| Distinct new-record campaign total |'));lines[ix]='| Distinct new-record campaign total | **9,583** | **'+str(report['institutions_expanded'])+' collections** |'
 root.write_text(intro+'\n'.join(lines)+'\n\n## Seventeenth pass — Cognacq-Jay\n\nThe [seventeenth pass](native/france-seventeenth-minimum-20261008/README.md) added **125 review records**.\n\n'+table+'\n\nExact readback, thirteen offline safeguards and a zero-write replay passed. The [wave72 verification](verification-after-wave-72.json) records **9,583 additions and785 holding reconciliations across202 institutions**. '+format(after['museums_below_100'],',')+' canonical museums remain below100 linked works. The five-museum research queue retains60 held and53 deferred notices; the all-museum goal remains active.\n')
 m.save(a.RUN/'readme-supersessions-001.json',dict(at=m.now(),changes=[dict(path=str(root.relative_to(m.ROOT)),before_sha256=pin['sha256'],after_sha256=sha(root),backup_path=str(backup),backup_sha256=sha(backup))],policy='Only the campaign README superseded; prior text preserved in Library backup.'))
 print(json.dumps(dict(documented=125,campaign_total=9583,expanded=202,remaining_below100=after['museums_below_100'])),flush=True)
if __name__=='__main__':main()
