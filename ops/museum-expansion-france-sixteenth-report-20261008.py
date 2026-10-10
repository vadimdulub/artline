"""Wave71 coverage, with unrelated registry changes tracked separately."""
import collections,copy,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-sixteenth-apply-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
io=a.module('io','museum-expansion-detroit-final-report-20261007.py')
def main():
    label='after-wave-71';assert not (m.RUN/('verification-'+label+'.json')).exists();p,digest=a.validate_plan();a.verify_baseline()
    with m.connect() as db:verified=a.verify(db,p,digest)
    live=m.load(m.RUN/(label+'.json'));summary=copy.deepcopy(m.load(m.RUN/'verification-after-wave-70.json'));coverage=io.read_csv(m.RUN/'museum-coverage-after-wave-70.csv');liveby={v['id']:v for v in live['institutions']};oldids={v['id'] for v in coverage};assert oldids<=set(liveby)
    new=[v for v in live['institutions'] if v['id'] not in oldids]
    for v in new:
        row={k:'' for k in coverage[0]};row.update(v);row.update(works_before=v['works'],eligible_before=v['eligible_works'],added_this_campaign=0,existing_artworks_linked_this_campaign=0,research_state='newly_observed_external_registry_addition_not_reviewed_by_this_campaign',native_source_probe_status='not_reviewed_by_this_campaign',coverage_baseline_label='first_observed_after_wave_71');coverage.append(row)
    changes=[];external=[];ds=m.load(a.REVIEW)['decisions']
    for row in coverage:
        v=liveby[row['id']];count=sum(x['institution_id']==row['id'] for x in p['records'])
        if row['id'] in a.IIDS:
            assert v['works']==int(row['works'])+count and v['eligible_works']==int(row['eligible_works'])+count
            assert v['illustrated_works']==int(row['illustrated_works']) and v['pending_associations']==int(row['pending_associations'])
            changes.append(dict(institution_id=row['id'],name=row['name'],new=count,linked_before=int(row['works']),linked_after=v['works'],eligible_before=int(row['eligible_works']),eligible_after=v['eligible_works']))
            states=collections.Counter(d['state'] for d in ds if d['institution_id']==row['id'])
            row.update(added_this_campaign=int(row['added_this_campaign'])+count,research_state=row['research_state']+'; france_sixteenth_'+str(count)+'_added_'+str(states['editorial_hold'])+'_held_'+str(states['deferred_identity_review'])+'_deferred',native_source_probe_status='official_selected_object_records_captured_review_continues',campaign_state=('preferred_200_met_eligible_'+str(v['eligible_works']) if v['eligible_works']>=200 else 'minimum_100_met_eligible_'+str(v['eligible_works'])+'_preferred_200_remaining' if v['eligible_works']>=100 else 'minimum_100_remaining_'+str(100-v['eligible_works'])+'_eligible_works'))
        elif row['id'] in oldids:
            delta={k:dict(before=int(row[k]),after=v[k]) for k in ['works','eligible_works','illustrated_works','pending_associations'] if int(row[k])!=v[k]}
            if delta:external.append(dict(institution_id=row['id'],name=row['name'],changes=delta))
        for k,value in v.items():
            if k!='campaign_state':row[k]=value
    growth=a.RUN/'coverage-registry-growth-001.json';assert not growth.exists();m.save(growth,dict(at=m.now(),live_audit_reference=a.reference(m.RUN/(label+'.json')),previous_coverage_reference=a.reference(m.RUN/'museum-coverage-after-wave-70.csv'),added_institutions=new,existing_institution_changes=external,policy='External changes remain distinct from campaign additions. Newly observed rows use first-observed counts as baseline.'))
    io.write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
    added=io.read_csv(m.RUN/'added-artworks-after-wave-70.csv')
    for v in p['records']:
        f=v['facts'];museum=v['decision']['museum'];added.append(dict(artwork_id=v['artwork_id'],museum=museum['name'],museum_slug=museum['slug'],title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],accession=f['inventory'],source_url=f['source_url'],status='review'))
    total=9337+len(p['records']);assert len(added)==len({v['artwork_id'] for v in added})==total;io.write_csv(m.RUN/('added-artworks-'+label+'.csv'),sorted(added,key=lambda v:(v['museum'],v['title'])))
    for name in ['reconciled-artworks','gac-date-enrichments']:io.write_csv(m.RUN/(name+'-'+label+'.csv'),io.read_csv(m.RUN/(name+'-after-wave-70.csv')))
    old_coverage=io.read_csv(m.RUN/'museum-coverage-after-wave-70.csv');new_museums=[c for c in changes if c['new'] and not int(next(v for v in old_coverage if v['id']==c['institution_id'])['added_this_campaign'])]
    summary.update(at=m.now(),verified_new_artworks=total,verified_existing_artworks_linked=785,after=live['summary'],france_sixteenth_additions=verified,france_sixteenth_museum_changes=changes,unrelated_coverage_changes_since_prior_report=external,newly_observed_institutions=new,external_registry_growth_reference=a.reference(growth),global_coverage_snapshot_at=live['summary']['at'])
    summary['by_source'][a.KEY]=dict(new_artworks=len(p['records']),existing_artworks_linked=0,institutions_expanded=2,newly_expanded_institutions=len(new_museums),captured_remaining_objects_reviewed=359,captured_holds=sum(v['state']=='editorial_hold' for v in ds),deferred_identity_candidates=sum(v['state']=='deferred_identity_review' for v in ds),type_counts=dict(collections.Counter(v['facts']['work_type'] for v in p['records'])),museum_changes=changes,plan_sha256=digest)
    summary['verification_components'] += [a.reference(m.RUN/'verification-after-wave-70.json'),a.reference(a.CHECKPOINT),a.reference(a.PLAN),a.reference(a.RUN/(a.KEY+'-applied.json'))]
    summary['institutions_expanded']=sum(int(v['added_this_campaign'])>0 for v in coverage);summary['museums_expanded']=sum(v['kind']=='museum' and int(v['added_this_campaign'])>0 for v in coverage);summary['expanded_institution_kinds']=dict(collections.Counter(v['kind'] for v in coverage if int(v['added_this_campaign'])>0));summary['institutions_with_new_records_or_reconciled_holdings']=sum(int(v['added_this_campaign'])+int(v['existing_artworks_linked_this_campaign'])>0 for v in coverage)
    for threshold in [100,200]:summary['museums_crossing_'+str(threshold)]=[dict(name=v['name'],before=int(v['works_before']),after=int(v['works'])) for v in coverage if v['kind']=='museum' and v['status']!='archived' and not v['canonical_institution_id'] and int(v['works_before'])<threshold<=int(v['works'])]
    assert sum(int(v['added_this_campaign']) for v in coverage)==sum(v['new_artworks'] for v in summary['by_source'].values())==total;assert sum(int(v['existing_artworks_linked_this_campaign']) for v in coverage)==785
    summary['identity_reference_downloads_this_wave']=dict(selected_wikiart_jpeg=2,catalogue_image_attachments=0)
    summary['verification_method']='Wave71 adds119 Écouen objects and2 Cognacq-Jay objects as review records. Écouen now exceeds100 eligible works. All359 remaining national source facts, expanded comparisons and within-batch groups were independently recomputed against a fresh44678-artwork/96226-citation scope. Explicit source-backed physical triage and individual comparison notes preserve unresolved cases, including new historicalCL22278 conflict. Two selected WikiArt identity images inspected; no catalogue attachments. Native J15 copy/former-workshop attribution retained in a qualified object label. Atomic local transaction, exact readback, prior10122 campaign records protected, nine offline release safeguards and zero-write replay. Goal unfinished; unresolved sources and broad museum queue remain open.'
    m.save(m.RUN/('verification-'+label+'.json'),summary);print(json.dumps(dict(new_total=total,changes=changes,after=live['summary'],institutions_expanded=summary['institutions_with_new_records_or_reconciled_holdings'],external_changes=len(external),new_external_institutions=len(new))),flush=True)
if __name__=='__main__':main()
