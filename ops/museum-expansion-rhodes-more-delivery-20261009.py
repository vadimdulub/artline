"""Rhodes further selection delivered, with dated counts and all remaining source gaps."""
import collections,csv,importlib.util,json,io
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-rhodes-more-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);m=a.m;RUN=a.RUN

def table(name,rows):
 fp=io.StringIO(newline='');w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows);raw=fp.getvalue().encode();path=RUN/name
 if path.exists():assert path.read_bytes()==raw,'Preserve existing delivery CSV: '+name
 else:path.write_bytes(raw)
def main():
 p,digest=a.validate_plan();receipt=m.load(RUN/(a.KEY+'-applied.json'));checks=m.load(RUN/'checks-001.json');assert checks['offline_tests_passed']==19 and checks['atomic_verification_passed']and checks['replay_zero_writes'];assert receipt['plan_sha256']==digest
 prior=m.load(a.CHECKPOINT);rr=prior['production_institution_register_reference'];register=m.load(a.checked(rr))['rows'];target=next(v for v in register if v['id']==a.IID);assert target['verified_production_works']==107
 with a.i.prod.connect()as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY');verified=a.verify(db,p,digest)
 with m.connect()as db:
  initial=m.load(RUN/'initial-scope-001.json.gz');assert a.snapshot(db,initial['scoped_ids'])==initial['snapshot']and a.counts(db)==initial['counts']
 at=m.now();after=verified['current_counts'][a.IID];before=p['before_counts'][a.IID]
 target.update(production_catalogue_count_to_200=172,production_date_eligible_count_to_200=166,production_catalogue_count_state='exact',production_date_eligible_count_state='exact',verified_production_works=after['linked'],verified_production_eligible_works=after['eligible'],production_catalogue_count_at=at,production_date_eligible_count_at=at)
 m.save(RUN/'production-institution-register-001.json.gz',dict(at=at,rows=register,previous_register_reference=rr,read_only=True,updated_institutions=[a.IID],global_exact_counts_refreshed=False,global_thresholds_refreshed=False,policy='Only Rhodes refreshed to172catalogue/166dateeligible. Other observations retain timestamps; the200-work aspiration remains open.'));table('production-institution-register-001.csv',register)
 qr=prior['priority_museum_queue_reference'];queue=m.load(a.checked(qr));assert not any(v['id']==a.IID for v in queue['rows']);queue.update(at=at,previous_queue_reference=qr,policy='Rhodes already cleared both100-work minimums in wave109. Now172catalogue/166dateeligible; continue bounded selection toward200 before next priority. Historical threshold-removal entries preserved.');m.save(RUN/'priority-museum-queue-001.json',queue)
 added=[]
 for v in p['records']:
  f=v['facts'];added.append(dict(artwork_id=v['artwork_id'],institution_id=a.IID,source_id=f['source_id'],title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],inventory=f['inventory'],source_url=f['source_url'],status='review'))
 table('added-production-artworks-001.csv',added);decisions=a.r.build();ledger=[dict(number=v['number'],source_url=v['facts']['source_url'],inventory=v['facts']['inventory'],title=v['facts']['title'],state=v['state'],reason=v['basis'],existing_artwork_ids=';'.join(sorted({c['entity_id']for c in v['comparison']['source_hits']})))for v in decisions];table('all-source-decisions-001.csv',ledger)
 total=prior['production_campaign_totals']['new_artworks']+65;assert total==777
 report=dict(at=at,goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=65,existing_links=0,date_eligible_added=65,before_date_added=1,editorial_holds=3,already_catalogued=1,unknown_date_deferred=27,after1970_excluded=64,reviewed_native_objects=160,cumulative_rhodes_reviewed_native_objects=280,source_collection_reported_objects=1502,remaining_metadata_not_fetched=1222,verification=verified,museum_before=dict(works=before['linked'],eligible_works=before['eligible']),museum_after=dict(works=after['linked'],eligible_works=after['eligible']),production_campaign_new_artworks=total,production_campaign_museums=6,historical_local_totals_unchanged=prior['historical_local_campaign_totals'],cross_database_totals_combined=False,global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,remaining_to_200_catalogue=28,remaining_to_200_dateeligible=34,source_access='Official Rhodes public portal accessible. Historical provider holds persist. Four selected reference images inspected for identity; no image attachments or catalogue image changes.',next_work='Use60 index leads280–339 from pages14–16 in next-source-discovery-001.json.gz; individual metadata still unreviewed. Then bounded page17 onward only if needed. Continue toward200 with physical creation/version checks. Preserve wave109 nineholds,18unknowns and wave110 threecutoffholds,27unknowns. After Rhodes, priority starts Nikos Kazantzakis Museum; literary documents are not automatically artworks.')
 m.save(RUN/'delivery-001.json',report)
 (RUN/'README.md').write_text(f'''# Rhodes — further selected artworks, 9 October 2026

Added **65 production review artworks**, taking the Municipal Art Gallery of Rhodes / Museum of Modern Greek Art from **107 to 172 catalogue works** and **101 to 166 date-eligible works**. The preferred 200-work target remains open: 28 more catalogue works, or 34 more date-eligible works. The real local catalogue remains unchanged at 3 linked works, 1 date eligible.

- [65 delivered artworks](added-production-artworks-001.csv)
- [All 160 source decisions](all-source-decisions-001.csv)
- [Dated museum register](production-institution-register-001.csv)
- [Verification and remaining work](delivery-001.json)

Individual records in the [official digital collection](https://portal.mgamuseum.gr/) establish object identities and museum holdings. The prior [institution reconciliation](../rhodes-20261009/institution-reconciliation-001.json) remains applicable. Holdings do not establish current display or venue.

This batch reviewed 160 further native records: 65 additions, 1 existing exact object skipped, 64 explicit post-1970 exclusions, 27 unknown-date research leads and 3 cutoff holds (two circa1970 portraits/studies and one1970s Weaver). Across both Rhodes rounds, 280 of the portal’s reported 1502 objects have individual metadata reviewed; 1222 remain unexamined. Sixty next index leads are captured separately, without individual detail review. This is selected research, not exhaustive downloading.

New works include Semertzidis paintings and separately documented physical studies, Afro’s four1938 season panels, Ajmone’s circa1939–1941 island views, works by Asteriadis,Parthenis,Lagana,Pentzikis,Bekiari,Vakalo and Vasiliou, and selected prints. Two threshing-machine studies depict different men despite equal titles and dimensions. Composite study sheets and painted manuscript double pages count as one artwork each. No mural, complete cycle or album was added as another parent object.

Physical creation remains separate from depicted events, ancient prototypes, artist lifespans and repository dates. Asteriadis’s Ploughing retains an unknown lower bound and the explicit before1948 endpoint. A1841/1841–1842 print-publication discrepancy remains a range. Exact1970 is eligible; circa1970 and the1970s remain held. Dry-media drawings and watercolours use their documented materials while retaining the portal’s broader painting classification in source evidence.

Four selected reference images were inspected for two translated-title comparisons. Kontopoulos’s1958 museum oil differs from the existing [1959 WikiArt drawing](https://www.wikiart.org/en/alekos-kontopoulos/one-country-1959). Parthenis’s square pomegranate still life differs from the [wide WikiArt still life](https://www.wikiart.org/en/konstantinos-parthenis/still-life-1935). Images, observations and checksums are retained in [visual assessment](visual-assessment-001.json). No new images were attached and existing catalogue images were preserved.

Nineteen offline tests passed. A successful Cloud SQL backup preceded the atomic write and readback; replay made zero writes. All {verified['protected_existing_records']} protected existing records and 712 prior production additions remained unchanged. Identity reconciliation reviewed 8879 bounded artwork candidates,17552 citations and153 focused full-row comparators. Query plans and timings are retained; they are not a10million-row load proof. Preparation first stopped on a file-enumeration typo before any database write; the helper was corrected, its existing identical prewrite backup preserved, and tests and preflight rerun.

This selected production phase totals **{total} additions across six museums**, separate from historical local totals. Only the Rhodes register row was refreshed; global counts retain their earlier observation dates. Continue Rhodes toward200 using index leads280–339,pages14–16,then page17 onward if needed. The all-museum goal remains active.
''');print(json.dumps(dict(added=65,counts=after,production_campaign=total,states=dict(collections.Counter(v['state']for v in ledger)),queue=len(queue['rows']))),flush=True)
if __name__=='__main__':main()
