"""Record verified NHM delivery and refresh only this museum's campaign observations."""
import csv,importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-nhm-delivery-20261010.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
a,c,m,RUN=d.a,d.c,d.m,d.RUN
NEXT='a4b7823c-f659-5413-9766-60c2306d8844'

def table(name,rows):
    with (RUN/name).open('x',encoding='utf-8-sig',newline='') as out:
        w=csv.DictWriter(out,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    assert not(RUN/'delivery-001.json').exists();checks=m.load(RUN/'checks-001.json');read=m.load(RUN/'readback-001.json');public=m.load(RUN/'public-delivery-001.json');assert checks['readback_passed'] and checks['replay_zero_writes'] and checks['local_unchanged'] and public['public_artwork_samples']==6
    p,digest=a.validate_plan();assert digest==d.EXPECTED;prior=m.load(c.CP);at=m.now();assert read['verification']['current_counts']=={c.IID:dict(linked=251,eligible=184)}
    rr=prior['production_institution_register_reference'];register=m.load(c.checked(rr))['rows'];target=next(x for x in register if x['id']==c.IID);assert target['verified_production_works']==13
    target.update(production_catalogue_count_to_200=251,production_date_eligible_count_to_200=184,production_catalogue_count_state='exact',production_date_eligible_count_state='exact',verified_production_works=251,verified_production_eligible_works=184,production_catalogue_count_at=read['at'],production_date_eligible_count_at=read['at'])
    m.save(RUN/'production-institution-register-001.json.gz',dict(at=at,rows=register,previous_register_reference=rr,read_only=True,updated_institutions=[c.IID],global_exact_counts_refreshed=False,global_thresholds_refreshed=False,policy='Only National Historical Museum refreshed:251 catalogue,184 numeric-date eligible,67 unknown/unresolved. Other observations retain their own timestamps.'));table('production-institution-register-001.csv',register)
    qr=prior['priority_museum_queue_reference'];queue=m.load(c.checked(qr));assert len(queue['rows'])==226 and any(x['id']==c.IID for x in queue['rows']);queue['rows']=[x for x in queue['rows'] if x['id']!=c.IID]
    reached=dict(id=c.IID,at=read['at'],catalogue=251,date_eligible=184,basis='238 new review artworks;62 new and5 old unknown-date works retained. Catalogue100 and200 targets reached; numeric-date eligible count184.')
    queue.setdefault('removed_threshold_reached',[]).append(reached);queue.setdefault('preferred_target_reached',[]).append(reached);queue['latest_removed_threshold_reached']=reached;queue['latest_preferred_target_remaining']=dict(institution_id=c.IID,catalogue=251,gap_to100=0,gap_to200=0,target_reached=True,numeric_eligible=184)
    queue.setdefault('date_research_remaining',[]).append(dict(id=c.IID,catalogue=251,date_eligible=184,unknown_dates=67,reason='62 new unresolved creation dates: sitter/event/prototype chronology, copies, and four Iatridis object/collection date conflicts. Five old unknown dates preserved.'))
    queue.update(at=at,previous_queue_reference=qr,policy='NHM reached251 catalogue works and leaves the inherited under100 subset.225 rows remain,65 Greek; not a refreshed global census.');m.save(RUN/'priority-museum-queue-001.json',queue)
    table('delivered-production-artworks-001.csv',[dict(artwork_id=v['artwork_id'],institution_id=c.IID,action='new_record',source_id=v['facts']['source_id'],title=v['facts']['title'],date_display=v['facts']['date_display'],creation_year_start=v['facts']['first'],creation_year_end=v['facts']['last'],source_url=v['facts']['source_url'],status='review') for v in p['records']])
    table('delivered-production-images-001.csv',[dict(artwork_id=x['artwork_id'],source_id=x['source_id'],number=x['number'],primary=x['set_primary'],storage_path=x['storage_path'],sha256=x['sha256'],bytes=x['bytes'],width=x['width'],height=x['height'],rights_status=x['rights_status'],rights_label=x['rights_label'],source_url=x['source_url']) for x in p['images']])
    protected=sorted(set(p['prior_ids'])|{x['artwork_id'] for x in p['records']});assert len(protected)==2515
    m.save(RUN/'protected-production-ids-001.json',dict(at=at,ids=protected,previous_protected_records=2277,new_records=238,new_existing_links=0,composition=dict(campaign_new_artworks=2491,campaign_existing_links=7,additional_existing_image_only_records=17),plan_reference=c.ref(a.PLAN)))
    remaining=dict(at=at,institution_id=c.IID,catalogue=251,preferred200_reached=True,catalogue_gap_to200=0,numeric_date_eligible=184,unknown_numeric_dates=67,new_unknown_numbers=[v['facts']['number'] for v in p['records'] if v['facts']['first'] is None],iatri_date_conflict_numbers=[168,169,170,171],source_total=4727,painting_facet_total=1006,date_sorted_painting_total=580,paintings_omitted_by_date_sort=426,painting_index_cards_reviewed=240,additional_old_photograph_comparators=11,individual_objects_reviewed=251,source_entries_without_individual_review=4476,ready_candidates=0,resolution_gap='176 delivered authentic380pxwide source thumbnails; fullresolution originals not downloaded. Five selected TIFF-wrapper pagesHTTP500; no retry/bypass. Source7previously exposed57MBTIFF but that original remains undownloaded.',next_priority='War Museum, Athens, IID '+NEXT+'; historical12 catalogue works. Fresh production/local baseline then selected art/date/type review of1888 mixed source entries.',next_source_reference=c.ref(RUN/'next-source-discovery-001.json.gz'))
    m.save(RUN/'remaining-research-001.json',remaining)
    backup=m.load(RUN/'cloud-backup-001.json');report=dict(at=at,goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=238,existing_links=0,date_eligible_new=176,new_unknown_numeric_dates=62,verification=read['verification'],museum_before=dict(works=13,eligible_works=8,primary_images=8),museum_after=dict(works=251,eligible_works=184,primary_images=184),minimum100_catalogue_reached=True,preferred200_catalogue_reached=True,catalogue_gap_to100=0,catalogue_gap_to200=0,production_campaign_totals=dict(new_artworks=2491,existing_links=7,museums=15),historical_local_totals_unchanged=prior['historical_local_campaign_totals'],cross_database_totals_combined=False,new_images=176,new_primary_images=176,new_alternate_images=0,new_artist_links=44,remaining_pending_candidates={},remaining_pending_total=0,global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,backup_id=backup['id'],source_access='251 museum-supplied item pages and thumbnails reviewed; native painting/collection/copy context, four Iatridis pages and two bridge objects captured; native bridge images and Getty Skene authority inspected. EIM facet-only endpointHTTP500; five selected digital-file wrappersHTTP500; HPS direct connection reset. Failed routes held, no bypass or unselected originals. Three next-museum public collection pagesHTTP200.',next_work=remaining['next_priority']);m.save(RUN/'delivery-001.json',report)
    text=f'''# National Historical Museum — 10 October 2026

Added **238 review artworks**, **176 authentic source images** and **44 links to the existing James Skene artist record** in production. The museum increased from **13 to251 catalogue works**, reaching the preferred200-item catalogue target. It now has184 works with supported numeric creation dates,67 with unknown or unresolved dates, and184 illustrated works. The real local database is unchanged.

- [Artwork delivery ledger](delivered-production-artworks-001.csv)
- [Image delivery ledger](delivered-production-images-001.csv)
- [Reviewed selection](reviewed-selection-001.csv)
- [Verification](checks-001.json)
- [Remaining research](remaining-research-001.json)

The [museum-supplied SearchCulture collection](https://www.searchculture.gr/aggregator/portal/collections/EIM?language=en) contains4727 mixed entries. Its painting facet has1006 records; the date-sorted result has580 and excludes426 undated entries. We reviewed the oldest240 painting cards and11 existing photograph comparators:251 individual records and thumbnails in total, including13 existing catalogue works. These collection totals are not eligible artwork counts, and4476 source entries have not received individual review in this pass.

Bounded reconciliation checked78 production artworks and185 citations through source identifiers, known inventories, selected creator identities, informative titles and image checksums. No established duplicate was found among the238 additions. All78 comparator records and2277 prior protected records remain unchanged. General landscape titles were checked within the returned creator/source scope; this is not an exhaustive global duplicate guarantee or a ten-million-row performance test.

Sixty-two new creation dates remain unknown. Sitter lifespans, depicted historical events, digital-record timestamps and prototype dates were retained as evidence without treating them as artwork creation dates. Copies after Hess, Garneray and Köllnberger retain qualified maker labels, including Hans Hanke where explicitly supplied. Pelekasis copies remain distinct from Kallivokas originals. One Ioannidis attribution remains tentative. Four Iatridis ink works have an unresolved conflict: object pages say1824 while the museum collection narrative gives1828–1832. No date was invented and no image was attached to these uncertain works.

All251 source thumbnails,11 source contact sheets and8 prepared contact sheets were inspected. Related Pitzamanos costume studies and landscapes remain separate compositions; multiple figures or views within a single sheet were not split into extra records. Exact album, sheet and recto-verso collation remains unknown. Two similar Alamana bridge views were confirmed as different objects using native inventories15153-52 and15153-7, different dimensions, and matching native/source images. Navarino and Kaisariani views differ in their viewpoints and foregrounds.

The44 Skene views were linked to the existing James Skene of Rubislaw record. The museum's [Skene publication](https://nhmuseum.gr/ekdoseis/imerologia/item/179-imerologio-2017) and [Getty ULAN500016543](https://www.getty.edu/vow/ULANFullDisplay?find=&nation=&role=&subjectid=500016543) corroborate the name, Scottish identity,1775–1864 lifespan and WikidataQ4421861. Other named makers remain source labels without invented authorities or biographies. Prototype artists were not linked as the direct makers of copies.

The176 delivered images are authentic museum-supplied thumbnails,380pixels wide, with complete source frames and original margins. They were not enlarged or reconstructed. Fourteen JPEGs were recompressed without resizing; every delivered file is at most99508bytes. Full-resolution originals remain an improvement gap: five selected digital-file wrapper requests returnedHTTP500 and the route was stopped. The earlier successful wrapper exposed one57MBTIFF, which was not downloaded. No unselected originals were downloaded.

The museum item rights state **CC BY-NC-ND4.0** while the aggregator badge and inspected file wrapper claim **CC BY4.0**. Both claims are preserved; delivered media are classified **restricted**. The site-footer BY-SA label is not treated as an object licence. Existing user approval for the Greek museum image workflow is recorded separately from copyright-holder permission. Source images, proofs and backups are under Library, outside Documents.

Backup **{backup['id']}** succeeded before application. Sixteen offline checks, live preflight, atomic verification, independent readback and zero-write replay passed. All176 public image hashes and six public artwork samples were verified. No publication or current-display claims were added. Plan SHA-256: `{digest}`.

The selected production campaign totals **2491 new artworks and seven existing-work links across15 museums**. The extended protected set contains2515 records, including17 prior image-only enrichments. Only this museum's counts were refreshed; the inherited under100 subset now has225 rows, including65 Greek institutions. This is not a fresh global census, and the every-museum goal remains active.

Next: a fresh baseline and selected artwork review for the Athens War Museum. Its public source has1888 mixed entries and its last catalogue count was12. Discovery also recorded Nikaia's101 entries and Spathario's450 searchable entries; Spathario's description separately says453 artifacts. None of these source totals guarantees100 eligible artworks.
'''
    # Keep human-facing prose readable while retaining exact identifiers and links.
    import re
    parts=re.split(r'(`[^`]*`|https?://[^\s)]+)',text)
    for i in range(0,len(parts),2):
        parts[i]=re.sub(r'(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])', ' ',parts[i])
    text=''.join(parts)
    (RUN/'README.md').open('x',encoding='utf-8').write(text)
    print(json.dumps(dict(added=238,images=176,catalogue=251,numeric_eligible=184,protected_ids=2515,priority_rows=225)),flush=True)

if __name__=='__main__':main()
