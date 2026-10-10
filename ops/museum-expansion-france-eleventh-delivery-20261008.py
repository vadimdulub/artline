"""Document wave66, preserve old README bytes and finalize evidence checks."""
import collections,hashlib,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-eleventh-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report=m.load(m.RUN/'verification-after-wave-66.json');assert report['verified_new_artworks']==7776 and report['institutions_with_new_records_or_reconciled_holdings']==189 and not report['unrelated_coverage_changes_since_prior_report']
 p,digest=a.validate_plan()
 with m.connect() as db:verified=a.verify(db,p,digest)
 logsroot=Path('/Users/vadimdulub/Library/Logs');prefix='artline-france-eleventh-'
 for name,count in [('tests',25),('context-tests',30)]:
  text=(logsroot/(prefix+name+'-20261008.log')).read_text();assert ('Ran '+str(count)+' tests') in text and text.rstrip().endswith('OK')
 assert (logsroot/(prefix+'replay-20261008.log')).read_text().strip()=='Unchanged replay: zero writes'
 logs={v.name:dict(path=str(v),sha256=sha(v)) for v in sorted(logsroot.glob(prefix+'*-20261008.log')) if v.name!=prefix+'delivery-20261008.log'}
 q=m.load(a.RUN/'selected-metadata-queue-001.json');discovery=m.load(a.RUN/'five-museum-discovery-001.json.gz')
 selected={v['source_id'] for v in q['selected']};held={v['source_id'] for v in q['held']};fresh={v['raw_source_record']['Reference'] for v in discovery['rows'] if not v['already_known']};excluded=fresh-selected-held
 assert (len(selected),len(held),len(excluded),len(fresh))==(354,1770,87,2211)
 assert not (a.RUN/'checks-001.json').exists()
 m.save(a.RUN/'checks-001.json',dict(at=m.now(),new_offline_tests_passed=55,context_tests_passed=30,physical_identity_tests_passed=25,historical_tests_passed=1175,cumulative_verified_tests=1230,historical_tests_rerun=False,replay_zero_writes=True,all_workers_completed=True,new_selected_sources=354,captured_review_holds=32,unique_unselected_or_index_held=1770,prior_captured_holds_excluded=87,prior_hold_ids=sorted(excluded),identity_version='002; all literal facts and indexed comparisons recomputed',logs=logs,other_job_totals_separate=True,preparation_notes='Five exact-code museum contexts captured HTTP 200. One bounded queue of 354 current object records captured in nine HTTP 200 batches. Initial identity scope retained; supplemental maker/model and former-attribution names broaden final query. No failed import, catalogue fixture, image download or attachment. Web-renderer internal errors for two photo notice pages did not indicate a source access restriction; preselected official tabular API returned all records HTTP 200.'))
 rows=report['france_eleventh_museum_changes'];table='| Museum | Added | Linked before → after | Eligible before → after |\n| --- | ---: | ---: | ---: |\n'+'\n'.join('| '+v['name']+' | '+str(v['new'])+' | '+str(v['linked_before'])+' → '+str(v['linked_after'])+' | '+str(v['eligible_before'])+' → '+str(v['eligible_after'])+' |' for v in rows)
 root=m.RUN/'README.md';cp=m.load(a.CHECKPOINT);relative=str(root.relative_to(m.ROOT));pin=next(v for v in cp['artifacts'] if v['path']==relative);assert sha(root)==pin['sha256']
 backup=m.BACKUP/'france-eleventh-root-readme-before-001.json.gz';assert not backup.exists();m.save(backup,dict(at=m.now(),path=relative,sha256=sha(root),text=root.read_text()));change=dict(path=relative,before_sha256=pin['sha256'],backup_path=str(backup),backup_sha256=sha(backup))
 types=collections.Counter(v['facts']['work_type'] for v in p['records']);kindtext=', '.join(str(v)+' '+k for k,v in sorted(types.items()))
 detail='''# Eleventh French museum pass — 8 October 2026

Added **322 real local artwork records**, all in review, across four of five reviewed museums. Vendôme now exceeds the preferred target with **201 eligible artworks**. Beaune, Vendôme and Saint-Denis all cross the minimum of 100 eligible works in this pass. Beaune reaches 167, Saint-Denis 179, Honfleur 45 and Belfort remains at 49. The overall campaign remains unfinished.

'''+table+'''

Types: '''+kindtext+'''. The pinned national catalogue index contains 2,648 records for these museums, including 2,211 source identities not already represented in the database at discovery. A bounded queue selected 354 objects, all returned in nine HTTP 200 current-metadata batches. Individual review approved 322 and held 32. There are 1,770 further index-held/unselected leads plus 87 prior captured holds deliberately excluded from reselection. The prior Lançon print-date holds remain unresolved; no fresh scene date is treated as proof of physical impression date. No image assets were downloaded or attached.

The [museum reconciliation](museum-name-reconciliation-001.json) uses five fresh official Museofile captures. Vendôme's municipal and Musée de Vendôme names are explicit aliases under M0277. Its literal local-authority ownership wording is retained. Beaune's historical Beaux-Arts et musée Marey destination is reconciled only for the exact M0134 Beaux-Arts object records and municipal collection owner; no separate institutions were merged. Other municipalities, Louvre/state deposits, missing objects and unreconciled custody remain excluded. Saint-Denis, Belfort and Honfleur retain the previously established exact-code contexts with fresh source captures. Holding evidence makes no current-display claim.

The selector now supports physical photographs where the source explicitly describes a photographic process and support, and pastel drawings with explicit drawing domain and pastel medium. Photograph records describe actual paper prints, not downloads or photographs of database objects. When Braquehais photographed an Etex relief, the resulting catalogue record is a photograph; the sculpture is merely the subject. Each accepted photograph has its own inventory, physical measurements and source description. The 1871 date is the museum's explicit creation field, separately retained from historical scene/building dates. Four records referring to another impression as Original remain held pending version/chronology reconciliation. Two anonymous workshop photographs sharing a frame and AT/D-7 remain held for unit review. Eluard's photomaton strip counts once. Two cropped/wider Pont-Neuf views have separate physical prints and mount inscriptions 29/30. Related-image references do not create extra records.

Creation dates and periods remain literal. Parenthetical circa values use only independently stated eligible period bounds, with no invented tolerance. Denis's lithograph has explicit between 1923/1926 endpoints; its plate signature .23 is not substituted for that interval. Before dates retain an unknown lower bound. Source date conflicts and ambiguous reproduction chronologies remain held. Boudin's Poudreux pastel is a drawing from the explicit domain, form and medium; its circa 1854–1860 wording remains qualified within the separately supplied second-half nineteenth century. Purchase and arrival dates remain acquisition evidence.

The final identity review covers **43,126 existing artworks and 94,996 citations**, with supplemental creator spellings, former attributions and model names. All 354 literal source facts and indexed comparisons were recomputed identically. The [58 primary comparator records](physical-comparison-context-001.json.gz) preserve source records, hashes and unresolved evidence. They distinguish Beaune's Mors Vitrix wood sketch 44.54 from the existing 300×182 cm final canvas 884.6.2, and Les Deux Amies study 72.3.2 from existing final canvas 893.1.2. Related paintings, model drawings and copied compositions remain distinct from physical prints. Shared historical inventory fragments are evaluated against complete inventories, makers, media and sizes. Missing dimensions remain unknown.

The **32 captured holds** include sparse possible duplicates, mounted portrait components, contradictory dates/creators, uncertain impressions and an administrative diploma needing artwork-scope review. No unknown fields or source contradictions were silently corrected. Creator/model qualifications and the explicit joint painting roles remain object-level labels; no artist authorities or biographies were created.

The [individual decisions](editorial-reviewed-001.json.gz), [plan](france-eleventh-additions-001-plan.json.gz), [application receipt](france-eleventh-additions-001-applied.json), [wave 66 verification](../../verification-after-wave-66.json) and [checkpoint](delivery-checkpoint-001.json) document the atomic additions. Exact readback verifies every new artwork, native identifier, citation and accepted collection-holding assertion. All **2,917 protected existing comparison records**, **8,239 prior campaign records** and five institution records remain unchanged. The initial target-museum scope contains 442 existing records. Replay wrote nothing. No images, artist links, publication or display claims were added.

**55 fresh offline checks passed:** 30 museum/date/type guards and 25 physical-identity regressions. The 1,175 historical checks remain pinned, giving 1,230 cumulative verified checks; they were not all rerun. This is not a ten-million-row performance proof. Backups and logs are under Library, including the prior campaign README bytes.

Campaign totals are **7,776 new artworks and 785 existing-record holding links across 189 expanded institutions**. New records cover 186 museums plus Barnes. Source-pass totals remain 350 museums plus Barnes. The audit has **1,160 canonical museums below 100 linked records** and **1,286 below 200**. Linked and creation-eligible counts remain separate. The separate minimum-100 job remains terminal, unchanged and separately counted. The Baltimore access hold remains in force; no retry or alternate route was attempted.
'''
 assert not (a.RUN/'README.md').exists();(a.RUN/'README.md').write_text(detail)
 old=root.read_text();split=old.index('\n## Added works');intro=old[:split].replace('7,454','7,776').replace('184 local museums','186 local museums').replace('expand 187 institutions','expand 189 institutions').replace('1,161','1,160').replace('after-wave-65','after-wave-66')
 lines=old[split:].splitlines();ix=next(i for i,v in enumerate(lines) if v.startswith('| Joconde — tenth five-museum'));lines.insert(ix+1,'| Joconde — eleventh five-museum review, current official records | 322 | 4 museums, 2 newly expanded |')
 ix=next(i for i,v in enumerate(lines) if v.startswith('| Distinct new-record campaign total |'));lines[ix]='| Distinct new-record campaign total | **7,776** | **187 collections** |'
 section='''

## Eleventh five-museum pass — 8 October continuation

The [eleventh five-museum review](native/france-eleventh-minimum-20261008/README.md) added **322 review records** from 354 current Joconde records, with 32 captured holds, 1,770 further index-held/unselected leads and 87 prior captured holds excluded from reselection.

'''+table+'''

Vendôme reaches **201 eligible artworks**; Saint-Denis crosses 100 and reaches 179, and Beaune reaches 167. Honfleur 45 and Belfort 49 remain below 100. Physical photographs and pastel drawings are supported from explicit catalogue evidence. Primary comparisons distinguish separate studies, final paintings, printed copies and physical impressions. Unresolved duplicates, component groups and print dates remain held. All 354 source facts and comparisons recomputed identically, 55 new checks passed, exact database readback succeeded, and replay wrote nothing.

The [wave 66 verification](verification-after-wave-66.json) and [checkpoint](native/france-eleventh-minimum-20261008/delivery-checkpoint-001.json) confirm **7,776 additions and 785 existing-record links across 189 expanded institutions**. Source-pass totals remain 350 museums plus Barnes. **1,160 canonical museums remain below 100 linked works and 1,286 below 200.** The goal remains active; the separate minimum-100 job remains unchanged and separately counted.
'''
 root.write_text(intro+'\n'.join(lines)+'\n'+section);change['after_sha256']=sha(root)
 m.save(a.RUN/'readme-supersessions-001.json',dict(at=m.now(),changes=[change],policy='Intentional wave66 progress update; previous root README bytes preserved in Library. Earlier evidence, plans, reports and code remain immutable. Eleventh-pass README is new.'))
 print('Wave66 documentation verified; prior root README retained in Library',flush=True)
if __name__=='__main__':main()
