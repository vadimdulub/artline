#!/usr/bin/env python3
"""Verify Russell-Cotes' 98 holdings and 89 native additions in the campaign report."""
import argparse
import copy
import csv
import importlib.util
import json
from pathlib import Path
s=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('museum-expansion-gac-target-report-20261007.py'))
prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior)
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-russell-followup-apply-20261007.py'))
a=importlib.util.module_from_spec(s);s.loader.exec_module(a);w=a.w;m=a.m


def report(label):
    assert not (m.RUN/('verification-'+label+'.json')).exists()
    hp,hd=w.validate_plan();np,nd=a.prior.validate_plan();fp,fd=a.validate_plan()
    assert m.load(a.RUN/(a.prior.KEY+'-applied.json'))['plan_sha256']==nd and m.load(a.RUN/(a.KEY+'-applied.json'))['plan_sha256']==fd and m.load(w.RUN/(w.KEY+'-applied.json'))['plan_sha256']==hd
    with m.connect() as db:new=a.prior.verify(db,np,nd);followup=a.verify(db,fp,fd);holding=w.verify(db,hp,hd)
    base=label+'-prior-batches'
    if not (m.RUN/('verification-'+base+'.json')).exists():prior.report(base)
    summary=copy.deepcopy(m.load(m.RUN/('verification-'+base+'.json')));assert summary['verified_new_artworks']==3611 and summary['verified_existing_artworks_linked']==661
    with (m.RUN/('museum-coverage-'+base+'.csv')).open(newline='') as f:coverage=list(csv.DictReader(f))
    target=next(r for r in coverage if r['id']==a.IID);assert target['kind']=='museum' and target['added_this_campaign']==target['existing_artworks_linked_this_campaign']=='0'
    assert (int(target['works']),int(target['eligible_works']))==(new['current_counts']['linked'],new['current_counts']['eligible'])==(200,200)
    target.update(added_this_campaign='89',existing_artworks_linked_this_campaign='98',research_state='native_additions_and_existing_holdings_verified',campaign_state='target_200_reached_this_campaign')
    prior.write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
    for r in hp['records']:
        f,d=r['facts'],r['decision'];summary['existing_holding_verifications'].append(dict(artwork_id=f['artwork_id'],institution_id=a.IID,source_url=f['source_url'],verified_existing_metadata_unchanged=True,confidence=d['confidence'],evidence_basis=d['basis']+' '+d['version_review'],source_limitation=d['limitation']))
    rows=summary['existing_holding_verifications'];assert len(rows)==len({r['artwork_id'] for r in rows})==759;prior.write_csv(m.RUN/('reconciled-artworks-'+label+'.csv'),rows)
    with (m.RUN/('added-artworks-'+base+'.csv')).open(newline='') as f:added=list(csv.DictReader(f))
    for r in np['records']+fp['records']:
        f=r['facts'];added.append(dict(artwork_id=r['artwork_id'],museum='Russell-Cotes Art Gallery & Museum',museum_slug='museum-authority-q7381305',title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],accession=f['inventory'],source_url=f['source_url'],status='review'))
    assert len(added)==len({r['artwork_id'] for r in added})==3700;prior.write_csv(m.RUN/('added-artworks-'+label+'.csv'),sorted(added,key=lambda r:(r['museum'],r['title'])))
    summary.update(at=m.now(),verified_new_artworks=3700,verified_existing_artworks_linked=759,museums_expanded=summary['museums_expanded']+1,institutions_expanded=summary['institutions_expanded']+1,source_pass_museums=summary['source_pass_museums']+1,source_pass_institutions=summary['source_pass_institutions']+1,institutions_with_new_records_or_reconciled_holdings=summary['institutions_with_new_records_or_reconciled_holdings']+1,russell_cotes_holding_reconciliation=holding,russell_cotes_native_additions=new,russell_cotes_native_followup=followup)
    summary['expanded_institution_kinds']['museum']+=1
    summary['by_source'][a.prior.KEY]=dict(new_artworks=68,native_captures=140,not_added=72,plan_sha256=nd)
    summary['by_source'][a.KEY]=dict(new_artworks=21,native_captures=88,not_added=67,plan_sha256=fd)
    summary['verification_components'] += [a.reference(m.RUN/('verification-'+base+'.json')),a.reference(w.PLAN),a.reference(w.RUN/(w.KEY+'-applied.json')),a.reference(a.prior.PLAN),a.reference(a.RUN/(a.prior.KEY+'-applied.json')),a.reference(a.PLAN),a.reference(a.RUN/(a.KEY+'-applied.json'))]
    assert sum(int(r['added_this_campaign']) for r in coverage)==sum(r['new_artworks'] for r in summary['by_source'].values())==3700 and sum(int(r['existing_artworks_linked_this_campaign']) for r in coverage)==759
    for prefix,ext in [('', '.json'),('', '.csv'),('gac-date-enrichments-', '.csv')]:
        with (m.RUN/(prefix+label+ext)).open('xb') as f:f.write((m.RUN/(prefix+base+ext)).read_bytes())
    m.save(m.RUN/('verification-'+label+'.json'),summary)
    print(json.dumps({k:summary[k] for k in ['verified_new_artworks','verified_existing_artworks_linked','museums_expanded','source_pass_museums','after']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--label',default='after-wave-34');report(p.parse_args().label)
