"""Document wave65 and preserve the campaign README preimage."""
import collections,hashlib,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-tenth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report=m.load(m.RUN/'verification-after-wave-65.json');assert report['verified_new_artworks']==7454 and report['institutions_with_new_records_or_reconciled_holdings']==187 and not report['unrelated_coverage_changes_since_prior_report']
 p,digest=a.validate_plan()
 with m.connect() as db:verified=a.verify(db,p,digest)
 logsroot=Path('/Users/vadimdulub/Library/Logs');prefix='artline-france-tenth-'
 for name,count in [('tests',24),('context-tests',25)]:
  text=(logsroot/(prefix+name+'-20261008.log')).read_text();assert ('Ran '+str(count)+' tests') in text and text.rstrip().endswith('OK')
 assert (logsroot/(prefix+'replay-20261008.log')).read_text().strip()=='Unchanged replay: zero writes'
 logs={v.name:dict(path=str(v),sha256=sha(v)) for v in sorted(logsroot.glob(prefix+'*-20261008.log')) if v.name!=prefix+'delivery-20261008.log'}
 qs=[m.load(a.RUN/('selected-metadata-queue-00'+str(i)+'.json')) for i in [1,2]]
 selected={v['source_id'] for q in qs for v in q['selected']};held={v['source_id'] for q in qs for v in q['held']}-selected
 assert (len(selected),len(held),len(selected|held))==(331,3102,3433)
 assert not (a.RUN/'checks-001.json').exists()
 m.save(a.RUN/'checks-001.json',dict(at=m.now(),new_offline_tests_passed=49,context_tests_passed=25,physical_identity_tests_passed=24,historical_tests_passed=1126,cumulative_verified_tests=1175,historical_tests_rerun=False,replay_zero_writes=True,all_workers_completed=True,new_selected_sources=331,captured_review_holds=114,unique_unselected_or_index_held=3102,identity_version='002; all literal facts and indexed comparisons recomputed',logs=logs,other_job_totals_separate=True,preparation_notes='First bounded queue selected221. Bayonne source-city reconciliation preserved missing database city and enabled110 additional selections in a separate pinned queue/capture. Initial query and validator retained; supplemental maker/model terms broadened final comparisons. No failed import or fixture write.'))
 rows=report['france_tenth_museum_changes'];table='| Museum | Added | Linked before → after | Eligible before → after |\n| --- | ---: | ---: | ---: |\n'+'\n'.join('| '+v['name']+' | '+str(v['new'])+' | '+str(v['linked_before'])+' → '+str(v['linked_after'])+' | '+str(v['eligible_before'])+' → '+str(v['eligible_after'])+' |' for v in rows)
 root=m.RUN/'README.md';cp=m.load(a.CHECKPOINT);relative=str(root.relative_to(m.ROOT));pin=next(v for v in cp['artifacts'] if v['path']==relative);assert sha(root)==pin['sha256']
 backup=m.BACKUP/'france-tenth-root-readme-before-001.json.gz';assert not backup.exists();m.save(backup,dict(at=m.now(),path=relative,sha256=sha(root),text=root.read_text()));change=dict(path=relative,before_sha256=pin['sha256'],backup_path=str(backup),backup_sha256=sha(backup))
 types=collections.Counter(v['facts']['work_type'] for v in p['records']);kindtext=', '.join(str(v)+' '+k for k,v in sorted(types.items()))
 detail='''# Tenth French museum pass — 8 October 2026

Added **217 real local artwork records**, all in review, across five museums newly expanded in this campaign. Strasbourg's Cabinet des estampes et des dessins reaches 104 eligible works and Bayonne's Musée Bonnat-Helleu reaches 123. Belfort, Saint-Denis and Honfleur remain below 100. All five preferred-200 targets remain unfinished.

'''+table+'''

Types: '''+kindtext+'''. The pinned official Joconde index has 3,615 rows for these museums, including 3,433 source identities not already catalogued. Two bounded queues selected 331 distinct objects, captured in nine HTTP 200 metadata batches. Individual review approved 217 and held 114. Another 3,102 distinct source leads remain held at selection or unreviewed; overlapping queue holds are not added together. No image downloads or attachments were made.

The [museum reconciliation](museum-name-reconciliation-002.json) preserves official Museofile context for all five exact codes, cities, names and collection destinations. Belfort's history and fine-arts venues are described as one administrative entity in Museofile; Jardot and other collections are not merged. Saint-Denis is the Paul Eluard institution at its documented address, not another similarly named museum. Honfleur's municipal and Eugène Boudin labels reconcile to M0661. Strasbourg CEDS M0013 remains separate from MAMCS M0016. Bayonne's database city is missing: the verified source city Bayonne is used for source matching while the institution record remains unchanged. Literal ownership labels are retained; historic deposit aliases do not replace current collection evidence. Louvre-owned or deposited Bayonne drawings were excluded at selection.

Creation eligibility is checked against explicit source dates and periods. Parenthetical circa years/ranges use independently stated eligible periods for conservative bounds, without an invented tolerance or single year. Compound periods retain their literal labels and full bounds. Unknown lower bounds on before-dates remain unknown. The 25 context/date tests cover these cases and exact museum destination guards.

The final identity scope contains **44,668 existing artworks and 95,735 citations**. All 331 literal current source records and indexed comparisons were recomputed. The initial scope and code remain preserved; additional surname variants and source-note models broaden the final query. The [66 primary comparator records](physical-comparison-context-001.json.gz) retain exact saved official evidence, source hashes and unresolved comparator IDs. Sparse Helleu records for Alice, baby Paulette, a woman in a boat and the Dieppe church resolve to oils, physically distinct from the selected paper works. Vannes head drawing 34.2.2 and portrait print 92.2.1 have distinct sheet sizes and acquisition histories from the Howard-Johnston donation sheets. Missing source dimensions remain unknown.

Physical units were reviewed individually. A recto-verso drawing or print sheet counts once regardless of its number of motifs. Six CMNI 3017 drawings have individual inventories and sheet dimensions despite sharing a mount. Six 1914 auction sketches were explicitly separate fragments formerly glued onto a Biron catalogue page; neither the shared support nor its frame is counted as an extra work. Queen Alexandra's black and colour impressions and the two Noailles impressions have distinct physical records. Source attribution, model, publisher and printer qualifications remain object-level labels without new artist authorities. The lithographic reproduction after Helleu is classified as a print from the explicit physical description; its original drawing-domain label remains in the evidence.

The **114 research holds** include four exact-inventory Strasbourg duplicates already linked to MAMCS, unresolved sparse possible duplicates, contradictory dates or techniques, and mixed-document frames. Twenty-two Saint-Denis frames contain letters, photographs and multiple artworks whose component identities need reconciliation. Fifty-two Lançon war-series impressions remain held because 1870 scene inscriptions may not date the physical print. The [BnF primary catalogue](https://catalogue.bnf.fr/rechercher.do?index=AUT3&numNotice=14949296) lists corresponding publications in 1876; this establishes the need to distinguish scene and edition chronology, not the edition or creation date of each Saint-Denis impression. The [captured source context](lancon-chronology-web-001.json) records the lookup. None of these dates were silently rewritten.

The [individual decisions](editorial-reviewed-001.json.gz), [plan](france-tenth-additions-001-plan.json.gz), [application receipt](france-tenth-additions-001-applied.json), [wave65 verification](../../verification-after-wave-65.json) and [checkpoint](delivery-checkpoint-001.json) document the atomic additions. Exact readback verifies each new artwork, native identifier, citation and accepted collection-holding assertion. All **2,149 protected existing comparison records**, **8,022 prior campaign records** and the five institution records remain unchanged. The initial target-museum scope contains 187 existing records. Replay wrote nothing. No images, artist links, publication or current-display claims were added.

**49 fresh offline checks passed:** 25 museum/date/context and 24 physical-identity checks. The 1,126 historical checks remain pinned, giving 1,175 cumulative verified checks; historical tests were not all rerun. This is not evidence of ten-million-row query performance. Backups and logs remain under Library; the previous campaign README bytes were saved before updating progress.

Campaign totals are **7,454 new artworks and 785 existing-record holding links across 187 expanded institutions**. New records cover 184 museums plus Barnes. Source-pass totals remain 350 museums plus Barnes. The latest audit has **1,161 canonical museums below 100 linked records** and **1,288 below 200**. Linked records and creation-eligible artworks remain separate measures. The goal remains active and unfinished. The separate minimum-100 job remains terminal, unchanged and separately counted. The Baltimore access hold remains in force; no retry or alternate route was attempted.
'''
 assert not (a.RUN/'README.md').exists();(a.RUN/'README.md').write_text(detail)
 old=root.read_text();split=old.index('\n## Added works');intro=old[:split].replace('7,237','7,454').replace('179 local museums','184 local museums').replace('expand 182 institutions','expand 187 institutions').replace('1,163','1,161').replace('after-wave-64','after-wave-65')
 lines=old[split:].splitlines();ix=next(i for i,v in enumerate(lines) if v.startswith('| Joconde — ninth five-museum'));lines.insert(ix+1,'| Joconde — tenth five-museum selections, current official records | 217 | 5 newly expanded museums |')
 ix=next(i for i,v in enumerate(lines) if v.startswith('| Distinct new-record campaign total |'));lines[ix]='| Distinct new-record campaign total | **7,454** | **185 collections** |'
 section='''

## Tenth five-museum pass — 8 October continuation

The [tenth five-museum pass](native/france-tenth-minimum-20261008/README.md) added **217 review records** from 331 current Joconde records. There are 114 captured research holds and 3,102 distinct further source leads held or unselected.

'''+table+'''

Strasbourg CEDS and Bayonne cross 100 eligible artworks. Belfort, Saint-Denis and Honfleur remain below 100; all preferred-200 targets remain unfinished. Museum reconciliation preserves missing Bayonne place metadata and keeps Strasbourg CEDS separate from MAMCS. Exact-inventory duplicates, mixed-document frames and uncertain physical print dates remain held. Saved primary comparisons distinguish sparse oil records from paper works and separate print impressions. All 331 source facts and comparisons reproduced correctly, 49 fresh tests passed, and replay wrote nothing. Existing catalogue records are unchanged.

The [wave65 verification](verification-after-wave-65.json) and [checkpoint](native/france-tenth-minimum-20261008/delivery-checkpoint-001.json) confirm **7,454 additions and 785 existing-record links across 187 expanded institutions**. Source-pass totals remain 350 museums plus Barnes. There are **1,161 canonical museums below 100 linked works** and **1,288 below 200**. The goal remains active; the separate minimum-100 job remains unchanged and separately counted.
'''
 root.write_text(intro+'\n'.join(lines)+'\n'+section);change['after_sha256']=sha(root)
 m.save(a.RUN/'readme-supersessions-001.json',dict(at=m.now(),changes=[change],policy='Intentional wave65 progress update; previous root README bytes preserved in Library. Earlier source evidence, plans, reports and code remain immutable. Tenth-pass README is new.'))
 print('Wave65 documentation verified; prior root README retained in Library',flush=True)
if __name__=='__main__':main()
