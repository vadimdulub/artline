"""Document wave64 with preserved campaign README preimage and test receipts."""
import collections,hashlib,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-ninth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report=m.load(m.RUN/'verification-after-wave-64.json');assert report['verified_new_artworks']==7237 and report['institutions_with_new_records_or_reconciled_holdings']==182 and not report['unrelated_coverage_changes_since_prior_report']
 p,digest=a.validate_plan()
 with m.connect() as db:verified=a.verify(db,p,digest)
 logsroot=Path('/Users/vadimdulub/Library/Logs');prefix='artline-france-ninth-'
 for name,count in [('tests-v2',30),('context-tests',18)]:
  text=(logsroot/(prefix+name+'-20261008.log')).read_text();assert ('Ran '+str(count)+' tests') in text and text.rstrip().endswith('OK')
 assert (logsroot/(prefix+'replay-20261008.log')).read_text().strip()=='Unchanged replay: zero writes'
 logs={v.name:dict(path=str(v),sha256=sha(v)) for v in sorted(logsroot.glob(prefix+'*-20261008.log')) if v.name!=prefix+'delivery-20261008.log'}
 q=m.load(a.RUN/'selected-metadata-queue-001.json');selected={v['source_id'] for v in q['selected']};held={v['source_id'] for v in q['held']}-selected
 assert (len(selected),len(held),len(selected|held))==(345,2874,3219)
 assert not (a.RUN/'checks-001.json').exists()
 m.save(a.RUN/'checks-001.json',dict(at=m.now(),new_offline_tests_passed=48,context_tests_passed=18,physical_identity_tests_passed=30,historical_tests_passed=1078,cumulative_verified_tests=1126,historical_tests_rerun=False,replay_zero_writes=True,all_workers_completed=True,new_selected_sources=345,captured_review_holds=26,unique_unselected_or_index_held=2874,identity_version='002; all literal facts and indexed comparisons recomputed',logs=logs,other_job_totals_separate=True,preparation_notes='Initial context extraction assertion was corrected for citation source-ID prefixes; source facts unchanged. Initial Nadar test expected a generic uncertainty word but the reviewed labels state the precise name/date conflict; assertion corrected. Read-only preparation interrupted before backup/plan creation to add both fresh test files to evidence pins. Completed v2 logs retained alongside initial logs.'))
 rows=report['france_ninth_museum_changes']
 table='| Museum | Added | Linked before → after | Eligible before → after |\n| --- | ---: | ---: | ---: |\n'+'\n'.join('| '+v['name']+' | '+str(v['new'])+' | '+str(v['linked_before'])+' → '+str(v['linked_after'])+' | '+str(v['eligible_before'])+' → '+str(v['eligible_after'])+' |' for v in rows)
 root=m.RUN/'README.md';cp=m.load(a.CHECKPOINT);relative=str(root.relative_to(m.ROOT));pin=next(v for v in cp['artifacts'] if v['path']==relative);assert sha(root)==pin['sha256']
 backup=m.BACKUP/'france-ninth-root-readme-before-001.json.gz';assert not backup.exists();m.save(backup,dict(at=m.now(),path=relative,sha256=sha(root),text=root.read_text()));change=dict(path=relative,before_sha256=pin['sha256'],backup_path=str(backup),backup_sha256=sha(backup))
 types=collections.Counter(v['facts']['work_type'] for v in p['records']);kindtext=', '.join(str(v)+' '+k for k,v in sorted(types.items()))
 detail='''# Ninth French museum pass — 8 October 2026

Added **319 real local artwork records**, all in review. Châlons-en-Champagne, Metz, Bernay and the Paris Musée Hébert collection now exceed 100 eligible artworks. Brest reaches 79. The preferred 200 target remains unfinished for all five.

'''+table+'''

Types: '''+kindtext+'''. The pinned Joconde index contains 3,525 records for these museums, including 3,219 source identities not already known in the database. A bounded queue selected 345 records, captured in nine HTTP 200 batches from the official national catalogue API. Individual review approved 319 and held 26; another 2,874 source leads remain held at selection or unreviewed. Brest had only 30 records passing the initial selection checks, of which 28 were approved. No quota override was used.

Official museum context is preserved in [museum identity reconciliation](museum-name-reconciliation-001.json). Metz's literal public intermunicipal ownership label is accepted only for exact museum code M0529, city, official name and collection destination. The parser's temporary commune token is not stored as source evidence or asserted as legal title. Châlons' municipal museum is reconciled to the Musée des Beaux-Arts et d'Archéologie at Place Godart; Garinet and Notre-Dame-en-Vaux remain separate venues. Historic Garinet testament provenance in individual records does not override their explicit current M0307 collection designation. Bernay's municipal and beaux-arts labels resolve to M0701. Other owners, deposits, missing objects, private ownership and ambiguous plural-venue labels fail the scoped guards.

The Paris Musée Hébert source explicitly says closed. A government reply identifies the national collection and its administration by Orsay, but this does not establish current display or merge the collection into Orsay or La Tronche. New records describe the documented collection connection only. Dates in the source and literal legal/source-use labels remain unchanged.

The final read-only identity scope contains **78,307 artworks and 172,222 citations**. All 345 literal current records and indexed comparisons were recomputed. Additional terms include former attributions, signatures, copy models and maker spelling variants. Some legacy normalized artist names retain accents, so comparison queries also include literal accented source spellings. This brought additional Hébert records into scope; the original comparison capture and code remain preserved. No artist authority was created or assigned.

Ten exact saved primary-source comparisons are preserved in [physical comparison context](physical-comparison-context-001.json.gz). Separate Bernard, Gauguin, Ibels, Maufra, Flipart, Nicolas de Son, Braque and Rouault impressions are supported by physical descriptions, inscriptions, support differences and distinct collection acquisition histories. Where the comparison source has no dimensions, that absence is retained; provenance is stated as the basis rather than invented measurements. Braque's Metz China-paper proof differs from Dieppe's Arches-paper Laurens gift. Hébert's five-prow watercolour, 26.8 × 37.4 cm, differs from the existing two-boat oil on canvas, 27.4 × 45.3 cm, dated 28 July 1872. The title's word “suite” describes the represented prows, not a five-sheet portfolio.

Physical units are reviewed individually. Hébert sheets sharing a mount remain independently inventoried drawings with their own dimensions and inscriptions. The two same-size Bosco sheets carry different carton numbers and mount associations. A Bernard recto and verso count as one physical sheet. Distinct Manessier Cantique impressions are separated from held colophon-bearing books or multi-sheet suites. Bernay's anonymous decorated plate is one measured vessel, not the whole service; Atalaya drawings of decorative objects remain drawings.

Object-level labels retain contested or qualified authorship. Le Pautre is identified as plate engraver for the source's 1835 sycamore impression, not a nineteenth-century living creator. Née's signature dispute, the contested Girodet attribution, the Van Tilborch source-name conflict and Nadar's conflicting forenames/lifespans remain explicit. Anonymous Le Nain pastiche and copies after Rubens or possibly Boucher preserve their qualifications. No biography or certain authorship is invented. The 1970 Chillida, Giguet and Reuter prints are eligible at the inclusive cutoff; acquisition dates and later artist death dates do not alter creation eligibility. Unknown lower bounds, missing dimensions and unnamed makers remain unknown.

The 26 holds include sparse same-title possible duplicates, two-print and portfolio units, contradictory inscriptions or creation dates, uncertain restrikes and unresolved physical-version or attribution conflicts. These include Jouanny landscapes, two Reichel Compositions, Hébert's Pasqua Maria, Manessier suites, a Vaucanu dedication dated after the named maker's death, and conflicting Hébert dates. Holds remain research evidence and were not inserted as newly resolved objects.

The [individual decisions](editorial-reviewed-001.json.gz), [plan](france-ninth-additions-001-plan.json.gz), [application receipt](france-ninth-additions-001-applied.json), [wave64 verification](../../verification-after-wave-64.json) and [checkpoint](delivery-checkpoint-001.json) document the atomic local additions. Exact readback verifies each new artwork, identifier, citation and accepted collection-holding assertion. Unchanged snapshots protect '''+str(verified['protected_existing_records'])+''' comparison/scope records and all 7,703 prior campaign objects, including their media, creator links, citations, holdings and publication states. The initial museum scope contains 316 existing artworks. Replay wrote nothing. No images, publication or current-display assertions were added.

Forty-eight fresh offline tests passed: 18 museum/date/context checks and 30 physical-identity regressions. The 1,078 historical checks remain pinned, giving 1,126 cumulative verified checks; historical tests were not all rerun. These checks do not establish ten-million-row performance. Backups and execution logs remain under Library. Previous campaign README bytes were preserved before this update.

Campaign totals: **7,237 new artworks and 785 existing-record holding links across 182 expanded institutions**. Châlons, Metz, Bernay and Paris Hébert are newly expanded in this campaign. New records cover 179 museums plus Barnes; source-pass totals remain 350 museums plus Barnes. The latest audit has **1,163 canonical museums below 100 linked records** and **1,288 below 200**. Linked records, eligible dates and distinct physical-object reconciliation remain separate measures. The overall goal remains active and unfinished. The separate minimum-100 job remains terminal and unchanged with separate totals. The Baltimore access hold remains in force; no retry or alternate route was attempted.
'''
 assert not (a.RUN/'README.md').exists();(a.RUN/'README.md').write_text(detail)
 old=root.read_text();split=old.index('\n## Added works')
 intro=old[:split].replace('6,918','7,237').replace('175 local museums','179 local museums').replace('expand 178 institutions','expand 182 institutions').replace('1,167','1,163').replace('after-wave-63','after-wave-64')
 lines=old[split:].splitlines();ix=next(i for i,v in enumerate(lines) if v.startswith('| Joconde — eighth five-museum'))
 lines.insert(ix+1,'| Joconde — ninth five-museum selections, current official records | 319 | 5 museums; 4 newly expanded |')
 ix=next(i for i,v in enumerate(lines) if v.startswith('| Distinct new-record campaign total |'));lines[ix]='| Distinct new-record campaign total | **7,237** | **180 collections** |'
 section='''

## Ninth five-museum pass — 8 October continuation

The [ninth five-museum pass](native/france-ninth-minimum-20261008/README.md) added **319 review records** from 345 current Joconde records. Twenty-six unresolved cases remain held; 2,874 other new source identities remain held or unselected.

'''+table+'''

Châlons, Metz, Bernay and Paris Hébert cross 100 eligible artworks. Brest remains at 79; all five preferred-200 targets remain unfinished. Museum aliases are reconciled using exact source identities, location and ownership labels. The closed Hébert collection is not described as on display. Individual review distinguishes print impressions, copies, uncertain maker roles and separate mounted sheets. The final identity scope covers 78,307 artworks and 172,222 citations, including accented artist-name variants. All selected facts and comparisons were recomputed, 48 fresh tests passed and replay wrote nothing. Existing records remain unchanged.

The [wave64 verification](verification-after-wave-64.json) and [checkpoint](native/france-ninth-minimum-20261008/delivery-checkpoint-001.json) confirm **7,237 additions and 785 existing-record links across 182 expanded institutions**. Source-pass totals remain 350 museums plus Barnes. There are **1,163 canonical museums below 100 linked works** and **1,288 below 200**. The goal remains active; the separate minimum-100 job remains unchanged and separately counted.
'''
 root.write_text(intro+'\n'.join(lines)+'\n'+section);change['after_sha256']=sha(root)
 m.save(a.RUN/'readme-supersessions-001.json',dict(at=m.now(),changes=[change],policy='Intentional wave64 progress update; previous root README bytes retained in Library. Earlier source evidence, plans, reports and code remain immutable. Ninth-pass README is new.'))
 print('Wave64 documentation verified; prior root README retained in Library',flush=True)
if __name__=='__main__':main()
