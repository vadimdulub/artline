"""Record verified production results and update only Larissa's dated register row."""
import csv
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-larissa-delivery-20261010.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
a,c,m,RUN=d.a,d.c,d.m,d.RUN

def table(name,rows):
    with (RUN/name).open('x',encoding='utf-8-sig',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def main():
    assert not(RUN/'delivery-001.json').exists()
    checks=m.load(RUN/'checks-001.json');public=m.load(RUN/'public-delivery-001.json');readback=m.load(RUN/'readback-001.json')
    assert checks['readback_passed'] and checks['replay_zero_writes'] and checks['local_unchanged'] and public['public_image_hashes_matched']==205
    p,digest=a.validate_plan();assert digest==d.EXPECTED;prior=m.load(c.CP);at=m.now()
    assert readback['verification']['current_counts']=={c.IID:dict(linked=205,eligible=193)}
    rr=prior['production_institution_register_reference'];register=m.load(c.checked(rr))['rows'];target=next(x for x in register if x['id']==c.IID)
    assert target['verified_production_works']==18 and target['verified_production_eligible_works']==15
    target.update(production_catalogue_count_to_200=205,production_date_eligible_count_to_200=193,production_catalogue_count_state='exact',production_date_eligible_count_state='exact',verified_production_works=205,verified_production_eligible_works=193,production_catalogue_count_at=readback['at'],production_date_eligible_count_at=readback['at'])
    m.save(RUN/'production-institution-register-001.json.gz',dict(at=at,rows=register,previous_register_reference=rr,read_only=True,updated_institutions=[c.IID],global_exact_counts_refreshed=False,global_thresholds_refreshed=False,policy='Only Larissa refreshed to205 catalogue/193 numeric date-eligible artworks. All other counts retain their observation dates.'))
    table('production-institution-register-001.csv',register)
    qr=prior['priority_museum_queue_reference'];queue=m.load(c.checked(qr));removed=[x for x in queue['rows'] if x['id']==c.IID];assert len(removed)==1
    queue['rows']=[x for x in queue['rows'] if x['id']!=c.IID];assert len(queue['rows'])==231
    queue.setdefault('removed_threshold_reached',[]).append(dict(id=c.IID,at=readback['at'],catalogue=205,date_eligible=193))
    queue.setdefault('preferred_target_reached',[]).append(dict(id=c.IID,at=readback['at'],catalogue=205,date_eligible=193,basis='Catalogue count including explicit review-date uncertainty; numeric date-eligible count remains193.'))
    queue.update(at=at,previous_queue_reference=qr,policy='Larissa now205/193 and removed from the inherited under100 priority subset.231 remaining queue rows are not a new global census.')
    m.save(RUN/'priority-museum-queue-001.json',queue)
    rows=[]
    for action,units in [('new',p['records']),('existing_work_link',p['holdings'])]:
        for v in units:
            f=v['facts'];rows.append(dict(action=action,artwork_id=v['artwork_id'],institution_id=c.IID,source_id=f['source_id'],title=f['title'],creator_label=f['creator_label'],source_date_display=f['date_display'],source_year_start=f['first'],source_year_end=f['last'],source_work_type=f['work_type'],source_url=f['source_url'],status='review',existing_metadata_preserved=action=='existing_work_link'))
    table('delivered-production-artworks-001.csv',rows)
    protected=sorted(set(p['prior_ids'])|{x['artwork_id'] for x in p['records']+p['holdings']});assert len(protected)==1213
    m.save(RUN/'protected-production-ids-001.json',dict(at=at,ids=protected,previous_protected_records=1026,new_records=184,new_existing_links=3,composition=dict(campaign_new_artworks=1209,campaign_existing_links=4),plan_reference=c.ref(a.PLAN)))
    remaining=dict(kilkis=26,theocharakis=197,zongolopoulos=199,chania=174);assert sum(remaining.values())==596
    backup=m.load(RUN/'cloud-backup-001.json')
    report=dict(at=at,goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=184,existing_links=3,date_eligible_new=177,date_eligible_existing_links=1,new_unknown_dates=7,existing_unknown_dates_preserved=2,verification=readback['verification'],museum_before=dict(works=18,eligible_works=15,primary_images=12),museum_after=dict(works=205,eligible_works=193,primary_images=194),preferred_200_catalogue_target_reached=True,preferred_200_numeric_date_target_reached=False,production_campaign_totals=dict(new_artworks=1209,existing_links=4,museums=8),historical_local_totals_unchanged=prior['historical_local_campaign_totals'],cross_database_totals_combined=False,new_images=205,new_primary_images=181,alternate_images=24,existing_primary_images_preserved=13,remaining_pending_candidates=remaining,remaining_pending_total=596,global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,backup_id=backup['id'],source_access='Inherited source holds remain. One exact native HTTPS image probe timed out; no retries. All205 explicitly observed SearchCulture HTTPS previews were identical in bytes to captured native originals. No schema relaxation or invented URL.',concurrent_comparison_update='Eight unrelated comparison records gained primary images. Identity metadata, all5250 creator links and12026 citations stayed unchanged. Fresh immutable baseline captured before applying; all71 scoped and1026 prior records remained protected.',next_work='Fresh live identity reconciliation and selected delivery for Chania174, Zongolopoulos199, Theocharakis197 and Kilkis26. Then continue Averoff native catalogue and Athens City research. All candidate counts remain subject to physical-object reconciliation.')
    m.save(RUN/'delivery-001.json',report)
    (RUN/'README.md').write_text(f'''# Larissa — selected collection delivery, 10 October 2026

Added **184 production review artworks**, linked **three existing artworks** to documented Larissa holdings, and attached **205 authentic images**. The Municipal Art Gallery of Larissa – G. I. Katsigras Museum now has **205 catalogue artworks**, up from 18; **193** have numeric creation dates within the cutoff, up from 15. **194** artworks have primary images. The real local catalogue remains unchanged.

- [187 added or linked works](delivered-production-artworks-001.csv)
- [Verification checks](checks-001.json)
- [Public delivery verification](public-delivery-001.json)
- [Source and identity review](editorial-reviewed-001.json.gz)
- [Delivery record](delivery-001.json)

The three reconciled existing works are Maleas's *Lavrio Landscape*, Triantafyllidis's *Girl with turkeys*, and Moralis's *Nude Standing*. Their catalogue titles, dates, creator links and publication states were preserved. The last two retain unknown catalogue dates; the museum's dated evidence is recorded separately. Seven new records retain unknown numeric dates or explicit source conflicts. New records retain their literal creator labels, including unresolved L.C. initials. No artist-authority links or current-display claims were invented.

The 1946 Kanas lithograph album counts once, with twelve source plates and image views. Separate print impressions and illustrated manuscript versions were checked using dedications, handwriting, dimensions and full frames. In particular, the Giallinas Gastouri watercolours, Galanis boy-on-horse impressions, and Vassiliou funeral-feast manuscripts remain distinct physical works. The selected new types are 120 paintings, eight drawings, 39 prints and 17 watercolours, supported by source categories and techniques.

The images comprise **181 new primary attachments and 24 alternate views**. All **13 existing primary images** remain unchanged. Full frames and watermarks are retained; every delivered JPEG is at most 100,000 bytes. Actual CC BY-NC 4.0 source labels and credits remain separate from the user's Greek-art source authorization. Five new works remain unillustrated because of missing source images or physical-date uncertainty. All 205 explicitly observed HTTPS SearchCulture image URLs returned bytes identical to captured native originals, satisfying the evidence schema without fabricating a secure native URL.

Successful Cloud SQL backup **{backup['id']}** preceded the atomic transaction. Seventeen offline tests passed. Live preflight, atomic verification, independent readback and a zero-write replay passed, protecting 71 existing comparison records and 1,026 previous campaign artworks. Public delivery checks fetched all 205 image files and verified exact SHA-256 matches; four public artwork API samples confirmed review records and documented holdings. The plan SHA-256 is `{digest}`. Use the reconciled apply adapter, which records eight unrelated image additions observed between comparison review and preflight; the original pinned writer remains unchanged.

The selected production campaign now totals **1,209 new artworks and four existing-work links across eight museums**, with 1,213 protected artwork IDs. Only Larissa's register row was refreshed; the remaining 231-row priority subset is not a fresh global census. Historical local totals stay separate. **596 reviewed candidates** remain pending live reconciliation: Chania 174, Zongolopoulos 199, Theocharakis 197 and Kilkis 26. The every-museum goal remains active and incomplete.
''',encoding='utf-8')
    print(json.dumps(dict(added=184,existing_links=3,images=205,catalogue=205,numeric_eligible=193,protected_ids=1213,pending_candidates=596,priority_rows=231)),flush=True)

if __name__=='__main__':main()
