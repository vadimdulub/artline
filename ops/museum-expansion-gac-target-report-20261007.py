#!/usr/bin/env python3
"""Verified GAC successor report:118 prior links,6 dates,5 links and58 new works."""
import argparse
import copy
import csv
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('museum-expansion-manchester-report-20261007.py'))
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
spec=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-gac-new-20261007.py'))
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
v=n.v;w=n.w;m=n.m


def write_csv(path,rows):
    with path.open('x',newline='') as f:
        keys=list(dict.fromkeys(k for row in rows for k in row))
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(rows)


def report(label):
    assert not (m.RUN/('verification-'+label+'.json')).exists()
    pp,pd=w.validate_plan();dp,dd=v.validate_plan();np,nd=n.validate_plan()
    for importer,digest in [(w,pd),(v,dd),(n,nd)]:assert m.load(importer.RUN/(importer.KEY+'-applied.json'))['plan_sha256']==digest
    with m.connect() as db:
        checked=n.verify(db,np,nd);dates=v.verify(db,dp,dd);holdings=v.verify_prior_holdings(db)
    base=label+'-prior-batches'
    if not (m.RUN/('verification-'+base+'.json')).exists():prior.report(base)
    summary=copy.deepcopy(m.load(m.RUN/('verification-'+base+'.json')))
    assert summary['verified_new_artworks']==3553 and summary['verified_existing_artworks_linked']==538
    with (m.RUN/('museum-coverage-'+base+'.csv')).open(newline='') as f:coverage=list(csv.DictReader(f))
    target=next(r for r in coverage if r['id']==n.IID)
    assert target['kind']=='museum' and target['added_this_campaign']==target['existing_artworks_linked_this_campaign']=='0'
    assert (int(target['works']),int(target['eligible_works']))==(checked['current_counts']['linked'],checked['current_counts']['eligible'])==(203,200)
    target.update(added_this_campaign='58',existing_artworks_linked_this_campaign='123',research_state='new_review_artworks_added_and_existing_dates_and_holdings_enriched',campaign_state='target_200_reached_this_campaign')
    write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
    for r in pp['records']:
        f,d=r['facts'],r['decision']
        summary['existing_holding_verifications'].append(dict(artwork_id=f['artwork_id'],institution_id=n.IID,source_url=f['source_url'],verified_existing_metadata_unchanged=True,confidence=d['confidence'],evidence_basis=d['basis']+' '+d['version_review'],source_limitation=d['limitation']))
    for r in dp['records']:
        f,d=r['facts'],r['decision']
        if f['accept_holding']:
            summary['existing_holding_verifications'].append(dict(artwork_id=f['artwork_id'],institution_id=n.IID,source_url=f['source_url'],verified_existing_metadata_unchanged=False,confidence=0.95,evidence_basis=d['physical_identity_basis']+' Separately audited four-field enrichment of an unknown creation date from native Date: '+f['patch']['date_display'],source_limitation=d['source_limitations']))
    holding_rows=summary['existing_holding_verifications'];assert len(holding_rows)==len({r['artwork_id'] for r in holding_rows})==661
    write_csv(m.RUN/('reconciled-artworks-'+label+'.csv'),holding_rows)
    with (m.RUN/('added-artworks-'+base+'.csv')).open(newline='') as f:added=list(csv.DictReader(f))
    for r in np['records']:
        f=r['facts'];added.append(dict(artwork_id=r['artwork_id'],museum='Government Art Collection',museum_slug='wikimedia-museum-q5588677',title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],accession=f['inventory'],source_url=f['source_url'],status='review'))
    assert len(added)==len({r['artwork_id'] for r in added})==3611
    write_csv(m.RUN/('added-artworks-'+label+'.csv'),sorted(added,key=lambda r:(r['museum'],r['title'])))
    enriched=[]
    for r in dp['records']:
        f=r['facts'];old=next(a for a in dp['before']['artworks'] if a['id']==f['artwork_id'])
        enriched.append(dict(artwork_id=f['artwork_id'],museum='Government Art Collection',title=f['title'],old_date_display=old['date_display'],old_year_start=old['creation_year_start'],old_year_end=old['creation_year_end'],old_precision=old['date_precision'],new_date_display=f['patch']['date_display'],new_year_start=f['patch']['creation_year_start'],new_year_end=f['patch']['creation_year_end'],new_precision=f['patch']['date_precision'],holding_added=f['accept_holding'],source_url=f['source_url']))
    write_csv(m.RUN/('gac-date-enrichments-'+label+'.csv'),enriched)
    summary.update(at=m.now(),verified_new_artworks=3611,verified_existing_artworks_linked=661,institutions_expanded=summary['institutions_expanded']+1,museums_expanded=summary['museums_expanded']+1,source_pass_museums=summary['source_pass_museums']+1,source_pass_institutions=summary['source_pass_institutions']+1,institutions_with_new_records_or_reconciled_holdings=summary['institutions_with_new_records_or_reconciled_holdings']+1,gac_holding_reconciliation=holdings,gac_existing_date_enrichment=dates,gac_new_artworks=checked)
    summary['expanded_institution_kinds']['museum']+=1
    summary['by_source'][n.KEY]=dict(new_artworks=58,held_or_deferred=42,successful_native_captures=99,failed_native_captures=1,plan_sha256=nd)
    summary['verification_components'] += [n.reference(m.RUN/('verification-'+base+'.json'))]
    for importer in [w,v,n]:summary['verification_components'] += [n.reference(importer.PLAN),n.reference(importer.RUN/(importer.KEY+'-applied.json'))]
    assert summary['verified_new_artworks']==sum(r['new_artworks'] for r in summary['by_source'].values())
    assert sum(int(r['added_this_campaign']) for r in coverage)==3611 and sum(int(r['existing_artworks_linked_this_campaign']) for r in coverage)==661
    for ext in ['.json','.csv']:
        with (m.RUN/(label+ext)).open('xb') as f:f.write((m.RUN/(base+ext)).read_bytes())
    m.save(m.RUN/('verification-'+label+'.json'),summary)
    print(json.dumps({k:summary[k] for k in ['verified_new_artworks','verified_existing_artworks_linked','museums_expanded','source_pass_museums','after']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',default='after-wave-31');report(p.parse_args().label)
