#!/usr/bin/env python3
"""Wave53: immutable historical verification with a fresh BMA delta and global audit."""
import copy,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-baltimore-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
io=a.module('report_io','museum-expansion-detroit-final-report-20261007.py')
def main():
 label='after-wave-53';assert not (m.RUN/('verification-'+label+'.json')).exists();p,digest=a.validate_plan();receipt=m.load(a.RUN/(a.KEY+'-applied.json'));assert receipt['plan_sha256']==digest;a.verify_baseline()
 with m.connect() as db:verified=a.verify(db,p,digest)
 m.audit(label);live=m.load(m.RUN/(label+'.json'));summary=copy.deepcopy(m.load(m.RUN/'verification-after-wave-52.json'))
 coverage=io.read_csv(m.RUN/'museum-coverage-after-wave-52.csv');liveby={x['id']:x for x in live['institutions']};assert set(liveby)=={x['id'] for x in coverage};external=[]
 for row in coverage:
  current=liveby[row['id']]
  if row['id']!=a.IID:
   changes={k:dict(before=int(row[k]),after=current[k]) for k in ['works','eligible_works','illustrated_works','pending_associations'] if int(row[k])!=current[k]}
   if changes:external.append(dict(institution_id=row['id'],changes=changes))
  for k,v in current.items():
   if k!='campaign_state':row[k]=v
 bma=next(x for x in coverage if x['id']==a.IID);assert (bma['works'],bma['eligible_works'],bma['pending_associations'])==(22,22,0)
 bma.update(added_this_campaign='21',existing_artworks_linked_this_campaign='0',research_state='23_complete_native_objects_reviewed_21_added_2_held',native_source_probe_status='HTTP429_challenge_capture_stopped_no_retry',campaign_state='below_minimum_100_native_access_hold')
 io.write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
 added=io.read_csv(m.RUN/'added-artworks-after-wave-52.csv')
 for row in p['records']:
  f=row['facts'];added.append(dict(artwork_id=row['artwork_id'],museum='Baltimore Museum of Art',museum_slug='wikimedia-museum-q377579',title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],accession=f['inventory'],source_url=f['source_url'],status='review'))
 assert len(added)==len({x['artwork_id'] for x in added})==5447
 io.write_csv(m.RUN/('added-artworks-'+label+'.csv'),sorted(added,key=lambda r:(r['museum'],r['title'])))
 for prefix in ['reconciled-artworks','gac-date-enrichments']:io.write_csv(m.RUN/(prefix+'-'+label+'.csv'),io.read_csv(m.RUN/(prefix+'-after-wave-52.csv')))
 summary.update(at=m.now(),verified_new_artworks=5447,verified_existing_artworks_linked=767,institutions_expanded=162,museums_expanded=161,expanded_institution_kinds=dict(museum=161,foundation=1),institutions_with_new_records_or_reconciled_holdings=164,source_pass_museums=349,source_pass_institutions=350,after=live['summary'],baltimore_selected_additions=verified,unrelated_coverage_changes_since_prior_report=external)
 summary['by_source'][a.KEY]=dict(new_artworks=21,existing_artworks_linked=0,institutions_expanded=1,captured_objects_reviewed=23,captured_holds=2,uncaptured_queue_entries=221,linked_records=22,eligible_records=22,remaining_to_100=78,remaining_to_200=178,plan_sha256=digest)
 summary['verification_components'] += [a.reference(m.RUN/'verification-after-wave-52.json'),a.reference(a.CHECKPOINT),a.reference(a.PLAN),a.reference(a.RUN/(a.KEY+'-applied.json'))]
 summary['verification_method']='Wave52 historical verification remains immutable and source-pinned. Wave53 freshly checks21 new records and complete protected preimages, and content digests prove all6193 earlier campaign objects and associated rows unchanged from immediate preflight. Fresh identity preflight covers16242 creator/title/inventory/source candidates and34175 citations. Historic count-sensitive validators are not rewritten. Global museum coverage is a fresh read-only audit.'
 for threshold in [100,200]:summary['museums_crossing_'+str(threshold)]=[dict(name=x['name'],before=int(x['works_before']),after=int(x['works'])) for x in coverage if x['kind']=='museum' and x['status']!='archived' and not x['canonical_institution_id'] and int(x['works_before'])<threshold<=int(x['works'])]
 assert sum(int(x['added_this_campaign']) for x in coverage)==sum(v['new_artworks'] for v in summary['by_source'].values())==5447
 assert sum(int(x['existing_artworks_linked_this_campaign']) for x in coverage)==767
 summary['identity_reference_downloads_this_wave']=dict(selected_wikiart_jpeg=0,selected_primary_educational_pdf=0,catalogue_image_attachments=0)
 m.save(m.RUN/('verification-'+label+'.json'),summary)
 print(json.dumps({k:summary[k] for k in ['verified_new_artworks','verified_existing_artworks_linked','institutions_with_new_records_or_reconciled_holdings','source_pass_museums','source_pass_institutions','after','unrelated_coverage_changes_since_prior_report']}),flush=True)
if __name__=='__main__':main()
