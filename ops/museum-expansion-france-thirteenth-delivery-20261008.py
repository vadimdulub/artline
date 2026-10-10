"""Document wave 68; preserve the previous campaign README in Library."""
import collections,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-thirteenth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    report=m.load(m.RUN/'verification-after-wave-68.json');assert report['verified_new_artworks']==8565 and report['institutions_with_new_records_or_reconciled_holdings']==195 and not report['unrelated_coverage_changes_since_prior_report']
    p,digest=a.validate_plan()
    with m.connect() as db:verified=a.verify(db,p,digest)
    logsroot=Path('/Users/vadimdulub/Library/Logs');prefix='artline-france-thirteenth-'
    for name,count in [('tests',30),('context-tests',29)]:
        text=(logsroot/(prefix+name+'-20261008.log')).read_text();assert ('Ran '+str(count)+' tests') in text and text.rstrip().endswith('OK')
    assert (logsroot/(prefix+'replay-20261008.log')).read_text().strip()=='Unchanged replay: zero writes'
    logs={v.name:dict(path=str(v),sha256=sha(v)) for v in sorted(logsroot.glob(prefix+'*-20261008.log')) if v.name!=prefix+'delivery-20261008.log'}
    q=m.load(a.RUN/'selected-metadata-queue-001.json');discovery=m.load(a.RUN/'five-museum-discovery-001.json.gz');selected={v['source_id'] for v in q['selected']};held={v['source_id'] for v in q['held']};fresh={v['raw_source_record']['Reference'] for v in discovery['rows'] if not v['already_known']}
    assert (len(selected),len(held),len(fresh))==(620,16762,17382) and selected.isdisjoint(held) and selected|held==fresh
    assert not (a.RUN/'checks-001.json').exists()
    m.save(a.RUN/'checks-001.json',dict(at=m.now(),new_offline_tests_passed=59,context_tests_passed=29,physical_identity_tests_passed=30,historical_tests_passed=1277,cumulative_verified_tests=1336,historical_tests_rerun=False,replay_zero_writes=True,all_workers_completed=True,new_selected_sources=620,captured_review_holds=49,unique_unselected_or_index_held=16762,prior_captured_holds_excluded=0,identity_version='002; all literal facts and indexed comparisons recomputed',logs=logs,other_job_totals_separate=True,preparation_notes='Five Museofile and sixteen current selected metadata batches returned HTTP 200. Source fields remain literal. Two reviewed date derivations apply only to new records; original modeling/supposed dates remain in audit evidence. Nineteen André François source-biography conflicts are explicit. Final context pins NGA primary comparator rows, museum authority capture and 56 within-selection comparison pairs. Offline checks use no database fixtures. No image downloading or attachment. Orsay Coubertin HTTP 403 and Baltimore access holds preserved without retries or alternate routes.'))
    rows=report['france_thirteenth_museum_changes'];table='| Museum | Added | Linked before → after | Eligible before → after |\n| --- | ---: | ---: | ---: |\n'+'\n'.join('| '+v['name']+' | '+str(v['new'])+' | '+str(v['linked_before'])+' → '+str(v['linked_after'])+' | '+str(v['eligible_before'])+' → '+str(v['eligible_after'])+' |' for v in rows)
    types=collections.Counter(v['facts']['work_type'] for v in p['records']);kindtext=', '.join(str(v)+' '+k for k,v in sorted(types.items()))
    root=m.RUN/'README.md';cp=m.load(a.CHECKPOINT);relative=str(root.relative_to(m.ROOT));pin=next(v for v in cp['artifacts'] if v['path']==relative);assert sha(root)==pin['sha256']
    backup=m.BACKUP/'france-thirteenth-root-readme-before-001.json.gz';assert not backup.exists();m.save(backup,dict(at=m.now(),path=relative,sha256=sha(root),text=root.read_text()));change=dict(path=relative,before_sha256=pin['sha256'],backup_path=str(backup),backup_sha256=sha(backup))
    detail='''# Thirteenth French museum pass — 8 October 2026

Added **571 real local artwork records**, all in review. All five museums now exceed 100 eligible artworks. The wider goal remains active and unfinished.

'''+table+'''

Types: '''+kindtext+'''. The official national catalogue discovery contains 17,432 records for these five museums, including 17,382 source identities not already represented. A bounded selection of 620 records was captured in sixteen HTTP 200 metadata batches. Individual review approved 571 and retained 49 holds. Another 16,762 leads remain index-held or unselected, not approved additions. No images were downloaded or attached.

Five official Museofile captures support [museum reconciliation](museum-name-reconciliation-001.json). The Musée de l’Image is distinguished from other Épinal collections, and the Strasbourg illustration centre is reconciled to the Tomi Ungerer museum. Exact institution codes, city, catalogue destination and source ownership labels support each holding. A collection holding does not establish current display.

The final identity scope covers **58,245 existing artworks and 130,852 citations**. All 620 literal source records and comparisons were independently recomputed. Maker variants, semicolon-separated titles and selected translations are search evidence, not catalogue replacements. The [final comparison bundle](physical-comparison-context-002.json.gz), [manual primary supplement](manual-comparison-supplement-001.json.gz) and [additional object context](final-object-context-001.json.gz) preserve physical-object evidence, including the official NGA snapshot and 56 within-selection comparison pairs.

The Bouchard Comédie bronze’s source commentary explicitly identifies a 1937 cast and an April 1937 invoice, while the headline dates the 1936 model. Its new record uses the cast year and retains the model date and source text in the derivation audit. The Delaporte print’s 1837 date is explicitly a supposition: display remains qualified and structured bounds use the separately supplied second quarter of the nineteenth century. These are selected new-record derivations; existing catalogue dates are unchanged.

Nineteen André François notices repeat Ungerer’s life dates. The captured Centre Pompidou authority supplies conflicting dates of 1915–2005. The new object-level maker labels preserve the supplied name and explicitly flag the biography conflict, without importing a false biography or creating an artist authority. Qualified copies, founders, publishers, unknown makers and historical catalogue wording remain explicit. Robert Weaver’s oil-and-ink portrait retains the source graphic-arts domain while its physical technique supports painting type.

Individual physical objects are counted once. Recto/verso drawings, multi-scene sheets, a sculpture with multiple components and campaign designs remain single inventory objects. The five Electric Circus drawings have distinct compositions and dimensions. St Moritz designs have different poses and sizes. Related print impressions require independent acquisition histories, marks or state evidence; Daumier’s French sheet and the NGA Corcoran impression have separate documented provenance. A flattened inventory collision between MM 84 11 4 and MM 84 1 14 is resolved by their literal inventories and bronze portrait versus large plaster statue. No edition size, book illustration count or number of figures inflates museum holdings.

The 49 holds preserve unresolved cast dates, possible duplicate notices, source chronology conflicts, workshop molds and uncertain album/multi-sheet units. A Rodin Victor Hugo cast remains unresolved against a physically similar existing plaster. Later-cast and post-1970 evidence is not overridden to meet the quota. Explicit before dates retain unknown lower bounds. The Tomi Ungerer studies dated 1970 remain eligible even when their broader project continued after 1970.

The [review decisions](editorial-reviewed-001.json.gz), [transaction plan](france-thirteenth-additions-001-plan.json.gz), [application receipt](france-thirteenth-additions-001-applied.json), [wave 68 verification](../../verification-after-wave-68.json) and [checkpoint](delivery-checkpoint-001.json) record the changes. Exact readback verified all 571 artworks, source identifiers, citations and accepted holding assertions. All 51 initial target-museum records, '''+str(verified['protected_existing_records'])+''' protected comparison records, 8,779 prior campaign objects and five institutions remain unchanged. Replay wrote nothing. No artist links, images, publication or display claims were added.

**59 offline checks passed:** 29 context/date tests and 30 physical-identity regressions. The 1,277 pinned historical checks bring the cumulative record to 1,336; they were not all rerun. This does not constitute a ten-million-row performance proof. Backups and logs are under Library; the previous root README is preserved there.

Campaign totals: **8,565 new artworks and 785 existing-record holding links across 195 expanded institutions**. New records cover 192 museums plus Barnes. Source-pass totals remain 350 museums plus Barnes. **1,155 canonical museums remain below 100 linked records and 1,285 below 200.** Linked and eligible counts remain distinct. The separate minimum-100 job remains terminal, unchanged and separately counted. Baltimore and the denied Orsay Coubertin page remain access holds; no retry or alternate retrieval was attempted.
'''
    assert not (a.RUN/'README.md').exists();(a.RUN/'README.md').write_text(detail)
    old=root.read_text();split=old.index('\n## Added works');intro=old[:split].replace('7,994','8,565').replace('188 local museums','192 local museums').replace('expand 191 institutions','expand 195 institutions').replace('1,160','1,155').replace('after-wave-67','after-wave-68')
    lines=old[split:].splitlines();ix=next(i for i,v in enumerate(lines) if v.startswith('| Joconde — twelfth five-museum'));lines.insert(ix+1,'| Joconde — thirteenth five-museum review, current official records | 571 | 5 museums, 4 newly expanded |');ix=next(i for i,v in enumerate(lines) if v.startswith('| Distinct new-record campaign total |'));lines[ix]='| Distinct new-record campaign total | **8,565** | **193 collections** |'
    section='''

## Thirteenth five-museum pass — 8 October continuation

The [thirteenth review](native/france-thirteenth-minimum-20261008/README.md) added **571 review records** from 620 current Joconde notices. Forty-nine cases remain held and 16,762 additional index leads remain outside the approved selection.

'''+table+'''

All five museums now exceed 100 eligible artworks. Dates, physical versions, qualified creators and individual sheets were checked; no book, campaign or edition was counted as multiple artworks without separate object evidence. All source facts and comparisons recomputed, 59 checks passed, exact readback succeeded and replay wrote nothing.

The [wave 68 verification](verification-after-wave-68.json) confirms **8,565 additions and 785 existing-record links across 195 expanded institutions**. Source-pass totals remain 350 museums plus Barnes. **1,155 canonical museums remain below 100 linked records and 1,285 below 200.** The broader goal remains active. The separate minimum-100 job is unchanged and separately counted.
'''
    root.write_text(intro+'\n'.join(lines)+'\n'+section);change['after_sha256']=sha(root)
    m.save(a.RUN/'readme-supersessions-001.json',dict(at=m.now(),changes=[change],policy='Intentional wave68 progress update; prior root README preserved in Library. Earlier evidence, plans, reports and scripts unchanged.'))
    print('Wave68 documentation verified; prior root README retained in Library',flush=True)
if __name__=='__main__':main()
