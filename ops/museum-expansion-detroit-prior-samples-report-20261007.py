#!/usr/bin/env python3
"""Fresh campaign verification, including two additions and three source passes."""
import argparse,copy,csv,importlib.util,json
from pathlib import Path
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=module('base','museum-expansion-detroit-prior-nelson-report-20261007.py');a=module('a','museum-expansion-next-samples-apply-20261007.py');m=a.m;write_csv=base.write_csv
prior=module('prior','museum-expansion-detroit-prior-samples-verify-20261007.py')
def report(label):
 assert not (m.RUN/('verification-'+label+'.json')).exists();plan,digest=a.validate_plan();assert m.load(a.RUN/(a.KEY+'-applied.json'))['plan_sha256']==digest
 with m.connect() as db:verification=prior.verify(db,plan,digest)
 adapters=a.h.install(base);previous='d51n'
 if not (m.RUN/('verification-'+previous+'.json')).exists():base.report(previous)
 summary=copy.deepcopy(m.load(m.RUN/('verification-'+previous+'.json')));assert summary['verified_new_artworks']==5327 and summary['verified_existing_artworks_linked']==765
 with (m.RUN/('museum-coverage-'+previous+'.csv')).open(newline='') as f:coverage=list(csv.DictReader(f))
 for key,mod in a.MODS.items():
  museum=next(r for r in coverage if r['id']==mod.IID);assert museum['added_this_campaign']==museum['existing_artworks_linked_this_campaign']=='0';assert (int(museum['works']),int(museum['eligible_works']))==((6,6) if key=='detroit' else (1,1))
  museum.update(added_this_campaign='1',research_state='one_complete_native_record_added_larger_queue_held',native_source_probe_status='native_metadata_captured_then_http429' if key=='detroit' else 'one_complete_web_extract_direct_http403_and_object_timeouts_retained',campaign_state='below_100_source_access_followup_required')
 museum=next(r for r in coverage if r['id']=='56d4409a-0bd4-5a2d-b5e6-575dab970235');assert int(museum['works'])==0;museum.update(research_state='source_access_hold',native_source_probe_status='official_collection_web_http403',campaign_state='below_100_source_access_followup_required')
 write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
 with (m.RUN/('added-artworks-'+previous+'.csv')).open(newline='') as f:added=list(csv.DictReader(f))
 for r in plan['records']:
  v=r['facts'];museum=next(z for z in coverage if z['id']==r['institution_id']);added.append(dict(artwork_id=r['artwork_id'],museum=museum['name'],museum_slug=museum['slug'],title=v['title'],creator_label=v['creator_label'],date_display=v['date_display'],creation_year_start=v['first'],creation_year_end=v['last'],accession=v['inventory'],source_url=v['source_url'],status='review'))
 assert len(added)==len({r['artwork_id'] for r in added})==5329;write_csv(m.RUN/('added-artworks-'+label+'.csv'),sorted(added,key=lambda r:(r['museum'],r['title'])))
 summary.update(at=m.now(),verified_new_artworks=5329,museums_expanded=summary['museums_expanded']+2,institutions_expanded=summary['institutions_expanded']+2,source_pass_museums=summary['source_pass_museums']+3,source_pass_institutions=summary['source_pass_institutions']+3,institutions_with_new_records_or_reconciled_holdings=summary['institutions_with_new_records_or_reconciled_holdings']+2,next_samples_verification=verification,historical_policy_snapshot_verification=dict(receipt=a.reference(a.h.RECEIPT),adapter=a.reference(Path(a.h.__file__).resolve()),adapted_validators=adapters))
 summary['expanded_institution_kinds']['museum']+=2
 summary['by_source'][a.KEY]=dict(new_artworks=2,institutions_expanded=2,ago_date_screened_queue=172,detroit_date_screened_queue=118,unapproved_queue_entries=289,separate_detroit_complete_highlight=1,index_date_holds=25,source_access_holds=3,plan_sha256=digest)
 summary['verification_components'] += [a.reference(m.RUN/('verification-'+previous+'.json')),a.reference(a.PLAN),a.reference(a.RUN/(a.KEY+'-applied.json')),a.reference(a.h.RECEIPT)]
 assert sum(int(r['added_this_campaign']) for r in coverage)==sum(r['new_artworks'] for r in summary['by_source'].values())==5329;assert sum(int(r['existing_artworks_linked_this_campaign']) for r in coverage)==765
 for prefix,ext in [('', '.json'),('', '.csv'),('gac-date-enrichments-', '.csv'),('reconciled-artworks-', '.csv')]:
  with (m.RUN/(prefix+label+ext)).open('xb') as f:f.write((m.RUN/(prefix+previous+ext)).read_bytes())
 m.save(m.RUN/('verification-'+label+'.json'),summary);print(json.dumps({k:summary[k] for k in ['verified_new_artworks','verified_existing_artworks_linked','museums_expanded','institutions_expanded','source_pass_museums','source_pass_institutions','institutions_with_new_records_or_reconciled_holdings','after']}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--label',default='after-wave-50');report(p.parse_args().label)
