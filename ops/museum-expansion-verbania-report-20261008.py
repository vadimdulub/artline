"""Wave77 verified coverage and separate external catalogue changes."""
import collections,copy,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-verbania-apply-20261008.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);m=a.m;io=a.module('io','museum-expansion-detroit-final-report-20261007.py')
def main():
 label='after-wave-77';assert not (m.RUN/('verification-'+label+'.json')).exists();p,digest=a.validate_plan();a.verify_baseline()
 with m.connect() as db:verified=a.verify(db,p,digest)
 live=m.load(m.RUN/(label+'.json'));summary=copy.deepcopy(m.load(m.RUN/'verification-after-wave-76.json'));coverage=io.read_csv(m.RUN/'museum-coverage-after-wave-76.csv');liveby={v['id']:v for v in live['institutions']};oldids={v['id'] for v in coverage};assert oldids<=set(liveby);new=[v for v in live['institutions'] if v['id'] not in oldids]
 for v in new:
  row={k:'' for k in coverage[0]};row.update(v);row.update(works_before=v['works'],eligible_before=v['eligible_works'],added_this_campaign=0,existing_artworks_linked_this_campaign=0,research_state='external_registry_addition_not_reviewed_by_this_campaign',native_source_probe_status='not_reviewed_by_this_campaign',coverage_baseline_label='first_observed_after_wave_77');coverage.append(row)
 changes=[];external=[]
 for row in coverage:
  v=liveby[row['id']]
  if row['id']==a.IID:
   assert int(row['works'])==int(row['eligible_works'])==0 and v['works']==155 and v['eligible_works']==140;assert v['illustrated_works']==int(row['illustrated_works']) and v['pending_associations']==int(row['pending_associations'])-155
   changes.append(dict(institution_id=a.IID,name=row['name'],new=0,existing_linked=155,linked_before=0,linked_after=155,eligible_before=0,eligible_after=140));row.update(existing_artworks_linked_this_campaign=int(row['existing_artworks_linked_this_campaign'])+155,research_state=row['research_state']+'; verbania_155_existing_holdings_accepted_6_held',native_source_probe_status='saved_official_object_evidence_verified',campaign_state='minimum_100_met_eligible_140_preferred_200_remaining')
  elif row['id'] in oldids:
   delta={k:dict(before=int(row[k]),after=v[k]) for k in ['works','eligible_works','illustrated_works','pending_associations'] if int(row[k])!=v[k]}
   if delta:external.append(dict(institution_id=row['id'],name=row['name'],changes=delta))
  for k,value in v.items():
   if k!='campaign_state':row[k]=value
 growth=a.RUN/'coverage-registry-growth-001.json';assert not growth.exists();m.save(growth,dict(at=m.now(),live_audit_reference=a.reference(m.RUN/(label+'.json')),previous_coverage_reference=a.reference(m.RUN/'museum-coverage-after-wave-76.csv'),added_institutions=new,existing_institution_changes=external,policy='External changes remain distinct from this campaign.'))
 io.write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
 for name in ['added-artworks','gac-date-enrichments']:io.write_csv(m.RUN/(name+'-'+label+'.csv'),io.read_csv(m.RUN/(name+'-after-wave-76.csv')))
 linked=io.read_csv(m.RUN/'reconciled-artworks-after-wave-76.csv')
 for v in p['holdings']:linked.append(dict(artwork_id=v['artwork_id'],institution_id=a.IID,source_url=v['facts']['source_url'],verified_existing_metadata_unchanged=True,confidence=v['decision']['confidence'],evidence_basis=v['decision']['basis'],source_limitation=v['decision']['limitation']))
 assert len(linked)==len({v['artwork_id'] for v in linked})==940;io.write_csv(m.RUN/('reconciled-artworks-'+label+'.csv'),linked)
 summary.update(at=m.now(),verified_new_artworks=10259,verified_existing_artworks_linked=940,after=live['summary'],verbania_holdings=verified,verbania_museum_changes=changes,unrelated_coverage_changes_since_prior_report=external,newly_observed_institutions=new,external_registry_growth_reference=a.reference(growth),global_coverage_snapshot_at=live['summary']['at'])
 summary['by_source'][a.KEY]=dict(new_artworks=0,existing_artworks_linked=155,institutions_expanded=1,newly_expanded_institutions=1,reviewed_objects=161,editorial_holds=6,qualified_dates_preserved=15,museum_changes=changes,plan_sha256=digest)
 summary['verification_components'] += [a.reference(m.RUN/'verification-after-wave-76.json'),a.reference(a.CHECKPOINT),a.reference(a.PLAN),a.reference(a.RUN/(a.KEY+'-applied.json'))]
 summary['institutions_with_new_records_or_reconciled_holdings']=sum(int(v['added_this_campaign'])+int(v['existing_artworks_linked_this_campaign'])>0 for v in coverage)
 for threshold in [100,200]:summary['museums_crossing_'+str(threshold)]=[dict(name=v['name'],before=int(v['works_before']),after=int(v['works'])) for v in coverage if v['kind']=='museum' and v['status']!='archived' and not v['canonical_institution_id'] and int(v['works_before'])<threshold<=int(v['works'])]
 assert sum(int(v['added_this_campaign']) for v in coverage)==sum(v['new_artworks'] for v in summary['by_source'].values())==10259;assert sum(int(v['existing_artworks_linked_this_campaign']) for v in coverage)==len(linked)==940
 summary['identity_reference_downloads_this_wave']=dict(selected_wikiart_jpeg=0,catalogue_image_attachments=0);summary['verification_method']='Wave77 accepts155 existing Verbania holdings from exact saved national catalogue records; zero new artworks. Exact source IDs, unique OA inventories, creator/title/date and museum/site/city reconciled. Private ownership retained separately from holding. Six date/version uncertainties held. Source context reconstructed from58 original response bodies; same-creator comparison context from20 bodies, including3 shared with target captures (75 distinct bodies overall). All3154 comparison records and11044 prior campaign artworks protected. Fourteen offline guard tests, atomic local transaction, exact readback and zero-write replay. No image, painter authority, date, publication or display changes. Goal active.'
 m.save(m.RUN/('verification-'+label+'.json'),summary);print(json.dumps(dict(campaign_new=10259,campaign_links=940,changes=changes,after=live['summary'],institutions_expanded=summary['institutions_with_new_records_or_reconciled_holdings'],external_changes=len(external),new_external_institutions=len(new))),flush=True)
if __name__=='__main__':main()
