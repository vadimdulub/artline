#!/usr/bin/env python3
"""Verify both Fitzwilliam batches and four reconciled holdings in current coverage."""
import argparse,copy,csv,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('museum-expansion-russell-target-report-20261007.py'));base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
s=importlib.util.spec_from_file_location('target',Path(__file__).with_name('museum-expansion-fitzwilliam-target-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
write_csv=base.prior.write_csv

def report(label):
    assert not (m.RUN/('verification-'+label+'.json')).exists()
    old,old_digest=a.prior.validate_plan();plan,digest=a.validate_plan()
    assert m.load(a.RUN/(a.KEY+'-applied.json'))['plan_sha256']==digest
    assert m.load(a.RUN/(a.prior.KEY+'-applied.json'))['plan_sha256']==old_digest
    with m.connect() as db:verification=a.verify(db,plan,digest)
    previous=label+'-prior-batches'
    if not (m.RUN/('verification-'+previous+'.json')).exists():base.report(previous)
    summary=copy.deepcopy(m.load(m.RUN/('verification-'+previous+'.json')))
    assert summary['verified_new_artworks']==3700 and summary['verified_existing_artworks_linked']==759
    with (m.RUN/('museum-coverage-'+previous+'.csv')).open(newline='') as f:coverage=list(csv.DictReader(f))
    museum=next(r for r in coverage if r['id']==a.IID)
    assert museum['kind']=='museum' and museum['added_this_campaign']==museum['existing_artworks_linked_this_campaign']=='0'
    assert (int(museum['works']),int(museum['eligible_works']))==(206,200)
    museum.update(added_this_campaign='189',existing_artworks_linked_this_campaign='4',research_state='native_additions_and_existing_holdings_verified',campaign_state='target_200_reached_this_campaign')
    write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
    for r in plan['holdings']:
        v,d=r['facts'],r['decision']
        summary['existing_holding_verifications'].append(dict(artwork_id=r['artwork_id'],institution_id=a.IID,source_url=v['source_url'],verified_existing_metadata_unchanged=True,confidence=d['confidence'],evidence_basis=d['basis'],source_limitation=d['limitation']))
    holds=summary['existing_holding_verifications'];assert len(holds)==len({r['artwork_id'] for r in holds})==763
    write_csv(m.RUN/('reconciled-artworks-'+label+'.csv'),holds)
    with (m.RUN/('added-artworks-'+previous+'.csv')).open(newline='') as f:added=list(csv.DictReader(f))
    for r in old['records']+plan['records']:
        v=r['facts'];added.append(dict(artwork_id=r['artwork_id'],museum='Fitzwilliam Museum',museum_slug='spain-research-museum-q1421440',title=v['title'],creator_label=v['creator_label'],date_display=v['date_display'],creation_year_start=v['first'],creation_year_end=v['last'],accession=v['inventory'],source_url=v['source_url'],status='review'))
    assert len(added)==len({r['artwork_id'] for r in added})==3889
    write_csv(m.RUN/('added-artworks-'+label+'.csv'),sorted(added,key=lambda r:(r['museum'],r['title'])))
    summary.update(at=m.now(),verified_new_artworks=3889,verified_existing_artworks_linked=763,museums_expanded=summary['museums_expanded']+1,institutions_expanded=summary['institutions_expanded']+1,source_pass_museums=summary['source_pass_museums']+1,source_pass_institutions=summary['source_pass_institutions']+1,institutions_with_new_records_or_reconciled_holdings=summary['institutions_with_new_records_or_reconciled_holdings']+1,fitzwilliam_target_200=verification)
    summary['expanded_institution_kinds']['museum']+=1
    summary['by_source'][a.prior.KEY]=dict(new_artworks=163,native_captures=313,not_added_at_initial_checkpoint=150,plan_sha256=old_digest)
    summary['by_source'][a.KEY]=dict(new_artworks=26,existing_holdings=4,additional_native_captures=72,remaining_unadded_unique_native_objects=192,plan_sha256=digest)
    summary['verification_components'] += [a.reference(m.RUN/('verification-'+previous+'.json')),a.reference(a.prior.PLAN),a.reference(a.RUN/(a.prior.KEY+'-applied.json')),a.reference(a.PLAN),a.reference(a.RUN/(a.KEY+'-applied.json'))]
    assert sum(int(r['added_this_campaign']) for r in coverage)==sum(r['new_artworks'] for r in summary['by_source'].values())==3889
    assert sum(int(r['existing_artworks_linked_this_campaign']) for r in coverage)==763
    for prefix,ext in [('', '.json'),('', '.csv'),('gac-date-enrichments-', '.csv')]:
        with (m.RUN/(prefix+label+ext)).open('xb') as f:f.write((m.RUN/(prefix+previous+ext)).read_bytes())
    m.save(m.RUN/('verification-'+label+'.json'),summary)
    print(json.dumps({k:summary[k] for k in ['verified_new_artworks','verified_existing_artworks_linked','museums_expanded','source_pass_museums','after']}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--label',default='after-wave-36');report(p.parse_args().label)
