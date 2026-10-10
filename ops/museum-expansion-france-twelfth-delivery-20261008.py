"""Document wave 67 and preserve the previous campaign README bytes."""
import collections,hashlib,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-twelfth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report=m.load(m.RUN/'verification-after-wave-67.json');assert report['verified_new_artworks']==7994 and report['institutions_with_new_records_or_reconciled_holdings']==191 and not report['unrelated_coverage_changes_since_prior_report']
 p,digest=a.validate_plan()
 with m.connect() as db:verified=a.verify(db,p,digest)
 logsroot=Path('/Users/vadimdulub/Library/Logs');prefix='artline-france-twelfth-'
 for name,count in [('tests',25),('context-tests',22)]:
  text=(logsroot/(prefix+name+'-20261008.log')).read_text();assert ('Ran '+str(count)+' tests') in text and text.rstrip().endswith('OK')
 assert (logsroot/(prefix+'replay-20261008.log')).read_text().strip()=='Unchanged replay: zero writes'
 logs={v.name:dict(path=str(v),sha256=sha(v)) for v in sorted(logsroot.glob(prefix+'*-20261008.log')) if v.name!=prefix+'delivery-20261008.log'}
 q=m.load(a.RUN/'selected-metadata-queue-001.json');discovery=m.load(a.RUN/'five-museum-discovery-001.json.gz')
 selected={v['source_id'] for v in q['selected']};held={v['source_id'] for v in q['held']};fresh={v['raw_source_record']['Reference'] for v in discovery['rows'] if not v['already_known']};excluded=fresh-selected-held
 assert (len(selected),len(held),len(excluded),len(fresh))==(279,8047,0,8326)
 assert not (a.RUN/'checks-001.json').exists()
 m.save(a.RUN/'checks-001.json',dict(at=m.now(),new_offline_tests_passed=47,context_tests_passed=22,physical_identity_tests_passed=25,historical_tests_passed=1230,cumulative_verified_tests=1277,historical_tests_rerun=False,replay_zero_writes=True,all_workers_completed=True,new_selected_sources=279,captured_review_holds=61,unique_unselected_or_index_held=8047,prior_captured_holds_excluded=0,prior_hold_ids=[],identity_version='002; all literal facts and indexed comparisons recomputed',logs=logs,other_job_totals_separate=True,preparation_notes='Five official museum contexts and seven selected object batches returned HTTP 200. Identity v2 preserves role boundaries and adds source-name variants and comparison-only translations. All 279 records individually reviewed. Forty distinct pinned primary comparator records across two bundles. Additional university and Paris Musées captures support edition holds; no publication or date overwrite. Initial offline test checked duplicate wording in the inventory instead of the source history; corrected source-field assertion passed. No DB fixture, failed import, image download or attachment.'))
 rows=report['france_twelfth_museum_changes'];table='| Museum | Added | Linked before → after | Eligible before → after |\n| --- | ---: | ---: | ---: |\n'+'\n'.join('| '+v['name']+' | '+str(v['new'])+' | '+str(v['linked_before'])+' → '+str(v['linked_after'])+' | '+str(v['eligible_before'])+' → '+str(v['eligible_after'])+' |' for v in rows)
 root=m.RUN/'README.md';cp=m.load(a.CHECKPOINT);relative=str(root.relative_to(m.ROOT));pin=next(v for v in cp['artifacts'] if v['path']==relative);assert sha(root)==pin['sha256']
 backup=m.BACKUP/'france-twelfth-root-readme-before-001.json.gz';assert not backup.exists();m.save(backup,dict(at=m.now(),path=relative,sha256=sha(root),text=root.read_text()));change=dict(path=relative,before_sha256=pin['sha256'],backup_path=str(backup),backup_sha256=sha(backup))
 types=collections.Counter(v['facts']['work_type'] for v in p['records']);kindtext=', '.join(str(v)+' '+k for k,v in sorted(types.items()))
 detail='''# Twelfth French museum pass — 8 October 2026

Added **218 real local artwork records**, all in review. Sens, Louis Senlecq, Denys Puech and Lavaur each cross 100 eligible works. Louviers reaches 79 eligible works and still needs 21 to meet the minimum. The global goal remains active and unfinished.

'''+table+'''

Types: '''+kindtext+'''. The pinned national catalogue index contains 8,897 records for the five museums, including 8,326 source identities not already represented at discovery. A bounded queue selected 279 objects, returned in seven HTTP 200 current-metadata batches. Individual review approved 218 and held 61. Another 8,047 leads remain index-held or outside this selected pass. These are research leads, not approved additions. No image assets were downloaded or attached.

Five fresh Museofile captures support [exact museum reconciliation](museum-name-reconciliation-001.json). Sens and Louviers require their literal municipal destinations. Louis Senlecq's short name is resolved by exact code M0435, city and municipal owner. Denys Puech's hyphenated short destination is resolved to M0550, excluding Fenaille and learned-society ownership. Lavaur's former Pays Vaurais name is explicitly documented under M0601; literal local-authority ownership remains unchanged. Old state inventory marks on the accepted Decamps and Tourneux works are accompanied by explicit municipal transfer histories. Holdings do not establish current display.

The final identity query covers **64,830 existing artworks and 142,508 citations**. All 279 literal source records and indexed comparisons were recomputed identically. The [first](physical-comparison-context-001.json.gz) and [final](physical-comparison-context-002.json.gz) physical comparison bundles preserve 40 distinct primary comparator records. Creator parsing now keeps semicolons inside attribution and role qualifiers together, preventing role words from being mistaken for people. Inscription spellings and maker/model names are additional search terms. French/English comparison-title variants identify sparse Brueghel, Gossaert and Lautrec versions, which remain held. No translated title or normalized creator label replaces source metadata.

Two Louviers notices, 07060014325 and 07060014354, explicitly identify the same Victor Bertinot portrait print: LOV723 / 2004.0.168, 40×30 cm, matching autograph and reverse mark. Only 07060014325 creates a record. The separately held smaller plain-paper proof has different physical evidence. Thisbé impressions share dimensions but have different personal dedications. The two male academies have different examination annotations. Saint Francis impressions have different sheet sizes, dated annotations and states; the completed Bertinot/Levasseur print preserves both makers. A drawing study of Jacques Maniel stays separate from its larger chine-collé print. Two scenes on one sheet, recto/verso drawings and the two-part Balthazar sculpture each count once.

The Greek sculptor Athanase Apartis's signed 1935 Georges Duhamel marble and an anonymous medieval Virgin sculpture are included. Original role qualifications and unresolved names remain object-level labels. The Condamin chromolithograph names the painted model without inventing a printer. Nattier-model and Baciccio/Velasquez attribution conflicts remain explicit. Creation dates come from source creation fields, independently supplied periods and dated physical inscriptions. Before dates keep unknown lower bounds; circa values never acquire invented tolerances. Acquisition dates and depicted historical events remain separate.

The 61 captured holds preserve sparse duplicate uncertainty, contradictory print dates, unclear mounted or bound units and uncertain sculpture casts. A university illustration study documents a Friesz Paul et Virginie image from 1947, prompting edition review against the local notice's period ending in 1925. Paris Musées' [primary plate record](https://parismuseescollections.paris.fr/fr/maison-de-balzac/oeuvres/en-verite-en-verite-je-vous-le-dis-il-en-est-un-parmi-vous-qui-me-trahira) identifies Bouquet and publication on 17 May 1832, conflicting with the selected notice's 1852 date and maker label. Both remain research holds; source dates were not silently rewritten.

The [individual decisions](editorial-reviewed-001.json.gz), [plan](france-twelfth-additions-001-plan.json.gz), [application receipt](france-twelfth-additions-001-applied.json), [wave 67 verification](../../verification-after-wave-67.json) and [checkpoint](delivery-checkpoint-001.json) document the atomic additions. Exact readback verifies all new artworks, identifiers, citations and accepted collection holdings. The '''+str(verified['protected_existing_records'])+''' protected comparison records, 574 initial target-museum records, 8,561 prior campaign records and five institution records remain unchanged. Replay wrote nothing. No images, artist authorities, publication or display claims were added.

**47 fresh offline checks passed:** 22 context/date guards and 25 physical-identity checks. The 1,230 historical checks remain pinned, yielding 1,277 cumulative checks; they were not all rerun. This is not a ten-million-row performance proof. Backups and logs are under Library. The prior root README bytes are preserved there.

Campaign totals: **7,994 new artworks and 785 existing-record holding links across 191 expanded institutions**. New records cover 188 museums plus Barnes. Source-pass totals remain 350 museums plus Barnes. **1,160 canonical museums remain below 100 linked records and 1,285 below 200.** Linked records and eligible works remain separate measures. The separate minimum-100 job is terminal, unchanged and separately counted. The Baltimore access hold remains; no retry or alternate route was attempted.
'''
 assert not (a.RUN/'README.md').exists();(a.RUN/'README.md').write_text(detail)
 old=root.read_text();split=old.index('\n## Added works');intro=old[:split].replace('7,776','7,994').replace('186 local museums','188 local museums').replace('expand 189 institutions','expand 191 institutions').replace('after-wave-66','after-wave-67')
 lines=old[split:].splitlines();ix=next(i for i,v in enumerate(lines) if v.startswith('| Joconde — eleventh five-museum'));lines.insert(ix+1,'| Joconde — twelfth five-museum review, current official records | 218 | 5 museums, 2 newly expanded |')
 ix=next(i for i,v in enumerate(lines) if v.startswith('| Distinct new-record campaign total |'));lines[ix]='| Distinct new-record campaign total | **7,994** | **189 collections** |'
 section='''

## Twelfth five-museum pass — 8 October continuation

The [twelfth review](native/france-twelfth-minimum-20261008/README.md) added **218 review records** from 279 current Joconde records. Sixty-one captured records remain held; 8,047 further index leads are held or outside this bounded pass.

'''+table+'''

Sens, Louis Senlecq, Denys Puech and Lavaur all cross 100 eligible works. Louviers reaches 79. One duplicate portrait notice is counted once; other print states have individual physical evidence. Greek and anonymous medieval sculpture are included. All source facts and comparisons recomputed, 47 checks passed, exact database readback succeeded, and replay wrote nothing.

The [wave 67 verification](verification-after-wave-67.json) and [checkpoint](native/france-twelfth-minimum-20261008/delivery-checkpoint-001.json) confirm **7,994 additions and 785 existing-record links across 191 expanded institutions**. Source-pass totals remain 350 museums plus Barnes. **1,160 canonical museums remain below 100 linked works and 1,285 below 200.** The goal remains active. The separate minimum-100 job remains unchanged and separately counted.
'''
 root.write_text(intro+'\n'.join(lines)+'\n'+section);change['after_sha256']=sha(root)
 m.save(a.RUN/'readme-supersessions-001.json',dict(at=m.now(),changes=[change],policy='Intentional wave67 progress update; previous root README bytes preserved in Library. Earlier evidence, plans, reports and code immutable. Twelfth-pass README is new.'))
 print('Wave67 documentation verified; prior root README retained in Library',flush=True)
if __name__=='__main__':main()
