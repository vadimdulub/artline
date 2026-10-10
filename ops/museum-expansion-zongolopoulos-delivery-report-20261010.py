"""Report verified Foundation delivery and refresh only its institutional count."""
import csv
import importlib.util
import json
from pathlib import Path
spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-zongolopoulos-delivery-20261010.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
a,c,m,RUN=d.a,d.c,d.m,d.RUN

def table(name,rows):
    with (RUN/name).open('x',encoding='utf-8-sig',newline='') as out:
        w=csv.DictWriter(out,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    assert not(RUN/'delivery-001.json').exists();checks=m.load(RUN/'checks-001.json');public=m.load(RUN/'public-delivery-001.json');read=m.load(RUN/'readback-001.json')
    assert checks['readback_passed'] and checks['replay_zero_writes'] and checks['local_unchanged'] and public['public_image_hashes_matched']==18 and public['public_artwork_samples']==4
    p,digest=a.validate_plan();assert digest==d.EXPECTED;prior=m.load(c.CP);at=m.now();assert read['verification']['current_counts']=={c.IID:dict(linked=216,eligible=67)}
    rr=prior['production_institution_register_reference'];register=m.load(c.checked(rr))['rows'];target=next(x for x in register if x['id']==c.IID)
    assert target['verified_production_works']==18 and target['verified_production_eligible_works']==18
    target.update(production_catalogue_count_to_200=216,production_date_eligible_count_to_200=67,production_catalogue_count_state='exact',production_date_eligible_count_state='exact',verified_production_works=216,verified_production_eligible_works=67,production_catalogue_count_at=read['at'],production_date_eligible_count_at=read['at'])
    m.save(RUN/'production-institution-register-001.json.gz',dict(at=at,rows=register,previous_register_reference=rr,read_only=True,updated_institutions=[c.IID],global_exact_counts_refreshed=False,global_thresholds_refreshed=False,policy='Only Zongolopoulos refreshed to216 catalogue/67numeric-date eligible records. Other observations retain their dates.'))
    table('production-institution-register-001.csv',register)
    qr=prior['priority_museum_queue_reference'];queue=m.load(c.checked(qr));assert len([x for x in queue['rows'] if x['id']==c.IID])==1
    queue['rows']=[x for x in queue['rows'] if x['id']!=c.IID];assert len(queue['rows'])==228
    queue.setdefault('removed_threshold_reached',[]).append(dict(id=c.IID,at=read['at'],catalogue=216,date_eligible=67,preferred_catalogue_target_reached=True,numeric_minimum100_reached=False,numeric_gap_to100=33))
    queue.setdefault('date_research_remaining',[]).append(dict(id=c.IID,catalogue=216,date_eligible=67,unknown_dates=149,gap_to100_numeric=33,reason='Catalogue target reached; creation-date evidence remains incomplete. Unknown records remain visible review works, not presumed pre1971.'))
    queue.update(at=at,previous_queue_reference=qr,policy='Zongolopoulos216 catalogue records exceeds preferred200 target.67 numeric-date eligible records remain below100;149unknown dates require further evidence.228remaining rows are an inherited under100catalogue subset, not a new global census. Chania still needs8catalogue additions for200.')
    m.save(RUN/'priority-museum-queue-001.json',queue)
    rows=[]
    for v in p['records']:
        f=v['facts'];rows.append(dict(artwork_id=v['artwork_id'],institution_id=c.IID,action='new_record',source_id=f['source_id'],title=f['title'],creator_label=f['creator_label'],artist_id=None,date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],source_url=f['source_url'],status='review'))
    table('delivered-production-artworks-001.csv',rows)
    protected=sorted(set(p['prior_ids'])|{v['artwork_id'] for v in p['records']});assert len(protected)==1782
    m.save(RUN/'protected-production-ids-001.json',dict(at=at,ids=protected,previous_protected_records=1584,new_records=198,new_existing_links=0,composition=dict(campaign_new_artworks=1777,campaign_existing_links=5),plan_reference=c.ref(a.PLAN)))
    backup=m.load(RUN/'cloud-backup-001.json');pending=dict(kilkis=26)
    report=dict(at=at,goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=198,existing_links=0,date_eligible_new=49,new_unknown_numeric_dates=149,existing_target_unknown_dates_preserved=0,verification=read['verification'],museum_before=dict(works=18,eligible_works=18,primary_images=6),museum_after=dict(works=216,eligible_works=67,primary_images=24),minimum100_reached_in_both_measures=False,preferred200_catalogue_reached=True,numeric_gap_to100=33,production_campaign_totals=dict(new_artworks=1777,existing_links=5,museums=11),historical_local_totals_unchanged=prior['historical_local_campaign_totals'],cross_database_totals_combined=False,new_images=18,new_primary_images=18,alternate_images=0,new_artist_links=0,remaining_pending_candidates=pending,remaining_pending_total=26,metadata_identity_holds=63,global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,backup_id=backup['id'],source_access='Complete retained museum-supplied SearchCulture captures and observed public preservation viewers support delivery. Native Zongolopoulos403/eMuseumPlus timeout remain; restricted hosts not retried. All inherited provider holds continue. New next-source Averoff /zografiki web-open403 recorded; no retry or alternate access route.',next_work='Reconcile and deliver Kilkis26 after fresh live identity/image-date review. Continue Averoff and Athens City source research, plus museums below100catalogue works. Preserve Zongolopoulos149 unknown dates and63source identity holds; current216catalogue total does not certify all older cast/version records as distinct physical works.')
    m.save(RUN/'delivery-001.json',report)
    (RUN/'README.md').open('x',encoding='utf-8').write(f'''# George Zongolopoulos Foundation — selected collection delivered, 10 October 2026

Added **198 production review artworks and 18 authentic primary images**. The foundation now has **216 catalogue records**, up from 18, including **67 works with qualifying numeric creation dates** and **24 works with primary images**. The real local database remains unchanged.

- [Delivered artwork ledger](delivered-production-artworks-001.csv)
- [Object identity and duplicate review](identity-review-001.json)
- [Database preservation checks](checks-001.json)
- [Public delivery verification](public-delivery-001.json)
- [Delivery record](delivery-001.json)
- [Initial sculpture and dated-work research](../zongolopoulos-20261010/README.md)
- [Painting and works-on-paper research](../zongolopoulos-paintings-20261010/README.md)

Museum-supplied records in [SearchCulture's foundation collection](https://www.searchculture.gr/aggregator/portal/collections/ZoggopoulosF?language=en) support selected holdings. The additions comprise 30 sculptures/models,26 drawings,65 watercolours,63 paintings,one print and 13 works whose controlled type remains unknown. Monument models do not establish ownership or current display of the full-size public monument. Holdings do not establish present display.

**149 creation dates remain unknown** and require further editorial evidence;49 new records have explicit date ranges ending by 1970. The 149 are not counted as numerically eligible. A lithograph's transcribed 1933 signature does not establish the production date of impression 17/20. The 1960 date of one Helen watercolour remains a source-reported inscription. No dates were inferred from creator lifespans. The preferred 200 catalogue target is reached, while numeric eligibility remains 33 short of 100.

**37 anonymous creators**, two qualified or conflicting named attributions,16 two-sided supports and a reused canvas remain explicit. Each physical support counts once. Fresh expanded live artist/alias searches found no George or Helen authority; original or qualified object-level creator labels remain, without fabricated painter records. Literal repeated export inventory strings are preserved in evidence, not halved into invented accessions.

The earlier 199 candidates resolved to 198 selected additions. Source 64302 is newly held because its Venice composition may be another photograph of the watercolour shown more fully in 64304. Both preservation previews were inspected; differing framing, colour and export digits do not prove two physical works. Source 64304 counts once, with no forced alias or second-image attachment. The 61 earlier unresolved casts/models/version entries and painting 64218 with an image/description conflict remain held, for 63 held source entries. Existing cast/version duplication flags are preserved without merging or deleting records;216 is a catalogue-record count, not a certification of distinctness for every older record.

Production identity research covered 949 bounded records and 1,924 citations. Full snapshots protect 64 focused comparators. Thirty-two existing primary images, three additional source images,19 prepared frames,37 anonymous candidate frames and two Venice preservation previews were examined in this delivery review. The earlier detailed source/version comparisons remain preserved. Twelve generic-title comparators lacked a directly exposed thumbnail; no visual comparison is claimed for them. Generic title matches alone do not establish a shared physical object. This is not an exhaustive duplicate guarantee or 10-million-row performance test.

The 18 images retain complete source JPEG bytes, all below 100,000 bytes, with originals/proofs outside Documents. Actual **CC BY-NC-ND 4.0** labels, provider credits and source links remain recorded as restricted. The user's Greek source approval is recorded separately and does not claim an independently obtained copyright-holder licence. Unknown-date and post 1955 works remain unillustrated under this image pass.

Backup **{backup['id']}** succeeded before atomic application. Twenty offline checks, live preflight, transaction verification, independent readback and a zero-write replay passed. All 18 public image hashes matched, and four dated artwork API samples returned the expected review records and holdings. All 18 old foundation records,64 focused comparators and 1,584 previous campaign IDs were preserved. Plan SHA-256: `{digest}`.

The selected production campaign totals **1,777 new artworks and five existing-work links across 11 museums**, protecting 1,782 IDs. Only this foundation's register row was refreshed; the 228-row priority subset is not a new global census. Kilkis has 26 researched candidates pending fresh reconciliation. The every-museum goal remains active and incomplete.
''')
    print(json.dumps(dict(added=198,images=18,catalogue=216,numeric_eligible=67,protected_ids=1782,pending_candidates=26,priority_rows=228)),flush=True)

if __name__=='__main__':main()
