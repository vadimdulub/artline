"""Verified delivery ledger and explicit remaining museum/source/date gaps."""
import csv,importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-jewish-delivery-20261010.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
a,c,m,RUN=d.a,d.c,d.m,d.RUN
NEXT='fbb86dfe-de37-5942-b762-0585ae753b31'

def table(name,rows):
    with (RUN/name).open('x',encoding='utf-8-sig',newline='') as h:
        w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    assert not(RUN/'delivery-001.json').exists();checks=m.load(RUN/'checks-001.json');read=m.load(RUN/'readback-001.json');public=m.load(RUN/'public-delivery-001.json');p,digest=a.validate_plan();prior=m.load(c.CP);at=m.now()
    assert checks['readback_passed'] and checks['replay_zero_writes'] and checks['local_unchanged'] and public['public_artwork_samples']==6 and read['verification']['current_counts']=={c.IID:dict(linked=148,eligible=142)}
    rr=prior['production_institution_register_reference'];register=m.load(c.checked(rr))['rows'];target=next(x for x in register if x['id']==c.IID);assert target['verified_production_works']==8
    target.update(production_catalogue_count_to_200=148,production_date_eligible_count_to_200=142,production_catalogue_count_state='exact',production_date_eligible_count_state='exact',verified_production_works=148,verified_production_eligible_works=142,production_catalogue_count_at=read['at'],production_date_eligible_count_at=read['at'])
    m.save(RUN/'production-institution-register-001.json.gz',dict(at=at,rows=register,previous_register_reference=rr,read_only=True,updated_institutions=[c.IID],global_exact_counts_refreshed=False,global_thresholds_refreshed=False,policy='OnlyJewishMuseumofGreece refreshed:148catalogue,142numericdateeligible,5unknown,1crossingrange. Otherobservations retain timestamps.'));table('production-institution-register-001.csv',register)
    qr=prior['priority_museum_queue_reference'];queue=m.load(c.checked(qr));assert len(queue['rows'])==223;queue['rows']=[x for x in queue['rows'] if x['id']!=c.IID];assert len(queue['rows'])==222
    reached=dict(id=c.IID,at=read['at'],catalogue=148,date_eligible=142,basis='140newreviewunits,134newnumericeligible,5unknown,1crossingrange. Minimum100met,52catalogueworks remain topreferred200.')
    queue.setdefault('removed_threshold_reached',[]).append(reached);queue['latest_removed_threshold_reached']=reached
    preferred={x.get('id',x.get('institution_id')):dict(x) for x in queue.get('preferred_target_remaining',[])}
    previous_latest=queue.get('latest_preferred_target_remaining')
    if previous_latest:
        key=previous_latest.get('id',previous_latest.get('institution_id'));preferred.setdefault(key,{}).update(previous_latest)
    for row in register:
        count=row.get('verified_production_works')
        if row.get('production_catalogue_count_state')=='exact' and isinstance(count,int) and 100<=count<200:
            item=preferred.setdefault(row['id'],{})
            item.update(id=row['id'],name=row['name'],at=row['production_catalogue_count_at'],catalogue=count,date_eligible=row.get('verified_production_eligible_works'),catalogue_gap_to_200=200-count,gap_to100=0,gap_to200=200-count,target_reached=False,observation_source='production_institution_register')
    queue['preferred_target_remaining']=sorted(preferred.values(),key=lambda x:x['id'])
    assert len(queue['preferred_target_remaining'])==272
    queue['preferred_target_queue_note']='Reconciled from existing exact-count register observations, retaining their original timestamps and source-research fields. Only Jewish Museum of Greece was freshly counted; this is not a refreshed global census.'
    queue['latest_preferred_target_remaining']=dict(institution_id=c.IID,at=read['at'],catalogue=148,gap_to100=0,gap_to200=52,target_reached=False,numeric_eligible=142)
    queue.setdefault('date_research_remaining',[]).append(dict(id=c.IID,catalogue=148,date_eligible=142,unknown_dates=5,crossing_cutoff=1,reason='Twoimpressiondates unresolved; threededicationdatesnotmanufacture; oneconflicting20thcenturyrange.'))
    queue.update(at=at,previous_queue_reference=qr,policy='JewishMuseum leavesinheritedunder100subset;222rowsremain,62Greek. Notglobalcensus.52workgap topreferred200.');m.save(RUN/'priority-museum-queue-001.json',queue)
    table('delivered-production-artworks-001.csv',[dict(artwork_id=v['artwork_id'],institution_id=c.IID,action='new_record',source_ids=' | '.join(v['facts']['source_ids']),title=v['facts']['title'],date_display=v['facts']['date_display'],creation_year_start=v['facts']['first'],creation_year_end=v['facts']['last'],source_url=v['facts']['source_url'],status='review') for v in p['records']])
    table('delivered-production-images-001.csv',[dict(artwork_id=x['artwork_id'],source_id=x['source_id'],number=x['number'],primary=True,storage_path=x['storage_path'],sha256=x['sha256'],bytes=x['bytes'],width=x['width'],height=x['height'],rights_status=x['rights_status'],rights_label=x['rights_label'],source_url=x['source_url']) for x in p['images']])
    protected=sorted(set(p['prior_ids'])|{x['artwork_id'] for x in p['records']});assert len(protected)==2938
    totals=dict(new_artworks=prior['production_campaign_totals']['new_artworks']+140,existing_links=prior['production_campaign_totals']['existing_links'],museums=prior['production_campaign_totals']['museums']+1);assert totals==dict(new_artworks=2914,existing_links=7,museums=18)
    m.save(RUN/'protected-production-ids-001.json',dict(at=at,ids=protected,previous_protected_records=2798,new_records=140,new_existing_links=0,composition=dict(campaign_new_artworks=2914,campaign_existing_links=7,additional_existing_image_only_records=17),plan_reference=c.ref(a.PLAN)))
    nextwork='MOMus initial institution '+NEXT+' last11catalogue/7eligible. Freshbaseline andinstitutionreconciliation needed:7001aggregatorrecords spanmultipleMOMusmuseums, notallheldbyMuseumofContemporaryArt. Prioritize supported pre1971 art, includingRussianavantgarde; preserve actualcollectionassignment. Faltaits4153mixedrecords andAgrinio165mostlypostwarrecords alsofreshlydiscovered; noindividualobjects/imagesdownloaded.'
    remaining=dict(at=at,institution_id=c.IID,catalogue=148,preferred200_reached=False,catalogue_gap_to200=52,numeric_date_eligible=142,unknown_numeric_dates=5,crossing_cutoff_dates=1,new_unknown_numbers=[76,154,1038,1063,1115],new_crossing_numbers=[1053],source_total=13533,digital_narratives_source_total=1044,art_type_index_records=196,textile_type_index_records=585,individual_objects_reviewed=311,textile_captures=128,textile_failed_objects=6,textile_unattempted_selected=146,textile_other_index_leads=305,external_collection_holds=11,photographic_surrogate_holds=74,other_date_version_leads=71,post1970_event_holds=[176,177],scope_holds=[1072],identity_holds=[1117],merged_units={1021:[1021,1023],1038:[1038,1039],1195:[1195,1194]},ready_candidates=0,existing_medal_note='Oldmedal203/source38ancientdate versuspendantmanufacture andimage/description remainsresearchquestion; existing recordandimagepreserved.',native_resolution_note='131authenticnativeJPEGs,52byteunchanged79compressedproportionally,max99905B; originalsuppliedframes preserved includingfolds/detailviews. Noenlargementorgeneratedimages.',source_access_holds_reference=c.ref(RUN/'source-access-holds-001.json'),next_priority=nextwork,next_source_reference=c.ref(RUN/'next-source-discovery-001.json.gz'));m.save(RUN/'remaining-research-001.json',remaining)
    backup=m.load(RUN/'cloud-backup-001.json');report=dict(at=at,goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=140,existing_links=0,date_eligible_new=134,new_unknown_numeric_dates=5,new_crossing_cutoff_dates=1,verification=read['verification'],museum_before=dict(works=8,eligible_works=8,primary_images=8),museum_after=dict(works=148,eligible_works=142,primary_images=139),minimum100_catalogue_reached=True,preferred200_catalogue_reached=False,catalogue_gap_to100=0,catalogue_gap_to200=52,production_campaign_totals=totals,historical_local_totals_unchanged=prior['historical_local_campaign_totals'],cross_database_totals_combined=False,new_images=131,new_primary_images=131,new_alternate_images=0,new_artist_links=0,remaining_pending_candidates={},remaining_pending_total=0,global_production_counts_refreshed=False,global_production_thresholds_refreshed=False,backup_id=backup['id'],source_access='SixindividualtextileSCpagesHTTP500held,no retries.146selectedtextilepagesunattempted aftertwo3failurestops.311otherindividualsourcepages,selectednativepages and153selectedsourceimages available. NativeHTMLandhigherresolutionimages accessible. NextMOMus/Faltaits/Agrinio collectionlandings200.',next_work=nextwork);m.save(RUN/'delivery-001.json',report)
    text=f'''# Jewish Museum of Greece — 10 October 2026

Added **140 review artwork units and 131 authentic images** in production. The museum increased from **8 to 148 catalogue works**, with **142 numerically date-eligible works**, five unknown creation dates, one range crossing 1970, and **139 illustrated works**. The minimum 100 target is met; **52 more works** are needed for the preferred 200. The real local database remains unchanged.

- [Delivered artworks](delivered-production-artworks-001.csv)
- [Delivered images](delivered-production-images-001.csv)
- [Candidate decisions](candidate-review-001.csv)
- [Verification](checks-001.json)
- [Remaining research](remaining-research-001.json)
- [Museum research queue and gaps toward 200](priority-museum-queue-001.json)

The [museum's general SearchCulture collection](https://www.searchculture.gr/aggregator/portal/collections/jewishmuseum) has 13,533 mixed records. Its separate [digital narratives collection](https://www.searchculture.gr/aggregator/portal/collections/DigJewish?language=en) has 1,044 searchable records. These totals include documents, pages, photographs, details and repeat views, and do not establish eligible artwork counts. We captured bounded indexes for 196 fine-art entries and 585 needlework entries, then reviewed 311 individual metadata records, including 128 textile records and all eight existing catalogue works.

The additions include paintings, drawings, prints, a sculpture, a composite belt with dedicatory plaques, and historic embroidered and woven textiles. Eleven records explicitly belong to the Municipality Museum of Ioannina or the Society for Epirotic Studies; they were not assigned to the Jewish Museum of Greece merely because it supplied the metadata. Seventy-four photographic surrogates of artworks or buildings remain separate research leads. Two cartoons about the 1972 Munich murders were excluded. A roll of lace and a near-identical cushion-cover record remain held for scope and identity review.

The 140 physical units retain 143 source records. Duplicate records for one uncut slipper panel, two photographs of one dedication panel, and the decorated front and lining detail of one marriage canopy were reconciled. Full native filename tokens, descriptions, measurements and visual comparisons support these decisions; filename tokens were not invented as catalogue accession numbers. Similar decorative motifs alone did not cause distinct cushion covers to be merged. Maker, collector, donor and prototype-artist roles remain qualified. An existing Gillot alias for Claude Gillot was not accepted as the identity behind late-nineteenth-century print credits.

Literal date ranges retain both centuries where the aggregator index had dropped the nineteenth-century component. The Moses painting remains dated to the 1930s rather than exactly 1930. Three dedication dates do not establish manufacture dates. An engraving labelled 1811 conflicts with its Bartlett attribution and [the Government Art Collection's artist chronology](https://artcollection.dcms.gov.uk/person/bartlett-william-henry/); no replacement impression year was invented. Another Jerusalem image may use a depicted-period date. Both remain undated review records. One textile's native twentieth-century date conflicts with the aggregator's narrower early-century date; the broader range remains explicit.

We reviewed 153 authentic source frames on seven contact sheets and two focused comparison sheets, then all 131 prepared images on six further sheets. All delivered images come from the primary image URLs of the [museum's native collection pages](https://artifacts.jewishmuseum.gr/). Fifty-two JPEGs are unchanged; 79 were proportionally resized or compressed. Every derivative is at most **99,905 bytes**, without cropping, enlargement, retouching or generated detail. Original files are archived outside Documents. Some source photographs show folded textiles or details; complete supplied image does not mean complete unfolded object.

The actual **In Copyright (InC)** statement and museum credit are retained as restricted rights evidence. Existing user approval for this Greek museum workflow is recorded separately and is not represented as copyright-holder permission or public-domain status. No new image is delivered for a creation after 1955, an unknown date or the crossing-century range.

Six individual textile pages returned HTTP500 and were not retried. A previously unattempted page succeeded, allowing a bounded continuation before three further failures stopped that stream. There are 146 selected but unattempted textile records and 305 other index leads, plus unresolved fine-art dates and versions. Earlier successfully captured canopy pages were reused without further requests. Source access gaps and all inherited holds remain recorded.

Bounded production reconciliation checked source identities, titles, creators and image hashes across 581 returned artworks. Four additional exact-title counterparts were distinguished by makers, media, dates and institution/source identities; those records were preserved. All eight existing museum artworks and **2,798 prior protected records** remain unchanged. No artist records, biographies, publication changes or current-display claims were created. Query plans were retained; this is not a ten-million-row load test or an exhaustive global duplicate guarantee.

The first write attempt timed out waiting for the shared import lock, before changing any records. Read-only checks confirmed zero new artwork, source and audit rows, unchanged protected state, and that the lock had cleared. The same reviewed plan and uploaded files were then reused; no other transaction was cancelled. After the successful commit, the local CloudSQL proxy received a termination signal from an unknown sender. The server remained running. Restoring the same verified proxy configuration allowed independent readback to resume without importing again.

Backup **{backup['id']}** succeeded before the atomic write. **21 checks**, independent readback, zero-write replay, all **131 public image hashes**, and six public artwork samples passed. Plan SHA-256: `{digest}`.

The selected production campaign now totals **2,914 new artworks and seven existing-work links across 18 museums**. The protected set contains 2,938 records, including 17 earlier image-only enrichments. Only this museum's totals were refreshed; the inherited under-100 subset has 222 rows, including 62 Greek institutions. The preferred-200 queue preserves 272 museums with existing exact observations of 100–199 catalogue works, retaining their original count timestamps and research notes; this is not a new global count. The every-museum goal remains active. Next research will reconcile MOMus's multiple museum collections before selecting works; Faltaits and Agrinio source collections are also recorded.
'''
    with (RUN/'README.md').open('x',encoding='utf-8') as h:h.write(text)
    print(json.dumps(dict(added=140,images=131,catalogue=148,numeric_eligible=142,protected_ids=2938,priority_rows=222)),flush=True)

if __name__=='__main__':main()
