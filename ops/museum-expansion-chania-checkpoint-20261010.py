"""Validate source provenance, reviewed physical units and unattached image files."""
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

spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-chania-review-20261010.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
m,RUN,PROOF=r.m,r.RUN,r.PROOF
ref=r.v.ref

def checked(pin):
    p=Path(pin['path']);p=p if p.is_absolute()else m.ROOT/p
    assert p.is_file()and hashlib.sha256(p.read_bytes()).hexdigest()==pin['sha256'],str(p)

def body(rc):
    raw=gzip.decompress((m.ROOT/rc['body_path']).read_bytes())
    assert rc['status']==200 and len(raw)==rc['bytes']and hashlib.sha256(raw).hexdigest()==rc['sha256']
    return raw

def main():
    prior_path=m.RUN/'native/zongolopoulos-paintings-20261010/research-checkpoint-001.json'
    assert ref(prior_path)['sha256']=='b62abdfbe4fa05e5309431b9e78baae7baea6859403f47f9a4d3d58ef060c49c'
    prior=m.load(prior_path)
    for pin in prior['artifacts']+prior['external_artifacts']:checked(pin)
    checked(prior['last_successful_production_checkpoint'])
    production=m.ROOT/prior['last_successful_production_checkpoint']['path'];prod=m.load(production)
    assert ref(production)['sha256']=='21973a04eb7411fec1875f49baa8f0ac9f426e5de3effd5da24ca028b22b891a'
    index=m.load(RUN/'bounded-index-001.json.gz');selection=m.load(RUN/'object-selection-001.json')
    sources=m.load(RUN/'selected-source-records-001.json.gz')['rows'];facts=m.load(RUN/'candidate-facts-001.json.gz')['rows']
    decisions=m.load(RUN/'editorial-source-decisions-002.json.gz')['rows'];units=m.load(RUN/'candidate-physical-units-002.json.gz')['rows']
    cards=[c for p in index['pages']for c in p['cards']]
    assert index['observed_collection_records']==320 and len(index['pages'])==7 and len(cards)==len({c['source_id']for c in cards})==210
    assert len(selection['selected'])==len(sources)==len(facts)==len(decisions)==212
    assert selection['new_description_leads']==194 and selection['existing_comparators']==18
    assert sum(c['historical_source_match']for c in cards)==16
    receipts=[m.load(p)for p in sorted((RUN/'captures').glob('*.json'))];html=[rc for rc in receipts if 'body_path'in rc]
    assert len(receipts)==635 and len(html)==433 and all(rc['status']==200 for rc in receipts)
    for rc in html:body(rc)
    for src,f,d in zip(sources,facts,decisions):
        assert src['number']==f['number']==d['number']
        agg=BeautifulSoup(body(src['receipt']),'html.parser');fields,enrichment=r.v.q.fields(agg)
        native=BeautifulSoup(body(src['native_receipt']),'html.parser')
        nf=r.v.s.native_fields(native)
        assert fields==src['fields']==f['source_fields']==d['source_fields']
        assert enrichment==src['enrichment']==d['aggregator_enrichment']
        assert nf==src['native_fields']==f['native_fields']==d['native_fields']
        assert d['inventory_literal']==nf['Κωδικός']and d['painter_id']is None
        main=native.select('h4.jet-listing-dynamic-field__content');desc=native.select('h6.jet-listing-dynamic-field__content')
        assert len(main)==1 and r.v.q.clean(main[0].get_text(' ',strip=True))==f['title']
        assert (r.v.q.clean(desc[0].get_text(' ',strip=True))if desc else None)==f['native_description']==d['native_description']
        assert d['native_dating_claims']==r.date_claims(f)
        assert d['proposed_status']=='review'and not d['ready_to_apply']and not d['applied']and not d['current_display_verified']
        assert 'http://creativecommons.org/licenses/by-nc-nd/3.0/gr/'in d['rights_links']
        if d['first']is not None:assert d['first']<=d['last']<=1970 and 0 not in(d['first'],d['last'])
    counts=collections.Counter(d['decision']for d in decisions)
    assert counts==dict(candidate_primary=174,existing_comparator=18,hold_art_scope=14,same_physical_work_secondary=6)
    assert len(units)==174 and sum(u['first']is not None for u in units)==117
    assert sum(u['first']is None for u in units)==57
    assert collections.Counter(u['work_type']for u in units)==dict(metalwork=68,ceramic=54,sculpture=40,unknown=12)
    assert sum('workshop'in u['creator_label']for u in units)==9
    ids=[sid for u in units for sid in u['source_ids']];assert len(ids)==len(set(ids))==180
    by={d['number']:d for d in decisions};ub={u['number']:u for u in units}
    assert ub[120]['source_numbers']==[120,108,109,133,143,144]and all('825'in by[n]['inventory_literal']for n in ub[120]['source_numbers'])
    assert ub[67]['source_numbers']==[67,151]and all('763'in by[n]['inventory_literal']for n in ub[67]['source_numbers'])
    assert all(ub[n]['first']is None and ub[n]['last']is None for n in [67,78,99,120,187])
    assert all(ub[n]['metadata_retained_despite_image_hold']and not ub[n]['image_candidate']for n in [38,110,161])
    assert(ub[185]['first'],ub[185]['last'])==(117,138)
    assert(ub[131]['first'],ub[131]['last'])==(-1400,-1300)and '1300 π.Χ.'in ub[131]['native_dating_claims']
    assert(ub[197]['first'],ub[197]['last'])==(1,50)and '14-37'in ub[197]['native_description']
    assert not facts[74]['title']and ub[75]['title']=='Περιδέραιο'and ub[75]['inventory_literal']=='Λ 2038'
    assert by[186]['work_type']=='sculpture'and 'Native dating field'in by[118]['date_review']
    ledger=list(csv.DictReader((RUN/'review-ledger-002.csv').open(encoding='utf-8-sig')));assert len(ledger)==212
    assert[(int(x['number']),x['decision'],x['title'])for x in ledger]==[(x['number'],x['decision'],x['title'])for x in decisions]
    visual=m.load(RUN/'visual-references-001.json');comp=m.load(RUN/'comparison-references-001.json');prep=m.load(RUN/'image-delivery-prepared-001.json')
    assert len(visual['rows'])==198 and len(visual['sheets'])==10 and not visual['exact_duplicate_images']
    assert len(comp['thumbnails'])==4 and len(comp['sheets'])==10
    assert len(prep['rows'])==188 and len(prep['sheets'])==10 and prep['production_attached']==prep['production_uploaded']==0
    for pin in visual['rows']+visual['sheets']+comp['thumbnails']+comp['sheets']+prep['sheets']:checked(pin)
    for p in visual['rows']+comp['thumbnails']:
        with Image.open(p['path'])as im:im.load();assert im.size==(p['width'],p['height'])
    for p in prep['rows']:
        checked(dict(path=p['prepared_path'],sha256=p['sha256']));checked(p['original_reference'])
        assert Path(p['prepared_path']).stat().st_size==p['bytes']<=100000 and p['complete_source_frame']and not p['attached']
        assert by[p['number']]['image_candidate']and by[p['number']]['image_date_policy_passed']
        with Image.open(p['prepared_path'])as im:im.load();assert im.format=='JPEG'and im.size==(p['width'],p['height'])
        assert abs(p['width']/p['height']-p['original_width']/p['original_height'])<0.002
    assert len({p['primary_number']for p in prep['rows']if p['role']=='new_description_lead'})==167
    assert sum(p['role']=='existing_comparator'for p in prep['rows'])==16
    assert max(p['bytes']for p in prep['rows'])==99979
    assert{p['number']for p in prep['rows']}=={d['number']for d in decisions if d['image_candidate']}
    assert len({p['sha256']for p in prep['rows']})==188
    scripts=sorted((m.ROOT/'ops').glob('museum-expansion-chania*20261010.py'));assert len(scripts)==12
    for p in scripts:ast.parse(p.read_text(),filename=str(p))
    m.save(RUN/'image-qa-001.json',dict(at=m.now(),prepared_frames_reviewed=188,prepared_contacts_reviewed=prep['sheets'],
        result='Passed: full frames retained, no introduced crop or duplicate attachment target. Original photographs, restorations, supports, seal-impression details and fragment views remain explicit. No independent resolution enhancement claimed.',
        related_coin_review='Source mint labels retained. Related Rhodes rows14/40 and Kydonia61/155/156 remain distinct photographed specimens with separate accessions and different designs or edge wear; Phaistos159/167/177/193/194 have different designs/flans and source accessions. Both coin faces count once.',
        source_review_reference=ref(RUN/'physical-unit-review-001.json'),prepared_reference=ref(RUN/'image-delivery-prepared-001.json'),production_uploaded=0,production_attached=0))
    m.save(RUN/'remaining-research-001.json',dict(at=m.now(),institution_id=r.IID,goal_complete=False,last_verified_catalogue_count=18,last_verified_dateeligible_count=0,last_verified_at='2026-10-09',fresh_production_counts=False,
        proposed_new_candidates=174,numeric_date_candidates=117,period_conflict_or_unknown_date_candidates=57,conditional_catalogue_total_before_live_reconciliation=192,
        source_records=320,index_cards_inspected=210,index_cards_uninspected=110,extra_historical_comparators=2,total_unique_source_records_reviewed=212,source_records_not_reviewed=108,
        art_scope_holds=14,secondary_same_object_sources=6,metadata_candidates_with_image_holds=[38,110,161],unknown_physical_date_candidates=[67,78,99],qualified_possible_date_candidate=187,
        prepared_files=188,new_works_with_images=167,existing_comparator_images=16,extra_cauldron_views=5,actual_added=0,actual_images_attached=0,
        auth='Seventh consecutive continuation token refresh failure; non-interactive reauthentication error. Existing Google session requires gcloud auth login. No credential search, alternate identity or production mutation.',
        prior_pending=dict(kazantzakis=105,kilkis=26,theocharakis=197,zongolopoulos=199),combined_pending_candidates=701,
        unresolved=['Fresh institution and bounded global source/accession/title duplicate checks','Protected production plan, backup, apply, readback and zero-write replay','Upload and attach reviewed source files while preserving existing images and metadata','Three image-identity holds and seven source-frame date holds','Remaining108 unreviewed source records and14 art-scope holds'],
        next_public_research='Larissa, then Averoff and Athens City from last saved priority queue. More Chania sources remain available; do not equate source-record count to distinct artworks.',
        source_access='One transient SearchCulture1049 timeout resolved on a single bounded continuation. Titleless source150 handled as missing metadata, not a network failure. No new access denial; all earlier provider holds persist.',
        candidate_reference=ref(RUN/'candidate-physical-units-002.json.gz')))
    m.save(RUN/'checks-001.json',dict(at=m.now(),html_bodies_verified=433,source_pairs_reparsed=212,source_receipts_verified=635,native_frames_verified=198,extra_aggregator_thumbnails_verified=4,
        initial_and_focused_sheets_verified=20,prepared_frames_verified=188,prepared_sheets_verified=10,maximum_prepared_bytes=99979,
        decisions=dict(counts),physical_units=174,numeric_date_units=117,period_or_unknown_date_units=57,source_ids_in_candidates=180,workshop_labels=9,
        actual_added=0,actual_images_attached=0,production_mutation_attempted=False,local_database_writes=0,database_fixtures_created=0,
        prior_artifact_pins_verified=len(prior['artifacts']),prior_external_pins_verified=len(prior['external_artifacts']),
        validation_limit='Offline provenance, literal-source, physical-unit, date and image checks. No fresh production count, global uniqueness or accepted existing-record metadata mutation is established.',script_reference=ref(Path(__file__).resolve())))
    paths={p for p in RUN.rglob('*')if p.is_file()}|set(scripts)|{prior_path,production}
    pins=[ref(p)for p in sorted(paths)];external=[ref(p)for p in sorted(PROOF.rglob('*'))if p.is_file()]
    cp=RUN/'research-checkpoint-001.json'
    m.save(cp,dict(at=m.now(),wave=119,previous_goal_turn='progress',goal_status='active',goal_complete=False,
        previous_research_checkpoint=ref(prior_path),last_successful_production_checkpoint=ref(production),production_campaign_totals_unchanged=prod['production_campaign_totals'],
        production_register_reference_unchanged=prod['production_institution_register_reference'],priority_queue_reference_unchanged=prod['priority_museum_queue_reference'],initial_full_historical_verification_reference=prod['initial_full_historical_verification_reference'],
        proposed_new_physical_units=174,kazantzakis_pending_candidates=105,kilkis_pending_candidates=26,theocharakis_pending_candidates=197,zongolopoulos_pending_candidates=199,combined_pending_candidates=701,
        actual_new_records=0,actual_images_attached=0,new_prepared_images=188,artifacts=pins,external_artifacts=external,checks_reference=ref(RUN/'checks-001.json'),remaining_reference=ref(RUN/'remaining-research-001.json'),
        next_work='Chania wave119 complete source review:212 paired native/SC records from210/320 index cards plus2 historical.194new sources→174 physical candidates,14 scopeholds,6 duplicate component/pairpages;18existing comparators. Canonical editorial/units/CSV version002 preserves001.117numeric dates+57 qualifiedperiod/conflict/unknown;3unknown and1possibleRoman.9workshoplabels, no painterIDs; types68metalwork54ceramic40sculpture12unknown. CauldronM825A–ΣΤ6pages countedonce,6fragmentviews; gold hairornament pairM763A/B2pages once.38/SC1013 claydisk vsagatephoto,110/SC241 claydisk vsflaskphoto,161/SC784 beardedbust vsunclearhead: imageholds butsecureaccessioned metadata retainedunillustrated.75/SC150 blankheading titlefromnativebrowser/alt/shortdesc,accessionΛ2038kept.198nativePNG+4SCcomparisonthumbs+10initial/10focused reviewed;188completeframeJPEG<=99979bytes+10preparedcontactsreviewed,167newworks+16existing+5extra cauldronviews,25proportionallyresized, originalPNGsLibrary. ActualCCBYNCND3.0GR separateGreekby1955authorization; footerBYSAnotimagelicence.0uploads/attachments/DBwrites. Auth7thconsecutivefailure gcloudauthloginneeded, publicresearchprogresssoactive. ActualChania18/0stale9Oct;conditional192onlyafterliveglobal/institutionidentitychecks. Pendingall5museums701;lastactualCP112920new+1linkacross7 unchanged. NextLarissa18/15, Averoff18/9,AthensCity18/16fromsavedqueuewhileauthpending.108sourcecardsunreviewedafter2extraold;14scopeholdsnotdelete. Needlivecomparators,exacthashplan,protectedbackup,apply/readback/replay,andimageupload. Validateonlynew+CP118506/174pins; inheritfullarchiveW101. Immutableartifacts;noagents/commits/deploy/localwrites/fixtures/proxyrestart/credentialsearch.'))
    for pin in pins+external:checked(pin)
    m.save(RUN/'research-checkpoint-verification-001.json',dict(at=m.now(),checkpoint=ref(cp),artifact_pins_verified=len(pins),external_pins_verified=len(external),production_delivery=False,goal_complete=False))
    print(json.dumps(dict(checkpoint=ref(cp),artifacts=len(pins),external=len(external),candidates=174,prepared=188,actual_added=0)),flush=True)

if __name__=='__main__':main()
