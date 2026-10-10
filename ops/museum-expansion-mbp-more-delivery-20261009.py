"""Further MBP production delivery; prior all-museum audit timestamps preserved."""
import collections,csv,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-mbp-more-apply-v2-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);m=a.m;RUN=a.RUN
def table(name,rows):
 with(RUN/name).open('x',newline='')as fp:w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 p,digest=a.validate_plan();receipt=m.load(RUN/(a.KEY+'-applied.json'));checks=m.load(RUN/'checks-001.json');assert checks['offline_tests_passed']==10 and checks['atomic_verification_passed']and checks['replay_zero_writes'];assert receipt['plan_sha256']==digest
 prior=m.load(a.CHECKPOINT);rr=prior['production_institution_register_reference'];register=m.load(a.checked(rr))['rows'];target=next(v for v in register if v['id']==a.IID);assert target['verified_production_works']==120
 with a.i.prod.connect()as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY');verified=a.verify(db,p,digest)
 at=m.now();after=verified['current_counts'][a.IID];before=p['before_counts'][a.IID];target.update(production_catalogue_count_to_200=min(200,after['linked']),production_date_eligible_count_to_200=min(200,after['eligible']),production_catalogue_count_state='at_least_200'if after['linked']>=200 else'exact',production_date_eligible_count_state='at_least_200'if after['eligible']>=200 else'exact',verified_production_works=after['linked'],verified_production_eligible_works=after['eligible'],production_catalogue_count_at=at,production_date_eligible_count_at=at)
 m.save(RUN/'production-institution-register-001.json.gz',dict(at=at,rows=register,previous_register_reference=rr,read_only=True,updated_institutions=[a.IID],global_exact_counts_refreshed=False,global_thresholds_refreshed=False,policy='Only MBP refreshed. Other institutions retain their original observation timestamps. Threshold columns cap at200; verified MBP counts are exact.'))
 table('production-institution-register-001.csv',register)
 qr=prior['priority_museum_queue_reference'];queue=m.load(a.checked(qr));assert not any(v['id']==a.IID for v in queue['rows']);queue.update(at=at,previous_queue_reference=qr,policy='Priority queue inherited unchanged. MBP remains outside the under100 queue and now exceeds200. Other observations retain their original timestamps.');m.save(RUN/'priority-museum-queue-001.json',queue)
 added=[]
 for v in p['records']:
  f=v['facts'];added.append(dict(artwork_id=v['artwork_id'],institution_id=a.IID,source_id=f['source_id'],title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],object_form=f['object_form'],inventory=f['inventory'],source_url=f['source_url'],status='review'))
 table('added-production-artworks-001.csv',added)
 facts=m.load(RUN/'candidate-facts-001.json.gz');ds={v['source_id']:v for v in a.r.build()};held={v['source_id']:v for v in facts['held']};known={v['source_id']:v for v in facts['existing']};discovery=m.load(RUN/'national-discovery-001.json.gz');ledger=[]
 for v in discovery['rows']:
  rid=str(v['recordId']);d=ds.get(rid);h=held.get(rid);k=known.get(rid);state=d['state']if d else'source_fact_or_scope_hold'if h else'already_catalogued'if k else'deferred_outside_bounded_selection';reason=d['basis']if d else h['reason']if h else k['basis']if k else'Discovery only; outside this selected120object review. No metadata or image attachment.'
  ledger.append(dict(source_id=rid,title=v['title'].get('en')or v['title'].get('gr'),inventory=a.i.f.inventory(v),state=state,reason=reason,existing_artwork_id=k['existing_artwork_id']if k else None,source_url='https://nationalarchive.culture.gr/exhibits/'+rid))
 assert len(ledger)==200;table('all-source-decisions-001.csv',ledger)
 total=prior['production_campaign_totals']['new_artworks']+len(added);report=dict(at=at,goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=len(added),existing_links=0,date_eligible_added=verified['date_eligible_new_records'],unknown_date_added=0,crossing1970_added=verified['crossing1970_new_records'],reviewed_national_source_records=120,discovery_records=200,already_catalogued=len(known),source_fact_or_scope_holds=len(held),editorial_holds=verified['editorial_holds'],deferred_discovery_records=80,verification=verified,museum_before=dict(works=before['linked'],eligible_works=before['eligible']),museum_after=dict(works=after['linked'],eligible_works=after['eligible']),production_campaign_new_artworks=total,production_campaign_museums=4,historical_local_totals_unchanged=prior['historical_local_campaign_totals'],cross_database_totals_combined=False,production_canonical_museums=2135,global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,previous_global_threshold_checkpoint=a.reference(a.CHECKPOINT),remaining_national_records_not_fetched=347,next_national_offset=400,remaining_to_200_catalogue=max(0,200-after['linked']),remaining_to_200_dateeligible=max(0,200-after['eligible']),source_access='Greek Ministry public metadata accessible. No new provider access hold. Earlier provider holds persist. No image downloads this wave.',preserved_queues_checkpoint=a.reference(a.CHECKPOINT),priority_queue=a.reference(RUN/'priority-museum-queue-001.json'))
 m.save(RUN/'delivery-001.json',report)
 text=f'''# Museum of Byzantine Culture — further production expansion, 9 October 2026

Added **{len(added)} production review artworks**, taking the museum from **{before['linked']} to {after['linked']} catalogue records** and from **{before['eligible']} to {after['eligible']} date-eligible works**. This museum now exceeds the 200-work target. The real local catalogue remains unchanged at 27 records, 26 date-eligible. The full all-museum goal remains active.

- [Delivered artworks](added-production-artworks-001.csv)
- [All 200 source decisions](all-source-decisions-001.csv)
- [Institution register with observation timestamps](production-institution-register-001.csv)
- [Verification and remaining research](delivery-001.json)

The Greek Ministry of Culture’s [National Archive of Monuments](https://nationalarchive.culture.gr/) supplied 200 further discovery records (offsets 200 and 300) and 120 selected individual object records. Each identifies Museum of Byzantine Culture provider 274 and location 6051. Eight source or scope holds and five already catalogued objects are retained in the ledger. Another 80 records were deferred outside this bounded selection. There are 347 source records beyond offset 400; no exhaustive download is needed to meet the museum target.

Physical objects control identity and dates. The explicitly 1977 Saint Catherine impression and 2007 Nikos Alexiou print were excluded despite their older models. The recent Catherine print 175 retains 1900–1999 and remains outside date-eligible counts. Ca. 1820 remains approximate. The conflicting 1845/1849 Philotheou record and 19th/20th-century Virgin impression remain held. Two floor fragments, one colonette component and the Papaloukas Horarion group require parent/component reconciliation.

The already catalogued triclinium wall painting BT136 matches source BT136/A–I by subject and 14.52 × 1.69 m measurements; it was not added again. Combined floors and triptych leaves count once. Surviving panels are explicitly fragments. Poulakis 957 depicts the Potiphar-wife/trial episode and is distinct from 956, 958 and 959. The pre-existing duplicate of 959 remains in the [preceding follow-up ledger](../mbp-20261009/poulakis-duplicate-review-001.json); neither existing record was merged or changed here.

The Chrysoloras attribution remains a workshop attribution. The Deesis icon 58 has a Poulakis signature which the museum says is not genuine; its label remains anonymous. Another inscription only possibly names Constantine and Sergius. Museum workshop qualifications are preserved without creating or assigning artist authorities. Mosaic records preserve their literal classification and use the database’s permitted unknown work type.

Ten offline boundary tests passed. A successful Cloud SQL backup preceded the atomic addition and readback, followed by a zero-write replay. All {verified['protected_existing_records']} protected existing rows and {verified['prior_campaign_records_preserved']} prior production additions were preserved. No images, publication changes or current-display claims were added.

The selected production phase totals **{total} additions across four museums**; historical local totals remain separate. Only the MBP register row is refreshed; other museum counts retain their dated global audit observations. Continue with the remaining underfilled museum queue and retain unresolved MBP source/duplicate follow-ups.
'''
 (RUN/'README.md').write_text(text);print(json.dumps(dict(added=len(added),counts=after,production_campaign=total,states=dict(collections.Counter(v['state']for v in ledger)))),flush=True)
if __name__=='__main__':main()
