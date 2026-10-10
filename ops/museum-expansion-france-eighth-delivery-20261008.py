"""Document wave63 with a preserved preimage of the campaign README."""
import collections, hashlib, importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-eighth-apply-20261008.py'))
a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report=m.load(m.RUN/'verification-after-wave-63.json')
 assert report['verified_new_artworks']==6918 and report['institutions_with_new_records_or_reconciled_holdings']==178 and not report['unrelated_coverage_changes_since_prior_report']
 p,digest=a.validate_plan()
 with m.connect() as db:verified=a.verify(db,p,digest)
 logsroot=Path('/Users/vadimdulub/Library/Logs');prefix='artline-france-eighth-'
 tests=(logsroot/(prefix+'tests-20261008.log')).read_text();assert 'Ran 32 tests' in tests and tests.rstrip().endswith('OK')
 assert (logsroot/(prefix+'replay-20261008.log')).read_text().strip()=='Unchanged replay: zero writes'
 logs={v.name:dict(path=str(v),sha256=sha(v)) for v in sorted(logsroot.glob(prefix+'*-20261008.log')) if v.name!=prefix+'delivery-20261008.log'}
 q=m.load(a.RUN/'selected-metadata-queue-001.json');selected={v['source_id'] for v in q['selected']};held={v['source_id'] for v in q['held']}-selected
 assert len(selected)==265 and len(held)==4208 and len(selected|held)==4473
 assert not (a.RUN/'checks-001.json').exists()
 m.save(a.RUN/'checks-001.json',dict(at=m.now(),new_offline_tests_passed=32,historical_tests_passed=1046,cumulative_verified_tests=1078,historical_tests_rerun=False,replay_zero_writes=True,all_workers_completed=True,new_selected_sources=265,captured_review_holds=19,unique_unselected_or_index_held=4208,identity_version='003; all literal facts and indexed comparisons recomputed',logs=logs,other_job_totals_separate=True))
 rows=report['france_eighth_museum_changes']
 table='| Museum | Added | Linked before → after | Eligible before → after |\n| --- | ---: | ---: | ---: |\n'+'\n'.join('| '+v['name']+' | '+str(v['new'])+' | '+str(v['linked_before'])+' → '+str(v['linked_after'])+' | '+str(v['eligible_before'])+' → '+str(v['eligible_after'])+' |' for v in rows)
 root=m.RUN/'README.md';cp=m.load(a.CHECKPOINT);relative=str(root.relative_to(m.ROOT));pin=next(v for v in cp['artifacts'] if v['path']==relative);assert sha(root)==pin['sha256']
 backup=m.BACKUP/'france-eighth-root-readme-before-001.json.gz';assert not backup.exists();m.save(backup,dict(at=m.now(),path=relative,sha256=sha(root),text=root.read_text()));change=dict(path=relative,before_sha256=pin['sha256'],backup_path=str(backup),backup_sha256=sha(backup))
 types=collections.Counter(v['facts']['work_type'] for v in p['records']);kindtext=', '.join(str(v)+' '+k for k,v in sorted(types.items()))
 detail='''# Eighth French museum pass — 8 October 2026

Added **246 real local artwork records**, all in review. La Châtre, Arbois, Fabre and Nice now exceed 100 eligible artworks. Montargis remains below 100. The preferred 200 target remains unfinished for all five.

'''+table+'''

Types: '''+kindtext+'''. The pinned Joconde index contains 4,783 rows for these museums, including 4,473 source identities not already known in the database. One bounded metadata queue selected 265 records, captured in seven HTTP 200 batches from the official national catalogue API. Individual review approved 246 and held 19. Another 4,208 source leads remain held at selection or unreviewed. Montargis supplied only five new records passing the initial checks, of which three were approved. No quota override was used.

The final read-only identity scope contains 43,511 artworks and 90,809 citations. All 265 literal current records and indexed comparisons were recomputed. Additional names from signatures, previous attributions, copy models and source notes broadened comparison searches. Japanese generation names and romanization variants are comparison terms only; no artist authority was created or assigned. The final comparator separates French, Japanese and transliterated title components from repeated catalogue labels, retaining the full original titles in storage. Earlier comparator captures and code remain preserved.

Physical-object review distinguishes Calamatta's three Sand impressions by date, dimensions, inventory and dedication; Couture prints from their drawing or oil models; Bourdelle's three Duncan sheets by medium, size and inventory; and Gengembre/Cicéri's reclining and running greyhound compositions. The Girodet recto and verso are one sheet. The Choisy butterfly-service addition is one marked plate, not the whole service. The 1970 Jarnoux drawing remains eligible; acquisition numbers beginning 2025 and later artist death dates do not change creation eligibility.

Four saved primary-source comparisons resolve close versions: Brouardel's Arbois sheet is dated 29 January 1910, while the smaller Lisieux board is dated 28 January; Marilhat's Fabre Hakim mosque graphite study differs from the large Louvre RF184 oil; the méharistes graphite canvas differs in medium and inventory from Clermont-Ferrand's close-size oil; and Harpignies's 1871 Fabre watercolour differs from National Gallery NG2256 oil. These extracts are preserved with exact source dependencies in [comparison context](physical-comparison-context-001.json.gz). Existing records were not enriched or rewritten.

Nice additions retain the distinction between individual series images, complete triptychs, incomplete triptychs and a cut harimaze fragment. A triptych is counted as one catalogued composition. The Fusatane record listing an extra central impression is held for unit reconciliation. Eiri's source explicitly describes a twentieth-century copy of an Edo original: its object-level label is qualified as after Eiri, with the original label, description and derivation retained. Sadanobu III is taken from the current source, which differs from the older index. Seihō's original-versus-1935-reissue uncertainty remains within the source's first-half-century period; no edition is invented. Unknown dimensions, unnamed makers, uncertain sitters and source generation-number discrepancies remain visible in evidence.

The 19 holds cover unresolved duplicates, contradictory physical dates, uncertain reproduction chronology, ambiguous object groupings and a functional cadastral plan requiring artwork-scope review. In particular, the sparse Janssens gallery record cannot yet be assigned to either Montargis canvas. Asselin's 1837 headline is not silently corrected to 1937. Burdy's two possible makers are not converted into a joint attribution. Source acquisition and ownership labels remain literal, including pending-transfer notes; collection evidence is distinct from legal title and current display.

The [individual decisions](editorial-reviewed-001.json.gz), [plan](france-eighth-additions-001-plan.json.gz), [application receipt](france-eighth-additions-001-applied.json), [wave63 verification](../../verification-after-wave-63.json) and [checkpoint](delivery-checkpoint-001.json) record the atomic local additions. Exact readback verifies each new artwork, identifier, citation and accepted collection-holding assertion. Unchanged snapshots protect '''+str(verified['protected_existing_records'])+''' comparison/scope records and all 7,457 prior campaign objects, including their media, creator links, citations, holdings and publication states. The initial target-museum scope contains 319 existing artworks. Replay wrote nothing. No images, publication or current-display assertions were added.

Thirty-two fresh offline tests passed; 1,046 historical checks remain pinned, giving 1,078 cumulative verified checks. Historical tests were not all rerun. These tests do not establish ten-million-row performance. Backups and execution logs remain under Library; previous campaign README bytes were preserved before this update.

Campaign totals: **6,918 new artworks and 785 existing-record holding links across 178 expanded institutions**. Arbois, Fabre and Nice are newly expanded in this campaign. New records cover 175 museums plus Barnes; source-pass totals remain 350 museums plus Barnes. The latest audit has **1,167 canonical museums below 100 linked records** and **1,288 below 200**. Linked records, eligible dates and distinct physical-object reconciliation remain separate measures. The overall goal remains active and unfinished. The separate minimum-100 job remains terminal and unchanged with separate totals. The Baltimore access hold remains in force; no retry or alternate route was attempted.
'''
 assert not (a.RUN/'README.md').exists();(a.RUN/'README.md').write_text(detail)
 old=root.read_text();split=old.index('\n## Added works')
 intro=old[:split].replace('6,672','6,918').replace('172 local museums','175 local museums').replace('expand 175 institutions','expand 178 institutions').replace('1,171','1,167').replace('after-wave-62','after-wave-63')
 lines=old[split:].splitlines();ix=next(i for i,v in enumerate(lines) if v.startswith('| Joconde — seventh five-museum'))
 lines.insert(ix+1,'| Joconde — eighth five-museum selections, current official records | 246 | 5 museums; 3 newly expanded |')
 ix=next(i for i,v in enumerate(lines) if v.startswith('| Distinct new-record campaign total |'));lines[ix]='| Distinct new-record campaign total | **6,918** | **176 collections** |'
 section='''

## Eighth five-museum pass — 8 October continuation

The [eighth five-museum pass](native/france-eighth-minimum-20261008/README.md) added **246 review records** from 265 current Joconde records. Nineteen unresolved cases remain held; 4,208 other new source identities remain held or unselected.

'''+table+'''

La Châtre, Arbois, Fabre and Nice cross 100 eligible artworks. Montargis remains below 100; all five preferred-200 targets remain unfinished. Review distinguishes editions, copies, preparatory drawings, artist generations and incomplete compositions, preserving unknown fields and literal source evidence. The final identity scope covers 43,511 artworks and 90,809 citations. All selected facts and comparisons were recomputed, 32 fresh tests passed and replay wrote nothing. Existing records remain unchanged.

The [wave63 verification](verification-after-wave-63.json) and [checkpoint](native/france-eighth-minimum-20261008/delivery-checkpoint-001.json) confirm **6,918 additions and 785 existing-record links across 178 expanded institutions**. Source-pass totals remain 350 museums plus Barnes. There are **1,167 canonical museums below 100 linked works** and **1,288 below 200**. The goal remains active; the separate minimum-100 job remains unchanged and separately counted.
'''
 root.write_text(intro+'\n'.join(lines)+'\n'+section);change['after_sha256']=sha(root)
 m.save(a.RUN/'readme-supersessions-001.json',dict(at=m.now(),changes=[change],policy='Intentional wave63 progress update; previous root README bytes retained in Library. Earlier source evidence, plans, reports and code remain immutable. Eighth-pass README is new.'))
 print('Wave63 documentation verified; prior root README retained in Library',flush=True)
if __name__=='__main__':main()
