"""Document wave61 with a saved preimage of the frozen campaign README."""
import collections,hashlib,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-sixth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report=m.load(m.RUN/'verification-after-wave-61.json');assert report['verified_new_artworks']==6535 and report['institutions_with_new_records_or_reconciled_holdings']==172 and not report['unrelated_coverage_changes_since_prior_report']
 p,digest=a.validate_plan()
 with m.connect() as db:verified=a.verify(db,p,digest)
 logsroot=Path('/Users/vadimdulub/Library/Logs');prefix='artline-france-sixth-'
 tests=(logsroot/(prefix+'tests-20261008.log')).read_text();assert 'Ran 32 tests' in tests and tests.rstrip().endswith('OK')
 assert (logsroot/(prefix+'replay-20261008.log')).read_text().strip()=='Unchanged replay: zero writes'
 logs={v.name:dict(path=str(v),sha256=sha(v)) for v in sorted(logsroot.glob(prefix+'*-20261008.log')) if v.name!=prefix+'delivery-20261008.log'}
 assert not (a.RUN/'checks-001.json').exists()
 m.save(a.RUN/'checks-001.json',dict(at=m.now(),new_offline_tests_passed=32,historical_tests_passed=982,cumulative_verified_tests=1014,historical_tests_rerun=False,replay_zero_writes=True,all_workers_completed=True,new_selected_sources=239,captured_review_holds=11,unique_unselected_or_index_held=7663,identity_version='002;001 preserved; expanded source-note and former-attribution comparison terms',logs=logs,other_job_totals_separate=True))
 rows=report['france_sixth_museum_changes'];table='| Museum | Added | Linked before → after | Eligible before → after |\n| --- | ---: | ---: | ---: |\n'+'\n'.join('| '+v['name']+' | '+str(v['new'])+' | '+str(v['linked_before'])+' → '+str(v['linked_after'])+' | '+str(v['eligible_before'])+' → '+str(v['eligible_after'])+' |' for v in rows)
 root=m.RUN/'README.md';cp=m.load(a.CHECKPOINT);relative=str(root.relative_to(m.ROOT));pin=next(v for v in cp['artifacts'] if v['path']==relative);assert sha(root)==pin['sha256']
 backup=m.BACKUP/'france-sixth-root-readme-before-001.json.gz';assert not backup.exists();m.save(backup,dict(at=m.now(),path=relative,sha256=sha(root),text=root.read_text()));change=dict(path=relative,before_sha256=pin['sha256'],backup_path=str(backup),backup_sha256=sha(backup))
 types=collections.Counter(v['facts']['work_type'] for v in p['records']);kindtext=', '.join(str(v)+' '+k for k,v in sorted(types.items()))
 detail='''# Sixth French museum pass — 8 October 2026

Added **228 real local artwork records**, all in review. Libourne, Senlis and Amiens now exceed 100 eligible artworks. Béziers and Cambrai still need additions to reach 100. The preferred 200 target remains unfinished for all five.

'''+table+'''

Types: '''+kindtext+'''. The pinned September Joconde index contains 8,276 rows for these museums, of which 7,902 source identities were new to the database match scope. A bounded selection of 239 object records was captured from the current official national catalogue API in six HTTP 200 batches. Individual review approved 228 and held 11; another 7,663 source leads remain held at selection or unreviewed. No image downloads or attachments were made.

The final read-only identity scope contains 22,183 existing artworks and 47,635 citations. All 239 current records and the final indexed comparisons were recomputed. Comparison terms include former attributions, copy models and source-note alternatives; they are not new artist authorities. The first comparison version remains preserved. Four verified archived source-body extracts distinguish the Lagrenée preparatory drawing, Lacaze pastel self-portrait and Clovis charcoal studies from known oil canvases, and distinguish Cambrai's collaborative market canvas from a Louvre Snyders painting. These older captures are used only for physical comparison, not to create fresh holding claims.

A source-parser hold on Jean Moulin's drawing was resolved by inspecting its current record: the paragraph about 600 drawings and carrying a notebook is a collection biography, while this object is an individually inventoried 1936 drawing on torn tracing paper. The exception requires the exact reference, museum, inventory, title, date, medium, description, absence of assembly fields and the exact commentary hash. The complete original paragraph is retained. Changing any relevant object-unit evidence rejects the exception. The original failed parser and log remain preserved alongside the successor.

Duthoit notes say that either brother could be the author; 18 labels preserve those alternatives rather than asserting collaboration. Brouwer's beer-drinker attribution and the anonymous copy after Teniers are qualified from the source history. The Venetian Virgin retains Daggiu/Cappella or Maggiotto as alternatives. Two circa-1850 descriptions qualify the new records' dates, preserving the literal original fields and nominal year without inventing a tolerance. No existing catalogue dates or labels changed.

Object review distinguishes drawings from represented medieval sculptures, historical city views from their nineteenth-century execution, paper prints from woodblocks, plaster and terracotta versions from bronzes, and copies from painted originals. Double-sided sheets, multi-study sheets, the double-faced bust and fountain with basin each count once. Busson's same-title hunting prints have different Series A/D inscriptions; Hallo's Ketzing drawings have different dated inscriptions and sizes; Delarozière's actress sheets differ in date, size and inscription. Four groups of short inventory-number collisions were resolved against full identifiers and physical descriptions. Anonymous makers and unknown structured medium or dimensions remain unknown. Museum collection evidence does not establish current display or independent legal title.

The eleven holds cover an already-recorded Delacroix copy, a Goya/Mordant execution contradiction, unresolved portrait/landscape identities, disputed attributions, ambiguous physical-copy dates and conflicting source dates. The [individual decisions](editorial-reviewed-001.json.gz) retain reasons and comparison leads for every captured object. Unselected candidates remain evidence, not automatic approvals or quota fillers.

The [plan](france-sixth-additions-001-plan.json.gz), [application receipt](france-sixth-additions-001-applied.json), [wave61 verification](../../verification-after-wave-61.json) and [delivery checkpoint](delivery-checkpoint-001.json) document the exact local additions. Readback verifies every new artwork, identifier, citation and accepted holding assertion, plus unchanged snapshots of 2,807 existing scope records and all 7,092 prior campaign objects with associated media, creator links, citations, holdings and publication states. The transaction was loopback-local and atomic. Replay wrote nothing. No new artist authorities or publications were made.

Thirty-two fresh offline tests passed; 982 historical checks remain pinned, for 1,014 cumulative verified checks. Historical tests were not all rerun. One initial test expected the nineteenth century to start in 1800; it was corrected to 1801 without changing source facts or parser behavior, and the failed log was retained. These checks do not establish ten-million-row performance. Backups and execution logs remain under Library. The previous campaign README bytes are preserved before this documented update.

Campaign totals: **6,535 new artworks and 785 existing-record holding links across 172 expanded institutions**. All five museums had prior additions, so institution totals remain unchanged. Source-pass totals remain 350 museums plus Barnes. The new audit has **1,174 canonical museums below 100 linked records** and **1,288 below 200**. Linked records, eligible creation dates and distinct physical-object reconciliation remain separate measures. The goal is active and unfinished. The separate minimum-100 job remains terminal and unchanged, with separate totals. The Baltimore access hold remains in force; no retry or alternate transport was attempted.
'''
 assert not (a.RUN/'README.md').exists();(a.RUN/'README.md').write_text(detail)
 old=root.read_text();split=old.index('\n## Added works');intro=old[:split].replace('6,307','6,535').replace('1,177','1,174').replace('after-wave-60','after-wave-61');lines=old[split:].splitlines()
 ix=next(i for i,v in enumerate(lines) if v.startswith('| Joconde — fifth five-museum'));lines.insert(ix+1,'| Joconde — sixth five-museum selections, current official records | 228 | 5 continuations |')
 ix=next(i for i,v in enumerate(lines) if v.startswith('| Distinct new-record campaign total |'));lines[ix]='| Distinct new-record campaign total | **6,535** | **170 collections** |'
 section='''

## Sixth five-museum pass — 8 October continuation

The [sixth five-museum pass](native/france-sixth-minimum-20261008/README.md) added **228 review records** from 239 current Joconde records. Eleven duplicate or unresolved cases remain held, and 7,663 other new source identities remain held or unselected.

'''+table+'''

Libourne, Senlis and Amiens now exceed 100 eligible works. Béziers and Cambrai remain below 100; all five preferred-200 targets remain unfinished. Review preserves alternative attributions, qualified source dates, physical copies and anonymous makers. Distinct drawings and prints were separated from existing paintings, and sheets with multiple studies count once. The final identity scope contains 22,183 artworks and 47,635 citations. All selected facts and comparisons were recomputed,32 fresh tests passed, and replay wrote nothing. Existing records remain unchanged.

The [wave61 verification](verification-after-wave-61.json) and [checkpoint](native/france-sixth-minimum-20261008/delivery-checkpoint-001.json) confirm **6,535 additions and 785 existing-record links across 172 expanded institutions**. Source-pass totals stay 350 museums plus Barnes. There are **1,174 canonical museums below 100 linked works** and **1,288 below 200**. The goal remains active; the separate minimum-100 job remains unchanged and separately counted.
'''
 root.write_text(intro+'\n'.join(lines)+'\n'+section);change['after_sha256']=sha(root)
 m.save(a.RUN/'readme-supersessions-001.json',dict(at=m.now(),changes=[change],policy='Intentional wave61 progress update; previous root README bytes retained in Library. Earlier source evidence, plans, reports and code remain immutable. Sixth-pass README is new.'))
 print('Wave61 documentation verified; prior root README retained in Library',flush=True)
if __name__=='__main__':main()
