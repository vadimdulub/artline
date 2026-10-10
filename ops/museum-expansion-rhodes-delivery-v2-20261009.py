"""Rhodes minimum reached; preserve dated global register and remaining collection research."""
import collections,csv,importlib.util,json,io
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-rhodes-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);m=a.m;RUN=a.RUN

def table(name,rows):
 fp=io.StringIO(newline='');w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows);raw=fp.getvalue().encode();path=RUN/name
 if path.exists():assert path.read_bytes()==raw,'Preserve existing delivery CSV: '+name
 else:path.write_bytes(raw)
def main():
 p,digest=a.validate_plan();receipt=m.load(RUN/(a.KEY+'-applied.json'));checks=m.load(RUN/'checks-001.json');assert checks['offline_tests_passed']==13 and checks['atomic_verification_passed']and checks['replay_zero_writes'];assert receipt['plan_sha256']==digest
 prior=m.load(a.CHECKPOINT);rr=prior['production_institution_register_reference'];register=m.load(a.checked(rr))['rows'];target=next(v for v in register if v['id']==a.IID);assert target['verified_production_works']==21
 with a.i.prod.connect()as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY');verified=a.verify(db,p,digest)
 with m.connect()as db:
  initial=m.load(RUN/'initial-scope-001.json.gz');assert a.snapshot(db,initial['scoped_ids'])==initial['snapshot']and a.counts(db)==initial['counts']
 at=m.load(RUN/'production-institution-register-001.json.gz')['at']if(RUN/'production-institution-register-001.json.gz').exists()else m.now();after=verified['current_counts'][a.IID];before=p['before_counts'][a.IID]
 target.update(production_catalogue_count_to_200=107,production_date_eligible_count_to_200=101,production_catalogue_count_state='exact',production_date_eligible_count_state='exact',verified_production_works=after['linked'],verified_production_eligible_works=after['eligible'],production_catalogue_count_at=at,production_date_eligible_count_at=at)
 m.save(RUN/'production-institution-register-001.json.gz',dict(at=at,rows=register,previous_register_reference=rr,read_only=True,updated_institutions=[a.IID],global_exact_counts_refreshed=False,global_thresholds_refreshed=False,policy='Only Rhodes refreshed to107/101. Other institutions retain observation timestamps. The200-work aspiration remains open.'));table('production-institution-register-001.csv',register)
 qr=prior['priority_museum_queue_reference'];queue=m.load(a.checked(qr));assert any(v['id']==a.IID for v in queue['rows']);queue['rows']=[v for v in queue['rows']if v['id']!=a.IID];queue.update(at=at,previous_queue_reference=qr,policy='Rhodes removed from under100 queue after reaching107 catalogue/101 eligible. It remains93catalogue/99eligible short of200; continue bounded Rhodes source selection before moving to next priority.');queue['removed_threshold_reached']=queue.get('removed_threshold_reached',[])+[dict(id=a.IID,at=at,catalogue=107,date_eligible=101)];m.save(RUN/'priority-museum-queue-001.json',queue)
 added=[]
 for v in p['records']:
  f=v['facts'];added.append(dict(artwork_id=v['artwork_id'],institution_id=a.IID,source_id=f['source_id'],title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],inventory=f['inventory'],source_url=f['source_url'],status='review'))
 table('added-production-artworks-001.csv',added);decisions=a.r.build();ledger=[dict(number=v['number'],source_url=v['facts']['source_url'],inventory=v['facts']['inventory'],title=v['facts']['title'],state=v['state'],reason=v['basis'],existing_artwork_ids=';'.join(sorted({c['entity_id']for c in v['comparison']['source_hits']})))for v in decisions];table('all-source-decisions-001.csv',ledger)
 total=prior['production_campaign_totals']['new_artworks']+86;report=dict(at=at,goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=86,existing_links=0,date_eligible_added=86,editorial_holds=9,already_catalogued=4,unknown_date_deferred=18,after1970_excluded=3,reviewed_native_objects=120,source_collection_reported_objects=1502,remaining_metadata_not_fetched=1382,verification=verified,museum_before=dict(works=before['linked'],eligible_works=before['eligible']),museum_after=dict(works=after['linked'],eligible_works=after['eligible']),production_campaign_new_artworks=total,production_campaign_museums=6,historical_local_totals_unchanged=prior['historical_local_campaign_totals'],cross_database_totals_combined=False,global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,remaining_to_200_catalogue=93,remaining_to_200_dateeligible=99,source_access='Official Rhodes public metadata portal accessible. All historical provider holds retained. No artwork images fetched or attached.',next_work='Continue Rhodes using60 already captured index leads120–179 from pages6–8 in next-source-discovery-001.json.gz, then bounded public children pages startingpage9,size20, with date/version selection toward200. Retain18unknown leads and9version/dateholds; current120alreadyclassified. After Rhodes, priority queue starts Nikos Kazantzakis Museum; literary documents must not be treated automatically as artworks.')
 m.save(RUN/'delivery-001.json',report)
 (RUN/'README.md').write_text(f'''# Rhodes — minimum reached, 9 October 2026

Added **86 production review artworks**, bringing the Municipal Art Gallery of Rhodes / Museum of Modern Greek Art from **21 to 107 catalogue works** and from **15 to 101 date-eligible works**. Both measures now meet the100-work minimum. The preferred200-work target remains open. The real local catalogue is unchanged at3 linked works,1 date eligible.

- [86 delivered artworks](added-production-artworks-001.csv)
- [All120 source decisions](all-source-decisions-001.csv)
- [Dated museum register](production-institution-register-001.csv)
- [Verification and remaining work](delivery-001.json)

The [official museum history](https://mgamuseum.gr/en/the-museum/) establishes continuity from the Municipal Gallery to the current museum and distinguishes its several venues. The [digital collection](https://portal.mgamuseum.gr/) supplies individual object records and inventories. These additions assert collection holdings, with no venue or current-display claim.

Of120 selected metadata records from a reported1502,86 were added,4 already existed,3 were dated after1970,18 lacked dates and remain research leads, and9 were held for edition/version reconciliation. This is selected coverage, not an exhaustive download. No images were downloaded or attached.

New works include Greek paintings, historical map and travel prints, and Semertzidis studies and prints. Physical print editions remain separate from older designs, book first editions, depicted events and artist lifespans. Probable editions retain qualifications. Conflicting dates are explicit in notes and conservative intervals where both source dates are within scope. Studies, composite sheets and panorama plates retain their documented boundaries.

Held records include possible repeats of the Mallet Rhodes/Colossus plates, a Mayer print, a combined harbour sheet, a LeBrun panorama plate, a soup-queue print, a second small Demonstration linocut, and two unresolved map-edition dates. No uncertain duplicate was added to meet the target. Source details and all original labels remain in the evidence.

Thirteen offline tests passed. A successful Cloud SQL backup preceded the atomic write and readback; a replay made zero writes. All86 protected existing records and626 prior production additions remained unchanged. The duplicate review used4097 existing artwork candidates and73 focused full-row comparison snapshots. A corrected comparison pass excludes empty-title false positives. Read-only query plans and timings are retained; they do not establish10million-row performance.

This selected production phase now totals **{total} additions across six museums**, separate from historical local totals. Only the Rhodes register row was refreshed. Continue bounded Rhodes selection toward200, using the60 captured index leads from pages6–8, then page9 onward;1382 individual object records remain unexamined. The all-museum goal remains active.
''');print(json.dumps(dict(added=86,counts=after,production_campaign=total,states=dict(collections.Counter(v['state']for v in ledger)),queue=len(queue['rows']))),flush=True)
if __name__=='__main__':main()
