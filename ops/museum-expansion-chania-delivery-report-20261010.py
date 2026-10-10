"""Record actual Chania delivery and update its row in the dated museum register."""
import csv
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-chania-delivery-20261010.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
a,c,m,RUN=d.a,d.c,d.m,d.RUN

def table(name,rows):
    with (RUN/name).open('x',encoding='utf-8-sig',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def main():
    assert not(RUN/'delivery-001.json').exists()
    checks=m.load(RUN/'checks-001.json');public=m.load(RUN/'public-delivery-001.json');readback=m.load(RUN/'readback-001.json')
    assert checks['readback_passed'] and checks['replay_zero_writes'] and checks['local_unchanged'] and public['public_image_hashes_matched']==188
    p,digest=a.validate_plan();assert digest==d.EXPECTED;prior=m.load(c.CP);at=m.now()
    assert readback['verification']['current_counts']=={c.IID:dict(linked=192,eligible=117)}
    rr=prior['production_institution_register_reference'];register=m.load(c.checked(rr))['rows'];target=next(x for x in register if x['id']==c.IID)
    assert target['verified_production_works']==18 and target['verified_production_eligible_works']==0
    target.update(production_catalogue_count_to_200=192,production_date_eligible_count_to_200=117,production_catalogue_count_state='exact',production_date_eligible_count_state='exact',verified_production_works=192,verified_production_eligible_works=117,production_catalogue_count_at=readback['at'],production_date_eligible_count_at=readback['at'])
    m.save(RUN/'production-institution-register-001.json.gz',dict(at=at,rows=register,previous_register_reference=rr,read_only=True,updated_institutions=[c.IID],global_exact_counts_refreshed=False,global_thresholds_refreshed=False,policy='Only Chania refreshed to192 catalogue/117 numeric date-eligible artworks. Other counts retain their observation dates.'))
    table('production-institution-register-001.csv',register)
    qr=prior['priority_museum_queue_reference'];queue=m.load(c.checked(qr));removed=[x for x in queue['rows'] if x['id']==c.IID];assert len(removed)==1
    queue['rows']=[x for x in queue['rows'] if x['id']!=c.IID];assert len(queue['rows'])==230
    queue.setdefault('removed_threshold_reached',[]).append(dict(id=c.IID,at=readback['at'],catalogue=192,date_eligible=117))
    queue.setdefault('preferred_target_remaining',[]).append(dict(id=c.IID,at=readback['at'],catalogue=192,date_eligible=117,catalogue_gap_to_200=8,date_eligible_gap_to_200=83,unreviewed_source_records=108))
    queue.update(at=at,previous_queue_reference=qr,policy='Chania192/117 reaches100 in both measures and leaves the inherited under100 subset. Preferred200 remains8catalogue works away.230remaining queue rows are not a new global census.')
    m.save(RUN/'priority-museum-queue-001.json',queue)
    rows=[]
    for v in p['records']:
        f=v['facts'];rows.append(dict(artwork_id=v['artwork_id'],institution_id=c.IID,source_id=f['source_id'],title=f['title'],accession=f['inventory'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],source_url=f['source_url'],status='review'))
    table('added-production-artworks-001.csv',rows)
    protected=sorted(set(p['prior_ids'])|{x['artwork_id'] for x in p['records']});assert len(protected)==1387
    m.save(RUN/'protected-production-ids-001.json',dict(at=at,ids=protected,previous_protected_records=1213,new_records=174,new_existing_links=0,composition=dict(campaign_new_artworks=1383,campaign_existing_links=4),plan_reference=c.ref(a.PLAN)))
    remaining=dict(kilkis=26,theocharakis=197,zongolopoulos=199);assert sum(remaining.values())==422
    backup=m.load(RUN/'cloud-backup-001.json')
    report=dict(at=at,goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=174,existing_links=0,date_eligible_new=117,new_unknown_numeric_dates=57,existing_unknown_dates_preserved=18,verification=readback['verification'],museum_before=dict(works=18,eligible_works=0,primary_images=0),museum_after=dict(works=192,eligible_works=117,primary_images=183),minimum100_reached_in_both_measures=True,preferred200_reached=False,catalogue_gap_to200=8,production_campaign_totals=dict(new_artworks=1383,existing_links=4,museums=9),historical_local_totals_unchanged=prior['historical_local_campaign_totals'],cross_database_totals_combined=False,new_images=188,new_primary_images=183,alternate_images=5,remaining_pending_candidates=remaining,remaining_pending_total=422,unreviewed_chania_source_records=108,chania_art_scope_holds=14,global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,backup_id=backup['id'],source_access='New web-open403responses at amch.gr and www.artic.edu were not retried or bypassed. Complete Chania source/image captures already obtained earlier today remained hash-verified and available. Five healthy Acropolis comparator frames were checked; eight captured comparator sources were verified. All inherited provider holds persist.',next_work='Deliver reviewed Zongolopoulos 199, Theocharakis 197 and Kilkis 26 after fresh identity reconciliation. Continue Averoff native collection/Athens City research. Chania retains108unreviewed records and 14 scope holds; reaching200 requires actual additional eligible physical objects, not reused fragments or filler.')
    m.save(RUN/'delivery-001.json',report)
    (RUN/'README.md').write_text(f'''# Chania — selected collection delivered, 10 October 2026

Added **174 production review artworks** and attached **188 authentic images**. The Archaeological Museum of Chania now has **192 catalogue artworks**, up from 18, and **117 numerically date-eligible works**, up from zero. **183 artworks have primary images**. The real local catalogue remains unchanged.

- [174 added artworks](added-production-artworks-001.csv)
- [Verification checks](checks-001.json)
- [Public image and artwork checks](public-delivery-001.json)
- [Source and identity decisions](identity-review-001.json)
- [Delivery record](delivery-001.json)
- [Original source review](../chania-20261010/README.md)

The new collection includes 68 metalworks, 54 ceramics, 40 sculptures and 12 works with an unresolved controlled type. Nine qualified workshop labels remain object-level attributions; anonymous makers remain explicit. **57 new records retain qualified periods, source conflicts or unknown numeric dates**, while all **18 existing catalogue dates remain unchanged**. No painter identity, publication or current-display claim was added. Hadrian's 117–138 CE range and Tiberius's creation attribution to the first half of the first century CE are preserved; a ruler's reign, excavation year or ancient prototype does not substitute for the physical object's creation date.

The cauldron Μ 825 Α–ΣΤ counts once with six component pages and views. The gold hair-ornament pair Μ 763 Α/Β also counts once. One canonical source identifier is stored for each physical artwork; all 180 source records remain in metadata and image evidence. Fourteen art-scope holds remain excluded from this selected delivery. The earlier 212-source review and fresh catalogue comparison protect distinct specimens, impressions, fragments and versions.

Global source/accession/title/image checks returned 41 existing comparison records. Eight similarly titled ancient sculptures were checked against their official accessions, dimensions and descriptions; five Acropolis source photographs provided further visual comparison. None established an existing identity for a new Chania candidate. Incidental accession collisions with later paintings and prints were recorded as distinct objects.

The 188 attachments comprise 183 primary images and five additional cauldron-fragment views. They illustrate 167 new works and 16 existing records. Seven new works remain unillustrated because of source image mismatches or unresolved physical dating. Complete frames are retained, including native labels and supports; original transparent PNGs remain archived. JPEG derivatives are at most 100,000 bytes. Actual **CC BY-NC-ND 3.0 GR** labels and credits remain separate from the user's Greek-source authorization; no independent copyright-holder licence is claimed.

Fresh web requests to the Chania and Art Institute websites returned 403. They were not retried or bypassed. This delivery uses complete, previously obtained Chania evidence and images, all revalidated by checksum. The earlier captured official Art Institute and Cyprus evidence was verified offline. New source restrictions therefore did not trigger invented metadata or image substitutions.

Successful Cloud SQL backup **{backup['id']}** preceded atomic application. **23 offline tests**, live preflight, atomic verification, independent readback and zero-write replay passed. All 188 public image files matched their reviewed SHA-256 hashes, and four dated artwork API samples returned the expected review records and holdings. All 41 existing comparison records and 1,213 prior campaign artworks were protected. The exact plan SHA-256 is `{digest}`.

The selected production campaign now totals **1,383 new artworks and four existing-work links across nine museums**, with 1,387 protected IDs. Only Chania's register row was refreshed; the 230-row priority subset is not a fresh global census. Historical local totals remain separate. **422 reviewed candidates** remain pending reconciliation: Zongolopoulos 199, Theocharakis 197 and Kilkis 26.

Chania reaches the 100-work minimum in both catalogue and numeric-date measures. Its preferred 200 catalogue target still needs **eight additional supported physical artworks**. There are 108 unreviewed source records, which are not a promise of 108 eligible new works. Existing date/image uncertainties and 14 scope holds remain tracked. The every-museum goal stays active and incomplete.
''',encoding='utf-8')
    print(json.dumps(dict(added=174,images=188,catalogue=192,numeric_eligible=117,protected_ids=1387,pending_candidates=422,priority_rows=230)),flush=True)

if __name__=='__main__':main()
