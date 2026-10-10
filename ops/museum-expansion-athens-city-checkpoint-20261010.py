"""Verify source evidence and preserve unfinished Athens City reconciliation."""
import ast
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-athens-city-source-20261010.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
c,q,m,RUN=v.c,v.q,v.m,v.RUN
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    dest=RUN/'research-checkpoint-001.json';assert not dest.exists()
    assert c.ref(c.CP)['sha256']==c.CP_SHA;prior=m.load(c.CP)
    baseline=m.load(RUN/'baseline-verification-001.json');assert baseline['previous_goal_turn']=='progress' and len(baseline['prior_production_ids'])==1837
    assert baseline['previous_delivery_verification']['verified_new_records']==38 and baseline['previous_delivery_verification']['new_images']==53
    scope=m.load(RUN/'production-initial-scope-001.json.gz');assert scope['counts']=={c.IID:dict(linked=18,eligible=16)} and len(scope['scoped_ids'])==18
    index=m.load(RUN/'bounded-index-001.json.gz');selection=m.load(RUN/'metadata-selection-001.json');sources=m.load(RUN/'selected-source-records-001.json.gz')['rows'];review=m.load(RUN/'editorial-source-decisions-001.json.gz');summary=m.load(RUN/'source-review-summary-001.json');visual=m.load(RUN/'visual-references-001.json');images=m.load(RUN/'image-delivery-prepared-001.json')['rows'];identity=m.load(RUN/'production-identity-001.json.gz')
    assert len(index['unique_cards'])==162 and len({x['source_id'] for x in index['unique_cards']})==162
    assert len(index['pages'])==10 and len(selection['selected'])==len(sources)==len(review['rows'])==145 and len(selection['deferred'])==17
    by_source={x['source_id']:x for x in sources};decisions={x['number']:x for x in review['rows']}
    receipts=[x['receipt'] for x in sources]+[x['receipt'] for x in index['pages']]
    for rc in receipts:
        raw=gzip.decompress((m.ROOT/rc['body_path']).read_bytes());assert rc['status']==200 and len(raw)==rc['bytes'] and hashlib.sha256(raw).hexdigest()==rc['sha256']
    for row in review['rows']:
        src=by_source[row['source_id']];rc=src['receipt'];doc=BeautifulSoup(gzip.decompress((m.ROOT/rc['body_path']).read_bytes()),'html.parser');fields,enriched=q.fields(doc)
        assert fields==row['source_fields']==src['fields'] and enriched==row['aggregator_enrichment']==src['enrichment']
        assert row['proposed_status']=='review' and not row['ready_to_apply'] and not row['applied'] and row['artist_id'] is None
        if row['first'] is not None:assert row['last']<=1970 and fields.get('Ημερομηνία')
    for card in selection['deferred']:assert not(RUN/('captures/object-'+card['source_id'].split('000190-')[1]+'-001.json')).exists()
    assert summary['proposed_new_records']==135 and summary['numeric_dated_candidates']==47 and summary['unknown_date_candidates']==88
    assert decisions[111]['first'] is None and decisions[111]['source_date_literal']=='Γύρω στο 1850'
    assert all(decisions[x]['first'] is None for x in [1,2,3,7,8,31,49,50,62,105,112])
    assert decisions[35]['decision']==decisions[94]['decision']==decisions[108]['decision']=='hold_scope'
    assert all(decisions[x]['creator_label'] is None for x in [27,37]) and decisions[84]['creator_label'].startswith('Attributed to') and decisions[87]['creator_label'].startswith('Unresolved')
    assert decisions[63]['object_form'] is None and sum(x['object_form']=='icon' for x in review['rows'])==14
    assert len(visual['rows'])==142 and len(visual['sheets'])==6 and visual['unavailable_numbers']==[42] and not visual['exact_duplicate_groups']
    for pin in visual['rows']+visual['sheets']:assert sha(pin['path'])==pin['sha256']
    assert review['visual_review']['sheets_viewed']==6 and review['visual_review']['thumbnails_viewed']==142
    assert len(images)==39
    for im in images:
        row=decisions[im['number']];raw=Path(im['prepared_path']).read_bytes()
        assert row['decision']=='proposed_review_artwork' and im['last']==row['last']<=1955 and row['source_image_reviewed']
        assert raw==Path(im['original_reference']['path']).read_bytes() and hashlib.sha256(raw).hexdigest()==im['sha256'] and len(raw)==im['bytes']<=100000
        assert not im['attached'] and not im['ready_to_attach'] and im['production_artwork_id'] is None
        assert im['rights_status']=='public_domain' and im['rights_url'] in row['source_fields']['Δικαιώματα']
        with Image.open(im['prepared_path']) as image:assert image.size==(im['width'],im['height'])
    assert len(identity['state']['artwork_ids'])==1240 and len(identity['state']['artist_ids'])==17
    assert sum(bool(x['source_hits']) for x in identity['comparisons'])==7
    assert all(not x['source_hits'] for x in identity['comparisons'] if x['decision']=='proposed_review_artwork')
    assert len(identity['state']['matching_media'])==6
    m.save(RUN/'checks-001.json',dict(at=m.now(),source_html_bodies_verified=len(receipts),source_decisions_verified=145,unique_index_cards=162,index_post1970_exclusions=17,proposed_new_records=135,unknown_date_proposals=88,dated_proposals=47,source_scope_holds=3,existing_comparators=7,icon_proposals=14,thumbnails_verified=142,contact_sheets_verified=6,prepared_images_verified=39,images_uploaded=0,images_attached=0,actual_added=0,production_mutation_attempted=False,local_writes=0,previous_delivery_reverified=True,global_identity_artworks=1240,global_identity_artists=17,full_citations=2624,remaining='Focused same-object comparisons, remaining artist aliases/roles, target counts and prospective application plan not complete. No production import or upload is authorized by this checkpoint alone; existing user authorization remains subject to identity/date/source workflow.',script_reference=c.ref(Path(__file__).resolve())))
    remaining=dict(at=m.now(),institution_id=c.IID,catalogue=18,numeric_date_eligible=16,observed_at=scope['at'],goal_complete=False,actual_added=0,proposed_new_records=135,prepared_images=39,expected_catalogue_if_all_proposals_survive=153,additional_catalogue_gap_to200_if_all_survive=47,scope_holds={str(k):decisions[k]['review_notes'] for k in [35,94,108]},index_post1970_excluded=17,unavailable_image42='Non-image response; not retried; no visual claim.',next_work='Review focused title/creator comparators from live identity evidence; reconcile artist roles and expanded aliases before a selected plan/backup/apply. Then add another bounded group of documented pre1971 photographs/original art to pursue200. Catalogue2405 includes2243 records outside the eight reviewed art categories; this is not an eligible-work count.',notes=['Same-title prints2/3,4/5,10/11,15/16 and159/160 have different compositions/physical labels.44/45 and45/128 are distinct views; initial duplicate suspicion cleared by full thumbnail inspection.','Five sheets65/69/70/75/80 contain two drawings on one support, countonce each.','Thirteen Markezinis adolescent studies140-152 include copies of old masters; distinguish the student physical studies from prototypes. Keep dates unknown; no numeric lifespan inference.','Source31 has only a verso thumbnail; C.Vernet1758-1836 is lifespan. No frontimage attachment.','37 EastmanKodak and27 NYPL are not securely identified makers; preserve literal credits in citations.84Kalmouchos qualified;87Foltz/T.Foye unresolved.162PinxR.A. not a human creator.','Artist search has broad false positives (Serebriakova/Mayakovsky viaiakov,TsolakArmeniancreators) and does not fully cover Turner/Haupt/Roux/P.Paulide variants. Expand targeted queries; no automatic links.','EdwardBrandard-linked existing727bae1c-b8c0-53f7-9973-caf07b2e792c Venice from the Canal of the Giudecca may be a useful composition/impression comparator for162; distinct institutional impressions must not be merged automatically.','Possible secure existingauthorities to review: Iakovidis5c005acb-575b-44db-97c8-1680d829a479 for117, FloraKaravia6bc44dd0-9a43-4709-8fd4-454ead88bb15 for103; CarleVernet41ff76e2-fc39-463a-8a27-5529e096d2ca andDebucourta46f7573-fdd7-4265-99c0-e6edecb19d55 for31 roles. AlekosKontopoulos is not VyronKontopoulos109.','Source thumbnail quality only, mostly380px.39 pre1956 JPEGs unchanged bytes<=34499 prepared, actualCC0 labels; native high-resolution files not captured.','Native portal returned public SPA shell. Retained first-party public bundle reveals a public-client API contract with authorization configuration; no embedded authorization value was reused, no backend API called, do not print bundle credential-like contents. Public source HTML/thumbnails sufficient for current research.','Filterquery eightcategories together returned200Noresults (conjunctive). Separatequeries succeeded. PaginationJS omitted forsinglepages; v4handlesvisiblecountincluding singularitem. Originalfailedwriters immutable.','Visualv1 got non-image on42 after46successfulreceipts; v2reusedreceipts, skipped42 withoutretry andcompleted142. No other thumbnailfailures.','All inheritedprovider holds persist. No new access denial; SCwebtool eedb... cachemiss was internal and observednormalrequest200. No commits/deployment/subagents/localDBwrites.'])
    m.save(RUN/'remaining-research-001.json',remaining)
    (RUN/'README.md').open('x',encoding='utf-8').write('''# Athens City Museum — collection review, 10 October 2026

Identified **135 proposed additions**, including **14 icons**, after reviewing162 distinct records in eight art categories. **No Athens City records have been added yet.** Fresh production counts remain18 catalogue works and16 with qualifying numeric dates.

- [Candidate review ledger](candidate-review-001.csv)
- [Source decisions](editorial-source-decisions-001.json.gz)
- [Live identity comparisons](production-identity-001.json.gz)
- [Evidence checks](checks-001.json)
- [Remaining work](remaining-research-001.json)

The [museum-supplied SearchCulture collection](https://www.searchculture.gr/aggregator/portal/collections/DigAthensMuseum?language=en) contains2,405 mixed records. Bounded art-category queries produced162 unique entries;17 explicitly dated after1970 were excluded before detail/image capture.145 object pages were reviewed, including seven existing Artline works. Three further entries are held: a menu inscribed72, a work described as2018 and a later digital print on vinyl after another original. The shortlist contains47 dated and88 undated proposals; unknown dates are not presumed eligible. The three holds are separate from17 index exclusions.

The135 proposals comprise47 prints,35 paintings(including14 icons),three watercolours,38 drawings,10 sculptures and two decorative objects of unknown controlled type. Five supports carry two drawings each and count once. The icon with a case/metal covering and the icon joined from two fragments each count once. A framed postcard of the Tinos icon is recorded as its own decorative object, not as ownership of the original icon. Student copies remain distinct from the masters' originals.

All142 available source thumbnails and six contact sheets were visually reviewed; one lion-statuette thumbnail could not be decoded and was not retried. Different compositions and physical labels distinguish repeated print titles. Close inspection cleared the suspected duplicate between drawings45 and128. Incorrect institution/manufacturer creator labels, questioned signatures, date conflicts and inscription dates remain explicit. No new artist authority has been created or linked.

Prepared39 authentic sourceJPEGs for dated candidates created by1955, retaining complete source bytes, all at most34,499bytes. These are low-resolution source thumbnails, generally380pixels wide, with actualCC0 labels and source credits. They are **not uploaded or attached**. Unknown-date, later-date and held entries receive no prepared delivery image. Existing six primaries remain unchanged.

Fresh production research examined1,240 bounded artwork records,17 artist/alias candidates,1,024 creator links and2,624 citations. All seven selected existing identities were recovered; no proposed source ID matched an existing work. Six media hits correspond to existing images. These checks do not prove every physical identity or artist attribution; focused comparisons and some additional name/role searches remain necessary. Query plans are evidence of this research run, not a10-million-row load test.

The previous Kilkis delivery was reverified and all1,837 protected campaign records retained. Production totals remain1,815 new artworks plus five existing-work links across12 museums. Local data is unchanged. If all135 proposals survive reconciliation, Athens City would reach153 catalogue items; more documented works would still be needed for200. The overall every-museum goal remains active and incomplete.
''')
    scripts=sorted((m.ROOT/'ops').glob('*athens-city*20261010.py'))
    for path in scripts:ast.parse(path.read_text(),filename=str(path))
    paths={p for p in RUN.rglob('*') if p.is_file()}|set(scripts)|{c.CP,m.ROOT/'AGENTS.md',m.ROOT/'docs/ARTLINE_IMAGE_USE.md',m.RUN/'native/kilkis-delivery-20261010/next-source-discovery-001.json.gz'}
    pins=[c.ref(p) for p in sorted(paths)];external=[dict(path=str(p),sha256=sha(p)) for p in sorted(c.PROOF.rglob('*')) if p.is_file()]
    for pin in pins:c.checked(pin)
    for pin in external:assert sha(pin['path'])==pin['sha256']
    checkpoint=dict(at=m.now(),wave=127,previous_goal_turn='progress',goal_status='active',goal_complete=False,last_successful_production_checkpoint=c.ref(c.CP),production_campaign_totals_unchanged=prior['production_campaign_totals'],production_register_reference_unchanged=prior['production_institution_register_reference'],priority_queue_reference_unchanged=prior['priority_museum_queue_reference'],protected_production_ids_reference_unchanged=prior['protected_production_ids_reference'],initial_full_historical_verification_reference=prior['initial_full_historical_verification_reference'],prior_artifact_pins_inherited=len(prior['artifacts']),prior_external_pins_inherited=len(prior['external_artifacts']),artifacts=pins,external_artifacts=external,baseline_reference=c.ref(RUN/'baseline-verification-001.json'),checks_reference=c.ref(RUN/'checks-001.json'),remaining_reference=c.ref(RUN/'remaining-research-001.json'),candidate_reference=c.ref(RUN/'editorial-source-decisions-001.json.gz'),image_reference=c.ref(RUN/'image-delivery-prepared-001.json'),identity_reference=c.ref(RUN/'production-identity-001.json.gz'),pending_candidates=dict(athens_city=135),pending_candidate_total=135,proposed_new_records=135,prepared_images=39,actual_added=0,actual_images_attached=0,production_mutation_attempted=False,local_unchanged=True,next_work=remaining)
    m.save(dest,checkpoint)
    m.save(RUN/'checkpoint-verification-001.json',dict(at=m.now(),checkpoint=c.ref(dest),artifact_pins_verified=len(pins),external_pins_verified=len(external),proposals=135,prepared_images=39,actual_added=0,goal_complete=False))
    print(json.dumps(dict(checkpoint=c.ref(dest),artifact_pins=len(pins),external_pins=len(external),proposals=135,prepared_images=39,actual_added=0)),flush=True)

if __name__=='__main__':main()
