"""Record verified wave59 progress with retained preimages of both README files."""
import collections,hashlib,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-fourth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report=m.load(m.RUN/'verification-after-wave-59.json');assert report['verified_new_artworks']==6160 and not report['unrelated_coverage_changes_since_prior_report']
 p,digest=a.validate_plan()
 with m.connect() as db:verified=a.verify(db,p,digest)
 logdir=Path('/Users/vadimdulub/Library/Logs');prefix='artline-france-fourth-'
 tests=(logdir/(prefix+'tests-002-20261008.log')).read_text();assert 'Ran 27 tests' in tests and tests.rstrip().endswith('OK')
 assert (logdir/(prefix+'replay-20261008.log')).read_text().strip()=='Unchanged replay: zero writes'
 logs={v.name:dict(path=str(v),sha256=sha(v)) for v in sorted(logdir.glob(prefix+'*-20261008.log')) if v.name!=prefix+'delivery-20261008.log'}
 assert not (a.RUN/'checks-001.json').exists()
 m.save(a.RUN/'checks-001.json',dict(at=m.now(),new_offline_tests_passed=27,historical_tests_passed=926,cumulative_verified_tests=953,historical_tests_rerun=False,replay_zero_writes=True,all_workers_completed=True,new_selected_sources=240,captured_review_holds=39,unique_unselected_or_index_held=7683,identity_version='002;001 preserved and superseded with source-note maker aliases and manufacturer names',logs=logs,other_job_totals_separate=True))
 rows=report['france_fourth_museum_changes'];table='| Museum | Added | Linked before → after | Eligible before → after |\n| --- | ---: | ---: | ---: |\n'+'\n'.join('| '+v['name']+' | '+str(v['new'])+' | '+str(v['linked_before'])+' → '+str(v['linked_after'])+' | '+str(v['eligible_before'])+' → '+str(v['eligible_after'])+' |' for v in rows)
 cp=m.load(a.CHECKPOINT);research=m.load(a.RUN/'research-checkpoint-001.json');changes=[]
 for path,checkpoint,stem in [(m.RUN/'README.md',cp,'root'),(a.RUN/'README.md',research,'research')]:
  relative=str(path.relative_to(m.ROOT));pin=next(v for v in checkpoint['artifacts'] if v['path']==relative);assert sha(path)==pin['sha256']
  backup=m.BACKUP/('france-fourth-'+stem+'-readme-before-001.json.gz');assert not backup.exists();m.save(backup,dict(at=m.now(),path=relative,sha256=sha(path),text=path.read_text()));changes.append(dict(path=relative,before_sha256=pin['sha256'],backup_path=str(backup),backup_sha256=sha(backup)))
 types=collections.Counter(v['facts']['work_type'] for v in p['records']);kindtext=', '.join(str(v)+' '+k for k,v in sorted(types.items()))
 detail='''# Fourth French museum pass — 8 October 2026

Added **201 real local artwork records**, all in review. All five museums now exceed 100 eligible works. Their preferred target of 200 still requires further research.

'''+table+'''

Types: '''+kindtext+'''. The verified September Joconde snapshot contained 8,313 target rows and 7,923 new source identities. A bounded selection of 240 current records was retrieved in six HTTP 200 batches. Individual review approved 201 and held 39; 7,683 other leads remain held at selection or unreviewed. Source metadata and response bytes remain preserved; no images were downloaded.

The final identity scope checks 49,832 existing artworks and 112,173 citations. It expands manufacturer names, first-name-first surnames and source-note aliases including Fischetti, Artus, Lauriol, Savy, ROBJ, Johnston, Vieillard, Barbieri/Guercino and Baudouin. All 240 literal facts and comparisons were recomputed. The earlier identity scope remains immutable. Twelve creator labels explicitly retain qualifications found outside the headline Auteur field; each citation keeps the original label, exact source field and derived qualified label. No artist authorities were created.

The catalogue's Vitré city and museum code match the existing city-qualified institution name; the empty database city stays unchanged. Five SN inventory labels remain literal unknowns, with separate physical works established through subjects, signed dates, formats and source identities. Source whitespace remains in raw evidence. Ceramic plates, their paper designs, preparatory architectural drawings and executed objects remain distinct. Multi-figure and recto/verso sheets each count once. The Denon group has separate sheets supported by dimensions, paper and techniques; no matching parent object was found in the scoped museum and creator evidence. A shared 2017.1.1 inventory between a Claudet ceramic and an unrelated Perronneau pastel is explicitly distinguished by maker, subject, medium, date and collection.

Holds include a previously recorded Niel print; Bernier, Babey, Hardouin and Roth identities requiring reconciliation; closely related casts and service pieces; generic or unknown physical counterparts; conflicting date inscriptions; and a two-inventory Dehuz record. Unknown makers, measurements, lower date bounds, attribution alternatives and source labels remain explicit. Before endpoints remain exclusive. Holdings do not establish current display.

The [review plan](france-fourth-additions-001-plan.json.gz), [individual decisions](editorial-reviewed-001.json.gz), [application receipt](france-fourth-additions-001-applied.json) and [wave59 verification](../../verification-after-wave-59.json) document the additions. Readback verifies every artwork, identifier, citation and holding assertion, preserving '''+str(verified['protected_existing_records'])+''' scoped existing records and all 6,744 prior campaign objects with their associated metadata, images, artist links, holdings and publication states. The write was atomic and loopback-local. Replay wrote nothing.

Twenty-seven fresh offline tests passed; 926 historical checks remain pinned, for 953 cumulative verified checks. Historical tests were not all rerun. These checks do not establish ten-million-row performance. Backups and execution logs are retained in Library. The [delivery checkpoint](delivery-checkpoint-001.json) preserves prior evidence and explicit preimages for both README updates.

Campaign totals: **6,160 additions and 785 existing-record holding links across 169 expanded institutions**. All five targets were already expanded, so distinct institution and source-pass totals do not increase. The fresh audit has **1,179 canonical museums below 100 linked records** and **1,288 below 200**, with no unrelated coverage changes. The goal remains active. The separate minimum-100 job stays terminal and unchanged, with totals separate. The Baltimore access hold remains in force.
'''
 (a.RUN/'README.md').write_text(detail)
 root=m.RUN/'README.md';old=root.read_text();split=old.index('\n## Added works');intro=old[:split].replace('5,959','6,160').replace('1,184','1,179').replace('after-wave-58','after-wave-59');rest=old[split:];lines=rest.splitlines();ix=next(i for i,v in enumerate(lines) if v.startswith('| Joconde') and '| 73 |' in v);lines.insert(ix+1,'| Joconde — fourth five-museum selections, current official records | 201 | 5 continuations |')
 section='''

## Fourth five-museum pass — 8 October continuation

The [fourth five-museum pass](native/france-fourth-minimum-20261008/README.md) added **201 review records** from 240 current Joconde records. Thirty-nine remain held for unresolved identity, date or physical-unit questions; 7,683 other new source leads remain held or unselected.

'''+table+'''

All five museums now exceed 100 eligible works. Twelve derived creator labels preserve attribution qualifiers found in source notes while retaining the literal original field. Unknown inventory labels remain unknown; ceramic objects and their designs, copies and originals, physical sheets and depicted subjects stay distinct. The final identity scope covers 49,832 artworks and 112,173 citations. All selected facts and comparisons were recomputed, 27 fresh tests passed, and replay wrote nothing. Existing records, images, publication and display states were preserved.

The [wave59 verification](verification-after-wave-59.json) and [checkpoint](native/france-fourth-minimum-20261008/delivery-checkpoint-001.json) confirm **6,160 campaign additions and 785 existing-record links across 169 expanded institutions**. These five targets were already expanded; source-pass totals stay 350 museums plus Barnes. There are **1,179 canonical museums below 100 linked works** and **1,288 below 200**. The goal remains active and the separate minimum-100 job remains unchanged and counted separately.
'''
 root.write_text(intro+'\n'.join(lines)+'\n'+section)
 for change in changes:change['after_sha256']=sha(m.ROOT/change['path'])
 m.save(a.RUN/'readme-supersessions-001.json',dict(at=m.now(),changes=changes,policy='Intentional wave59 progress updates; both previous README byte sequences retained in Library. All earlier source evidence, plans, reports and code immutable.'))
 print('Verified checks and documentation saved; both README preimages retained in Library',flush=True)
if __name__=='__main__':main()
