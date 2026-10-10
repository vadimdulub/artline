#!/usr/bin/env python3
"""Wave54: immutable earlier proofs, verified Princeton delta and fresh coverage."""
import copy,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-princeton-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
io=a.module('io','museum-expansion-detroit-final-report-20261007.py')
def main():
 label='after-wave-54';assert not (m.RUN/('verification-'+label+'.json')).exists();p,digest=a.validate_plan();receipt=m.load(a.RUN/(a.KEY+'-applied.json'));assert receipt['plan_sha256']==digest;a.verify_baseline()
 with m.connect() as db:verified=a.verify(db,p,digest)
 m.audit(label);live=m.load(m.RUN/(label+'.json'));summary=copy.deepcopy(m.load(m.RUN/'verification-after-wave-53.json'))
 coverage=io.read_csv(m.RUN/'museum-coverage-after-wave-53.csv');liveby={v['id']:v for v in live['institutions']};assert set(liveby)=={v['id'] for v in coverage};external=[]
 for row in coverage:
  current=liveby[row['id']]
  if row['id']!=a.IID:
   changes={k:dict(before=int(row[k]),after=current[k]) for k in ['works','eligible_works','illustrated_works','pending_associations'] if int(row[k])!=current[k]}
   if changes:external.append(dict(institution_id=row['id'],changes=changes))
  for k,v in current.items():
   if k!='campaign_state':row[k]=v
 princeton=next(v for v in coverage if v['id']==a.IID);assert (princeton['works'],princeton['eligible_works'],princeton['pending_associations'])==(164,164,9)
 princeton.update(added_this_campaign='146',existing_artworks_linked_this_campaign='18',research_state='256_native_objects_reviewed_146_added_18_reconciled_92_held',native_source_probe_status='documented_public_API_selected_capture_complete_HTTP200',campaign_state='minimum_100_met_36_eligible_short_of_200')
 io.write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
 added=io.read_csv(m.RUN/'added-artworks-after-wave-53.csv')
 for row in p['records']:
  f=row['facts'];added.append(dict(artwork_id=row['artwork_id'],museum='Princeton University Art Museum',museum_slug='spain-research-museum-q2603905',title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],accession=f['inventory'],source_url=f['source_url'],status='review'))
 assert len(added)==len({v['artwork_id'] for v in added})==5593;io.write_csv(m.RUN/('added-artworks-'+label+'.csv'),sorted(added,key=lambda v:(v['museum'],v['title'])))
 holds=io.read_csv(m.RUN/'reconciled-artworks-after-wave-53.csv')
 for row in p['holdings']:holds.append(dict(artwork_id=row['artwork_id'],institution_id=a.IID,source_url=row['facts']['source_url'],verified_existing_metadata_unchanged=True,confidence=row['decision']['confidence'],evidence_basis=row['decision']['basis'],source_limitation=row['decision']['limitation']))
 assert len(holds)==len({v['artwork_id'] for v in holds})==785;io.write_csv(m.RUN/('reconciled-artworks-'+label+'.csv'),holds)
 io.write_csv(m.RUN/('gac-date-enrichments-'+label+'.csv'),io.read_csv(m.RUN/'gac-date-enrichments-after-wave-53.csv'))
 summary.update(at=m.now(),verified_new_artworks=5593,verified_existing_artworks_linked=785,institutions_expanded=163,museums_expanded=162,expanded_institution_kinds=dict(museum=162,foundation=1),institutions_with_new_records_or_reconciled_holdings=165,source_pass_museums=350,source_pass_institutions=351,after=live['summary'],princeton_selected_additions=verified,unrelated_coverage_changes_since_prior_report=external)
 summary['by_source'][a.KEY]=dict(new_artworks=146,existing_artworks_linked=18,institutions_expanded=1,captured_objects_reviewed=256,captured_holds=92,index_holds=132,distinct_discovery_objects=388,linked_records=164,eligible_records=164,remaining_to_100=0,remaining_to_200=36,plan_sha256=digest)
 summary['verification_components'] += [a.reference(m.RUN/'verification-after-wave-53.json'),a.reference(a.CHECKPOINT),a.reference(a.PLAN),a.reference(a.RUN/(a.KEY+'-applied.json'))]
 summary['verification_method']='Wave53 historical proofs remain immutable and hash-pinned. Wave54 freshly verifies146 new review records and18 exact existing-object holding reconciliations; complete scoped preimages protect metadata, images and publication, and table digests protect all6214 earlier campaign objects. Read-only identity preflight covers48681 artwork candidates and104656 citations plus literal Latin maker aliases. Full identity comparisons were recomputed and their immutable inputs pinned. Global museum coverage is freshly audited; historical count-sensitive validators are not rewritten.'
 for threshold in [100,200]:summary['museums_crossing_'+str(threshold)]=[dict(name=v['name'],before=int(v['works_before']),after=int(v['works'])) for v in coverage if v['kind']=='museum' and v['status']!='archived' and not v['canonical_institution_id'] and int(v['works_before'])<threshold<=int(v['works'])]
 assert sum(int(v['added_this_campaign']) for v in coverage)==sum(v['new_artworks'] for v in summary['by_source'].values())==5593
 assert sum(int(v['existing_artworks_linked_this_campaign']) for v in coverage)==785
 summary['identity_reference_downloads_this_wave']=dict(selected_wikiart_jpeg=0,selected_primary_educational_pdf=0,catalogue_image_attachments=0)
 m.save(m.RUN/('verification-'+label+'.json'),summary);print(json.dumps({k:summary[k] for k in ['verified_new_artworks','verified_existing_artworks_linked','institutions_with_new_records_or_reconciled_holdings','source_pass_museums','source_pass_institutions','after','unrelated_coverage_changes_since_prior_report']}),flush=True)
if __name__=='__main__':main()
