"""Validate wave117 source/physical review and prepared images without claiming delivery."""
import ast
import collections
import gzip
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image

spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-zongolopoulos-review-20261010.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
m,RUN,PROOF=r.m,r.RUN,r.PROOF


def checked(pin):
    p=Path(pin['path'])
    if not p.is_absolute():p=m.ROOT/p
    assert p.is_file(),str(p)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==pin['sha256'],str(p)


def main():
    previous=m.RUN/'native/theocharakis-dated-20261010/research-checkpoint-001.json'
    assert r.ref(previous)['sha256']=='19104950752f9be76c22d8cbf159f569f38ad56ab5c78b24b807ba6e7a5423ec'
    prior=m.load(previous)
    for pin in prior['artifacts']+prior['external_artifacts']:checked(pin)
    checked(prior['last_successful_production_checkpoint'])
    production=m.ROOT/prior['last_successful_production_checkpoint']['path'];prod=m.load(production)
    assert r.ref(production)['sha256']=='21973a04eb7411fec1875f49baa8f0ac9f426e5de3effd5da24ca028b22b891a'
    discovery=m.load(RUN/'source-discovery-001.json.gz')
    index=m.load(RUN/'bounded-index-001.json.gz')
    selected=m.load(RUN/'object-selection-001.json')
    sources=m.load(RUN/'selected-source-records-001.json.gz')['rows']
    decisions=m.load(RUN/'editorial-source-decisions-001.json.gz')['rows']
    units=m.load(RUN/'candidate-physical-units-001.json.gz')['rows']
    assert len(index['pages'])==6 and index['cards']==180
    cards=[v for p in index['pages']for v in p['cards']]
    assert len({v['source_id']for v in cards})==180
    assert collections.Counter(v['selection_state']for v in selected['deferred'])==dict(hold_date_crosses_1970=29,excluded_post_1970=20,excluded_document=3)
    assert len(selected['selected'])==len(sources)==len(decisions)==128
    assert len(discovery['historical_records'])==18
    receipts=[discovery['receipt']]+[p['receipt']for p in index['pages']]+[s['receipt']for s in sources]
    assert len(receipts)==135
    for rc in receipts:
        raw=gzip.decompress((m.ROOT/rc['body_path']).read_bytes())
        assert rc['status']==200 and len(raw)==rc['bytes'] and hashlib.sha256(raw).hexdigest()==rc['sha256']
    for key in ['foundation-home-001','metadata-64826-xml-001']:
        rc=m.load(RUN/('captures/'+key+'.json'));raw=gzip.decompress((m.ROOT/rc['body_path']).read_bytes())
        assert len(raw)==rc['bytes'] and hashlib.sha256(raw).hexdigest()==rc['sha256']
        if key.startswith('foundation'):assert rc['status']==403
        else:
            assert rc['status']==200
            assert 'Παρουσιάστηκε σφάλμα'in BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
    first=index['pages'][0]['receipt'];firsthtml=gzip.decompress((m.ROOT/first['body_path']).read_bytes())
    text=r.q.clean(BeautifulSoup(firsthtml,'html.parser').get_text(' ',strip=True))
    assert '1 - 30 from 482 items'in text and '997 items'in discovery['text']
    by_source={v['source_id']:v for v in sources}
    for row in decisions:
        s=by_source[row['source_id']];f=s['fields']
        assert row['source_fields']==f and row['aggregator_enrichment']==s['enrichment']
        years=[int(v)for v in f['Ημερομηνία'][0].split('/')]
        assert (row['first'],row['last'])==(years[0],years[-1]) and row['last']<=1970
        assert row['creator_label']==f['Δημιουργός'][0] and row['title']==f['Τίτλος'][0]
        assert 'Inventory number '+row['inventory_source_literal']in f['Περιγραφή']
        assert row['inventory_literal']is None and row['painter_id']is None
        assert row['dimensions_text']is None and row['proposed_status']=='review'
        assert not row['ready_to_apply']and not row['applied']and not row['current_display_verified']
    assert len(units)==49
    assert collections.Counter(v['work_type']for v in units)==dict(sculpture=30,drawing=9,watercolor=4,painting=6)
    assert sum(v['creator_label'].startswith('Ελένη')for v in units)==8
    assert sum(v['last']<=1955 for v in units)==19
    used=[sid for v in units for sid in v['source_ids']]
    historical={v['source_id']for v in discovery['historical_records']}
    held={v['source_id']for v in decisions if v['decision']=='hold_physical_identity'}
    assert len(used)==len(set(used))==49 and len(held)==61
    assert not(set(used)&(held|historical))
    for card in selected['deferred']:
        assert not(RUN/('captures/selected-'+card['source_id'].rsplit('-',1)[1]+'-001.json')).exists()
    visual=m.load(RUN/'visual-references-001.json');comp=m.load(RUN/'comparison-references-001.json')
    assert len(visual['rows'])==128 and len(visual['sheets'])==7 and len(comp['sheets'])==11
    assert len(visual['exact_duplicate_images'])==15 and sum(len(v)for v in visual['exact_duplicate_images'])==47
    assert len({v['sha256']for v in visual['rows']})==96
    for pin in visual['rows']+visual['sheets']+comp['sheets']:checked(pin)
    images=m.load(RUN/'image-delivery-prepared-001.json')['rows']
    assert len(images)==19
    candidate_by_id={v['primary_source_id']:v for v in units}
    for row in images:
        p=Path(row['prepared_path']);raw=p.read_bytes()
        assert len(raw)==row['bytes']<=100000
        assert hashlib.sha256(raw).hexdigest()==row['sha256']==row['original_reference']['sha256']
        assert p.read_bytes()==Path(row['original_reference']['path']).read_bytes()
        assert candidate_by_id[row['source_id']]['last']==row['last']<=1955
        assert not row['attached']and not row['ready_to_attach']and row['production_artwork_id']is None
        assert row['rights_status']=='restricted'
        with Image.open(p)as im:assert im.size==(row['width'],row['height'])
    assert max(v['bytes']for v in images)==30101
    scripts=sorted((m.ROOT/'ops').glob('museum-expansion-zongolopoulos*20261010.py'))
    assert len(scripts)==7
    for p in scripts:ast.parse(p.read_text(),filename=str(p))
    general_rc=discovery['receipt'];general=BeautifulSoup(gzip.decompress((m.ROOT/general_rc['body_path']).read_bytes()),'html.parser')
    default_cards=r.z.index(general)
    assert len(default_cards)==30
    m.save(RUN/'next-source-leads-001.json',dict(at=m.now(),default_index_cards=default_cards,
        receipt=general_rc,policy='Already captured default collection page; date-sort omission does not exclude undated artwork records. Next bounded pass can inspect default pages and prioritize distinct paintings/drawings. Do not count these unreviewed index cards as candidates.'))
    m.save(RUN/'remaining-research-001.json',dict(at=m.now(),institution_id=r.IID,goal_complete=False,
        last_verified_catalogue_count=18,last_verified_dateeligible_count=18,last_verified_at='2026-10-09',fresh_production_counts=False,
        researched_new_candidates=49,physical_identity_hold_records=61,prepared_images=19,actual_added=0,actual_images_attached=0,
        observed_collection_records=997,observed_dated_records=482,date_sorted_cards_inspected=180,
        unknown_date_records_omitted_by_source_sort=515,uninspected_date_sorted_cards=302,
        index_date_crossing_holds=29,index_post1970_exclusions=20,index_document_exclusions=3,
        auth='Fifth continuation token refresh still fails; terminal exit1 confirmed. gcloud auth login required before fresh production reconciliation or upload. Public research made progress, so the overall goal is not at an impasse.',
        next_source_work='Bounded undated/eligible painting and drawing selection from the observed default collection index. Current49 proposals do not reach the target; do not fill gaps with unverified sculpture copies.',
        source_access=['www.zongolopoulos.gr403 hold; do not retry/bypass','collection.zongolopoulos.gr homepage ConnectTimeout once; no native object data captured','SearchCulture observed XML download returned200errorHTML; do not treat as metadata or retry json workaround'],
        historical_audit='Review existing nude/Olive shared-photo records and related Horse/Cyclopean versions using fresh production evidence. No automatic merge or deletion.',
        image_policy_correction='Specific Greek museum/artist approval supports selected restricted-labelled images created by1955. Preserve labels and source evidence; do not reapply an NC/ND-only blanket hold in this authorized scope.',
        candidate_reference=r.ref(RUN/'candidate-physical-units-001.json.gz'),image_reference=r.ref(RUN/'image-delivery-prepared-001.json')))
    m.save(RUN/'checks-001.json',dict(at=m.now(),valid_source_html_bodies_verified=135,separate_failure_bodies_verified=2,
        literal_fields_preserved=True,source_images_verified=128,review_montages_verified=18,prepared_images_verified=19,
        exact_duplicate_groups=15,duplicate_group_source_records=47,physical_candidates=49,held_source_records=61,
        prepared_images_with_identical_original_bytes=19,prepared_images_over100000bytes=0,
        actual_added=0,production_images_attached=0,production_mutation_attempted=False,local_database_writes=0,database_fixtures_created=0,
        previous_artifact_pins_verified=len(prior['artifacts']),previous_external_pins_verified=len(prior['external_artifacts']),
        validation_limit='Source metadata, image and physical-unit review only. No fresh production identity, canonical accession, verified live painter ID, count refresh, execution plan or backup. Prepared images are source thumbnails and remain unattached.',
        script_reference=r.ref(Path(__file__).resolve())))
    paths={p for p in RUN.rglob('*')if p.is_file()}|set(scripts)|{previous,production,m.ROOT/'docs/ARTLINE_IMAGE_USE.md'}
    pins=[r.ref(p)for p in sorted(paths)]
    external=[r.ref(p)for p in sorted(PROOF.rglob('*'))if p.is_file()]
    checkpoint=RUN/'research-checkpoint-001.json'
    m.save(checkpoint,dict(at=m.now(),wave=117,previous_goal_turn='progress',goal_status='active',goal_complete=False,
        previous_research_checkpoint=r.ref(previous),last_successful_production_checkpoint=r.ref(production),
        production_campaign_totals_unchanged=prod['production_campaign_totals'],
        production_register_reference_unchanged=prod['production_institution_register_reference'],priority_queue_reference_unchanged=prod['priority_museum_queue_reference'],
        initial_full_historical_verification_reference=prod['initial_full_historical_verification_reference'],
        proposed_new_physical_units=49,prepared_images=19,actual_new_records=0,actual_images_attached=0,
        kazantzakis_pending_candidates=105,kilkis_pending_candidates=26,theocharakis_pending_candidates=197,
        artifacts=pins,external_artifacts=external,checks_reference=r.ref(RUN/'checks-001.json'),remaining_reference=r.ref(RUN/'remaining-research-001.json'),
        next_work='Zongolopoulos49proposed physicalworks from110newsourcepages,61held;18historicalcomparators unchanged and some shared-photo conflicts flagged.128SCpages+profile+6datedindexes(180cards)reviewed;29cross1970,20later,3documentsnotfetched.15exactimagegroupscover47records,96uniquehashes.7contacts+11montagesreviewed.49types30sculpture/9drawing/4watercolor/6painting,41George+8Helen. Inventory strings visibly doubled but retainedliteral; canonical accessionnull, nohalving.19by1955authentic sourceJPEGframesprepared unchangedbytes<=30101,restrictedCCBYNCND actual labels underSPECIFIC authorizedGreeksourceworkflow. CorrectprioroverbroadNCNDholdinterpretation usingimage-policy-review; noindependentlicenceclaim. Currentproductionauthstillfailsfifthturnterminalexit1, restoregcloudauthlogin. Publicresearchprogresscontinues so notblockedoverall. Next boundeddefaultindex paintings/drawings inclunknownreviewdates toexpand toward100; nativecollection997records/482dated,515omittedfromdatesort. Do notaddunverifiedsculpturecopies. Mainwww.zongolopoulos.gr403newhold; collection.zongolopoulos.gr oneconnecttimeout(noobjectdata); observedSC/xml200errorHTMLdonotuse/retryJSON. NewimagefileprepLibraryonly; noDBwrites/localchanges/assetsuploads. InheritCP112lastproduction920new+1linkacross7,921protectedIDs. PendingKaz105missingcomparator;Kilkis26;Theo197(125dated72unknown),19Zongimagesunattached. Needfreshscoped/globalduplicate/painterchecks thenexactplan/backup/apply/readback/replay. Existinghistoricalstatus/date/imagepreserved. Noagents/commits/deploy/proxyrestart/credentialsearch; preserve immutableartifacts.'))
    for pin in pins+external:checked(pin)
    m.save(RUN/'research-checkpoint-verification-001.json',dict(at=m.now(),checkpoint=r.ref(checkpoint),
        artifact_pins_verified=len(pins),external_pins_verified=len(external),production_delivery=False,goal_complete=False))
    print(json.dumps(dict(checkpoint=r.ref(checkpoint),artifacts=len(pins),external=len(external),proposed_physical_units=49,prepared_images=19,actual_added=0)),flush=True)


if __name__=='__main__':main()
