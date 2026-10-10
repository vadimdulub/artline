#!/usr/bin/env python3
"""Add 98 verified Russell-Cotes holding links to the campaign report."""
import argparse
import copy
import csv
import importlib.util
import json
from pathlib import Path

s=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('museum-expansion-gac-target-report-20261007.py'))
prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior)
s=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-russell-holdings-20261007.py'))
w=importlib.util.module_from_spec(s);s.loader.exec_module(w);m=w.m


def report(label):
    assert not (m.RUN/('verification-'+label+'.json')).exists()
    plan,digest=w.validate_plan();receipt=m.load(w.RUN/(w.KEY+'-applied.json'))
    assert receipt['plan_sha256']==digest and receipt['verification']['existing_artworks_linked']==98
    with m.connect() as db:checked=w.verify(db,plan,digest)
    base=label+'-prior-batches'
    if not (m.RUN/('verification-'+base+'.json')).exists():prior.report(base)
    summary=copy.deepcopy(m.load(m.RUN/('verification-'+base+'.json')))
    assert summary['verified_new_artworks']==3611 and summary['verified_existing_artworks_linked']==661
    with (m.RUN/('museum-coverage-'+base+'.csv')).open(newline='') as f:coverage=list(csv.DictReader(f))
    target=next(r for r in coverage if r['id']==w.IID)
    assert target['kind']=='museum' and target['added_this_campaign']==target['existing_artworks_linked_this_campaign']=='0'
    assert (int(target['works']),int(target['eligible_works']))==(checked['current_counts']['linked'],checked['current_counts']['eligible'])==(111,111)
    target.update(existing_artworks_linked_this_campaign='98',research_state='existing_holdings_reconciled_native_additions_under_review',campaign_state='minimum_100_reached_this_campaign')
    prior.write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
    for r in plan['records']:
        f,d=r['facts'],r['decision'];summary['existing_holding_verifications'].append(dict(artwork_id=f['artwork_id'],institution_id=w.IID,source_url=f['source_url'],verified_existing_metadata_unchanged=True,confidence=d['confidence'],evidence_basis=d['basis']+' '+d['version_review'],source_limitation=d['limitation']))
    rows=summary['existing_holding_verifications'];assert len(rows)==len({r['artwork_id'] for r in rows})==759
    prior.write_csv(m.RUN/('reconciled-artworks-'+label+'.csv'),rows)
    summary.update(at=m.now(),verified_existing_artworks_linked=759,source_pass_museums=summary['source_pass_museums']+1,source_pass_institutions=summary['source_pass_institutions']+1,institutions_with_new_records_or_reconciled_holdings=summary['institutions_with_new_records_or_reconciled_holdings']+1,russell_cotes_holding_reconciliation=checked)
    summary['verification_components'] += [w.reference(m.RUN/('verification-'+base+'.json')),w.reference(w.PLAN),w.reference(w.RUN/(w.KEY+'-applied.json'))]
    assert sum(int(r['added_this_campaign']) for r in coverage)==3611 and sum(int(r['existing_artworks_linked_this_campaign']) for r in coverage)==759
    for prefix,ext in [('', '.json'),('', '.csv'),('added-artworks-', '.csv'),('gac-date-enrichments-', '.csv')]:
        with (m.RUN/(prefix+label+ext)).open('xb') as f:f.write((m.RUN/(prefix+base+ext)).read_bytes())
    m.save(m.RUN/('verification-'+label+'.json'),summary)
    print(json.dumps({k:summary[k] for k in ['verified_new_artworks','verified_existing_artworks_linked','museums_expanded','source_pass_museums','after']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',default='after-wave-32');report(p.parse_args().label)
