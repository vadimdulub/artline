"""MBP delivery and complete bounded-source ledger; prior global counts remain dated."""
import collections,csv,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-mbp-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);m=a.m;RUN=a.RUN
def table(name,rows):
 with (RUN/name).open('x',newline='')as fp:w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 p,digest=a.validate_plan();receipt=m.load(RUN/(a.KEY+'-applied.json'));checks=m.load(RUN/'checks-001.json');assert checks['offline_tests_passed']==12 and checks['atomic_verification_passed']and checks['replay_zero_writes'];assert receipt['plan_sha256']==digest
 prior=m.load(a.CHECKPOINT);register_ref=prior['production_institution_register_reference'];old=m.load(a.checked(register_ref));register=old['rows'];target=next(v for v in register if v['id']==a.IID);assert target['verified_production_works']==31
 with a.i.prod.connect()as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY');verified=a.verify(db,p,digest)
 at=m.now();target.update(production_catalogue_count_to_200=120,production_date_eligible_count_to_200=113,verified_production_works=120,verified_production_eligible_works=113,production_catalogue_count_at=at,production_date_eligible_count_at=at)
 reg=RUN/'production-institution-register-001.json.gz';m.save(reg,dict(at=at,rows=register,previous_register_reference=register_ref,read_only=True,updated_institutions=[a.IID],global_exact_counts_refreshed=False,global_thresholds_refreshed=False,policy='OnlyMBPcountsrefreshed;allotherrowcountsandtimestampsinheritedfromwave104thresholdaudits.200meansatleast200;lowercountsexactatindividualrowtimestamp.'))
 table('production-institution-register-001.csv',register)
 q=prior['priority_museum_queue_reference'];queue=m.load(a.checked(q));queue['rows']=[v for v in queue['rows']if v['id']!=a.IID];queue.update(at=at,previous_queue_reference=q,removed_threshold_reached=[a.IID],policy='InheritedpriorityqueuewithMBPremovedafterreaching100. Othermuseumobservationsremainatwave104timestamps;no freshglobalcountclaim.');m.save(RUN/'priority-museum-queue-001.json',queue)
 added=[]
 for v in p['records']:
  f=v['facts'];added.append(dict(artwork_id=v['artwork_id'],institution_id=a.IID,source_id=f['source_id'],title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],object_form=f['object_form'],inventory=f['inventory'],source_url=f['source_url'],status='review'))
 table('added-production-artworks-001.csv',added)
 facts=m.load(RUN/'candidate-facts-001.json.gz');ds={v['source_id']:v for v in a.r.build()};held={v['source_id']:v for v in facts['held']};known={v['source_id']:v for v in facts['existing']};discovery=m.load(RUN/'national-discovery-001.json.gz');ledger=[]
 for v in discovery['rows']:
  rid=str(v['recordId']);d=ds.get(rid);h=held.get(rid);k=known.get(rid)
  state=d['state']if d else 'source_fact_or_scope_hold'if h else 'already_catalogued'if k else 'deferred_outside_selected_artwork_types'
  reason=d['basis']if d else h['reason']if h else k['basis']if k else 'Discoveryonly;coins,seals,ordinaryvessels,tools,andotherunselectedtypesnotindividuallyreviewed.'
  ledger.append(dict(source_id=rid,title=v['title'].get('en')or v['title'].get('gr'),inventory=a.i.f.inventory(v),state=state,reason=reason,existing_artwork_id=k['existing_artwork_id']if k else None,source_url='https://nationalarchive.culture.gr/exhibits/'+rid))
 assert len(ledger)==200;table('all-source-decisions-001.csv',ledger)
 visual=dict(at=at,inputs_reference=a.reference(RUN/'poulakis-visual-inputs-001.json'),existing_artwork_ids=['a5d1275c-f630-5bd9-a16e-aee4ab6cf54d','5eade82b-a59b-5ff5-b1d9-50449760f1ae'],inventory='ΒΕΙ 959',state='existing_duplicate_confirmed_for_followup',basis='ExistingCommonsimageandmuseum959imagevisuallyshowidenticalwellscene,inscription,figurepositions,camels,sheepandpaintloss.Sameobject;neitherisnewlyadded.958Potipharand956Jacobpanelsdepictdifferentscenes.',action='Noarchive,merge,linkorimagechange;prepareseparatereconciliationwithallcitationsandmediapreserved.');m.save(RUN/'poulakis-duplicate-review-001.json',visual)
 report=dict(at=at,goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=89,existing_links=0,date_eligible_added=83,unknown_date_added=1,crossing1970_added=5,reviewed_national_source_records=117,discovery_records=200,already_catalogued=17,source_fact_or_scope_holds=9,editorial_holds=2,deferred_discovery_records=83,verification=verified,museum_before=dict(works=31,eligible_works=30),museum_after=dict(works=120,eligible_works=113),production_campaign_new_artworks=328,production_campaign_museums=4,historical_local_totals_unchanged=prior['historical_local_campaign_totals'],cross_database_totals_combined=False,production_canonical_museums=2135,global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,previous_global_threshold_checkpoint=a.reference(a.CHECKPOINT),remaining_national_records_not_fetched=547,next_national_offset=200,remaining_to_200_catalogue=80,remaining_to_200_dateeligible=87,source_access='OfficialMBPpagesandMinistrypubliccatalogueavailable.Oneconnectiontimeoutatobject453087recoveredononeordinaryretry.Priorproviderholdscontinue.Noexhaustivedownload.',preserved_queues_checkpoint=a.reference(a.CHECKPOINT),priority_queue=a.reference(RUN/'priority-museum-queue-001.json'))
 m.save(RUN/'delivery-001.json',report)
 text='''# Museum of Byzantine Culture — production expansion, 9 October 2026

Added **89 production review artworks**, taking the Thessaloniki museum from **31 to 120 catalogue records**. **83 additions have eligible creation dates**, taking that count from 30 to **113**. Five physical prints retain a 1900–1999 range crossing the cutoff, and one print remains undated. The real local catalogue remains unchanged at 27 records, 26 date-eligible.

- [89 delivered artworks](added-production-artworks-001.csv)
- [All 200 discovery decisions](all-source-decisions-001.csv)
- [Institution register with observation timestamps](production-institution-register-001.csv)
- [Verification and remaining research](delivery-001.json)

The source is the Greek Ministry of Culture’s [National Archive of Monuments](https://nationalarchive.culture.gr/), whose individual records explicitly identify Museum of Byzantine Culture provider 274 and museum location 6051. The museum’s [wooden icons](https://www.mbp.gr/en/collections/wooden-icons/) and [paper icons](https://www.mbp.gr/en/collections/chartines-eikones/) supplied independent collection and object context. Holdings are recorded separately from current display.

The initial 200 metadata records yielded 117 selected individual object reviews: 89 additions, 17 already catalogued, nine factual or scope holds and two further identity holds. Another 83 discovery records were deferred outside this selection. The public search reported 747 objects; 547 records remain beyond the first 200. This is a bounded selection, not a complete download.

The additions comprise 52 prints, 19 paintings (18 classified as icons), four carved sculptures, 11 fresco records and three floor-mosaic records. The current database lacks a mosaic type; those three use the permitted unknown category while preserving explicit floor-mosaic descriptions and source classification. Combined tomb-wall and floor-mosaic inventories each count once. The two-leaf iconostasis door counts once. Surviving central triptych panels and cut Joseph-cycle panels are described as fragments; complete parent works are not invented.

Physical edition dates control. A 1950 lithographic reproduction retains 1950 rather than the original engraving’s 1847 date; a 1936 copy retains its own date. Three explicitly dated 1977 impressions were excluded despite older plate dates in structured metadata. An uncertain 1846 inscription remains qualified. Prints with identical subjects retain distinct inventories and sheet measurements. A separate print with conflicting 1855/1885 dates remains held.

Three groups of loose decorative inlays and two fragments sharing parent inventory BT190 remain held. Two tomb records, BT170 and BT139, have overlapping descriptions, equal dimensions and the same findspot despite different inventories and dates; both remain held for stronger identity evidence.

Greek and English museum pages were compared where the English page for inventory 230 duplicated the narrative of a different Saint George engraving. Greek 230 describes an 1871 relic-procession lithograph; national 715484/127 corroborates the separate 1833 Saint George print. Inventory 230 was not added in this national selection. Its corrected source remains a follow-up lead.

Visual comparison confirmed a pre-existing duplicate: the unlinked “Brothers Sell Joseph into Slavery” image and the already linked “Joseph in the well” depict the same inventory 959. Neither was added again or merged in this pass. The new 958 and 956 cut panels depict different scenes. [Duplicate evidence and follow-up](poulakis-duplicate-review-001.json).

Twelve offline boundary checks passed. A successful Cloud SQL backup preceded atomic application and readback; replay verified the result with zero writes. All 85 protected existing records and 239 earlier production additions were preserved. No images, artist-authority links, publication changes or current-display claims were added.

This selected production phase totals **328 additions across four museums**. Historical local-only totals remain separate. Museum counts outside MBP retain their wave 104 audit timestamps; no new global count is claimed. MBP needs 80 more catalogue records, or 87 more date-eligible records, to reach 200. Continue at national search offset 200, review the remaining source gaps, and reconcile the confirmed existing duplicate before changing either record.
'''
 dest=RUN/'README.md';assert not dest.exists();dest.write_text(text);print(json.dumps(dict(added=89,linked=120,eligible=113,production_campaign=328,states=dict(collections.Counter(v['state']for v in ledger)))),flush=True)
if __name__=='__main__':main()
