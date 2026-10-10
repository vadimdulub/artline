#!/usr/bin/env python3
"""Verify the selected Fitzwilliam additions and refresh complete museum coverage."""
import argparse,copy,csv,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('museum-expansion-russell-target-report-20261007.py'));prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior)
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-fitzwilliam-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
write_csv=prior.prior.write_csv
def report(label):
 assert not (m.RUN/('verification-'+label+'.json')).exists();plan,digest=a.validate_plan();assert m.load(a.RUN/(a.KEY+'-applied.json'))['plan_sha256']==digest
 with m.connect() as db:verification=a.verify(db,plan,digest)
 base=label+'-prior-batches'
 if not (m.RUN/('verification-'+base+'.json')).exists():prior.report(base)
 summary=copy.deepcopy(m.load(m.RUN/('verification-'+base+'.json')));assert summary['verified_new_artworks']==3700 and summary['verified_existing_artworks_linked']==759
 with (m.RUN/('museum-coverage-'+base+'.csv')).open(newline='') as f:coverage=list(csv.DictReader(f))
 target=next(r for r in coverage if r['id']==a.IID);assert target['kind']=='museum' and target['added_this_campaign']==target['existing_artworks_linked_this_campaign']=='0'
 assert (int(target['works']),int(target['eligible_works']))==(176,170)
 target.update(added_this_campaign='163',research_state='native_additions_verified',campaign_state='minimum_100_reached_this_campaign')
 write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
 with (m.RUN/('added-artworks-'+base+'.csv')).open(newline='') as f:added=list(csv.DictReader(f))
 for r in plan['records']:
  v=r['facts'];added.append(dict(artwork_id=r['artwork_id'],museum='Fitzwilliam Museum',museum_slug='spain-research-museum-q1421440',title=v['title'],creator_label=v['creator_label'],date_display=v['date_display'],creation_year_start=v['first'],creation_year_end=v['last'],accession=v['inventory'],source_url=v['source_url'],status='review'))
 assert len(added)==len({r['artwork_id'] for r in added})==3863;write_csv(m.RUN/('added-artworks-'+label+'.csv'),sorted(added,key=lambda r:(r['museum'],r['title'])))
 summary.update(at=m.now(),verified_new_artworks=3863,museums_expanded=summary['museums_expanded']+1,institutions_expanded=summary['institutions_expanded']+1,source_pass_museums=summary['source_pass_museums']+1,source_pass_institutions=summary['source_pass_institutions']+1,institutions_with_new_records_or_reconciled_holdings=summary['institutions_with_new_records_or_reconciled_holdings']+1,fitzwilliam_native_additions=verification)
 summary['expanded_institution_kinds']['museum']+=1;summary['by_source'][a.KEY]=dict(new_artworks=163,native_captures=313,not_added=150,plan_sha256=digest)
 summary['verification_components'] += [a.reference(m.RUN/('verification-'+base+'.json')),a.reference(a.PLAN),a.reference(a.RUN/(a.KEY+'-applied.json'))]
 assert sum(int(r['added_this_campaign']) for r in coverage)==sum(r['new_artworks'] for r in summary['by_source'].values())==3863
 for prefix,ext in [('', '.json'),('', '.csv'),('gac-date-enrichments-', '.csv'),('reconciled-artworks-', '.csv')]:
  with (m.RUN/(prefix+label+ext)).open('xb') as f:f.write((m.RUN/(prefix+base+ext)).read_bytes())
 m.save(m.RUN/('verification-'+label+'.json'),summary)
 print(json.dumps({k:summary[k] for k in ['verified_new_artworks','verified_existing_artworks_linked','museums_expanded','source_pass_museums','after']}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--label',default='after-wave-35');report(p.parse_args().label)
