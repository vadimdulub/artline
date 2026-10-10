"""Document wave62, saving the pinned campaign README preimage first."""
import collections,hashlib,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-seventh-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report=m.load(m.RUN/'verification-after-wave-62.json');assert report['verified_new_artworks']==6672 and report['institutions_with_new_records_or_reconciled_holdings']==175 and not report['unrelated_coverage_changes_since_prior_report']
 p,digest=a.validate_plan()
 with m.connect() as db:verified=a.verify(db,p,digest)
 logsroot=Path('/Users/vadimdulub/Library/Logs');prefix='artline-france-seventh-'
 tests=(logsroot/(prefix+'tests-20261008.log')).read_text();assert 'Ran 32 tests' in tests and tests.rstrip().endswith('OK')
 assert (logsroot/(prefix+'replay-20261008.log')).read_text().strip()=='Unchanged replay: zero writes'
 logs={v.name:dict(path=str(v),sha256=sha(v)) for v in sorted(logsroot.glob(prefix+'*-20261008.log')) if v.name!=prefix+'delivery-20261008.log'}
 queues=[m.load(a.RUN/('selected-metadata-queue-'+v+'.json')) for v in ['001','002']]
 selected={v['source_id'] for q in queues for v in q['selected']};held={v['source_id'] for q in queues for v in q['held']}-selected
 assert len(selected)==164 and len(held)==804 and len(selected|held)==968
 assert not (a.RUN/'checks-001.json').exists()
 m.save(a.RUN/'checks-001.json',dict(at=m.now(),new_offline_tests_passed=32,historical_tests_passed=1014,cumulative_verified_tests=1046,historical_tests_rerun=False,replay_zero_writes=True,all_workers_completed=True,new_selected_sources=164,captured_review_holds=27,unique_unselected_or_index_held=804,identity_version='001; all literal facts and indexed comparisons recomputed',logs=logs,other_job_totals_separate=True))
 rows=report['france_seventh_museum_changes'];table='| Museum | Added | Linked before → after | Eligible before → after |\n| --- | ---: | ---: | ---: |\n'+'\n'.join('| '+v['name']+' | '+str(v['new'])+' | '+str(v['linked_before'])+' → '+str(v['linked_after'])+' | '+str(v['eligible_before'])+' → '+str(v['eligible_after'])+' |' for v in rows)
 root=m.RUN/'README.md';cp=m.load(a.CHECKPOINT);relative=str(root.relative_to(m.ROOT));pin=next(v for v in cp['artifacts'] if v['path']==relative);assert sha(root)==pin['sha256']
 backup=m.BACKUP/'france-seventh-root-readme-before-001.json.gz';assert not backup.exists();m.save(backup,dict(at=m.now(),path=relative,sha256=sha(root),text=root.read_text()));change=dict(path=relative,before_sha256=pin['sha256'],backup_path=str(backup),backup_sha256=sha(backup))
 types=collections.Counter(v['facts']['work_type'] for v in p['records']);kindtext=', '.join(str(v)+' '+k for k,v in sorted(types.items()))
 detail='''# Seventh French museum pass — 8 October 2026

Added **137 real local artwork records**, all in review. Abbeville now exceeds 100 eligible artworks. Auxerre and Saint-Cloud exceed 100 linked records but remain below 100 eligible works. Granville and Voiron remain below both measures; all five preferred-200 targets remain unfinished.

'''+table+'''

Types: '''+kindtext+'''. The pinned September Joconde index contains 1,347 rows for these five museums, including 968 new source identities. Two bounded queues selected 164 current records, captured in six HTTP 200 batches from the official national catalogue API. Individual review approved 137 and held 27. Another 804 distinct source leads remain held at selection or unreviewed. The two queues' held lists overlap: these totals count unique source IDs after removing all selected records, not the sum of the held-list lengths. No images were downloaded or attached.

The read-only identity scope covers 58,971 artworks and 126,370 citations. All 164 literal source records and indexed comparisons were recomputed. Source-derived former names, signatures and aliases broaden comparison searches. Rodin for the type-F dance and Mengs for the literal Minge label are comparison hypotheses only, not creator assignments. No artist authorities were created or linked.

Auxerre's abbreviated location label was reconciled using the exact M0184 Museofile identity, city, full official museum name, municipal acquisition label and the [city's Saint-Germain page](https://www.auxerre.fr/labbaye-saint-germain). The archived city HTML, text and receipt are linked in the name-reconciliation evidence. The exception rejects changed identities, private ownership, deposits and missing-object flags; the original location and ownership labels are retained verbatim. Saint-Cloud's source explicitly names the city while the database city is empty. The exact museum ID, full city-qualified name and M0416 code support the match without filling the existing database field. Neither reconciliation establishes current display or independent legal title.

Physical review separates newspaper or book impressions from depicted event dates, copies from original paintings, ceramic edition numbers from object counts, and double-sided drawings from separate works. Genin's lighthouse gouaches differ in date and size; Gen Paul's Jouhandeau drawings differ in date, medium and size; Bridoux's Madonna copies have different inventories, media and measurements. Stockl's ruins panels retain distinct complete archival inventories. One short historical 279 collision belongs to a different Clouet portrait; an untitled Thomas Rowlandson etching is distinguished from Louis Charlemagne Thomas's sanguine child study. Source workshop, school, after, attributed and questioned labels remain qualified. The Galanis drawing is retained as a Greek creator's work outside Greece without an invented authority assignment.

Blank Granville maker fields remain unknown even when inscriptions mention Derain, Seyssaud or Friesz. Auxerre's winter-reading canvas has a blank main creator field but the author-note field explicitly says DURAND Charles; that literal object-level label is derived with both original fields and the derivation recorded. No biography is invented. Abbeville's acquisition unknowns caused by archive loss remain unknown. Former Vigée Le Brun and Blanchard attributions remain historical evidence rather than promoted authorship. Historical deposits and current municipal source labels are both retained.

Four captured Granville source identities already exist under older catalogue identifiers and are held against their exact existing artwork IDs. The other 23 holds cover a contaminated source title, unresolved copies or impressions, possible same-title duplicates and conflicting physical-version evidence. Sparse Zingg, Hupin, Dughet and Van de Venne leads remain unresolved. The [individual decisions](editorial-reviewed-001.json.gz) document every reviewed source record; no quota overrides were used.

The [plan](france-seventh-additions-001-plan.json.gz), [application receipt](france-seventh-additions-001-applied.json), [wave62 verification](../../verification-after-wave-62.json) and [delivery checkpoint](delivery-checkpoint-001.json) record the local atomic additions. Exact readback verifies each new artwork, identifier, citation and accepted collection-holding assertion. Unchanged snapshots protect '''+str(verified['protected_existing_records'])+''' existing comparison/scope records and all 7,320 prior campaign objects with their media, creator links, citations, holdings and publication states. The initial five-museum scope contains 383 existing artworks. Replay wrote nothing. No publication, current-display or image claims were made.

Thirty-two fresh offline tests passed; 1,014 historical checks remain pinned, for 1,046 cumulative verified checks. Historical tests were not all rerun. These checks do not establish ten-million-row performance. Backups and execution logs remain under Library; previous campaign README bytes are preserved before this update.

Campaign totals: **6,672 new artworks and 785 existing-record holding links across 175 expanded institutions**. Auxerre, Saint-Cloud and Granville are newly expanded in this campaign. New records cover 172 museums plus Barnes; source-pass totals remain 350 museums plus Barnes. The new audit has **1,171 canonical museums below 100 linked records** and **1,288 below 200**. Linked records, eligible dates and distinct physical-object reconciliation remain separate measures. The overall goal remains active and unfinished. The separate minimum-100 job remains terminal and unchanged with separate totals. The Baltimore access hold remains in force; no retry or alternate route was attempted.
'''
 assert not (a.RUN/'README.md').exists();(a.RUN/'README.md').write_text(detail)
 old=root.read_text();split=old.index('\n## Added works');intro=old[:split].replace('6,535','6,672').replace('169 local museums','172 local museums').replace('expand 172 institutions','expand 175 institutions').replace('1,174','1,171').replace('after-wave-61','after-wave-62');lines=old[split:].splitlines()
 ix=next(i for i,v in enumerate(lines) if v.startswith('| Joconde — sixth five-museum'));lines.insert(ix+1,'| Joconde — seventh five-museum selections, current official records | 137 | 5 museums; 3 newly expanded |')
 ix=next(i for i,v in enumerate(lines) if v.startswith('| Distinct new-record campaign total |'));lines[ix]='| Distinct new-record campaign total | **6,672** | **173 collections** |'
 section='''

## Seventh five-museum pass — 8 October continuation

The [seventh five-museum pass](native/france-seventh-minimum-20261008/README.md) added **137 review records** from 164 current Joconde records. Four known duplicate source identities and 23 unresolved cases remain held; 804 other distinct new source identities remain held or unselected.

'''+table+'''

Abbeville crosses 100 eligible works. Auxerre and Saint-Cloud cross 100 linked records while remaining below 100 eligible; Granville and Voiron remain below both. Museum-name reconciliation retains original labels and unknown database fields. Object review preserves qualified creators, separates physical versions and leaves unresolved duplicates on hold. The identity scope contains 58,971 artworks and 126,370 citations. All selected facts and comparisons were recomputed, 32 fresh tests passed and replay wrote nothing. Existing records remain unchanged.

The [wave62 verification](verification-after-wave-62.json) and [checkpoint](native/france-seventh-minimum-20261008/delivery-checkpoint-001.json) confirm **6,672 additions and 785 existing-record links across 175 expanded institutions**. Source-pass totals stay 350 museums plus Barnes. There are **1,171 canonical museums below 100 linked works** and **1,288 below 200**. The goal remains active; the separate minimum-100 job remains unchanged and separately counted.
'''
 root.write_text(intro+'\n'.join(lines)+'\n'+section);change['after_sha256']=sha(root)
 m.save(a.RUN/'readme-supersessions-001.json',dict(at=m.now(),changes=[change],policy='Intentional wave62 progress update; previous root README bytes retained in Library. Earlier source evidence, plans, reports and code remain immutable. Seventh-pass README is new.'))
 print('Wave62 documentation verified; prior root README retained in Library',flush=True)
if __name__=='__main__':main()
