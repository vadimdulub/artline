"""Document wave69 and preserve the prior campaign README in Library."""
import collections,hashlib,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-fourteenth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    report=m.load(m.RUN/'verification-after-wave-69.json');assert report['verified_new_artworks']==9046 and report['institutions_with_new_records_or_reconciled_holdings']==199 and not report['unrelated_coverage_changes_since_prior_report']
    p,digest=a.validate_plan()
    with m.connect() as db:verified=a.verify(db,p,digest)
    logsroot=Path('/Users/vadimdulub/Library/Logs');prefix='artline-france-fourteenth-'
    tests=(logsroot/(prefix+'tests-20261008.log')).read_text();assert 'Ran 20 tests' in tests and tests.rstrip().endswith('OK')
    assert (logsroot/(prefix+'replay-20261008.log')).read_text().strip()=='Unchanged replay: zero writes'
    pagepins=m.load(a.RUN/'native-page-pins-verified-001.json');assert pagepins['checked_native_pages']==599 and pagepins['checked_file_pins']==1797 and pagepins['all_compressed_body_text_receipt_pins_equal'] and pagepins['all_uncompressed_response_hashes_equal'];a.checked(pagepins['context_reference'])
    logs={v.name:dict(path=str(v),sha256=sha(v)) for v in sorted(logsroot.glob(prefix+'*-20261008.log')) if v.name not in [prefix+'delivery-20261008.log',prefix+'checkpoint-20261008.log']}
    q=m.load(a.RUN/'selected-metadata-queue-001.json');discovery=m.load(a.RUN/'five-museum-discovery-001.json.gz');selected={v['source_id'] for v in q['selected']};held={v['source_id'] for v in q['held']};fresh={v['raw_source_record']['Reference'] for v in discovery['rows'] if not v['already_known']}
    assert (len(selected),len(held),len(fresh))==(605,47736,48350) and selected.isdisjoint(held) and selected|held<=fresh and len(fresh-(selected|held))==9
    assert not (a.RUN/'checks-001.json').exists()
    m.save(a.RUN/'checks-001.json',dict(at=m.now(),new_offline_tests_passed=20,historical_tests_passed=1336,cumulative_verified_tests=1356,historical_tests_rerun=False,replay_zero_writes=True,all_workers_completed=True,new_selected_sources=605,captured_review_holds=124,unique_unselected_or_index_held=47736,prior_captured_holds_excluded=9,identity_version='002; all literal facts and comparisons independently recomputed; all newly introduced leads covered by individual supplemental review',checked_native_pages=599,failed_native_page=583,logs=logs,other_job_totals_separate=True,preparation_notes='605 current Joconde notices and599 checked native Paris pages. One timeout has no response body and remains held without retry. Supplemental primary context preserves2268 catalogue records plus a repaired slash-bearing identifier; repair supplements immutable earlier output. Two cancelled Carnavalet transfer aliases were checked against existing identifiers/citations with zero hits. No images or artist-authority writes. Backups and completed logs remain in Library.'))
    rows=report['france_fourteenth_museum_changes'];table='| Museum | Added | Linked before → after | Eligible before → after |\n| --- | ---: | ---: | ---: |\n'+'\n'.join('| '+v['name']+' | '+str(v['new'])+' | '+str(v['linked_before'])+' → '+str(v['linked_after'])+' | '+str(v['eligible_before'])+' → '+str(v['eligible_after'])+' |' for v in rows)
    types=collections.Counter(v['facts']['work_type'] for v in p['records']);kindtext=', '.join(str(v)+' '+k for k,v in sorted(types.items()))
    detail='''# Fourteenth French museum pass — 8 October 2026

Added **481 real local artwork records**, all in review. All five museums now have at least100 eligible artworks. The wider goal remains active and unfinished.

'''+table+'''

Types: '''+kindtext+'''. The bounded selection contains605 current Joconde notices. Individual review approved481 and retained124 holds. Another47,736 leads remain index-held or unselected, with9 earlier selected holds excluded from reselection. The discovery contains48,671 national catalogue records, including48,350 source identities not represented at its snapshot. These are leads, not approved additions. No images were downloaded or attached.

Five Museofile pages and Paris Musées operator evidence support the exact museum-code, name and collection reconciliation. Blank ownership fields and acquisition-only labels remain literal; they do not imply legal title. The Maison de Victor Hugo source combines Paris and Hauteville House in Guernsey, so its accepted holding does not assert a current site, room or display.

The final identity scope covers **61,370 existing artworks and134,514 citations**. All605 literal source records and comparisons were independently recomputed. Native URLs, redirects, historic inventories, translations, shortened titles and additional maker roles expanded the initial comparison. Every new lead affecting an approved candidate has an explicit supplemental decision. Two cancelled Carnavalet records related to the transferred Sand arm and Chopin hand were checked by both node and canonical URLs; no existing identifier/citation matched.

The saved native object evidence contains599 checked Paris pages. Candidate583 timed out without a response body and remains held; it was not retried. The primary-comparison bundle preserves2,268 existing-object catalogue records. Its one unresolved lookup was a helper error that truncated a slash-bearing Joconde identifier: the supplemental bundle resolves the complete identifier against the original checked response, preserving both artifacts. It is not reported as a missing source record.

Materials, sizes and compositions distinguish models from reproductions: Charpentier’s Sand and Monnier’s self-portrait are oils, whereas the selected related works are lithographs. Scheffer’s painting versions are distinct from the selected etchings, lithographs and drawing studies. Native labels preserve attributions, copy/model relationships, engravers, founders, printers and publishers. Three Jules David notices retain the original conflicting national biography in audit evidence while using the exact native object label. No artist authority was created or changed. The failed BnF capture is not authority evidence.

Physical units are counted once. Multi-scene prints and recto/verso sheets remain one record. Bound album folios, shared fashion-volume inventories and unresolved duplicate impressions stay held. Whole independently catalogued sketchbooks count once; a publication title or edition size does not multiply artworks. Unknown lower bounds remain unknown, and no creation date is inferred from acquisition, inventory, publication history or depicted event without source support. Existing dates remain unchanged.

The [review decisions](editorial-reviewed-001.json.gz), [supplemental review](supplemental-review-001.json.gz), [transaction plan](france-fourteenth-additions-001-plan.json.gz), [application receipt](france-fourteenth-additions-001-applied.json), [wave69 verification](../../verification-after-wave-69.json) and [checkpoint](delivery-checkpoint-001.json) record the result. Exact readback verified481 artworks, identifiers, citations and accepted holding assertions. All322 initial target-museum records, '''+str(verified['protected_existing_records'])+''' protected comparison records,9,350 prior campaign records and five institutions remain unchanged. Replay wrote nothing. No images, publication, artist links or current-display claims were added.

**20 offline regression checks passed**, covering source preservation, dates, qualified creators, unresolved impressions, bound units, missing native pages, transfer aliases and rejection of missing comparison decisions. The1,336 pinned historical checks were not rerun, yielding a cumulative record of1,356. These checks do not establish ten-million-row performance. Backups and completed logs are under Library.

Campaign totals: **9,046 new artworks and785 existing-record holding links across199 expanded institutions**. New records cover196 museums plus Barnes. Source-pass totals remain350 museums plus Barnes. **1,152 canonical museums remain below100 linked records and1,283 below200.** Linked and eligible counts remain distinct. The separate minimum-100 job remains terminal, unchanged and separately counted. Baltimore and the denied Orsay Coubertin page remain access holds without retry or alternate retrieval.
'''
    detail=re.sub(r'(?<=[A-Za-zÀ-ÿ])(?=\d)|(?<=\d)(?=[A-Za-zÀ-ÿ])',' ',detail)
    assert not (a.RUN/'README.md').exists();(a.RUN/'README.md').write_text(detail)
    root=m.RUN/'README.md';cp=m.load(a.CHECKPOINT);relative=str(root.relative_to(m.ROOT));pin=next(v for v in cp['artifacts'] if v['path']==relative);assert sha(root)==pin['sha256']
    backup=m.BACKUP/'france-fourteenth-root-readme-before-001.json.gz';assert not backup.exists();m.save(backup,dict(at=m.now(),path=relative,sha256=sha(root),text=root.read_text()));change=dict(path=relative,before_sha256=pin['sha256'],backup_path=str(backup),backup_sha256=sha(backup))
    old=root.read_text();split=old.index('\n## Added works');intro=old[:split].replace('8,565','9,046').replace('192 local museums','196 local museums').replace('expand 195 institutions','expand 199 institutions').replace('1,155','1,152').replace('after-wave-68','after-wave-69')
    lines=old[split:].splitlines();ix=next(i for i,v in enumerate(lines) if v.startswith('| Joconde — thirteenth five-museum'));lines.insert(ix+1,'| Joconde — fourteenth five-museum review, national and native records | 481 | 5 museums, 4 newly expanded |');ix=next(i for i,v in enumerate(lines) if v.startswith('| Distinct new-record campaign total |'));lines[ix]='| Distinct new-record campaign total | **9,046** | **197 collections** |'
    section='''

## Fourteenth five-museum pass — 8 October continuation

The [fourteenth review](native/france-fourteenth-minimum-20261008/README.md) added **481 review records** from605 current Joconde notices and599 checked Paris Musées pages. All five collections reach100 eligible works. The124 holds preserve identity, dating and physical-unit uncertainty;47,736 index leads remain outside the approved selection.

'''+table+'''

Twenty offline checks passed, exact readback succeeded and replay wrote nothing. Native qualifications and original national metadata remain in the audit trail. Bound components and unresolved duplicates were not used to reach the target.

The [wave69 verification](verification-after-wave-69.json) confirms **9,046 additions and785 existing-record links across199 expanded institutions**. **1,152 canonical museums remain below100 linked records and1,283 below200.** The broader goal remains active; the separate minimum-100 job is unchanged and separately counted.
'''
    section=re.sub(r'(?<=[A-Za-zÀ-ÿ])(?=\d)|(?<=\d)(?=[A-Za-zÀ-ÿ])',' ',section)
    root.write_text(intro+'\n'.join(lines)+'\n'+section);change['after_sha256']=sha(root)
    m.save(a.RUN/'readme-supersessions-001.json',dict(at=m.now(),changes=[change],policy='Intentional wave69 update. Previous campaign README preserved in Library; earlier evidence, plans, reports and scripts unchanged.'))
    print('Wave69 documentation verified; previous campaign README preserved in Library',flush=True)
if __name__=='__main__':main()
