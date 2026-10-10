#!/usr/bin/env python3
"""Wave 69 coverage and additions report, preserving earlier proofs unchanged."""
import collections,copy,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-fourteenth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
io=a.module('io','museum-expansion-detroit-final-report-20261007.py')
def main():
    label='after-wave-69';assert not (m.RUN/('verification-'+label+'.json')).exists();p,digest=a.validate_plan();receipt=m.load(a.RUN/(a.KEY+'-applied.json'));assert receipt['plan_sha256']==digest;a.verify_baseline()
    with m.connect() as db:verified=a.verify(db,p,digest)
    m.audit(label);live=m.load(m.RUN/(label+'.json'));summary=copy.deepcopy(m.load(m.RUN/'verification-after-wave-68.json'))
    coverage=io.read_csv(m.RUN/'museum-coverage-after-wave-68.csv');liveby={v['id']:v for v in live['institutions']};assert set(liveby)=={v['id'] for v in coverage};external=[];changes=[]
    for row in coverage:
        current=liveby[row['id']]
        if row['id'] not in a.IIDS:
            delta={k:dict(before=int(row[k]),after=current[k]) for k in ['works','eligible_works','illustrated_works','pending_associations'] if int(row[k])!=current[k]}
            if delta:external.append(dict(institution_id=row['id'],changes=delta))
        else:
            n=sum(v['institution_id']==row['id'] for v in p['records'])
            assert current['works']==int(row['works'])+n and current['eligible_works']==int(row['eligible_works'])+n
            assert current['pending_associations']==int(row['pending_associations']) and current['illustrated_works']==int(row['illustrated_works'])
            changes.append(dict(institution_id=row['id'],name=row['name'],new=n,linked_before=int(row['works']),linked_after=current['works'],eligible_before=int(row['eligible_works']),eligible_after=current['eligible_works']))
            held=sum(v['institution_id']==row['id'] and v['state']=='editorial_hold' for v in m.load(a.REVIEW)['decisions'])
            row.update(added_this_campaign=str(int(row['added_this_campaign'])+n),research_state=row['research_state']+'; france_fourteenth_followup_'+str(n)+'_added_'+str(held)+'_held',native_source_probe_status=('current_official_national_catalogue_API_selected_capture_complete_HTTP200' if n else 'read_only_index_pass_no_eligible_selected_metadata'),campaign_state=('preferred_200_met_eligible_'+str(current['eligible_works']) if current['eligible_works']>=200 else 'minimum_100_met_eligible_'+str(current['eligible_works'])+'_preferred_200_remaining' if current['eligible_works']>=100 else 'minimum_100_remaining_'+str(100-current['eligible_works'])+'_eligible_works'))
        for k,v in current.items():
            if k!='campaign_state':row[k]=v
    io.write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
    added=io.read_csv(m.RUN/'added-artworks-after-wave-68.csv')
    for row in p['records']:
        f=row['facts'];museum=row['decision']['museum'];added.append(dict(artwork_id=row['artwork_id'],museum=museum['name'],museum_slug=museum['slug'],title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],accession=f['inventory'],source_url=f['source_url'],status='review'))
    total=8565+len(p['records']);assert len(added)==len({v['artwork_id'] for v in added})==total;io.write_csv(m.RUN/('added-artworks-'+label+'.csv'),sorted(added,key=lambda v:(v['museum'],v['title'])))
    holds=io.read_csv(m.RUN/'reconciled-artworks-after-wave-68.csv');assert len(holds)==785;io.write_csv(m.RUN/('reconciled-artworks-'+label+'.csv'),holds)
    io.write_csv(m.RUN/('gac-date-enrichments-'+label+'.csv'),io.read_csv(m.RUN/'gac-date-enrichments-after-wave-68.csv'))
    summary.update(at=m.now(),verified_new_artworks=total,verified_existing_artworks_linked=785,after=live['summary'],france_fourteenth_additions=verified,france_fourteenth_museum_changes=changes,unrelated_coverage_changes_since_prior_report=external)
    summary['by_source'][a.KEY]=dict(new_artworks=len(p['records']),existing_artworks_linked=0,institutions_expanded=5,newly_expanded_institutions=4,captured_objects_reviewed=605,captured_holds=124,index_held_or_unselected=47736,prior_captured_holds_excluded=9,distinct_source_leads=48350,type_counts=dict(collections.Counter(v['facts']['work_type'] for v in p['records'])),museum_changes=changes,plan_sha256=digest)
    summary['verification_components'] += [a.reference(m.RUN/'verification-after-wave-68.json'),a.reference(a.CHECKPOINT),a.reference(a.PLAN),a.reference(a.RUN/(a.KEY+'-applied.json'))]
    summary['institutions_expanded']=sum(int(v['added_this_campaign'])>0 for v in coverage)
    summary['museums_expanded']=sum(v['kind']=='museum' and int(v['added_this_campaign'])>0 for v in coverage)
    summary['expanded_institution_kinds']=dict(collections.Counter(v['kind'] for v in coverage if int(v['added_this_campaign'])>0))
    summary['institutions_with_new_records_or_reconciled_holdings']=sum(int(v['added_this_campaign'])+int(v['existing_artworks_linked_this_campaign'])>0 for v in coverage)
    summary['verification_method']='Wave 68 remains immutable. Wave 69 adds 481 local review records across five museums; all five reach 100 eligible works. The 322 initial target-museum records, all protected comparison records and 9350 prior campaign records remain unchanged. Final read-only identity scope: 61370 artworks and 134514 citations. All 605 literal source facts and indexed comparisons recomputed. 599 selected Paris native pages checked; failed 583 remains held. The 124 holds retain physical-unit, duplicate and chronology uncertainties. Native-qualified creator labels preserve original national fields without artist-authority writes. Twenty offline regression tests passed. Atomic local additions, exact readback and zero-write replay. No images, publication or display claims. Global scope unfinished.'



    for threshold in [100,200]:summary['museums_crossing_'+str(threshold)]=[dict(name=v['name'],before=int(v['works_before']),after=int(v['works'])) for v in coverage if v['kind']=='museum' and v['status']!='archived' and not v['canonical_institution_id'] and int(v['works_before'])<threshold<=int(v['works'])]
    assert sum(int(v['added_this_campaign']) for v in coverage)==sum(v['new_artworks'] for v in summary['by_source'].values())==total
    assert sum(int(v['existing_artworks_linked_this_campaign']) for v in coverage)==785
    assert summary['institutions_with_new_records_or_reconciled_holdings']==199 and summary['source_pass_museums']==350 and summary['source_pass_institutions']==351
    summary['identity_reference_downloads_this_wave']=dict(selected_wikiart_jpeg=0,selected_primary_educational_pdf=0,catalogue_image_attachments=0)
    m.save(m.RUN/('verification-'+label+'.json'),summary);print(json.dumps({k:summary[k] for k in ['verified_new_artworks','verified_existing_artworks_linked','france_fourteenth_museum_changes','after','unrelated_coverage_changes_since_prior_report']}),flush=True)
if __name__=='__main__':main()
