"""Report verified photographic additions and the museum's200-item milestone."""
import csv,importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-athens-city-photographs-delivery-20261010.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
a,c,m,RUN=d.a,d.c,d.m,d.RUN

def table(name,rows):
    with (RUN/name).open('x',encoding='utf-8-sig',newline='') as out:
        w=csv.DictWriter(out,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    assert not(RUN/'delivery-001.json').exists();checks=m.load(RUN/'checks-001.json');read=m.load(RUN/'readback-001.json');public=m.load(RUN/'public-delivery-001.json');assert checks['readback_passed'] and checks['replay_zero_writes'] and checks['local_unchanged'] and public['public_artwork_samples']==4
    p,digest=a.validate_plan();assert digest==d.EXPECTED;prior=m.load(c.CP);at=m.now();assert read['verification']['current_counts']=={c.IID:dict(linked=208,eligible=111)}
    rr=prior['production_institution_register_reference'];register=m.load(c.checked(rr))['rows'];target=next(x for x in register if x['id']==c.IID);assert target['verified_production_works']==153 and target['verified_production_eligible_works']==63
    target.update(production_catalogue_count_to_200=208,production_date_eligible_count_to_200=111,production_catalogue_count_state='exact',production_date_eligible_count_state='exact',verified_production_works=208,verified_production_eligible_works=111,production_catalogue_count_at=read['at'],production_date_eligible_count_at=read['at'])
    m.save(RUN/'production-institution-register-001.json.gz',dict(at=at,rows=register,previous_register_reference=rr,read_only=True,updated_institutions=[c.IID],global_exact_counts_refreshed=False,global_thresholds_refreshed=False,policy='Only Athens City refreshed:208catalogue,111numeric-date eligible,97unknown/unresolved. Other observations retain their timestamps.'));table('production-institution-register-001.csv',register)
    qr=prior['priority_museum_queue_reference'];queue=m.load(c.checked(qr));assert len(queue['rows'])==227 and all(x['id']!=c.IID for x in queue['rows'])
    reached=dict(id=c.IID,at=read['at'],catalogue=208,date_eligible=111,basis='Catalogue target reached with explicit review-date uncertainty and digital-only photograph medium;97unknown/unresolved dates remain.')
    queue.setdefault('preferred_target_reached',[]).append(reached);queue['latest_preferred_target_remaining']=dict(institution_id=c.IID,catalogue=208,gap_to100=0,gap_to200=0,target_reached=True,numeric_eligible=111);queue.setdefault('date_research_remaining',[]).append(dict(id=c.IID,catalogue=208,date_eligible=111,unknown_dates=97,reason='Seven photograph date conflicts and90earlier unknown dates remain visible review records; no numeric dates inferred.'))
    queue.update(at=at,previous_queue_reference=qr,policy='Athens City now208catalogue works and has passed the preferred200target. It already left the under100subset, which remains227inherited rows, not a fresh global census. Other museum gaps remain active.');m.save(RUN/'priority-museum-queue-001.json',queue)
    ledger=[]
    for v in p['records']:
        f=v['facts'];ledger.append(dict(artwork_id=v['artwork_id'],institution_id=c.IID,action='new_record',source_id=f['source_id'],title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type='photograph',medium_text=f['medium'],source_url=f['source_url'],status='review'))
    table('delivered-production-artworks-001.csv',ledger)
    protected=sorted(set(p['prior_ids'])|{x['artwork_id'] for x in p['records']});assert len(protected)==2027
    m.save(RUN/'protected-production-ids-001.json',dict(at=at,ids=protected,previous_protected_records=1972,new_records=55,new_existing_links=0,composition=dict(campaign_new_artworks=2005,campaign_existing_links=5,additional_existing_image_only_records=17),plan_reference=c.ref(a.PLAN)))
    coverage=m.load(RUN/'coverage-clarification-001.json');assert coverage['photo_objects_not_reviewed']==1569
    remaining=dict(at=at,institution_id=c.IID,catalogue=208,preferred200_reached=True,catalogue_gap_to200=0,numeric_date_eligible=111,unknown_numeric_dates=97,new_date_conflict_numbers=list(range(1,8)),previous_art_scope_holds=[35,94,108],previous_art_scope_hold_namespace='athens-city-20261010',photo_source_objects_reviewed=65,photo_source_objects_not_reviewed=1569,total_collection_entries_outside_reviewed_art_indexes_and_photo_objects=2178,coverage_clarification_reference=c.ref(RUN/'coverage-clarification-001.json'),ready_candidates=0,source_medium_limit='All selected photographs say digital photograph only; original negatives/print support and digitisation/printing dates remain unspecified.',next_priority='Continue other under-target museums. Athens School of Fine Arts Gallery last8works, SearchCulture4012records and separate physical-collection claim>9000; National Historical Museum last13works, SearchCulture4727mixed records. Fresh production baselines and date/art-type selection required.',next_discovery_reference=c.ref(RUN/'next-source-discovery-001.json.gz'))
    m.save(RUN/'remaining-research-001.json',remaining)
    backup=m.load(RUN/'cloud-backup-001.json');report=dict(at=at,goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=55,existing_links=0,date_eligible_new=48,new_unknown_numeric_dates=7,verification=read['verification'],museum_before=dict(works=153,eligible_works=63,primary_images=45),museum_after=dict(works=208,eligible_works=111,primary_images=45),minimum100_catalogue_reached=True,preferred200_catalogue_reached=True,catalogue_gap_to100=0,catalogue_gap_to200=0,production_campaign_totals=dict(new_artworks=2005,existing_links=5,museums=13),historical_local_totals_unchanged=prior['historical_local_campaign_totals'],cross_database_totals_combined=False,new_images=0,new_primary_images=0,new_artist_links=0,remaining_pending_candidates={},remaining_pending_total=0,source_photo_objects_reviewed=65,source_photo_objects_remaining=1569,global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,backup_id=backup['id'],source_access='65selected SearchCulture object pages and thumbnails, donor interview and two next-museum collection pages returned200. No new provider restriction or bypass. All inherited holds preserved.',next_work=remaining['next_priority']);m.save(RUN/'delivery-001.json',report)
    (RUN/'README.md').open('x',encoding='utf-8').write(f'''# Athens City Museum — photographic works, 10 October 2026

Added **55 historical photographic works in production**, taking Athens City from **153 to 208 catalogue works**. The preferred 200-item target is reached. There are 111 numeric-date eligible works,97 with unknown or unresolved dates, and 45 illustrated works. All additions remain in review; the real local database is unchanged.

- [Delivered record ledger](delivered-production-artworks-001.csv)
- [Identity and source review](identity-review-001.json)
- [Date and catalogue source decisions](editorial-source-decisions-001.json.gz)
- [Verification](checks-001.json)
- [Remaining research and next museums](remaining-research-001.json)

The [museum-supplied SearchCulture records](https://www.searchculture.gr/aggregator/portal/collections/DigAthensMuseum?language=en) identify individual photographic images in the Koutsapli donation. Two index pages supplied 60 leads:55 new source IDs and five existing ones. Five additional existing photographs were included for comparison, so all ten old museum photographs and 65 source images were reviewed. Three contact sheets and four individual comparisons were inspected; no duplicate composition was established. Similar Piraeus church views have different camera positions, lamps and foregrounds. Similar corner buildings have different facades. Repeated generic series titles did not establish identity.

Every source medium says **“digital photograph only.”** The catalogue records the historical photographic work and its documented museum collection connection. Original negatives, vintage-print ownership, physical support and printing/digitisation dates are not asserted. A [2023 first-person donor interview](https://www.lifo.gr/culture/photography/i-mystiki-istoria-tis-elladas-se-mia-fotografiki-selida-sto-facebook) corroborates donation of an archive in printed form; it does not establish the original support or print date of each selected image. This contextual distinction remains in the records and holding evidence.

Forty-eight additions preserve source dates of 1965 or 1965–1970, including one 1965–1968 range. Seven records say 1960 in their date field while the series title says 1965–1970; their numeric dates remain null with the conflict explicit. Building dates, demolition dates and modern 2019/2025 caption notes are not photographic creation dates. Tentative place names remain tentative. Photographs of buildings and statues do not create holdings of those depicted objects.

The exact Georgios Bakouros–Liza Koutsapli archive credit remains in descriptions and citations. No individual photographer authority or biography was invented, and the donor, depicted people, architects and sculptors were not automatically made creators. Fresh bounded production checks found 153 artworks, two existing creator links and 198 citations; all 153 existing records were fully preserved. No proposed source ID or image checksum matched an existing work. This is a bounded reconciliation, not exhaustive global duplicate or 10-million-row performance proof.

No images were attached: these source dates fall after 1955 in the current Greek image-delivery workflow. The 65 authentic source thumbnails are retained only as research evidence outside Documents. All 45 existing primary images remain unchanged, as do every old title, date, source, creator link and publication state. Actual source CC0 labels remain in the evidence.

Backup **{backup['id']}** succeeded before application. Eighteen offline checks, live preflight, atomic transaction verification, independent readback and a zero-write replay passed. Four public directory searches verified one unresolved-date and three dated review records. All 1972 previously protected IDs and 153 existing museum records were preserved. Plan SHA-256: `{digest}`.

The selected production campaign now totals **2005 new artworks and five existing-work links across 13 museums**; the protected set contains 2027 IDs including 17 earlier image-only updates. Only Athens City's counts were refreshed. The 227-row under 100 priority queue is still an inherited subset, not a new global census.

Athens City's target is met, but collection/date research remains incomplete. Of 1634 source photograph entries,65 were reviewed and 1569 remain unreviewed. A coverage clarification corrects the earlier summary that omitted the five extra comparisons. The prior art-category scope holds and image holds remain. Next, review other under-target museums using the newly captured Athens School of Fine Arts Gallery and National Historical Museum collection indexes. Their source totals are not eligible artwork counts. The every-museum goal remains active.
''')
    print(json.dumps(dict(added=55,catalogue=208,numeric_eligible=111,protected_ids=2027,priority_rows=227)),flush=True)

if __name__=='__main__':main()
