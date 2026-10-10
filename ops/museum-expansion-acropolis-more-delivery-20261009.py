"""Further Acropolis delivery, combined object ledger and dated museum counts."""
import collections,csv,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-acropolis-more-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);m=a.m;RUN=a.RUN;OLD=m.RUN/'native/acropolis-20261009'
def table(name,rows):
 with(RUN/name).open('x',newline='')as fp:w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 p,digest=a.validate_plan();receipt=m.load(RUN/(a.KEY+'-applied.json'));checks=m.load(RUN/'checks-001.json');assert checks['offline_tests_passed']==14 and checks['atomic_verification_passed']and checks['replay_zero_writes'];assert receipt['plan_sha256']==digest
 prior=m.load(a.CHECKPOINT);rr=prior['production_institution_register_reference'];register=m.load(a.checked(rr))['rows'];target=next(v for v in register if v['id']==a.IID);assert target['verified_production_works']==141
 with a.i.prod.connect()as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY');verified=a.verify(db,p,digest)
 at=m.now();after=verified['current_counts'][a.IID];before=p['before_counts'][a.IID]
 target.update(production_catalogue_count_to_200=200,production_date_eligible_count_to_200=200,production_catalogue_count_state='at_least_200',production_date_eligible_count_state='at_least_200',verified_production_works=after['linked'],verified_production_eligible_works=after['eligible'],production_catalogue_count_at=at,production_date_eligible_count_at=at)
 m.save(RUN/'production-institution-register-001.json.gz',dict(at=at,rows=register,previous_register_reference=rr,read_only=True,updated_institutions=[a.IID],global_exact_counts_refreshed=False,global_thresholds_refreshed=False,policy='Only Acropolis refreshed to216/208. Other institutions retain original observation timestamps. Threshold columns cap200; verified counts exact.'));table('production-institution-register-001.csv',register)
 qr=prior['priority_museum_queue_reference'];queue=m.load(a.checked(qr));assert not any(v['id']==a.IID for v in queue['rows']);queue.update(at=at,previous_queue_reference=qr,policy='Acropolis remains outside under100 queue and now exceeds200 in both measures. Continue remaining Greek/Cypriot/Russian priorities and the all-museum register; other observations retain timestamps.');m.save(RUN/'priority-museum-queue-001.json',queue)
 added=[]
 for v in p['records']:
  f=v['facts'];added.append(dict(artwork_id=v['artwork_id'],institution_id=a.IID,source_id=f['source_id'],title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],inventory=f['inventory'],source_url=f['source_url'],status='review'))
 table('added-production-artworks-001.csv',added)
 with(OLD/'all-source-decisions-001.csv').open()as fp:ledger={int(v['number']):dict(v,number=int(v['number']))for v in csv.DictReader(fp)}
 for row in ledger.values():
  if row['state']=='approved_review_only_addition':row['state']='already_catalogued_previous_wave';row['reason']='Added and verified in wave107. '+row['reason']
  if row['number']==57:row['reason']+=' Related torso Acr.293 is added in wave108; this head remains held for reconciliation with that torso record.'
 for d in a.r.build():
  f=d['facts'];ledger[d['number']]=dict(number=d['number'],source_url=f['source_url'],source_index_text=f['source_fields']['index_text'],inventory=f['inventory'],state=d['state'],reason=d['basis'],existing_artwork_id=None)
 rows=[ledger[n]for n in sorted(ledger)];assert len(rows)==255;table('all-source-decisions-001.csv',rows)
 total=prior['production_campaign_totals']['new_artworks']+len(added);report=dict(at=at,goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=75,existing_links=0,date_eligible_added=73,open_after_dates_added=2,editorial_holds=9,reviewed_native_objects=84,greek_narratives_captured=31,combined_discovered_source_urls=255,reported_sculpture_count=256,reported_index_difference=1,prior_component_holds=4,combined_component_holds=13,deferred_discovery_records=42,verification=verified,museum_before=dict(works=before['linked'],eligible_works=before['eligible']),museum_after=dict(works=after['linked'],eligible_works=after['eligible']),production_campaign_new_artworks=total,production_campaign_museums=5,acropolis_campaign_added=191,historical_local_totals_unchanged=prior['historical_local_campaign_totals'],cross_database_totals_combined=False,production_canonical_museums=2135,global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,previous_global_threshold_checkpoint=a.reference(a.CHECKPOINT),remaining_to_200_catalogue=0,remaining_to_200_dateeligible=0,source_access='Acropolis official pages remain accessible. Next Rhodes official collection portal discovered; record its separate access receipt. Earlier provider holds persist. No images downloaded.',preserved_queues_checkpoint=a.reference(a.CHECKPOINT),priority_queue=a.reference(RUN/'priority-museum-queue-001.json'),next_museum=dict(id='f02b4c48-dd69-5319-8d22-e0de34436933',name='Municipal Art Gallery of Rhodes',website='https://mgamuseum.gr/en/',discovery_reference=a.reference(RUN/'next-museum-rhodes-discovery-001.json.gz'),policy='Verify institution and venue mapping before selected additions; current source contains post1970 works as well.'))
 m.save(RUN/'delivery-001.json',report)
 text=f'''# Acropolis Museum — target reached, 9 October 2026

Added **75 further production review artworks**, taking the museum from **141 to 216 catalogue works** and from **135 to 208 date-eligible works**. It now exceeds the preferred 200-work target in both measures. Across the two Acropolis passes, 191 new records were added. The real local catalogue remains unchanged at zero Acropolis records. The full all-museum objective remains active.

- [75 delivered artworks](added-production-artworks-001.csv)
- [Combined 255-object source ledger](all-source-decisions-001.csv)
- [Museum register with observation timestamps](production-institution-register-001.csv)
- [Verification and remaining research](delivery-001.json)

The museum's [official collection](https://www.theacropolismuseum.gr/en/explore-collections?field_exhibit_category_value=Sculpture&items_per_page=90) supplied 76 further leads, supplemented by eight heads deferred from the first pass. All84 individual pages were reviewed, including31 Greek narratives where English text was incomplete. Nine were held and75 approved. Across the full discovery set,42 fragments remain deferred and13 component/cast entries remain held; one difference between256 reported results and255 unique discovered URLs remains unresolved. Reaching the target does not imply exhaustive collection coverage.

The Rampin Rider and Fauvel-head scribe combine Athens originals with casts of Louvre fragments; neither was added. The arm Acr.4246 is attributed to Kouros Acr.665 and was excluded as a separate record. The possible Herakles torso/plinth group remains held, as do two disputed head associations, the unassigned rider hand, and seated goddess Acr.618 with its historical connection to already catalogued head Acr.659. The newly added Athena record Acr.293 represents the surviving torso; previously held head Acr.658 must be reconciled with it before any later import.

Physical Roman copies keep their Roman dates, regardless of an older Greek prototype. Two open after dates, Nike of Kallimachos and Kritios Boy, remain outside automatic date-eligible counts. Euenor and Endoios are distinguished from dedicators named on their respective inscriptions. Endoios Athena, Prokne/Itys and Kritios Boy retain qualified attributions. Multi-figure sculptures and their joined fragments count once. Unfinished ancient workshop pieces retain their unfinished condition without invented complete parent statues.

Exact-title matches were checked against physical identity. Existing Hermes Acr.2281α differs from new Acr.14877. Three Cleveland Harpocrates bronzes differ from the new marble NMA1807. The existing Solomko Scribe and Piranesi Silenus with Bacchus remain separate artworks. The review checked1019 existing identity candidates and320 supplementary comparators.

Fourteen offline tests passed. A successful Cloud SQL backup preceded the atomic write and readback, followed by a zero-write replay. All144 protected existing records and551 earlier production additions were preserved. No images, artist authority links, publication changes or current-display claims were added.

The selected production phase now totals **{total} additions across five museums**, separate from historical local totals. Only the Acropolis register row was refreshed. Continue with the next underfilled museum, the Municipal Art Gallery of Rhodes / Museum of Modern Greek Art, after checking the institution's venue mapping and the dates of individual artworks. Its [official collection website](https://mgamuseum.gr/en/permanent-collection/) and digital portal were located; this discovery is not yet a new catalogue addition.
'''
 (RUN/'README.md').write_text(text);print(json.dumps(dict(added=75,counts=after,production_campaign=total,states=dict(collections.Counter(v['state']for v in rows)))),flush=True)
if __name__=='__main__':main()
