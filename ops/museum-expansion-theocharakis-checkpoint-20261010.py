"""Verify wave 115 source research and inherit the last actual production receipt."""
import ast
import collections
import gzip
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-theocharakis-review-20261010.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
m,RUN,PROOF=r.m,r.RUN,r.PROOF


def checked(pin):
    p=Path(pin['path'])
    if not p.is_absolute():p=m.ROOT/p
    assert p.is_file(),str(p)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==pin['sha256'],str(p)


def main():
    previous=m.RUN/'native/kilkis-review-20261010/research-checkpoint-001.json'
    assert r.ref(previous)['sha256']=='b224245951d11814db9dcc2104b868f2b2600c7f7998c066097b4c6000a07f9e'
    prior=m.load(previous)
    for pin in prior['artifacts']+prior['external_artifacts']:checked(pin)
    checked(prior['last_successful_production_checkpoint'])
    production=m.ROOT/prior['last_successful_production_checkpoint']['path']
    prod=m.load(production)
    assert r.ref(production)['sha256']=='21973a04eb7411fec1875f49baa8f0ac9f426e5de3effd5da24ca028b22b891a'
    source=m.load(RUN/'selected-source-records-001.json.gz')['rows']
    native=m.load(RUN/'native-object-records-001.json.gz')['rows']
    decisions=m.load(RUN/'editorial-source-decisions-001.json.gz')['rows']
    units=m.load(RUN/'candidate-physical-units-001.json.gz')['rows']
    receipts={}
    for row in source+native:
        receipt=row['receipt'];raw=gzip.decompress((m.ROOT/receipt['body_path']).read_bytes())
        assert receipt['status']==200 and len(raw)==receipt['bytes']
        assert hashlib.sha256(raw).hexdigest()==receipt['sha256']
        receipts[receipt['body_path']]=receipt
    assert len(receipts)==360
    assert len(source)==len(native)==len(decisions)==180
    bsrc={v['source_id']:v for v in source};bnative={v['source_id']:v for v in native}
    for row in decisions:
        original=bnative[row['source_id']];s=bsrc[row['source_id']]
        assert all(original['source_comparison'].values())
        assert original['creators']==['Σπύρος Παπαλουκάς (1892 - 1957)']
        assert row['source_fields']==s['fields'] and row['native_fields']==original['fields']
        date=original['fields']['έτος']
        # Independently verify dedicated artwork dates, never creator life dates.
        if date=='χ.χ.':assert row['first'] is None and row['last'] is None
        else:
            years=[int(v.strip())for v in date.split('-')]
            assert row['first']==years[0] and row['last']==years[-1] and row['last']<=1970
        assert row['inventory_literal'] is None and row['painter_id'] is None
        assert row['creator_label']==s['fields']['Δημιουργός'][0]
        assert not row['applied'] and not row['ready_to_apply'] and not row['current_display_verified']
        assert row['proposed_status']=='review'
    assert len(units)==138
    used=[sid for unit in units for sid in unit['source_ids']]
    assert len(used)==len(set(used))==146
    protected={v['source_id']for v in source if v['role']=='historical_comparator'}
    holds={v['source_id']for v in decisions if v['decision']=='hold_physical_unit'}
    existing_sides={v['source_id']for v in decisions if v['decision']=='existing_sheet_reference_only'}
    assert not(set(used)&(protected|holds|existing_sides))
    assert len(protected)==18 and len(holds)==12 and len(existing_sides)==4
    assert sum(len(v['source_ids'])==2 for v in units)==8
    assert sum(v['date_scope']=='eligible'for v in units)==66
    assert sum(v['date_scope']=='requires_editorial_review'for v in units)==72
    visual=m.load(RUN/'visual-references-001.json')
    assert len(visual['rows'])==180 and len(visual['sheets'])==9 and not visual['exact_duplicate_images']
    images={v['path']:v for v in visual['rows']};sheets={v['path']:v for v in visual['sheets']}
    for i in [1,2,3]:
        data=m.load(RUN/('comparison-references-00'+str(i)+'.json'))
        images.update({v['path']:v for v in data['rows']})
        sheets.update({v['path']:v for v in data['sheets']})
    assert len(images)==243 and len(sheets)==40
    for pin in list(images.values())+list(sheets.values()):checked(pin)
    assert len({v['full_image_url']for v in native})==180
    index=m.load(RUN/'bounded-index-001.json.gz')
    assert len(index['pages'])==6 and sum(len(p['cards'])for p in index['pages'])==180
    assert '2,567 items' in m.load(RUN/'source-discovery-001.json.gz')['rows'][1]['text']
    selection=m.load(RUN/'object-selection-001.json')
    assert [v['source_id']for v in selection['excluded']]==['theocharakis/000163-111578']
    assert not (RUN/'captures/selected-111578-001.json').exists()
    for p in (m.ROOT/'ops').glob('museum-expansion-theocharakis*20261010.py'):ast.parse(p.read_text(),filename=str(p))
    collection_receipt=m.load(RUN/'captures/searchculture-collection-001.json')
    soup=BeautifulSoup(gzip.decompress((m.ROOT/collection_receipt['body_path']).read_bytes()),'html.parser')
    select=soup.find('select',id='sortResults')
    options=[dict(value=o['value'],label=o.get_text(' ',strip=True))for o in select.find_all('option')]
    m.save(RUN/'remaining-research-001.json',dict(at=m.now(),institution_id=r.t.IID,goal_complete=False,
        last_verified_catalogue_count=18,last_verified_dateeligible_count=12,fresh_production_counts=False,
        last_catalogue_count_at='2026-10-09T12:21:32Z',last_dateeligible_count_at='2026-10-09T12:23:56Z',
        researched_physical_candidates=138,known_date_candidates=66,unknown_date_candidates=72,
        source_hold_records=12,proposed_existing_sheet_references=4,actual_added=0,actual_images_attached=0,
        total_index_items=2567,index_cards_inspected=180,uninspected_index_cards=2387,
        outside_index_historical_comparators_captured=1,
        observed_sort_control=dict(name=select['name'],id=select['id'],options=options,
            form_action='/aggregator/portal/collections/theocharakis/search',method='GET',source_receipt=collection_receipt),
        next_source_research='Prioritize explicitly dated paintings/studies for a further bounded selection. YEAR_ASC sort option is observed, but request wiring and stable pagination still need inspection. Do not guess query behavior or download the whole archive.',
        auth='Third consecutive continuation sees token refresh fail. Public-source research made substantive progress; the goal is not at an impasse. gcloud auth login is needed before production work.',
        must_resolve=['Fresh scoped production baseline and global source/creator/title identity comparators',
          'Live Papaloukas painter identity and every source ID of proposed two-sided units',
          '12 physical-unit source holds; no quota additions from these records',
          'Exact-hash plan, protected prior campaign records, successful backup, apply, readback and zero-write replay'],
        candidate_reference=r.ref(RUN/'candidate-physical-units-001.json.gz')))
    m.save(RUN/'checks-001.json',dict(at=m.now(),source_page_bodies_verified=360,
        native_source_agreement_records=180,source_fields_preserved=True,original_images_verified=243,
        rendered_review_sheets_verified=40,physical_candidates=138,represented_source_records=146,
        sources_reused_across_new_units=0,known_date_candidates=66,unknown_date_candidates=72,
        excluded_photographic_documentation_not_fetched=True,actual_added=0,production_images_attached=0,
        production_mutation_attempted=False,local_database_writes=0,database_fixtures_created=0,
        previous_artifact_pins_verified=len(prior['artifacts']),previous_external_pins_verified=len(prior['external_artifacts']),
        validation_limit='Original-source metadata and physical-image review only. No fresh production identity/baseline, numerical museum count refresh, execution plan or backup. Hash uniqueness is not proof of artwork uniqueness.',
        script_reference=r.ref(Path(__file__).resolve())))
    paths={p for p in RUN.rglob('*')if p.is_file()}
    paths|=set((m.ROOT/'ops').glob('museum-expansion-theocharakis*20261010.py'))
    paths|={previous,production}
    pins=[r.ref(p)for p in sorted(paths)]
    external=[r.ref(p)for p in sorted(PROOF.rglob('*'))if p.is_file()]
    checkpoint=RUN/'research-checkpoint-001.json'
    m.save(checkpoint,dict(at=m.now(),wave=115,previous_goal_turn='progress',goal_status='active',goal_complete=False,
        previous_research_checkpoint=r.ref(previous),last_successful_production_checkpoint=r.ref(production),
        production_campaign_totals_unchanged=prod['production_campaign_totals'],
        production_register_reference_unchanged=prod['production_institution_register_reference'],
        priority_queue_reference_unchanged=prod['priority_museum_queue_reference'],
        initial_full_historical_verification_reference=prod['initial_full_historical_verification_reference'],
        proposed_new_physical_units=138,actual_new_records=0,actual_existing_sheet_updates=0,
        kazantzakis_pending_candidates=105,kilkis_pending_candidates=26,
        artifacts=pins,external_artifacts=external,checks_reference=r.ref(RUN/'checks-001.json'),
        remaining_reference=r.ref(RUN/'remaining-research-001.json'),
        next_work='Restore production authentication when available. Kazantzakis 105: missing fresh comparator snapshot then exact plan/backup/apply/verify/replay; CP112 remains last actual delivery, 920 new+1 link across7 museums,921 protected prior IDs. Kilkis26 physical candidates remain pending identity,6holds. Theocharakis138 proposed physical units derive from162 source candidates:138 primaries+8same-sheet secondaries+4existing-sheet references+12holds.66dated,72unknown.180SC+180native pages allagree; no fake accessions/painter IDs. Images180thumb+63selectednative are internal only. All9contacts+31comparison sheets reviewed. Native collection has2567records; first180indexcards inspected, one photo excluded, eighteenth old comparator fromoutside sample. Exact source/creator/physical identity and source aliases stillneed liveDBcheck. Last Theocharakis18/12 stale9Oct. No current-count projection or threshold completion claim. Can continue bounded dated source selection or next queue museums Zongolopoulos/Chania while auth remains unavailable. All providerholds inherited,including ejournals.epublishing.ekt.gr403. Do not retry blockedhosts, restart proxy, search credentials, mutate localDB, commit, deploy or spawn agents. Preserve immutable artifacts; version new reconciliation instead of rerunning writers.'))
    for pin in pins+external:checked(pin)
    m.save(RUN/'research-checkpoint-verification-001.json',dict(at=m.now(),checkpoint=r.ref(checkpoint),
        artifact_pins_verified=len(pins),external_pins_verified=len(external),production_delivery=False,goal_complete=False))
    print(json.dumps(dict(checkpoint=r.ref(checkpoint),artifacts=len(pins),external=len(external),proposed_physical_units=138,actual_added=0)),flush=True)


if __name__=='__main__':main()
