#!/usr/bin/env python3
"""Wave55: freshly verified local additions and current museum coverage."""
import copy,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-princeton-followup-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
io=a.module('io','museum-expansion-detroit-final-report-20261007.py')
def main():
    label='after-wave-55';assert not (m.RUN/('verification-'+label+'.json')).exists();p,digest=a.validate_plan();receipt=m.load(a.RUN/(a.KEY+'-applied.json'));assert receipt['plan_sha256']==digest;a.verify_baseline()
    with m.connect() as db:verified=a.verify(db,p,digest)
    m.audit(label);live=m.load(m.RUN/(label+'.json'));summary=copy.deepcopy(m.load(m.RUN/'verification-after-wave-54.json'))
    coverage=io.read_csv(m.RUN/'museum-coverage-after-wave-54.csv');liveby={v['id']:v for v in live['institutions']};assert set(liveby)=={v['id'] for v in coverage};external=[]
    for row in coverage:
        current=liveby[row['id']]
        if row['id']!=a.IID:
            changes={k:dict(before=int(row[k]),after=current[k]) for k in ['works','eligible_works','illustrated_works','pending_associations'] if int(row[k])!=current[k]}
            if changes:external.append(dict(institution_id=row['id'],changes=changes))
        for k,v in current.items():
            if k!='campaign_state':row[k]=v
    princeton=next(v for v in coverage if v['id']==a.IID);assert (princeton['works'],princeton['eligible_works'],princeton['pending_associations'],princeton['illustrated_works'])==(214,214,9,16)
    princeton.update(added_this_campaign='196',existing_artworks_linked_this_campaign='18',research_state='318_native_objects_reviewed_196_added_18_reconciled_104_held',native_source_probe_status='documented_public_API_selected_capture_complete_HTTP200',campaign_state='preferred_200_met_with_214_eligible')
    io.write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
    added=io.read_csv(m.RUN/'added-artworks-after-wave-54.csv')
    for row in p['records']:
        f=row['facts'];added.append(dict(artwork_id=row['artwork_id'],museum='Princeton University Art Museum',museum_slug='spain-research-museum-q2603905',title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],accession=f['inventory'],source_url=f['source_url'],status='review'))
    assert len(added)==len({v['artwork_id'] for v in added})==5643;io.write_csv(m.RUN/('added-artworks-'+label+'.csv'),sorted(added,key=lambda v:(v['museum'],v['title'])))
    holds=io.read_csv(m.RUN/'reconciled-artworks-after-wave-54.csv');assert len(holds)==785;io.write_csv(m.RUN/('reconciled-artworks-'+label+'.csv'),holds)
    io.write_csv(m.RUN/('gac-date-enrichments-'+label+'.csv'),io.read_csv(m.RUN/'gac-date-enrichments-after-wave-54.csv'))
    summary.update(at=m.now(),verified_new_artworks=5643,verified_existing_artworks_linked=785,after=live['summary'],princeton_followup_additions=verified,unrelated_coverage_changes_since_prior_report=external)
    summary['by_source'][a.KEY]=dict(new_artworks=50,existing_artworks_linked=0,institutions_expanded=1,captured_objects_reviewed=62,captured_holds=12,index_holds=116,distinct_discovery_objects=178,linked_records=214,eligible_records=214,remaining_to_100=0,remaining_to_200=0,plan_sha256=digest)
    summary['verification_components'] += [a.reference(m.RUN/'verification-after-wave-54.json'),a.reference(a.CHECKPOINT),a.reference(a.PLAN),a.reference(a.RUN/(a.KEY+'-applied.json'))]
    summary['verification_method']='Wave54 source evidence and database proofs remain immutable and hash-pinned. Wave55 freshly verifies50 new review records and zero changes to2613 scoped existing objects and all6378 prior campaign objects, including associated images, artist links, citations, holdings and publication. Fresh read-only identity preflight covers9814 artwork candidates and21967 citations; all62 comparisons were recomputed against frozen inputs. Global coverage is freshly audited. Historical count-sensitive validators are preserved, not rewritten.'
    for threshold in [100,200]:summary['museums_crossing_'+str(threshold)]=[dict(name=v['name'],before=int(v['works_before']),after=int(v['works'])) for v in coverage if v['kind']=='museum' and v['status']!='archived' and not v['canonical_institution_id'] and int(v['works_before'])<threshold<=int(v['works'])]
    assert sum(int(v['added_this_campaign']) for v in coverage)==sum(v['new_artworks'] for v in summary['by_source'].values())==5643
    assert sum(int(v['existing_artworks_linked_this_campaign']) for v in coverage)==785
    summary['identity_reference_downloads_this_wave']=dict(selected_wikiart_jpeg=0,selected_primary_educational_pdf=0,catalogue_image_attachments=0)
    m.save(m.RUN/('verification-'+label+'.json'),summary);print(json.dumps({k:summary[k] for k in ['verified_new_artworks','verified_existing_artworks_linked','institutions_with_new_records_or_reconciled_holdings','source_pass_museums','source_pass_institutions','after','unrelated_coverage_changes_since_prior_report']}),flush=True)
if __name__=='__main__':main()
