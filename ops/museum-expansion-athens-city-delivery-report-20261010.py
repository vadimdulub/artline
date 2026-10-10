"""Report verified Athens City additions and refresh only its observed counts."""
import csv,importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-athens-city-delivery-20261010.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
a,c,m,RUN=d.a,d.c,d.m,d.RUN

def table(name,rows):
    with (RUN/name).open('x',encoding='utf-8-sig',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def main():
    assert not(RUN/'delivery-001.json').exists();checks=m.load(RUN/'checks-001.json');public=m.load(RUN/'public-delivery-001.json');read=m.load(RUN/'readback-001.json')
    assert checks['readback_passed'] and checks['replay_zero_writes'] and checks['local_unchanged'];assert public['public_image_hashes_matched']==39 and public['public_artwork_samples']==4
    p,digest=a.validate_plan();assert digest==d.EXPECTED;prior=m.load(c.CP);at=m.now();assert read['verification']['current_counts']=={c.IID:dict(linked=153,eligible=63)}
    rr=prior['production_institution_register_reference'];register=m.load(c.checked(rr))['rows'];target=next(x for x in register if x['id']==c.IID);assert target['verified_production_works']==18 and target['verified_production_eligible_works']==16
    target.update(production_catalogue_count_to_200=153,production_date_eligible_count_to_200=63,production_catalogue_count_state='exact',production_date_eligible_count_state='exact',verified_production_works=153,verified_production_eligible_works=63,production_catalogue_count_at=read['at'],production_date_eligible_count_at=read['at'])
    m.save(RUN/'production-institution-register-001.json.gz',dict(at=at,rows=register,previous_register_reference=rr,read_only=True,updated_institutions=[c.IID],global_exact_counts_refreshed=False,global_thresholds_refreshed=False,policy='Only Athens City refreshed:153catalogue records,63numeric-date eligible,90unknown-date. Other institutional observations retain their timestamps.'))
    table('production-institution-register-001.csv',register)
    qr=prior['priority_museum_queue_reference'];queue=m.load(c.checked(qr));target=next(x for x in queue['rows'] if x['id']==c.IID);assert target['catalogue_count_to_200']==18 and len(queue['rows'])==228
    queue['rows']=[x for x in queue['rows'] if x['id']!=c.IID];queue.update(at=at,previous_queue_reference=qr,policy='Athens City passed100with153catalogue works and leaves this under100subset.47additional documented works needed for200;63numeric-date eligible.227inherited rows remain a subset, not a fresh global census.')
    remaining=dict(institution_id=c.IID,catalogue=153,gap_to100=0,gap_to200=47,target_reached=False,numeric_eligible=63)
    queue['latest_removed_threshold_reached']=dict(institution_id=c.IID,catalogue=153,at=read['at']);queue['latest_preferred_target_remaining']=remaining
    m.save(RUN/'priority-museum-queue-001.json',queue)
    rows=[]
    for v in p['records']:
        f=v['facts'];rows.append(dict(artwork_id=v['artwork_id'],institution_id=c.IID,action='new_record',source_id=f['source_id'],title=f['title'],creator_label=f['creator_label'],artist_id=f['artist_id'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],object_form=f['object_form'],source_url=f['source_url'],status='review'))
    table('delivered-production-artworks-001.csv',rows)
    new={v['artwork_id'] for v in p['records']};assert len(new)==135 and not new&set(p['prior_ids']);protected=sorted(set(p['prior_ids'])|new);assert len(protected)==1972
    m.save(RUN/'protected-production-ids-001.json',dict(at=at,ids=protected,previous_protected_records=1837,new_records=135,new_existing_links=0,additional_existing_image_only_ids=[],composition=dict(campaign_new_artworks=1950,campaign_existing_links=5,additional_existing_image_only_records=17),plan_reference=c.ref(a.PLAN)))
    remaining_research=dict(at=at,institution_id=c.IID,catalogue=153,gap_to100=0,gap_to200=47,source_total_observed=2405,selected_categories=['Painting','Engraving','Drawing','Lithography','Icon','Sculpture','Mixed media work of art','Mosaic'],unique_selected_index_records_reviewed=162,object_details_reviewed=145,index_post1970_excluded=17,delivered_new=135,existing_comparators=7,scope_holds=[35,94,108],other_records_unreviewed=2243,ready_candidates=0,unknown_numeric_dates_new=88,unknown_numeric_dates_total=90,next_selection='Review a bounded selection of dated photographs or other original art objects from the observed public SearchCulture filters. Inspect physical print/version dates and duplicate source IDs before adding.1634photograph records is a source facet count, not an eligible-artwork count.',next_index_reference=c.ref(RUN/'next-photograph-index-001.json.gz'),next_index_cards=60,next_index_already_catalogued=5,next_index_uncatalogued_leads=55,source42_image_hold='Thumbnail returned non-image200; no retry and no visual claim. Metadata object added without image.',native_portal='SPA shell observed200; high-resolution assets not obtained. Do not reuse embedded client authorization values or guess unobserved APIs.',research_checkpoint=c.ref(c.RESEARCH_CP))
    m.save(RUN/'remaining-research-001.json',remaining_research)
    backup=m.load(RUN/'cloud-backup-001.json')
    report=dict(at=at,goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=135,existing_links=0,date_eligible_new=47,new_unknown_numeric_dates=88,existing_target_unknown_dates_preserved=2,verification=read['verification'],museum_before=dict(works=18,eligible_works=16,primary_images=6),museum_after=dict(works=153,eligible_works=63,primary_images=45),minimum100_catalogue_reached=True,preferred200_catalogue_reached=False,catalogue_gap_to100=0,catalogue_gap_to200=47,production_campaign_totals=dict(new_artworks=1950,existing_links=5,museums=13),historical_local_totals_unchanged=prior['historical_local_campaign_totals'],cross_database_totals_combined=False,new_images=39,new_primary_images=39,images_on_new_records=39,images_on_existing_records=0,alternate_images=0,new_artist_links=2,remaining_pending_candidates={},remaining_pending_total=0,metadata_scope_holds=3,source_index_entries_reviewed=162,global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,backup_id=backup['id'],source_access='Four observed SearchCulture person-authority pages returned200. Three existing public Artline comparison images matched stored checksums. Source42non-image thumbnail hold and all inherited provider holds preserved; no blocked provider retried.',next_work=remaining_research['next_selection'])
    m.save(RUN/'delivery-001.json',report)
    (RUN/'README.md').open('x',encoding='utf-8').write(f'''# Athens City Museum — selected delivery, 10 October 2026

Added **135 review artworks and 39 authentic images to production**. Athens City now has **153 catalogue items**, up from 18, with 45 primary images. The 100-item minimum is reached; **47 more documented works are needed for 200**. The real local database remains unchanged.

- [Delivered artwork ledger](delivered-production-artworks-001.csv)
- [Identity and creator review](identity-review-001.json)
- [Preservation and delivery checks](checks-001.json)
- [Public image and artwork verification](public-delivery-001.json)
- [Remaining research](remaining-research-001.json)

The [museum's SearchCulture collection](https://www.searchculture.gr/aggregator/portal/collections/DigAthensMuseum?language=en) supplies the object evidence. All eight selected art categories were indexed: 162 unique records across ten pages. Seventeen explicitly post 1970 entries were excluded before object/image retrieval;145 detail pages produced 135 additions, seven existing comparators and three scope holds. The collection's 2405 mixed records include photographs, furniture, documents, reproductions and later objects. The 2243 records outside the selected art categories remain unreviewed; the total is not an eligible artwork count.

The additions include 47 prints,35 paintings,38 drawings,three watercolours,ten sculptures and two decorative objects whose controlled work type remains unknown. Fourteen paintings are explicitly marked as icons, including one Russian icon with its metal covering and case counted as one physical object. Joined parts, pairs of drawings on one sheet and individual student studies each count once per documented physical unit. A decorated frame with a Tinos-icon postcard is not catalogued as ownership of the original icon.

Forty-seven additions have source-supported numeric dates;88 remain undated or unresolved. The museum now has 63 numeric-date eligible records and 90 unknown-date records. Review items remain visible in the unified catalogue, while unknown dates do not become timeline eligibility. Source inscriptions, depicted events, artist lifespans and copied signatures are not invented creation dates. The conflicting circa 1850/1853–1854 Otto print remains undated. The likely 1972 menu lithograph, explicit 2018 work and undated modern digital print after another original remain held.

Fresh reconciliation retained 1740 bounded artwork observations,1368 creator links and 4079 citations;135 focused artworks have complete preservation snapshots. Three existing Artline images were compared with eight Athens source frames. Similar port titles identify different paintings or prints. The Venice print differs in composition from existing Edward Brandard B1977.14.13883. Full-length and oval Thon portraits remain distinct. Only two secure links were added to existing artists: Thaleia Flora-Karavia and Georgios Iakovidis. Their source-linked authorities and lifespans agree; sitters remain separate from makers. Vyron Kontopoulos is not Alekos Kontopoulos. Designer/engraver roles and questioned or contradictory attributions remain explicit object-level labels. This bounded check is not an exhaustive duplicate guarantee or a 10-million-row performance test.

All 39 images retain the complete source JPEG byte-for-byte, including frames and source inventory labels, at no more than 34,499 bytes. They are generally 380 pixels wide; native high-resolution files were not obtained. Actual source **Public Domain CC0** labels, credits and the separate Greek-source approval are preserved. All 39 selected works have explicit source dates at or before 1955. No existing primary image was replaced. Source 42's non-image thumbnail was not retried; the described lion statuette was added as metadata only. Source 31's available frame is a verso and was not attached as a front image.

Backup **{backup['id']}** succeeded before application. Twenty offline checks passed, followed by live preflight, atomic verification, independent readback and a zero-write replay. An initial test-harness error supplied draft images to a planned-image preservation check; the corrected test version passed with the writer unchanged. All 39 public image hashes matched, and four public searches returned two dated and two undated review works. All 1837 previously protected IDs and 135 focused existing records were preserved. Plan SHA-256: `{digest}`.

The selected production campaign totals **1950 new artworks and five existing-work links across 13 museums**. The protected set now has 1972 IDs, including 17 earlier image-only updates. Only Athens City's register row was refreshed; the remaining 227 under 100 priority rows are an inherited subset, not a new global census. The every-museum goal remains active and incomplete. Two new photograph-index pages provide 60 leads, including five already catalogued source IDs. The 55 other IDs have index dates between 1960 and 1970; full object, physical-version and duplicate review remains necessary before adding any. Continue that bounded research toward the 47-work gap, while preserving all source, date and identity holds.
''')
    print(json.dumps(dict(added=135,images=39,catalogue=153,protected_ids=1972,pending_candidates=0,priority_rows=227)),flush=True)

if __name__=='__main__':main()
