"""Verify the bounded Larissa review and preserve the unchanged delivery baseline."""
import ast
import collections
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image

spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-larissa-review-20261010.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
spec=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-larissa-selected-20261010.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
m,RUN,PROOF,ref=r.m,r.RUN,r.PROOF,r.ref

def checked(pin):
    p=Path(pin['path']);p=p if p.is_absolute()else m.ROOT/p
    assert p.is_file()and hashlib.sha256(p.read_bytes()).hexdigest()==pin['sha256'],str(p)

def body(rc):
    raw=gzip.decompress((m.ROOT/rc['body_path']).read_bytes())
    assert rc['status']==200 and len(raw)==rc['bytes']and hashlib.sha256(raw).hexdigest()==rc['sha256']
    return raw

def main():
    prior_path=m.RUN/'native/chania-20261010/research-checkpoint-001.json'
    assert ref(prior_path)['sha256']=='e4b9d345081aed5a1d1167b347d3472087291e2558e1c2fc1fa7f15a8629076a'
    prior=m.load(prior_path)
    for pin in prior['artifacts']+prior['external_artifacts']:checked(pin)
    checked(prior['last_successful_production_checkpoint']);prod_path=m.ROOT/prior['last_successful_production_checkpoint']['path'];prod=m.load(prod_path)
    assert ref(prod_path)['sha256']=='21973a04eb7411fec1875f49baa8f0ac9f426e5de3effd5da24ca028b22b891a'
    discovery=m.load(RUN/'source-discovery-001.json.gz');index=m.load(RUN/'bounded-date-index-001.json.gz');selection=m.load(RUN/'object-selection-001.json')
    sources=m.load(RUN/'selected-source-records-001.json.gz')['rows'];facts=m.load(RUN/'candidate-facts-001.json.gz')['rows']
    decisions=m.load(RUN/'editorial-source-decisions-001.json.gz')['rows'];units=m.load(RUN/'candidate-physical-units-001.json.gz')['rows']
    cards=[c for p in index['pages']for c in p['cards']]
    assert index['observed_collection_records']==820 and index['cards']==len(cards)==len({c['source_id']for c in cards})==210 and len(index['pages'])==7
    assert sum(c['historical_source_match']for c in cards)==12
    assert len(selection['selected'])==len(sources)==len(facts)==len(decisions)==216
    assert selection['new_description_leads']==198 and selection['existing_comparators']==18
    receipts=[m.load(p)for p in sorted((RUN/'captures').glob('*.json'))];html=[rc for rc in receipts if 'body_path'in rc]
    assert len(receipts)==666 and len(html)==449 and collections.Counter(rc['status']for rc in receipts)=={200:663,404:3}
    for rc in html:body(rc)
    for rc in receipts:
        if 'path'not in rc:continue
        if rc['status']==200:checked(rc);assert Path(rc['path']).stat().st_size==rc['bytes']
        else:assert rc['number']in r.MISSING_IMAGES and not Path(rc['path']).exists()
    historical={x['source_id']:x for x in discovery['historical_records']};assert len(historical)==18
    assert len({x['artwork_id']for x in historical.values()})==18
    for src,f,d in zip(sources,facts,decisions):
        assert src['number']==f['number']==d['number'];n=d['number']
        agg=BeautifulSoup(body(src['receipt']),'html.parser');fields,enrichment=s.q.fields(agg)
        native=BeautifulSoup(body(src['native_receipt']),'html.parser');nf,desc=s.native_fields(native)
        assert fields==src['fields']==f['source_fields']==d['source_fields']
        assert enrichment==src['enrichment']==d['aggregator_enrichment']
        assert nf==src['native_fields']==f['native_fields']==d['native_fields']
        assert desc==src['native_description']==f['native_description']==d['native_description']
        assert d['original_title']==nf['Τίτλος έργου']and d['native_date_literal']==nf.get('Χρονολογία έργου')
        assert d['inventory_literal']is None and d['painter_id']is None
        assert d['proposed_status']=='review'and not d['ready_to_apply']and not d['applied']and not d['current_display_verified']
        assert 'http://creativecommons.org/licenses/by-nc/4.0/'in d['rights_links']and d['rights_status']=='restricted'
        assert(d['role']=='existing_comparator')==(d['source_id']in historical)
        if d['first']is not None:assert d['first']<=d['last']<=1970
        if n in r.CONFLICTS:assert d['first']is d['last']is None and d['source_date_claims']['native_prose_conflicting_literal']==r.PROSE_DATES[n]
    counts=collections.Counter(d['decision']for d in decisions);assert counts==dict(candidate_primary=187,existing_comparator=18,same_album_plate_secondary=11)
    assert len(units)==187 and sum(u['first']is not None for u in units)==180
    assert collections.Counter(u['work_type']for u in units)==dict(painting=140,drawing=8,print=39)
    assert{u['number']for u in units if u['first']is None}=={30,32,39,51,54,80,102}
    source_ids=[sid for u in units for sid in u['source_ids']];assert len(source_ids)==len(set(source_ids))==198
    by={d['number']:d for d in decisions};ub={u['number']:u for u in units}
    assert ub[176]['source_numbers']==r.ALBUM and ub[176]['title']=='12 σχέδια από τη Κατοχή'and ub[176]['first']==ub[176]['last']==1946
    assert len(ub[176]['component_titles'])==len(set(ub[176]['component_titles']))==12
    assert all(by[n]['creator_label'].startswith('Γεωργιάδης')for n in [70,90,91])and by[193]['creator_label']=='L.C.'
    assert by[32]['image_candidate']is False and by[168]['last']==1960 and not by[168]['image_candidate']
    assert all(by[n]['image_candidate']and by[n]['first']is None for n in [30,39,51,54,80,102])
    assert all(by[n]['metadata_retained_despite_image_hold']and not by[n]['image_candidate']for n in r.MISSING_IMAGES)
    assert len({f['native_description']for f in facts})==191 and len({f['native_description']for f in facts if f['native_description']})==190
    assert sum(f['native_description']is None for f in facts)==10
    ledger=list(csv.DictReader((RUN/'review-ledger-001.csv').open(encoding='utf-8-sig')));assert len(ledger)==216
    assert[(int(x['number']),x['decision'],x['title'])for x in ledger]==[(x['number'],x['decision'],x['title'])for x in decisions]
    visual=m.load(RUN/'visual-references-001.json');comp=m.load(RUN/'comparison-references-001.json');prep=m.load(RUN/'image-delivery-prepared-001.json');review=m.load(RUN/'physical-unit-review-001.json')
    assert len(visual['rows'])==216 and sum(bool(x['path'])for x in visual['rows'])==213 and len(visual['sheets'])==11
    assert visual['missing_images']==[46,67,92]and not visual['exact_duplicate_images']and len(comp['sheets'])==4
    assert all({p['a'],p['b']}<=set(review['bifolios'])for p in comp['nearest_dhash_pairs'])
    for pin in visual['sheets']+comp['sheets']+prep['sheets']:checked(pin)
    for f in visual['rows']:
        if not f['path']:continue
        checked(f)
        with Image.open(f['path'])as im:im.load();assert im.size==(f['width'],f['height'])and im.format=='JPEG'
    assert len(prep['rows'])==205 and len(prep['sheets'])==11 and prep['production_attached']==prep['production_uploaded']==0
    for p in prep['rows']:
        checked(dict(path=p['prepared_path'],sha256=p['sha256']));checked(p['original_reference'])
        assert Path(p['prepared_path']).stat().st_size==p['bytes']<=100000 and p['complete_source_frame']and p['watermark_preserved']and not p['attached']
        assert by[p['number']]['image_candidate']and by[p['number']]['image_date_policy_passed']and p['primary_number']==by[p['number']]['primary_number']
        with Image.open(p['prepared_path'])as im:im.load();assert im.format=='JPEG'and im.size==(p['width'],p['height'])
        assert abs(p['width']/p['height']-p['original_width']/p['original_height'])<0.003
        if p['mode']=='source_bytes_unchanged':assert p['sha256']==p['original_reference']['sha256']
    assert len({p['primary_number']for p in prep['rows']if p['role']=='new_description_lead'})==182
    assert sum(p['role']=='existing_comparator'for p in prep['rows'])==12
    assert max(p['bytes']for p in prep['rows'])==99820 and len({p['sha256']for p in prep['rows']})==205
    assert{p['number']for p in prep['rows']}=={d['number']for d in decisions if d['image_candidate']}
    assert sum(p['mode']=='source_bytes_unchanged'for p in prep['rows'])==44
    assert sum((p['width'],p['height'])!=(p['original_width'],p['original_height'])for p in prep['rows'])==21
    album=m.load(RUN/'album-reference-001.json.gz');checked(album['receipt']);checked(album['text_reference'])
    for page in album['selected_pages']:checked(page['render'])
    checked(review['album']['additional_cover_render']);assert review['album']['pdf_pages_reviewed']==[148,149,153,199,206]
    scripts=sorted((m.ROOT/'ops').glob('museum-expansion-larissa*20261010.py'));assert len(scripts)==13
    for p in scripts:ast.parse(p.read_text(),filename=str(p))
    m.save(RUN/'image-qa-001.json',dict(at=m.now(),prepared_frames_reviewed=205,prepared_contacts_reviewed=prep['sheets'],
        result='Passed visual review:205 complete source frames, museum watermarks and paper margins retained; no wrong-work substitution or introduced crop. Source resolution is not enhanced. Album plate view labels remain separate from one physical catalogue count.',
        maximum_bytes=99820,source_bytes_unchanged=44,jpeg_reencoded=161,proportionally_resized=21,
        source_review_reference=ref(RUN/'physical-unit-review-001.json'),prepared_reference=ref(RUN/'image-delivery-prepared-001.json'),production_uploaded=0,production_attached=0))
    m.save(RUN/'remaining-research-001.json',dict(at=m.now(),institution_id=r.IID,goal_complete=False,last_verified_catalogue_count=18,last_verified_dateeligible_count=15,last_verified_at='2026-10-09',fresh_production_counts=False,
        proposed_new_candidates=187,numeric_date_candidates=180,qualified_or_conflicting_candidates=7,conditional_catalogue_total_before_live_reconciliation=205,conditional_numeric_dateeligible_total_before_live_reconciliation=195,
        source_records=820,index_cards_inspected=210,index_cards_uninspected=610,extra_historical_comparators=6,total_unique_source_records_reviewed=216,source_records_outside_completed_selection=604,
        deferred_additional_captured_lead='1961 chromolithograph Epameinondas; source sample is outside216 reviewed records and187 proposed units. Artist life is not printing date. No image downloaded for this deferred lead.',
        same_album_secondary_sources=11,date_conflicts=sorted(r.CONFLICTS),before_dates=[30,39,80],open_after_date=32,missing_images=sorted(r.MISSING_IMAGES),public_image_date_holds=sorted(r.DATE_IMAGE_HOLDS),
        prepared_files=205,new_works_with_images=182,existing_comparator_images=12,extra_album_plate_views=11,actual_added=0,actual_images_attached=0,
        auth=discovery['auth'],prior_pending=dict(kazantzakis=105,kilkis=26,theocharakis=197,zongolopoulos=199,chania=174),combined_pending_candidates=888,
        unresolved=['Fresh institution and bounded global source/title/creator/image identity checks','Protected production plan, backup, apply, readback and zero-write replay','Verified image storage upload and attachment preserving existing images','604 source records outside completed selection and3 missing image files','Unresolved dates and creator initialsL.C.; no fabricated canonical dates or painter IDs'],
        next_public_research='Averoff, then Athens City from the last saved priority queue. Production restoration remains independent of available public research.',
        source_access='No new provider denial. Three observed native image URLs404; row46 aggregator thumbnail was a non-image response with no retained body/headers. No exact retry or path guessing. Earlier provider access holds remain active.',
        candidate_reference=ref(RUN/'candidate-physical-units-001.json.gz')))
    m.save(RUN/'checks-001.json',dict(at=m.now(),source_receipts_verified=666,html_bodies_verified=449,source_pairs_reparsed=216,native_frames_verified=213,missing_frame_receipts=3,
        nonempty_descriptions_reviewed=206,distinct_nonempty_descriptions=190,description_groups_including_null=191,records_without_description=10,
        initial_sheets_verified=11,focused_sheets_verified=4,publication_pdf_and_five_rendered_pages_verified=True,prepared_frames_verified=205,prepared_sheets_verified=11,maximum_prepared_bytes=99820,
        decisions=dict(counts),physical_units=187,numeric_date_units=180,qualified_or_conflicting_units=7,source_ids_in_candidates=198,
        actual_added=0,actual_images_attached=0,production_mutation_attempted=False,local_database_writes=0,database_fixtures_created=0,
        prior_artifact_pins_verified=len(prior['artifacts']),prior_external_pins_verified=len(prior['external_artifacts']),
        validation_limit='Offline provenance, literal-source, physical-unit, date and image checks. Fresh production counts, global uniqueness and accepted existing-record mutations are not established.',script_reference=ref(Path(__file__).resolve())))
    paths={p for p in RUN.rglob('*')if p.is_file()}|set(scripts)|{prior_path,prod_path}
    pins=[ref(p)for p in sorted(paths)];external=[ref(p)for p in sorted(PROOF.rglob('*'))if p.is_file()]
    cp=RUN/'research-checkpoint-001.json'
    m.save(cp,dict(at=m.now(),wave=120,previous_goal_turn='progress',goal_status='active',goal_complete=False,
        previous_research_checkpoint=ref(prior_path),last_successful_production_checkpoint=ref(prod_path),production_campaign_totals_unchanged=prod['production_campaign_totals'],
        production_register_reference_unchanged=prod['production_institution_register_reference'],priority_queue_reference_unchanged=prod['priority_museum_queue_reference'],initial_full_historical_verification_reference=prod['initial_full_historical_verification_reference'],
        proposed_new_physical_units=187,kazantzakis_pending_candidates=105,kilkis_pending_candidates=26,theocharakis_pending_candidates=197,zongolopoulos_pending_candidates=199,chania_pending_candidates=174,combined_pending_candidates=888,
        actual_new_records=0,actual_images_attached=0,new_prepared_images=205,artifacts=pins,external_artifacts=external,checks_reference=ref(RUN/'checks-001.json'),remaining_reference=ref(RUN/'remaining-research-001.json'),
        next_work='Larissa wave120 complete research review:216 paired native/SC records from210/820 date-ordered cards plus6 historical;198new sources ->187 physical candidates,18existing,11secondary album plates. Kanas1946 album12 lithographs countedonce; exact album title from Parliament2019PDF148/149,153/199/206 corroborate publication only, not same impression. Retain12 named native Larissa views, noPDFphotoattachment. 140paintings8drawings39prints;180numeric dates7null(30/39before1920,80before1934,32After1920,51/54/102field-v-proseconflicts). Dateconflicts bothpre1955supportimageswithoutinventingnumericdate.18Vassilioubifolioscountonceeach.118/119differentnudes,109/187differentgardens,155/159differentNationalGardens; no merge.70/90/91Georgiadiscopies retaincopymaker;193L.C.initialsunknown; nopainterIDs/noaccessioninferredfromfilenames.213nativeJPEG+11contacts4focusedreviewed;3image404gaps46/67/92 metadataretained,SC46thumbnailnonimageunretainedheaders noexactstatusclaim; doNOTretryfilesorpaths.205preparedJPEG<=99820bytes:182newworks12existing11albumextraviews,44sourcebytesunchanged161recompressed21resized;11preparedcontactsreviewed;watermarks/fullframespreserved,actualCCBYNC4separateGreekpre1955authorization.8image-dateholds32/168/211-216.0DBwrites/uploads/attachments. Auth8thconsecutivefailuregcloudloginneeded, butpublicresearchprogress=>goalactive. ActualLarissa18/15stale9Oct;conditional205/195onlyafterliveidentitychecks.888pending6museums;actualCP112920new+1link7museumsunchanged.604sourcegaps;separate1961Epameinondasleadnotin216selectionnorcount. NextAveroff18/9thenAthensCity18/16fromsavedqueue. Needlivecomparators,exacthashplan,protectedbackup,apply/readback/replay,imageupload. Validateonlynew+CP1191108artifact420externalpins;inheritfullarchiveW101. Immutableartifacts,nocommit/deploy/agents/localfixtures/proxyrestart/credentialsearch.'))
    for pin in pins+external:checked(pin)
    m.save(RUN/'research-checkpoint-verification-001.json',dict(at=m.now(),checkpoint=ref(cp),artifact_pins_verified=len(pins),external_pins_verified=len(external),production_delivery=False,goal_complete=False))
    print(json.dumps(dict(checkpoint=ref(cp),artifacts=len(pins),external=len(external),candidates=187,prepared=205,actual_added=0)),flush=True)

if __name__=='__main__':main()
