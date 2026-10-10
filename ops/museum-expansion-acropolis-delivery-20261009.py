"""Acropolis production delivery and museum register with dated observations."""
import collections,csv,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-acropolis-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);m=a.m;RUN=a.RUN
def table(name,rows):
 with(RUN/name).open('x',newline='')as fp:w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 p,digest=a.validate_plan();receipt=m.load(RUN/(a.KEY+'-applied.json'));checks=m.load(RUN/'checks-001.json');assert checks['offline_tests_passed']==14 and checks['atomic_verification_passed']and checks['replay_zero_writes'];assert receipt['plan_sha256']==digest
 prior=m.load(a.CHECKPOINT);rr=prior['production_institution_register_reference'];register=m.load(a.checked(rr))['rows'];target=next(v for v in register if v['id']==a.IID)
 with a.i.prod.connect()as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY');verified=a.verify(db,p,digest)
 at=m.now();after=verified['current_counts'][a.IID];before=p['before_counts'][a.IID]
 target.update(production_catalogue_count_to_200=min(200,after['linked']),production_date_eligible_count_to_200=min(200,after['eligible']),production_catalogue_count_state='exact',production_date_eligible_count_state='exact',verified_production_works=after['linked'],verified_production_eligible_works=after['eligible'],production_catalogue_count_at=at,production_date_eligible_count_at=at)
 m.save(RUN/'production-institution-register-001.json.gz',dict(at=at,rows=register,previous_register_reference=rr,read_only=True,updated_institutions=[a.IID],global_exact_counts_refreshed=False,global_thresholds_refreshed=False,policy='Only Acropolis Museum refreshed. Other institutions retain their original observation timestamps.'))
 table('production-institution-register-001.csv',register)
 qr=prior['priority_museum_queue_reference'];queue=m.load(a.checked(qr));assert sum(v['id']==a.IID for v in queue['rows'])==1;queue['rows']=[v for v in queue['rows']if v['id']!=a.IID];queue['removed_threshold_reached']=queue.get('removed_threshold_reached',[])+[dict(id=a.IID,at=at,catalogue=after['linked'],date_eligible=after['eligible'])];queue.update(at=at,previous_queue_reference=qr,policy='Acropolis now exceeds100 in both measures and leaves the under100 priority queue; still needs59 catalogue or65 date-eligible additions to200. Other observations retain their timestamps.');m.save(RUN/'priority-museum-queue-001.json',queue)
 added=[]
 for v in p['records']:
  f=v['facts'];added.append(dict(artwork_id=v['artwork_id'],institution_id=a.IID,source_id=f['source_id'],title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],inventory=f['inventory'],source_url=f['source_url'],status='review'))
 table('added-production-artworks-001.csv',added)
 ds={v['number']:v for v in a.r.build()};selection=m.load(RUN/'native-selection-001.json');known={v['number']:v for v in selection['already']};discovery=m.load(RUN/'native-discovery-001.json.gz');ledger=[]
 for n,v in enumerate(discovery['rows'],1):
  d=ds.get(n);k=known.get(n);state=d['state']if d else'already_catalogued'if k else'deferred_outside_bounded_selection';reason=d['basis']if d else'Exact existing native object URL; preserved without another record.'if k else'Discovery only; fragment/parent or later head review deferred. No metadata or image attachment.'
  ledger.append(dict(number=n,source_url=v['url'],source_index_text=v['index_text'],inventory=d['facts']['inventory']if d else None,state=state,reason=reason,existing_artwork_id=k['existing_artwork_id']if k else None))
 assert len(ledger)==179;table('all-source-decisions-001.csv',ledger)
 followup=m.load(RUN/'next-source-discovery-001.json.gz');table('next-source-discovery-001.csv',[dict(number=n,source_url=v['url'],source_index_text=v['index_text'],state='discovery_only_pending_object_review')for n,v in enumerate(followup['rows'],180)])
 total=prior['production_campaign_totals']['new_artworks']+len(added);report=dict(at=at,goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=len(added),existing_links=0,date_eligible_added=111,open_after_dates_added=5,editorial_holds=4,already_catalogued=9,reviewed_native_objects=120,greek_narratives_captured=sum(bool(v.get('greek_description'))for v in m.load(RUN/'native-narratives-001.json.gz')['rows']),discovery_records=179,raw_discovery_rows=180,duplicate_boundary_urls=discovery['duplicate_page_boundary_urls'],reported_sculpture_count=256,deferred_discovery_records=50,followup_discovery_records=76,combined_unique_sculpture_urls=255,reported_index_difference=1,next_sculpture_index_page=None,verification=verified,museum_before=dict(works=before['linked'],eligible_works=before['eligible']),museum_after=dict(works=after['linked'],eligible_works=after['eligible']),production_campaign_new_artworks=total,production_campaign_museums=5,historical_local_totals_unchanged=prior['historical_local_campaign_totals'],cross_database_totals_combined=False,production_canonical_museums=2135,global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,previous_global_threshold_checkpoint=a.reference(a.CHECKPOINT),remaining_to_200_catalogue=59,remaining_to_200_dateeligible=65,source_access='Official Acropolis Museum English and Greek object pages accessible. No new access hold. Earlier provider holds persist. No image downloads.',preserved_queues_checkpoint=a.reference(a.CHECKPOINT),priority_queue=a.reference(RUN/'priority-museum-queue-001.json'))
 m.save(RUN/'delivery-001.json',report)
 text=f'''# Acropolis Museum — production expansion, 9 October 2026

Added **116 production review artworks**, taking the museum from **25 to 141 catalogue works** and from **24 to 135 date-eligible works**. The museum now exceeds the 100-work minimum. It still needs 59 catalogue additions, or 65 date-eligible additions, to reach 200. The real local database remains unchanged at zero Acropolis records. The all-museum objective remains active.

- [Delivered artworks](added-production-artworks-001.csv)
- [All 179 discovery decisions](all-source-decisions-001.csv)
- [Museum register with observation timestamps](production-institution-register-001.csv)
- [Verification and remaining research](delivery-001.json)

The museum's [official collection index](https://www.theacropolismuseum.gr/en/explore-collections?field_exhibit_category_value=Sculpture&items_per_page=90) reports 256 sculptures. Two index pages yielded 180 rows and 179 unique URLs; one repeated boundary URL was retained as evidence and deduplicated. We reviewed 120 selected individual object pages, including {report['greek_narratives_captured']} Greek narratives where the English description was incomplete. Nine existing objects were recognized by native URL; 50 discoveries remain deferred. A follow-up index page yielded [76 further discovery leads](next-source-discovery-001.csv), ready for individual review. Across three pages there are 255 unique URLs against 256 reported results; the one-record difference remains tracked, and directory discovery does not establish object coverage.

Four entries remain held: Telemachos' reconstructed stele, the male head combining an Athens fragment with a cast of a Rodin Museum fragment, the Athena head associated with torso/foot components, and the Lyon Kore assembly containing a cast of the upper body held in France. Surviving ancient fragments can be genuine artworks; assembled parts count together, and uncertain parent records are not invented. Dog head Acr.525 must be reconciled with the deferred body Acr.550 before further additions. Separate dog Acr.143 is a different animal. Dancer slabs EAM259 and EAM260 remain separate supports with a possible common base noted, without adding a hypothetical complete base.

The surviving objects control dates. Roman copies retain their Roman dates rather than the dates of their Greek models. BC ranges use negative years without year zero; century qualifiers remain literal, with conservative full-century bounds. Five open after dates remain outside automatic date-eligible counts. Dedicator names are not converted into sculptors. Rampin Master, Leochares and workshop attributions keep their qualifications, without new artist authority links.

The identity review checked 950 existing source/title/inventory/creator comparators and 730 supplementary subject matches. Existing 1911 watercolours of several Korai are depictions of the ancient sculptures and remain separate artworks at their recorded museum. Cleveland's Kore head and Alexander head and Chicago's Egyptian calf-bearer relief are distinct physical objects. Inventory namespaces are preserved: Acr.1329 and EAM1329 are different reliefs. Existing metadata and links were not rewritten.

Fourteen offline boundary tests passed. A successful Cloud SQL backup preceded the atomic write and readback, followed by a zero-write replay. All 26 protected existing records and 435 previous production additions were preserved; supplementary comparison snapshots were checked before the transaction. No images, publication changes or current-display claims were added.

The selected production phase totals **{total} additions across five museums**; historical local totals remain separate. Only the Acropolis register row was refreshed. Other museum counts retain their previous audit timestamps. Continue toward 200 here and through the remaining nationwide and all-museum registers.
'''
 (RUN/'README.md').write_text(text);print(json.dumps(dict(added=116,counts=after,production_campaign=total,states=dict(collections.Counter(v['state']for v in ledger)))),flush=True)
if __name__=='__main__':main()
