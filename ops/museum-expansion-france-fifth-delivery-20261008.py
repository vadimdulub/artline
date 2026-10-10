"""Document verified wave60 progress; preserve the previous root README bytes."""
import collections,hashlib,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-fifth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report=m.load(m.RUN/'verification-after-wave-60.json');assert report['verified_new_artworks']==6307 and report['institutions_with_new_records_or_reconciled_holdings']==172 and not report['unrelated_coverage_changes_since_prior_report']
 p,digest=a.validate_plan()
 with m.connect() as db:verified=a.verify(db,p,digest)
 logdir=Path('/Users/vadimdulub/Library/Logs');prefix='artline-france-fifth-'
 tests=(logdir/(prefix+'tests-20261008.log')).read_text();assert 'Ran 29 tests' in tests and tests.rstrip().endswith('OK')
 assert (logdir/(prefix+'replay-20261008.log')).read_text().strip()=='Unchanged replay: zero writes'
 logs={v.name:dict(path=str(v),sha256=sha(v)) for v in sorted(logdir.glob(prefix+'*-20261008.log')) if v.name!=prefix+'delivery-20261008.log'}
 assert not (a.RUN/'checks-001.json').exists()
 m.save(a.RUN/'checks-001.json',dict(at=m.now(),new_offline_tests_passed=29,historical_tests_passed=953,cumulative_verified_tests=982,historical_tests_rerun=False,replay_zero_writes=True,all_workers_completed=True,new_selected_sources=202,captured_review_holds=55,unique_unselected_or_index_held=6712,identity_version='002;001 preserved; expanded source-note names and former attributions',logs=logs,other_job_totals_separate=True))
 rows=report['france_fifth_museum_changes'];table='| Museum | Added | Linked before → after | Eligible before → after |\n| --- | ---: | ---: | ---: |\n'+'\n'.join('| '+v['name']+' | '+str(v['new'])+' | '+str(v['linked_before'])+' → '+str(v['linked_after'])+' | '+str(v['eligible_before'])+' → '+str(v['eligible_after'])+' |' for v in rows)
 root=m.RUN/'README.md';cp=m.load(a.CHECKPOINT);relative=str(root.relative_to(m.ROOT));pin=next(v for v in cp['artifacts'] if v['path']==relative);assert sha(root)==pin['sha256']
 backup=m.BACKUP/'france-fifth-root-readme-before-001.json.gz';assert not backup.exists();m.save(backup,dict(at=m.now(),path=relative,sha256=sha(root),text=root.read_text()))
 change=dict(path=relative,before_sha256=pin['sha256'],backup_path=str(backup),backup_sha256=sha(backup))
 types=collections.Counter(v['facts']['work_type'] for v in p['records']);kindtext=', '.join(str(v)+' '+k for k,v in sorted(types.items()))
 detail='''# Fifth French museum pass — 8 October 2026

Added **147 real local artwork records**, all in review. LaM and Granet now exceed 100 eligible works. Saint-Nazaire, MAC VAL and the Musée de l’Armée still need additions to reach 100; the preferred 200 target remains unfinished for all five.

'''+table+'''

Types: '''+kindtext+'''. The verified September Joconde snapshot contained 7,365 target rows and 6,914 new source identities. A bounded selection of 202 current object records was captured in six HTTP 200 batches. Individual review approved 147 and held 55. Another 6,712 source leads remain held at selection or unreviewed. The Musée de l’Armée source subset contains many deposits, military objects outside this artwork selection and unclear album components; only one new work was approved here. Quotas did not override those checks.

The final identity scope covers 40,313 existing artworks and 86,842 citations. Source-note names and former attributions were added to comparisons, including Casier, Derriennic, McCarthy, Cuyp, Napoletano, Grimaldi, Ribera, Bourdon, Poussin, Valentin, Guercino/Barbieri and Beham. All 202 literal records and the final comparisons were recomputed. The original identity capture remains immutable. No artist authorities were created or existing attribution changed.

LaM’s object records use the former museum name and often provide acquisition-to-museum labels without legal ownership. The successfully captured [official LaM history](https://www.musee-lam.fr/fr/lhistoire-du-lam), exact national museum code, current museum name, city, former location name and object acquisition labels support the same collection identity. Acceptance is restricted to that combination. Raw acquisition and location labels remain in every citation; temporary parser inputs never become stored source facts or an ownership claim. Works recorded on deposit elsewhere are excluded. Aloïse’s historical Grand-Hornu deposit has an explicit 2010 end date, which is preserved without a current-display assertion. An optional metropolitan archive context capture timed out; its failure remains recorded and it is not part of the acceptance gate.

The Musée de l’Armée’s empty database city stays empty. Its exact city-qualified institution name, official object code and source Paris location establish the match. Baschet’s old Dépôt 4368 identifier remains literal; the current source explicitly records State ownership/dation to this museum. Unknown makers, structured media, measurements and lower date bounds remain unknown. Qualified, workshop and copyist labels stay literal. Before-date endpoints remain exclusive. Source metadata is preserved even where descriptions supply detail absent from structured fields.

Object review separates small studies from full-size works, paper prints from painted prototypes and copies from originals. Recto/verso sheets and the two-part Henri IV bust each count once. Tal Coat’s two rooster drawings have opposing directions, different highlights and opposite signature positions. Three short historical inventory collisions are explicitly distinguished by their numbering series, subjects, dimensions and physical supports. Sahut’s secondary 1021/1027 numbering discrepancy remains preserved alongside primary inventory 2021.2.16.

Holds include a previously recorded Dante et Virgile, generic abstract works without enough physical metadata, duplicate-looking sheets and flower canvases, uncertain book/print units, conflicting dates and former/current attribution questions. They remain research evidence rather than duplicate catalogue additions.

The [review plan](france-fifth-additions-001-plan.json.gz), [individual decisions](editorial-reviewed-001.json.gz), [application receipt](france-fifth-additions-001-applied.json) and [wave60 verification](../../verification-after-wave-60.json) document the results. Readback verifies every new artwork, identifier, citation and accepted holding assertion while preserving '''+str(verified['protected_existing_records'])+''' scoped existing records and all 6,945 prior campaign objects with their associated metadata, images, creator links, holdings and publication states. The write was atomic and loopback-local. Replay wrote nothing. No images were attached and no works were published.

Twenty-nine fresh offline tests passed; 953 historical checks remain pinned, for 982 cumulative verified checks. Historical tests were not all rerun. These checks do not establish ten-million-row performance. Backups and execution logs remain in Library. The [delivery checkpoint](delivery-checkpoint-001.json) preserves earlier evidence and the root README preimage. The campaign table’s stale total was corrected to the verified current total in this documented update.

Campaign totals: **6,307 additions and 785 existing-record holding links across 172 expanded institutions**. Three of this pass’s museums are newly expanded in this campaign; source-pass totals remain 350 museums plus Barnes. The fresh audit has **1,177 canonical museums below 100 linked records** and **1,288 below 200**. Linked totals are separate from eligible dates and unique physical-object reconciliation. The goal remains active. The separate minimum-100 job remains terminal and unchanged, with separate totals. The Baltimore access hold remains in force.
'''
 assert not (a.RUN/'README.md').exists();(a.RUN/'README.md').write_text(detail)
 old=root.read_text();split=old.index('\n## Added works');intro=old[:split].replace('6,160','6,307').replace('166 local museums','169 local museums').replace('169 institutions','172 institutions').replace('1,179','1,177').replace('after-wave-59','after-wave-60');lines=old[split:].splitlines()
 ix=next(i for i,v in enumerate(lines) if v.startswith('| Joconde — fourth five-museum'));lines.insert(ix+1,'| Joconde — fifth five-museum selections, current official records | 147 | 5 museums; 3 newly expanded |')
 ix=next(i for i,v in enumerate(lines) if v.startswith('| Distinct new-record campaign total |'));lines[ix]='| Distinct new-record campaign total | **6,307** | **170 collections** |'
 section='''

## Fifth five-museum pass — 8 October continuation

The [fifth five-museum pass](native/france-fifth-minimum-20261008/README.md) added **147 review records** from 202 current Joconde object records. Fifty-five remain held for unresolved identity, date, attribution or physical-unit questions; 6,712 other new source leads remain held or unselected.

'''+table+'''

LaM and Granet now exceed 100 eligible works. The other three targets and every preferred-200 target remain unfinished. LaM’s former museum name and acquisition labels are reconciled with preserved source evidence, without legal-ownership or current-display claims. Deposits elsewhere remain excluded. The final identity scope covers 40,313 artworks and 86,842 citations. All selected facts and comparisons were recomputed, 29 fresh tests passed, and replay wrote nothing. Existing catalogue records were preserved.

The [wave60 verification](verification-after-wave-60.json) and [checkpoint](native/france-fifth-minimum-20261008/delivery-checkpoint-001.json) confirm **6,307 additions and 785 existing-record links across 172 expanded institutions**. The current added-work table total is corrected to match the verified report. Source-pass totals stay 350 museums plus Barnes. There are **1,177 canonical museums below 100 linked works** and **1,288 below 200**. The goal remains active; the separate minimum-100 job remains unchanged and separately counted.
'''
 root.write_text(intro+'\n'.join(lines)+'\n'+section);change['after_sha256']=sha(root)
 m.save(a.RUN/'readme-supersessions-001.json',dict(at=m.now(),changes=[change],policy='Intentional wave60 progress and stale campaign-table total correction; root README preimage retained in Library. Earlier source evidence, plans, reports and code remain immutable. Fifth-pass README is new.'))
 print('Verified checks and documentation saved; root README preimage retained in Library',flush=True)
if __name__=='__main__':main()
