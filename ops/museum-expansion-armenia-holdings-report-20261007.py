#!/usr/bin/env python3
"""Combine verified additions and Armenian holding reconciliations with unchanged shared-campaign reporting."""
import argparse
import collections
import copy
import csv
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-serbia-apply-20261007.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
m=a.m
spec=importlib.util.spec_from_file_location('armenia',Path(__file__).with_name('museum-expansion-armenia-apply-20261007.py'))
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-armenia-checkpoint-20261007.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


def report(label):
    # The live production continuation pins the shared importer. Its legacy
    # report verifies all previous batches in separate, explicitly named files.
    # This adapter adds the independently verified Serbian and Armenian batches without
    # monkey-patching that process or changing any existing snapshot.
    assert not (m.RUN/('verification-'+label+'.json')).exists()
    batches=[]
    for importer in [a,b]:
        plan,digest=importer.validate_plan();applied=m.load(m.RUN/(importer.SOURCE+'-applied.json'))
        assert applied['plan_sha256']==digest and applied['created']==len(plan['records'])
        with m.connect() as db:verified=c.verify_prior_additions(db,plan,digest) if importer is b else importer.verify(db,plan,digest)
        batches.append((importer,plan,digest,verified))
    if not (m.RUN/(label+'.json')).exists():m.audit(label)
    audit=m.load(m.RUN/(label+'.json'));legacy=label+'-prior-batches'
    m.save(m.RUN/(legacy+'.json'),audit)
    if not (m.RUN/('verification-'+legacy+'.json')).exists():m.report(legacy)
    summary=copy.deepcopy(m.load(m.RUN/('verification-'+legacy+'.json')))
    with (m.RUN/('museum-coverage-'+legacy+'.csv')).open(newline='') as f:coverage=list(csv.DictReader(f))
    for importer,plan,digest,verified in batches:
        target=next(r for r in coverage if r['id']==importer.IID)
        assert target['added_this_campaign']=='0' and target['kind']=='museum'
        assert int(target['works'])==verified['current_counts']['linked'] and int(target['eligible_works'])==verified['current_counts']['eligible']
        assert target['research_state']=='source_research_pending'
        target['added_this_campaign']=str(len(plan['records']));target['research_state']='new_review_artworks_added'
        if importer is b:
            assert target['existing_artworks_linked_this_campaign']=='0'
            target['existing_artworks_linked_this_campaign']='136'
    with (m.RUN/('museum-coverage-'+label+'.csv')).open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(coverage[0]));writer.writeheader();writer.writerows(coverage)
    with (m.RUN/('added-artworks-'+legacy+'.csv')).open(newline='') as f:added=list(csv.DictReader(f))
    assert len(added)==summary['verified_new_artworks']
    for importer,plan,digest,verified in batches:
        old_ids={r['artwork_id'] for r in added};assert not old_ids&{r['artwork_id'] for r in plan['records']}
        for r in plan['records']:
            f=r['facts'];added.append(dict(artwork_id=r['artwork_id'],museum=r['museum']['name'],museum_slug=r['museum']['slug'],title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],accession=f['accession'],source_url=f['source_url'],status='review'))
    with (m.RUN/('added-artworks-'+label+'.csv')).open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(added[0]));writer.writeheader();writer.writerows(sorted(added,key=lambda r:(r['museum'],r['title'])))
    summary.update(at=m.now(),verified_new_artworks=len(added),institutions_expanded=summary['institutions_expanded']+len(batches),museums_expanded=summary['museums_expanded']+len(batches),source_pass_museums=summary['source_pass_museums']+len(batches),source_pass_institutions=summary['source_pass_institutions']+len(batches))
    summary['expanded_institution_kinds']['museum']+=len(batches)
    summary['verification_components']=[a.reference(m.RUN/('verification-'+legacy+'.json'))]
    for importer,plan,digest,verified in batches:
        summary['by_source'][importer.SOURCE]=dict(new_artworks=len(plan['records']),held=len(plan['held']),plan_sha256=digest)
        summary[importer.SOURCE+'_verification']=verified
        summary['verification_components'] += [a.reference(m.RUN/(importer.SOURCE+'-applied.json')),a.reference(importer.PLAN)]
    holding_plan,holding_digest=c.h.validate_plan()
    with m.connect() as db:holding_verified=c.h.verify(db,holding_plan,holding_digest)
    summary['verified_existing_artworks_linked']+=136
    for r in holding_plan['records']:
        f=r['facts']
        summary['existing_holding_verifications'].append(dict(artwork_id=f['artwork_id'],institution_id=b.IID,source_url=f['source_url'],verified_existing_metadata_unchanged=True,confidence=r['decision']['confidence'],evidence_basis=r['decision']['basis'],source_limitation=r['decision']['limitation']))
    summary['armenia_holding_reconciliation']=holding_verified
    summary['verification_components'] += [a.reference(c.h.PLAN),a.reference(c.h.RUN/(c.h.KEY+'-applied.json'))]
    assert len(summary['existing_holding_verifications'])==summary['verified_existing_artworks_linked']==137
    with (m.RUN/('reconciled-artworks-'+label+'.csv')).open('x',newline='') as f:
        keys=['artwork_id','institution_id','source_url','verified_existing_metadata_unchanged','confidence','evidence_basis','source_limitation']
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(summary['existing_holding_verifications'])
    assert summary['verified_new_artworks']==sum(s['new_artworks'] for s in summary['by_source'].values())
    assert len({r['artwork_id'] for r in added})==len(added)
    m.save(m.RUN/('verification-'+label+'.json'),summary)
    print(json.dumps({k:summary[k] for k in ['verified_new_artworks','museums_expanded','source_pass_museums','after']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',default='after-wave-25');args=p.parse_args();report(args.label)
