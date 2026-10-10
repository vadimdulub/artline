"""Record actual verified Theocharakis delivery and update only its register row."""
import csv
import importlib.util
import json
from pathlib import Path
spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-theocharakis-delivery-20261010.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
a,c,m,RUN=d.a,d.c,d.m,d.RUN

def table(name,rows):
    with (RUN/name).open('x',encoding='utf-8-sig',newline='')as out:
        w=csv.DictWriter(out,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    assert not(RUN/'delivery-001.json').exists();checks=m.load(RUN/'checks-001.json');public=m.load(RUN/'public-delivery-001.json');readback=m.load(RUN/'readback-001.json')
    assert checks['readback_passed']and checks['replay_zero_writes']and checks['local_unchanged']and public['public_image_hashes_matched']==114 and public['public_artwork_samples']==6
    p,digest=a.validate_plan();assert digest==d.EXPECTED;prior=m.load(c.CP);at=m.now();assert readback['verification']['current_counts']=={c.IID:dict(linked=215,eligible=137)}
    rr=prior['production_institution_register_reference'];register=m.load(c.checked(rr))['rows'];target=next(x for x in register if x['id']==c.IID)
    assert target['verified_production_works']==18 and target['verified_production_eligible_works']==12
    target.update(production_catalogue_count_to_200=215,production_date_eligible_count_to_200=137,production_catalogue_count_state='exact',production_date_eligible_count_state='exact',verified_production_works=215,verified_production_eligible_works=137,production_catalogue_count_at=readback['at'],production_date_eligible_count_at=readback['at'])
    m.save(RUN/'production-institution-register-001.json.gz',dict(at=at,rows=register,previous_register_reference=rr,read_only=True,updated_institutions=[c.IID],global_exact_counts_refreshed=False,global_thresholds_refreshed=False,policy='Only Theocharakis refreshed to215 catalogue/137 numeric-date eligible artworks. Other observations retain their dates.'))
    table('production-institution-register-001.csv',register)
    qr=prior['priority_museum_queue_reference'];queue=m.load(c.checked(qr));assert len([x for x in queue['rows']if x['id']==c.IID])==1
    queue['rows']=[x for x in queue['rows']if x['id']!=c.IID];assert len(queue['rows'])==229
    queue.setdefault('removed_threshold_reached',[]).append(dict(id=c.IID,at=readback['at'],catalogue=215,date_eligible=137,preferred_catalogue_target_reached=True))
    queue.update(at=at,previous_queue_reference=qr,policy='Theocharakis215/137 exceeds200catalogue and100numeric-date eligible works.229remaining rows are an inherited under100subset, not a new global census. Chania still needs8additional catalogue works for200.')
    m.save(RUN/'priority-museum-queue-001.json',queue)
    rows=[]
    for v in p['records']+p['holdings']:
        f=v['facts'];rows.append(dict(artwork_id=v['artwork_id'],institution_id=c.IID,action='existing_work_link'if v['artwork_id']==a.r.BOAT else'new_record',source_id=f['source_id'],title=f['title'],creator_label=f['creator_label'],artist_id=a.r.ARTIST,date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],source_url=f['source_url'],status='review'))
    table('delivered-production-artworks-001.csv',rows)
    protected=sorted(set(p['prior_ids'])|{v['artwork_id']for v in p['records']+p['holdings']});assert len(protected)==1584
    m.save(RUN/'protected-production-ids-001.json',dict(at=at,ids=protected,previous_protected_records=1387,new_records=196,new_existing_links=1,composition=dict(campaign_new_artworks=1579,campaign_existing_links=5),plan_reference=c.ref(a.PLAN)))
    pending=dict(kilkis=26,zongolopoulos=199);backup=m.load(RUN/'cloud-backup-001.json')
    report=dict(at=at,goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=196,existing_links=1,date_eligible_new=124,new_unknown_numeric_dates=72,existing_target_unknown_dates_preserved=6,verification=readback['verification'],museum_before=dict(works=18,eligible_works=12,primary_images=12),museum_after=dict(works=215,eligible_works=137,primary_images=123),minimum100_reached_in_both_measures=True,preferred200_catalogue_reached=True,production_campaign_totals=dict(new_artworks=1579,existing_links=5,museums=10),historical_local_totals_unchanged=prior['historical_local_campaign_totals'],cross_database_totals_combined=False,new_images=114,new_primary_images=110,alternate_images=4,new_artist_links=196,remaining_pending_candidates=pending,remaining_pending_total=225,metadata_identity_holds=13,global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,backup_id=backup['id'],source_access='Foundation, native images, National Gallery artist authority and WikiArt Boat source responded successfully. All inherited provider access holds remain; none retried or bypassed.',next_work='Deliver reviewed Zongolopoulos199 andKilkis26 after fresh identity reconciliation. Continue Averoff/Athens City research and museums below100; Chania preferred target still needs8supported works. Theocharakis full archive not exhaustively reviewed;215catalogue target reached without counting ambiguous sheets or unselected documentation.')
    m.save(RUN/'delivery-001.json',report)
    (RUN/'README.md').open('x',encoding='utf-8').write(f'''# Theocharakis Foundation — selected collection delivered, 10 October 2026

Added **196 production review artworks**, linked **one existing artwork** to its documented holding, and attached **114 authentic images**. Theocharakis now has **215 catalogue artworks**, up from 18, including **137 works with qualifying numeric creation dates**, up from 12. **123 catalogue artworks have primary images**. The real local database remains unchanged.

- [Delivered artworks and existing-work link](delivered-production-artworks-001.csv)
- [Identity decisions](identity-review-001.json)
- [Database and preservation checks](checks-001.json)
- [Public image and artwork verification](public-delivery-001.json)
- [Delivery record](delivery-001.json)
- [Initial physical-sheet research](../theocharakis-20261010/README.md)
- [Dated selection research](../theocharakis-dated-20261010/README.md)

The 197 candidates resolved to 196 new physical artworks and one existing record. The new records comprise 147 drawings, 37 paintings and 12 watercolours. Native **Boat at Paros (1948), source 103169**, matches the existing [WikiArt Boat](https://www.wikiart.org/en/spyros-papaloukas/boat-1948): the red hull, benches, wave marks, shoreline and signature agree. The existing title, date, type, artist link and primary image were preserved; its museum image is an alternate. No duplicate artwork was created.

The unique existing **Spyros Papaloukas** authority matches the native attribution, English name and 1892–1957 lifespan in the [National Gallery artist record](https://www.nationalgallery.gr/en/artist/papaloukas-spyros/). All 196 new works link to that artist; original creator labels remain in citations and attribution notes. Artist metadata and all existing creator links remain unchanged. The [foundation's account](https://thf.gr/en/the-foundation/) confirms its Papaloukas collection; holdings do not establish current display.

Eight pairs of opposite sides count as eight sheets. Their source pages and side descriptions remain together in metadata. One canonical external identifier is stored per new physical artwork, with all **205 candidate source records** retained in the metadata evidence. Thirteen unresolved source identities remain held. Four additional references to existing sheets remain research evidence without changing their dates or generating extra artworks. The earlier subject-by-subject visual review remains applicable.

**72 new records remain undated**; no dates were inferred from Papaloukas's lifespan. Broader native date intervals for Spyros Marinatos and Danae are preserved alongside the shorter aggregator values. New records remain in review; all existing states, unknown dates and images are preserved. Page IDs and filenames are not invented accession numbers.

The 114 images comprise **110 new primary images**, three additional sides of new sheets and the alternate Boat image. Each complete frame was checked across eight contact sheets; JPEG derivatives are no more than 100,000 bytes, with originals retained separately. Actual **CC BY-SA 4.0** labels, credits and source links are preserved. The 72 undated works, 13 works ending after the museum-image cutoff of 1955, and the pear study with conflicting image/dimensions remain unillustrated. Their metadata remains available in review.

Live source, creator, exact-title and image checks returned 3,766 comparison records; 65 relevant records received full preserved snapshots. Eighteen existing Papaloukas photographs were inspected, including five self-portrait comparisons and monastery/landscape variants. Two older Boy with Suspenders records appear to duplicate each other; that separate pre-existing issue is recorded without merging or assigning them to Theocharakis.

Backup **{backup['id']}** succeeded before atomic application. **23 offline checks**, live preflight, atomic verification, independent readback and zero-write replay passed. All **114 public image hashes** matched; six API checks covered four dated new artworks, an undated work through its public artist route, and Boat with its original primary image and new holding. The 65 existing comparators and 1,387 previous campaign records were protected. Plan SHA-256: `{digest}`.

The selected production campaign now totals **1,579 new artworks and five existing-work links across ten museums**, protecting 1,584 IDs. Only Theocharakis's count was refreshed; the remaining 229-row priority subset is not a new global census. **225 researched candidates** remain pending: Zongolopoulos 199 and Kilkis 26. Historical local campaign totals stay separate.

Theocharakis has exceeded the preferred **200 catalogue artwork** target. Its full archive has not been exhausted, and source documentation is not automatically an eligible physical artwork. The every-museum goal remains active and incomplete.
''')
    print(json.dumps(dict(added=196,links=1,images=114,catalogue=215,numeric_eligible=137,protected_ids=1584,pending_candidates=225,priority_rows=229)),flush=True)
if __name__=='__main__':main()
