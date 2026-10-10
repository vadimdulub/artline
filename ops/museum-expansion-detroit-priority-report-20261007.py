#!/usr/bin/env python3
"""Fresh wave51 verification: five DIA additions and the MFA source-access hold."""
import argparse,copy,csv,importlib.util,json
from pathlib import Path
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=module('base','museum-expansion-detroit-prior-samples-report-20261007.py');a=module('a','museum-expansion-detroit-priority-apply-20261007.py');m=a.m;write_csv=base.write_csv;MFA='e817808a-be18-5348-896e-358bed088ac3'
def report(label):
 assert not (m.RUN/('verification-'+label+'.json')).exists();plan,digest=a.validate_plan();assert m.load(a.RUN/(a.KEY+'-applied.json'))['plan_sha256']==digest
 with m.connect() as db:
  verification=a.verify(db,plan,digest);before=m.load(m.RUN/'native/mfa/initial-scope-001.json.gz');assert a.old.snapshot(db,before['scoped_ids'],MFA)==before['snapshot'];assert a.old.counts(db,MFA)==before['counts']==dict(linked=0,eligible=0)
 a.h.install(base);previous='d51s';assert not (m.RUN/('verification-'+previous+'.json')).exists();base.report(previous)
 summary=copy.deepcopy(m.load(m.RUN/('verification-'+previous+'.json')));assert summary['verified_new_artworks']==5329 and summary['verified_existing_artworks_linked']==765
 with (m.RUN/('museum-coverage-'+previous+'.csv')).open(newline='') as f:coverage=list(csv.DictReader(f))
 museum=next(r for r in coverage if r['id']==a.IID);assert museum['added_this_campaign']=='1' and (int(museum['works']),int(museum['eligible_works']))==(6,6)
 museum.update(added_this_campaign='6',research_state='six_native_records_added_remaining_selected_objects_under_review',native_source_probe_status='native_continuation_after_documented_cooldown_one_object_timeout_held',campaign_state='below_100_native_research_continuing')
 museum=next(r for r in coverage if r['id']==MFA);assert int(museum['works'])==0 and museum['research_state']=='source_research_pending';museum.update(research_state='source_access_hold',native_source_probe_status='official_collection_robot_verification_gate_guide_readable',campaign_state='below_100_source_access_followup_required');write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
 with (m.RUN/('added-artworks-'+previous+'.csv')).open(newline='') as f:added=list(csv.DictReader(f))
 for r in plan['records']:
  v=r['facts'];added.append(dict(artwork_id=r['artwork_id'],museum='Detroit Institute of Arts',museum_slug='museum-authority-q1201549',title=v['title'],creator_label=v['creator_label'],date_display=v['date_display'],creation_year_start=v['first'],creation_year_end=v['last'],accession=v['inventory'],source_url=v['source_url'],status='review'))
 assert len(added)==len({r['artwork_id'] for r in added})==5334;write_csv(m.RUN/('added-artworks-'+label+'.csv'),sorted(added,key=lambda r:(r['museum'],r['title'])))
 summary.update(at=m.now(),verified_new_artworks=5334,source_pass_museums=summary['source_pass_museums']+1,source_pass_institutions=summary['source_pass_institutions']+1,detroit_priority_verification=verification,mfa_source_pass=dict(additions=0,old_pending_records_unchanged=15,source_reference=a.reference(m.RUN/'native/mfa/web-discovery-001.json')))
 summary['by_source'][a.KEY]=dict(new_artworks=5,institutions_expanded=0,previously_expanded_institution_continuation=True,priority_panels_reviewed=7,priority_panels_added=5,missing_location_hold=1,priority_object_timeout_hold=1,linked_records=6,eligible_records=6,remaining_to_100=94,plan_sha256=digest)
 summary['verification_components'] += [a.reference(m.RUN/('verification-'+previous+'.json')),a.reference(a.PLAN),a.reference(a.RUN/(a.KEY+'-applied.json'))]
 assert sum(int(r['added_this_campaign']) for r in coverage)==sum(r['new_artworks'] for r in summary['by_source'].values())==5334;assert sum(int(r['existing_artworks_linked_this_campaign']) for r in coverage)==765
 for prefix,ext in [('', '.json'),('', '.csv'),('gac-date-enrichments-', '.csv'),('reconciled-artworks-', '.csv')]:
  with (m.RUN/(prefix+label+ext)).open('xb') as f:f.write((m.RUN/(prefix+previous+ext)).read_bytes())
 m.save(m.RUN/('verification-'+label+'.json'),summary);print(json.dumps({k:summary[k] for k in ['verified_new_artworks','verified_existing_artworks_linked','museums_expanded','institutions_expanded','source_pass_museums','source_pass_institutions','institutions_with_new_records_or_reconciled_holdings','after']}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--label',default='after-wave-51');report(p.parse_args().label)
