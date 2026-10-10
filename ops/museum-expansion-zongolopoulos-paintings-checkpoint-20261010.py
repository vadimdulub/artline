"""Validate wave118 literal source evidence and pending physical-unit decisions."""
import ast
import collections
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-zongolopoulos-paintings-review-20261010.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
m,RUN,PROOF=r.m,r.RUN,r.PROOF
ref=r.c.ref

def checked(pin):
    p=Path(pin['path']);p=p if p.is_absolute()else m.ROOT/p
    assert p.is_file()and hashlib.sha256(p.read_bytes()).hexdigest()==pin['sha256'],str(p)

def main():
    previous=r.c.v.t.OLD/'research-checkpoint-001.json'
    assert ref(previous)['sha256']=='32b31e616cf63bd20a1edc62468fe01fb6c23fea9a8474e4b8aa91419402582e'
    prior=m.load(previous)
    for pin in prior['artifacts']+prior['external_artifacts']:checked(pin)
    checked(prior['last_successful_production_checkpoint'])
    production=m.ROOT/prior['last_successful_production_checkpoint']['path'];prod=m.load(production)
    assert ref(production)['sha256']=='21973a04eb7411fec1875f49baa8f0ac9f426e5de3effd5da24ca028b22b891a'
    facet=m.load(RUN/'facet-discovery-001.json.gz');index=m.load(RUN/'bounded-painting-index-001.json.gz')
    selection=m.load(RUN/'object-selection-001.json');sources=m.load(RUN/'selected-source-records-001.json.gz')['rows']
    decisions=m.load(RUN/'editorial-source-decisions-001.json.gz')['rows'];units=m.load(RUN/'candidate-physical-units-001.json.gz')['rows']
    cards=[c for p in index['pages']for c in p['cards']]
    assert index['observed_painting_records']==262 and len(index['pages'])==6 and len(cards)==len({c['source_id']for c in cards})==180
    assert len(selection['selected'])==len(sources)==len(decisions)==151
    assert sum(c['prior_source_review']for c in cards)==9
    assert sum(c['index_date_scope']=='unknown'and not c['prior_source_review']for c in cards)==151
    assert len(selection['deferred_or_excluded'])==29
    assert len(units)==150
    receipts=[facet['receipt']]+[p['receipt']for p in index['pages']]+[s['receipt']for s in sources]
    receipts += [m.load(p)for p in sorted((RUN/'captures').glob('file-viewer-*-001.json'))]
    assert len(receipts)==163
    for rc in receipts:
        raw=gzip.decompress((m.ROOT/rc['body_path']).read_bytes())
        assert rc['status']==200 and len(raw)==rc['bytes']and hashlib.sha256(raw).hexdigest()==rc['sha256']
    by={s['source_id']:s for s in sources}
    for row in decisions:
        s=by[row['source_id']];f=s['fields'];raw=gzip.decompress((m.ROOT/s['receipt']['body_path']).read_bytes())
        fields,enrichment=r.c.v.q.fields(BeautifulSoup(raw,'html.parser'))
        assert fields==f==row['source_fields']and enrichment==s['enrichment']==row['aggregator_enrichment']
        assert not f.get('Ημερομηνία')and row['title']==f['Τίτλος'][0]and row['creator_label']==f['Δημιουργός'][0]
        assert 'Inventory number '+row['inventory_source_literal']in f['Περιγραφή']
        assert row['inventory_literal']is None and row['painter_id']is None and row['dimensions_text']is None
        assert row['proposed_status']=='review'and not row['ready_to_apply']and not row['applied']and not row['current_display_verified']
        assert not row['image_date_policy_passed']
        if row['number']==97:assert row['first']==row['last']==1960 and row['date_scope']=='eligible'
        else:assert row['first']is None and row['last']is None and row['date_scope']=='requires_editorial_review'
    counts=collections.Counter(row['decision']for row in decisions)
    assert counts==dict(candidate_primary=150,hold_source_image_conflict=1)
    assert [r['number']for r in decisions if r['decision']!='candidate_primary']==[61]
    assert sum(u['two_sided_support']for u in units)==16
    assert sum(u['creator_label']=='Άγνωστος δημιουργός'for u in units)==37
    assert collections.Counter(u['work_type']for u in units)==dict(print=1,painting=57,watercolor=62,drawing=17,unknown=13)
    used=[s for u in units for s in u['source_ids']];assert len(used)==len(set(used))==150
    previous_sources=m.load(r.c.v.t.OLD/'selected-source-records-001.json.gz')['rows']
    assert not set(used)&{s['source_id']for s in previous_sources}
    prev_units=m.load(r.c.v.t.OLD/'candidate-physical-units-001.json.gz')['rows']
    assert len(prev_units)+len(units)==199 and sum(u['first']is not None for u in prev_units+units)==50
    for card in selection['deferred_or_excluded']:
        assert not (RUN/('captures/selected-'+card['source_id'].rsplit('-',1)[1]+'-001.json')).exists()
    visual=m.load(RUN/'visual-references-001.json');comp=m.load(RUN/'comparison-references-001.json');cross=m.load(RUN/'prior-pictorial-comparison-001.json')
    assert len(visual['rows'])==151 and len(visual['sheets'])==8 and len(comp['sheets'])==9 and len(comp['preservation_previews'])==5
    assert not visual['exact_duplicate_images']and not comp['exact_duplicate_images_with_previous']
    for pin in visual['rows']+visual['sheets']+comp['sheets']+comp['preservation_previews']+[cross['sheet']]:checked(pin)
    for row in visual['rows']+comp['preservation_previews']:
        with Image.open(row['path'])as im:assert im.size==(row['width'],row['height'])
    scripts=sorted((m.ROOT/'ops').glob('museum-expansion-zongolopoulos-paintings*20261010.py'));assert len(scripts)==8
    for p in scripts:ast.parse(p.read_text(),filename=str(p))
    assert not(PROOF/'prepared-images').exists()
    m.save(RUN/'remaining-research-001.json',dict(at=m.now(),institution_id=r.IID,goal_complete=False,
        last_verified_catalogue_count=18,last_verified_dateeligible_count=18,last_verified_at='2026-10-09',fresh_production_counts=False,
        proposed_new_candidates=150,source_image_holds=1,combined_pending_candidates=199,combined_numeric_date_candidates=50,combined_unknown_date_candidates=149,
        actual_added=0,actual_images_attached=0,new_prepared_images=0,prior_prepared_images_unattached=19,
        painting_facet_records=262,painting_cards_inspected=180,painting_cards_uninspected=82,prior_reviewed_cards_skipped=9,post1970_cards_excluded=20,
        auth='Sixth consecutive continuation: existing Google token refresh failed with non-interactive reauthentication error; no token printed, no credential search or substitute identity. gcloud auth login needed before fresh production reconciliation. Public source review remains possible.',
        next_source_work='Next institution Chania from the last saved priority queue. Do not enlarge the199 pending Zongolopoulos candidates merely to hit a round quota before live identity/date reconciliation.',
        unresolved=['Fresh global/institution production source and creator identity checks','Unknown physical creation dates149;1933 signed lithograph impression date unresolved','Source64218 description/image conflict','Qualified creator cases64360 and64479; anonymous front/probableHelen reverse64255','Doubled exported inventory strings and existing sculpture shared-photo flags','Remaining82 painting cards and other categories are unreviewed, not presumed eligible works'],
        provider_holds_inherited=['www.zongolopoulos.gr403','collection.zongolopoulos.gr prior single ConnectTimeout','Observed SearchCulture XML returned200errorHTML'],
        new_access_observation='Five public file viewers and their visible preservation previews accessible; no TIFF downloads. Web tool separately reported cache misses for two URLs already captured successfully through direct public requests.',
        candidate_reference=ref(RUN/'candidate-physical-units-001.json.gz')))
    m.save(RUN/'checks-001.json',dict(at=m.now(),html_response_bodies_verified=163,literal_source_records_reparsed=151,
        new_source_thumbnails_verified=151,preservation_previews_verified=5,review_montages_verified=18,
        candidates=150,unknown_date_candidates=149,source_inscription_dated_candidates=1,held_source_records=1,two_sided_supports_counted_once=16,
        anonymous_candidates=37,qualified_or_conflicting_named_candidates=2,combined_pending_candidates=199,
        new_prepared_images=0,production_images_attached=0,actual_added=0,production_mutation_attempted=False,local_database_writes=0,database_fixtures_created=0,
        prior_artifact_pins_verified=len(prior['artifacts']),prior_external_pins_verified=len(prior['external_artifacts']),
        validation_limit='Source, visual and physical-unit review only; fresh production identity/counts, canonical accession, accepted painter links and delivery remain pending. No source date is inferred from style or artist lifespan.',script_reference=ref(Path(__file__).resolve())))
    paths={p for p in RUN.rglob('*')if p.is_file()}|set(scripts)|{previous,production}
    pins=[ref(p)for p in sorted(paths)];external=[ref(p)for p in sorted(PROOF.rglob('*'))if p.is_file()]
    checkpoint=RUN/'research-checkpoint-001.json'
    m.save(checkpoint,dict(at=m.now(),wave=118,previous_goal_turn='progress',goal_status='active',goal_complete=False,
        previous_research_checkpoint=ref(previous),last_successful_production_checkpoint=ref(production),
        production_campaign_totals_unchanged=prod['production_campaign_totals'],production_register_reference_unchanged=prod['production_institution_register_reference'],
        priority_queue_reference_unchanged=prod['priority_museum_queue_reference'],initial_full_historical_verification_reference=prod['initial_full_historical_verification_reference'],
        proposed_new_physical_units=150,zongolopoulos_combined_pending_candidates=199,kazantzakis_pending_candidates=105,kilkis_pending_candidates=26,theocharakis_pending_candidates=197,
        actual_new_records=0,actual_images_attached=0,new_prepared_images=0,prior_zongolopoulos_prepared_images=19,
        artifacts=pins,external_artifacts=external,checks_reference=ref(RUN/'checks-001.json'),remaining_reference=ref(RUN/'remaining-research-001.json'),
        next_work='Wave118 Zongolopoulos painting facet:180/262cards reviewed,151newundated source pages+thumbs,9old+20later skipped.150candidate physicalsupports,61/64218held because GirlWithUmbrella description versusabstractimage in both thumbnail/preservationpreview.149unknownphysicaldates;97/64368qualifiedsource1960inscription eligible.1/64290lithograph17/20signature1933preserved butimpressiondateunknown.16two-sided supports countedonce;37anonymous candidates;50/64479GeorgefieldversusEsignature conflict and89/64360unsignedHelenfolder qualifiedobjectlabels, nopainterIDs.28/64255anonymousfront/probableHelenreverse preserved. Types57painting62watercolor17drawing1print13unknown(collage/mixed/sparse). All151descriptionsand8contacts+9focused+1priorpictorialmontage+5preservationpreviewsreviewed. Noexactimagehashduplicateswithin151orvsprior128; noimpliedglobalclearance.5observedfileviewerHTML+5visiblepreviewsaccessible; noTIFFdownloads.10Octauthstillfails6thcontinuation; needgcloudauthlogin, noDBwrite/backup/plan. Publicresearchprogresssogoalactive. CombinedZong199pending=49prior+150new,50numeric149unknown;actualstill18/18staleandhistoricalsculptureduplicatesunresolved.19priorpreparedby1955imagesunattached;current0becauseunknownor1960. SpecificGreekrestricted-sourceapprovalretained—NCNDaloneisnotblock. NextChaniafromCP112priorityqueue; do notextendZongmerelyroundquota beforelivechecks. PendingKaz105,Kilkis26,Theo197,Zong199total527 candidates. LastactualproductionCP112920new+1linkacross7;localreadonly. Validateonlynew+priorcheckpointpinsnotfullarchivalchain. Preserve immutableartifacts, noagents/commits/deploy/proxyrestart/credentialsearch. Needfreshscopedglobalidentity/painter/datechecks thenexacthashplan/protectedbackup/apply/readback/replay.'))
    for pin in pins+external:checked(pin)
    m.save(RUN/'research-checkpoint-verification-001.json',dict(at=m.now(),checkpoint=ref(checkpoint),artifact_pins_verified=len(pins),external_pins_verified=len(external),production_delivery=False,goal_complete=False))
    print(json.dumps(dict(checkpoint=ref(checkpoint),artifacts=len(pins),external=len(external),candidates=150,combined_pending=199,actual_added=0)),flush=True)

if __name__=='__main__':main()
