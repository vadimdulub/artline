"""Validate wave 116 evidence and preserve the distinction between candidates and delivery."""
import ast
import collections
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-theocharakis-dated-review-20261010.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
m,RUN,PROOF=r.m,r.RUN,r.PROOF


def checked(pin):
    p=Path(pin['path'])
    if not p.is_absolute():p=m.ROOT/p
    assert p.is_file(),str(p)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==pin['sha256'],str(p)


def main():
    previous=r.d.OLD/'research-checkpoint-001.json'
    assert r.ref(previous)['sha256']=='111102ce42532f27023cc3b2c22f580a547efc232896982933b4618b499dc8ba'
    prior=m.load(previous)
    for pin in prior['artifacts']+prior['external_artifacts']:checked(pin)
    checked(prior['last_successful_production_checkpoint'])
    production=m.ROOT/prior['last_successful_production_checkpoint']['path']
    prod=m.load(production)
    assert r.ref(production)['sha256']=='21973a04eb7411fec1875f49baa8f0ac9f426e5de3effd5da24ca028b22b891a'
    sources=m.load(RUN/'selected-source-records-001.json.gz')['rows']
    natives=m.load(RUN/'native-object-records-001.json.gz')['rows']
    rows=m.load(RUN/'editorial-source-decisions-001.json.gz')['rows']
    units=m.load(RUN/'candidate-physical-units-001.json.gz')['rows']
    bs={v['source_id']:v for v in sources};bn={v['source_id']:v for v in natives}
    index=m.load(RUN/'dated-index-001.json.gz')
    assert len(index['pages'])==3
    cards=[v for p in index['pages']for v in p['cards']]
    assert len(cards)==len({v['source_id']for v in cards})==90
    assert sum(v['prior_source_review']for v in cards)==1
    selection=m.load(RUN/'object-selection-001.json')
    assert len(selection['rows'])==60 and len(selection['deferred'])==30
    assert sum(not v['prior_source_review']for v in selection['deferred'])==29
    old_index=m.load(r.d.OLD/'bounded-index-001.json.gz')
    old_cards=[v for p in old_index['pages']for v in p['cards']]
    assert len({v['source_id']for v in cards+old_cards})==269
    receipts={}
    for row in sources+natives+index['pages']:
        receipt=row['receipt'];raw=gzip.decompress((m.ROOT/receipt['body_path']).read_bytes())
        assert receipt['status']==200 and len(raw)==receipt['bytes']
        assert hashlib.sha256(raw).hexdigest()==receipt['sha256']
        receipts[receipt['body_path']]=receipt
    assert len(receipts)==123 and len(sources)==len(natives)==len(rows)==60
    differences=collections.Counter()
    for row in rows:
        source=bs[row['source_id']];native=bn[row['source_id']]
        assert row['source_fields']==source['fields'] and row['native_fields']==native['fields']
        assert row['aggregator_date_literals']==source['fields']['Ημερομηνία δημιουργίας']
        years=[int(v.strip())for v in native['fields']['έτος'].split('-')]
        assert row['first']==years[0] and row['last']==years[-1] and row['last']<=1970
        assert row['date_display']==native['fields']['έτος']
        assert row['creator_label']==source['fields']['Δημιουργός'][0]
        assert row['native_creator_labels']==native['creators']
        assert row['inventory_literal']is None and row['painter_id']is None
        assert not row['applied'] and not row['ready_to_apply'] and not row['current_display_verified']
        assert row['proposed_status']=='review'
        for field,equal in native['source_comparison'].items():
            if not equal:differences[field]+=1
    assert differences==dict(creator=40,medium=26,date=2),differences
    assert len(units)==59 and all(v['date_scope']=='eligible'for v in units)
    assert collections.Counter(v['work_type']for v in units)==dict(painting=28,drawing=20,watercolor=11)
    used=[sid for v in units for sid in v['source_ids']]
    old_sources=m.load(r.d.OLD/'selected-source-records-001.json.gz')['rows']
    assert len(used)==len(set(used))==59
    assert not (set(used)&{v['source_id']for v in old_sources})
    assert 'theocharakis/000163-111641'not in used
    assert 'theocharakis/000163-111796'in used
    assert sum(v['last']>1955 for v in units)==13
    old_units=m.load(r.d.OLD/'candidate-physical-units-001.json.gz')['rows']
    assert len(old_units)==138 and len(old_units)+len(units)==197
    assert sum(v['date_scope']=='eligible'for v in old_units+units)==125
    visual=m.load(RUN/'visual-references-001.json')
    compare=m.load(RUN/'comparison-references-001.json')
    assert len(visual['rows'])==60 and len(visual['sheets'])==3 and not visual['exact_duplicate_images']
    assert len(compare['rows'])==26 and len(compare['sheets'])==10
    assert next(v for v in compare['rows']if v['number']==160)['source_id']=='theocharakis/000163-111110'
    for pin in visual['rows']+visual['sheets']+compare['rows']+compare['sheets']:checked(pin)
    old_visual=m.load(r.d.OLD/'visual-references-001.json')
    assert not ({v['sha256']for v in visual['rows']}&{v['sha256']for v in old_visual['rows']})
    old_native=m.load(r.d.OLD/'native-object-records-001.json.gz')['rows']
    assert len({v['full_image_url']for v in natives})==60
    assert not ({v['full_image_url']for v in natives}&{v['full_image_url']for v in old_native})
    scripts=sorted((m.ROOT/'ops').glob('museum-expansion-theocharakis-dated*20261010.py'))
    assert len(scripts)==6
    for path in scripts:ast.parse(path.read_text(),filename=str(path))
    m.save(RUN/'remaining-research-001.json',dict(at=m.now(),institution_id=r.IID,goal_complete=False,
        last_verified_catalogue_count=18,last_verified_dateeligible_count=12,
        last_catalogue_count_at='2026-10-09T12:21:32Z',last_dateeligible_count_at='2026-10-09T12:23:56Z',fresh_production_counts=False,
        this_wave_candidates=59,combined_pending_candidates=197,combined_known_date_candidates=125,combined_unknown_date_candidates=72,
        this_wave_held_source_records=1,prior_held_source_records=12,prior_existing_sheet_reference_candidates=4,
        total_collection_index_records_observed=2567,distinct_index_cards_inspected_across_two_waves=269,
        additional_historical_comparator_outside_these_cards=1,uninspected_index_cards=2298,
        this_wave_deferred_new_index_leads=29,actual_added=0,actual_images_attached=0,
        auth='Fourth consecutive continuation still has token-refresh failure. A gcloud auth print-access-token command with stdout suppressed failed at this wave start. Restore with gcloud auth login. No credential search or alternate account attempted.',
        next_source_work='Proceed to another queued museum, such as Zongolopoulos Foundation or Chania. Theocharakis now has 197 pending physical candidates; refresh live identity before claiming additions or threshold completion.',
        must_resolve=['Fresh scoped production baseline and source/creator/title identity comparators for all pending institutions',
            '111641 duplicate-image/metadata conflict; do not count as a second physical artwork',
            '103308 image/crop/dimension question before production image attachment',
            '13 selected works end after 1955: preserve eligible artwork metadata, hold museum-source production images',
            'Earlier Theocharakis 12 source holds and four existing-sheet citation proposals remain unchanged'],
        candidate_reference=r.ref(RUN/'candidate-physical-units-001.json.gz')))
    m.save(RUN/'checks-001.json',dict(at=m.now(),source_page_bodies_verified=123,individual_object_bodies_verified=120,index_page_bodies_verified=3,
        literal_source_and_native_metadata_preserved=True,metadata_differences_reconciled=dict(differences),
        reference_images_verified=86,rendered_review_sheets_verified=13,physical_candidates=59,held_source_records=1,
        combined_pending_theocharakis_candidates=197,combined_known_date_candidates=125,combined_unknown_date_candidates=72,
        actual_added=0,production_images_attached=0,production_mutation_attempted=False,local_database_writes=0,database_fixtures_created=0,
        previous_artifact_pins_verified=len(prior['artifacts']),previous_external_pins_verified=len(prior['external_artifacts']),
        validation_limit='Source research and visual review only. No fresh production baseline, painter reconciliation, duplicate check, count refresh, execution plan or backup. Different hashes or URLs do not prove different physical artworks.',
        script_reference=r.ref(Path(__file__).resolve())))
    paths={p for p in RUN.rglob('*')if p.is_file()}|set(scripts)|{previous,production}
    pins=[r.ref(p)for p in sorted(paths)]
    external=[r.ref(p)for p in sorted(PROOF.rglob('*'))if p.is_file()]
    checkpoint=RUN/'research-checkpoint-001.json'
    m.save(checkpoint,dict(at=m.now(),wave=116,previous_goal_turn='progress',goal_status='active',goal_complete=False,
        previous_research_checkpoint=r.ref(previous),last_successful_production_checkpoint=r.ref(production),
        production_campaign_totals_unchanged=prod['production_campaign_totals'],
        production_register_reference_unchanged=prod['production_institution_register_reference'],
        priority_queue_reference_unchanged=prod['priority_museum_queue_reference'],
        initial_full_historical_verification_reference=prod['initial_full_historical_verification_reference'],
        proposed_new_physical_units=59,actual_new_records=0,combined_theocharakis_pending_candidates=197,
        kazantzakis_pending_candidates=105,kilkis_pending_candidates=26,
        artifacts=pins,external_artifacts=external,checks_reference=r.ref(RUN/'checks-001.json'),
        remaining_reference=r.ref(RUN/'remaining-research-001.json'),
        next_work='Restore production authentication when available; last token refresh failed at wave116 start, fourth continuation. No overall impasse: meaningful public research continues. CP112 remains last production delivery, 920new+1link across7 museums,921 protected IDs. Kazantzakis105 needs missing fresh comparator then exactplan/backup/apply/verify/replay; Kilkis26 pending. Theocharakis now197 pending(138prior+59dated),125dated/72unknown; lastactual18/12stale9Oct. New60sources:hold111641 duplicateimage/metadata versus111796; do not add or silently alias111641.59types28oil/11watercolour/20drawing. Two native broaderdates1031571950-55 and1030681948-49;40creator-life-date and26medium wording differences preserved.13endafter1955 heldfrommuseumproductionimages;103308 additionalimagehold20x19dimensions versuslandscape asset.120objectpages+3index;60thumb+26selectednative;3contacts+10comparisonssheets allreviewed.269distinctindexcards acrosswaves of2567;29newdatedindexleadsdeferred. Native sourceIDs unique versusprior but liveglobalidentity pending. Currentcount and target notclaimed. Next public museumZongolopoulos orChania fromCP112queue; donot keep expandingTheocharakis beforeliveapplyunlessresolvingholds. Inherit allproviderholds inclEKTjournal403, immutableevidence, read-onlylocal, noagents/commits/deploy/restartproxy/credentialsearch.'))
    for pin in pins+external:checked(pin)
    m.save(RUN/'research-checkpoint-verification-001.json',dict(at=m.now(),checkpoint=r.ref(checkpoint),
        artifact_pins_verified=len(pins),external_pins_verified=len(external),production_delivery=False,goal_complete=False))
    print(json.dumps(dict(checkpoint=r.ref(checkpoint),artifacts=len(pins),external=len(external),proposed_physical_units=59,actual_added=0)),flush=True)


if __name__=='__main__':main()
