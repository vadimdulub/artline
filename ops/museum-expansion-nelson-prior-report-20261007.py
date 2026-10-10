#!/usr/bin/env python3
"""Fresh Thyssen predecessor verification for Nelson, using a new short report root."""
import argparse,copy,csv,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('museum-expansion-hamburg-report-20261007.py'));base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-thyssen-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m;write_csv=base.write_csv
def report(label):
 assert not (m.RUN/('verification-'+label+'.json')).exists();plan,digest=a.validate_plan();assert m.load(a.RUN/(a.KEY+'-applied.json'))['plan_sha256']==digest
 with m.connect() as db:verification=a.verify(db,plan,digest)
 # The inherited report chain appends a suffix at every generation. Keep the
 # root short enough for the filesystem's255-byte component limit.
 previous='n49'
 if not (m.RUN/('verification-'+previous+'.json')).exists():base.report(previous)
 summary=copy.deepcopy(m.load(m.RUN/('verification-'+previous+'.json')));assert summary['verified_new_artworks']==5006 and summary['verified_existing_artworks_linked']==765
 with (m.RUN/('museum-coverage-'+previous+'.csv')).open(newline='') as f:coverage=list(csv.DictReader(f))
 museum=next(r for r in coverage if r['id']==a.IID);assert museum['kind']=='museum' and museum['added_this_campaign']==museum['existing_artworks_linked_this_campaign']=='0'
 assert (int(museum['works']),int(museum['eligible_works']))==(202,200)
 museum.update(added_this_campaign='172',research_state='reviewed_native_additions_verified',native_source_probe_status='public_masterpieces_and_related_object_pages_verified_search_denial_retained',campaign_state='preferred_200_eligible_reached')
 write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
 with (m.RUN/('added-artworks-'+previous+'.csv')).open(newline='') as f:added=list(csv.DictReader(f))
 for r in plan['records']:
  v=r['facts'];added.append(dict(artwork_id=r['artwork_id'],museum='Museo Nacional Thyssen-Bornemisza',museum_slug='museo-thyssen-bornemisza',title=v['title'],creator_label=v['creator_label'],date_display=v['date_display'],creation_year_start=v['first'],creation_year_end=v['last'],accession=v['inventory'],source_url=v['source_url'],status='review'))
 assert len(added)==len({r['artwork_id'] for r in added})==5178;write_csv(m.RUN/('added-artworks-'+label+'.csv'),sorted(added,key=lambda r:(r['museum'],r['title'])))
 summary.update(at=m.now(),verified_new_artworks=5178,museums_expanded=summary['museums_expanded']+1,institutions_expanded=summary['institutions_expanded']+1,source_pass_museums=summary['source_pass_museums']+1,source_pass_institutions=summary['source_pass_institutions']+1,institutions_with_new_records_or_reconciled_holdings=summary['institutions_with_new_records_or_reconciled_holdings']+1,thyssen_preferred_200=verification)
 summary['expanded_institution_kinds']['museum']+=1
 summary['by_source'][a.KEY]=dict(new_artworks=172,selected_native_objects=267,source_eligible_candidates=209,editorial_version_holds=22,source_holds=58,existing_identity_reconciliation=15,linked_records=202,eligible_records=200,remaining_to_preferred_200=0,plan_sha256=digest)
 summary['verification_components'] += [a.reference(m.RUN/('verification-'+previous+'.json')),a.reference(a.PLAN),a.reference(a.RUN/(a.KEY+'-applied.json'))]
 assert sum(int(r['added_this_campaign']) for r in coverage)==sum(r['new_artworks'] for r in summary['by_source'].values())==5178
 assert sum(int(r['existing_artworks_linked_this_campaign']) for r in coverage)==765
 for prefix,ext in [('', '.json'),('', '.csv'),('gac-date-enrichments-', '.csv'),('reconciled-artworks-', '.csv')]:
  with (m.RUN/(prefix+label+ext)).open('xb') as f:f.write((m.RUN/(prefix+previous+ext)).read_bytes())
 m.save(m.RUN/('verification-'+label+'.json'),summary)
 print(json.dumps({k:summary[k] for k in ['verified_new_artworks','verified_existing_artworks_linked','museums_expanded','source_pass_museums','after']}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--label',default='after-wave-48');report(p.parse_args().label)
