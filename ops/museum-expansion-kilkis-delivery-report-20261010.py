"""Report verified Kilkis delivery and refresh its institutional count only."""
import csv
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-kilkis-delivery-20261010.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
a,c,m,RUN=d.a,d.c,d.m,d.RUN

def table(name,rows):
    with (RUN/name).open('x',encoding='utf-8-sig',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def main():
    assert not(RUN/'delivery-001.json').exists()
    checks=m.load(RUN/'checks-001.json');public=m.load(RUN/'public-delivery-001.json');read=m.load(RUN/'readback-001.json')
    assert checks['readback_passed'] and checks['replay_zero_writes'] and checks['local_unchanged']
    assert public['public_image_hashes_matched']==53 and public['public_artwork_samples']==4
    p,digest=a.validate_plan();assert digest==d.EXPECTED
    prior=m.load(c.CP);at=m.now();assert read['verification']['current_counts']=={c.IID:dict(linked=56,eligible=0)}
    rr=prior['production_institution_register_reference'];register=m.load(c.checked(rr))['rows'];target=next(x for x in register if x['id']==c.IID)
    assert target['verified_production_works']==18 and target['verified_production_eligible_works']==0
    target.update(production_catalogue_count_to_200=56,production_date_eligible_count_to_200=0,production_catalogue_count_state='exact',production_date_eligible_count_state='exact',verified_production_works=56,verified_production_eligible_works=0,production_catalogue_count_at=read['at'],production_date_eligible_count_at=read['at'])
    m.save(RUN/'production-institution-register-001.json.gz',dict(at=at,rows=register,previous_register_reference=rr,read_only=True,updated_institutions=[c.IID],global_exact_counts_refreshed=False,global_thresholds_refreshed=False,policy='Only Kilkis refreshed:56 catalogue records, all with unknown numeric creation years. Explicit source historical periods remain evidence. Other institutional observations retain their dates.'))
    table('production-institution-register-001.csv',register)
    qr=prior['priority_museum_queue_reference'];queue=m.load(c.checked(qr));target=next(x for x in queue['rows'] if x['id']==c.IID)
    assert target['catalogue_count_to_200']==18 and len(queue['rows'])==228
    target.update(catalogue_count_to_200=56,count_state='exact',gap_to_100=44,gap_to_200=144,date_eligible_count_to_200=0,catalogue_count_at=read['at'],date_eligible_count_at=read['at'])
    queue.update(at=at,previous_queue_reference=qr,policy='Kilkis refreshed to56 catalogue works;44 more documented works needed for100 and144 for200. All56 numeric dates remain unknown, with source historical periods preserved.228 inherited under100 catalogue rows remain a subset, not a new global census.')
    m.save(RUN/'priority-museum-queue-001.json',queue)
    rows=[]
    for v in p['records']:
        f=v['facts'];rows.append(dict(artwork_id=v['artwork_id'],institution_id=c.IID,action='new_record',source_id=f['source_id'],title=f['title'],creator_label=f['creator_label'],artist_id=None,date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],source_url=f['source_url'],status='review'))
    table('delivered-production-artworks-001.csv',rows)
    new={v['artwork_id'] for v in p['records']};old_images={v['artwork_id'] for v in p['images']}-new
    assert len(new)==38 and len(old_images)==17 and not old_images&set(p['prior_ids'])
    protected=sorted(set(p['prior_ids'])|new|old_images);assert len(protected)==1837
    m.save(RUN/'protected-production-ids-001.json',dict(at=at,ids=protected,previous_protected_records=1782,new_records=38,new_existing_links=0,additional_existing_image_only_ids=sorted(old_images),composition=dict(campaign_new_artworks=1815,campaign_existing_links=5,additional_existing_image_only_records=17),plan_reference=c.ref(a.PLAN)))
    backup=m.load(RUN/'cloud-backup-001.json')
    report=dict(at=at,goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=38,existing_links=0,date_eligible_new=0,new_unknown_numeric_dates=38,existing_target_unknown_dates_preserved=18,verification=read['verification'],museum_before=dict(works=18,eligible_works=0,primary_images=0),museum_after=dict(works=56,eligible_works=0,primary_images=53),minimum100_catalogue_reached=False,preferred200_catalogue_reached=False,catalogue_gap_to100=44,catalogue_gap_to200=144,production_campaign_totals=dict(new_artworks=1815,existing_links=5,museums=12),historical_local_totals_unchanged=prior['historical_local_campaign_totals'],cross_database_totals_combined=False,new_images=53,new_primary_images=53,images_on_new_records=36,images_on_existing_records=17,alternate_images=0,new_artist_links=0,remaining_pending_candidates={},remaining_pending_total=0,metadata_identity_holds=12,existing_image_identity_holds=1,source_index_entries_reviewed=65,additional_scholarly_entries_reviewed=3,global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,backup_id=backup['id'],source_access='Selected SearchCulture and native Kilkis pages/images returned200. No new access restrictions. Inherited restrictions, including the separate Morrylos journal403 and Averoff native403, remain unchanged; no retries or bypass.',next_work='Continue fresh Athens City collection research. Kilkis still needs44 documented works for100; all65 public index objects were reviewed, so additional sources are needed. Preserve12 source-entry holds and the existing statue image conflict. A book advertises87 sculptures, but its limited public excerpt is not87 importable objects.')
    m.save(RUN/'delivery-001.json',report)
    (RUN/'README.md').open('x',encoding='utf-8').write(f'''# Archaeological Museum of Kilkis — selected delivery, 10 October 2026

Added **38 production review artworks and 53 authentic primary images**. Kilkis now has **56 catalogue items**, up from 18; 53 have images. **44 more documented items are needed for 100**, or 144 for 200. The real local database remains unchanged.

- [Delivered artwork ledger](delivered-production-artworks-001.csv)
- [Object and duplicate review](identity-review-001.json)
- [Source decisions](source-review-001.json.gz)
- [Database preservation checks](checks-001.json)
- [Public delivery verification](public-delivery-001.json)
- [Delivery record](delivery-001.json)

The review covered all 65 objects in [SearchCulture's Kilkis collection](https://www.searchculture.gr/aggregator/portal/collections/Efa_Kilkis_col?language=en), corresponding native museum records and three additional entries in the public excerpt of Eleni Papagianni's 2025 sculpture catalogue, ISBN 9789601226781. The 38 additions comprise 36 selected online objects and two separately accessioned marble torsos,331 and 2046, documented in that scholarly excerpt. The two torsos remain unillustrated because their plate is absent. The fragmentary entry 134 remains held. A shared book URL is not evidence that different accessions are the same object.

**All 56 numeric creation dates remain unknown.** Ancient and Byzantine historical-period labels are preserved without invented year ranges. Discovery dates, modern publication dates, historical figures' activity dates and later reuse do not become manufacture dates. Explicit ancient/Byzantine periods support the pre 1956 image selection; these records still have no numeric timeline eligibility. One native Roman versus aggregator Hellenistic conflict remains explicit.

New records comprise 13 sculptures and 25 objects whose controlled type remains unknown. Actual vessel, jewellery, inscribed-stone, architectural and armour forms remain in source evidence. Anonymous creators stay unknown. A greave pair counts once, joined fragments of a vessel count once, and a reused inscribed block counts once; missing parent statues or conjectural complete ornaments were not invented. Holdings do not claim current display.

Twelve source entries remain held: six earlier incomplete or conflicting identities and six components sharing inventory 5044 whose relationship is unresolved. The AEMK 3 photograph conflicts with its object description, while existing AEMK 2 has a reciprocal mismatch. Neither image was swapped or attached. Existing AEMK 2 remains unillustrated. The other 17 existing items received matched photographs without changes to catalogue metadata, dates or publication state.

Fresh production comparison covered 267 bounded artwork records,152 creator links and 363 citations. Full snapshots protected 26 focused records, including all 18 existing Kilkis items and eight foreign title comparators. Five existing public images and four Kilkis comparison images were visually reviewed. Cleveland's silver amphoriskos and Larnaca's decorated glass vessel were distinguished using retained primary catalogue evidence; neither was confused with Kilkis clay vessels. Generic titles and coincident bare inventory digits did not establish identity. This is not an exhaustive duplicate guarantee or a 10-million-row performance test.

The 53 images retain complete frames, proportional dimensions and source credits; prepared JPEGs are at most 99,957 bytes. Originals and visual proofs remain outside Documents. Actual **CC BY-NC-ND 4.0** labels remain recorded as restricted. The user's Greek source approval is separate evidence and does not claim an independently obtained copyright-holder licence. Thirty-six images illustrate new records and 17 fill previously empty primaries; no existing primary was replaced.

Backup **{backup['id']}** succeeded before application. Twenty-three offline checks, live preflight, transaction verification, independent readback and a zero-write replay passed. All 53 public image hashes matched, and four public artwork-directory searches returned the expected undated review records, including an unillustrated torso. All 1,782 prior campaign IDs were preserved. Plan SHA-256: `{digest}`.

The selected production campaign totals **1,815 new artworks and five existing-work links across 12 museums**. Future preservation includes those 1,820 IDs plus 17 existing Kilkis works whose images were filled, for 1,837 protected IDs. Only Kilkis's register row was refreshed; the 228-row priority subset is not a new global census. No researched candidates remain ready in the previous pending queue; further source research is required. The every-museum goal remains active and incomplete.
''')
    print(json.dumps(dict(added=38,images=53,catalogue=56,protected_ids=1837,pending_candidates=0,priority_rows=228)),flush=True)

if __name__=='__main__':main()
