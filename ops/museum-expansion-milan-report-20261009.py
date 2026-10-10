"""Wave80 verified coverage and separate external catalogue changes."""
import collections,copy,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-milan-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);m=a.m;io=a.module('io','museum-expansion-detroit-final-report-20261007.py')
def main():
 label='after-wave-80';assert not (m.RUN/('verification-'+label+'.json')).exists();p,digest=a.validate_plan();a.verify_baseline()
 with m.connect() as db:verified=a.verify(db,p,digest)
 live=m.load(m.RUN/(label+'.json'));summary=copy.deepcopy(m.load(m.RUN/'verification-after-wave-79.json'));coverage=io.read_csv(m.RUN/'museum-coverage-after-wave-79.csv');liveby={v['id']:v for v in live['institutions']};oldids={v['id'] for v in coverage};assert oldids<=set(liveby);new=[v for v in live['institutions'] if v['id'] not in oldids]
 for v in new:
  row={k:'' for k in coverage[0]};row.update(v);row.update(works_before=v['works'],eligible_before=v['eligible_works'],added_this_campaign=0,existing_artworks_linked_this_campaign=0,research_state='external_registry_addition_not_reviewed_by_this_campaign',native_source_probe_status='not_reviewed_by_this_campaign',coverage_baseline_label='first_observed_after_wave_80');coverage.append(row)
 changes=[];external=[]
 for row in coverage:
  v=liveby[row['id']]
  if row['id']==a.IID:
   assert int(row['works'])==int(row['eligible_works'])==25 and v['works']==147 and v['eligible_works']==87;assert v['illustrated_works']==int(row['illustrated_works']) and v['pending_associations']==int(row['pending_associations'])-122
   changes.append(dict(institution_id=a.IID,name=row['name'],new=0,existing_linked=122,linked_before=25,linked_after=147,eligible_before=25,eligible_after=87));row.update(existing_artworks_linked_this_campaign=int(row['existing_artworks_linked_this_campaign'])+122,research_state=row['research_state']+'; milan_122_existing_holdings_accepted_29_held',native_source_probe_status='saved_official_object_evidence_verified',campaign_state='minimum_100_linked_met_eligible_87_needs_13_preferred_200_remaining')
  elif row['id'] in oldids:
   delta={k:dict(before=int(row[k]),after=v[k]) for k in ['works','eligible_works','illustrated_works','pending_associations'] if int(row[k])!=v[k]}
   if delta:external.append(dict(institution_id=row['id'],name=row['name'],changes=delta))
  for k,value in v.items():
   if k!='campaign_state':row[k]=value
 growth=a.RUN/'coverage-registry-growth-001.json';assert not growth.exists();m.save(growth,dict(at=m.now(),live_audit_reference=a.reference(m.RUN/(label+'.json')),previous_coverage_reference=a.reference(m.RUN/'museum-coverage-after-wave-79.csv'),added_institutions=new,existing_institution_changes=external,policy='External changes remain distinct from this campaign.'))
 io.write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
 for name in ['added-artworks','gac-date-enrichments']:io.write_csv(m.RUN/(name+'-'+label+'.csv'),io.read_csv(m.RUN/(name+'-after-wave-79.csv')))
 linked=io.read_csv(m.RUN/'reconciled-artworks-after-wave-79.csv')
 for v in p['holdings']:linked.append(dict(artwork_id=v['artwork_id'],institution_id=a.IID,source_url=v['facts']['source_url'],verified_existing_metadata_unchanged=True,confidence=v['decision']['confidence'],evidence_basis=v['decision']['basis'],source_limitation=v['decision']['limitation']))
 assert len(linked)==len({v['artwork_id'] for v in linked})==1450;io.write_csv(m.RUN/('reconciled-artworks-'+label+'.csv'),linked)
 summary.update(at=m.now(),verified_new_artworks=10259,verified_existing_artworks_linked=1450,after=live['summary'],milan_holdings=verified,milan_museum_changes=changes,unrelated_coverage_changes_since_prior_report=external,newly_observed_institutions=new,external_registry_growth_reference=a.reference(growth),global_coverage_snapshot_at=live['summary']['at'])
 summary['by_source'][a.KEY]=dict(new_artworks=0,existing_artworks_linked=122,institutions_expanded=1,newly_expanded_institutions=1,reviewed_objects=151,editorial_holds=29,qualified_dates_preserved=60,museum_changes=changes,plan_sha256=digest)
 summary['verification_components'] += [a.reference(m.RUN/'verification-after-wave-79.json'),a.reference(a.CHECKPOINT),a.reference(a.PLAN),a.reference(a.RUN/(a.KEY+'-applied.json'))]
 summary['institutions_with_new_records_or_reconciled_holdings']=sum(int(v['added_this_campaign'])+int(v['existing_artworks_linked_this_campaign'])>0 for v in coverage)
 for threshold in [100,200]:summary['museums_crossing_'+str(threshold)]=[dict(name=v['name'],before=int(v['works_before']),after=int(v['works'])) for v in coverage if v['kind']=='museum' and v['status']!='archived' and not v['canonical_institution_id'] and int(v['works_before'])<threshold<=int(v['works'])]
 assert sum(int(v['added_this_campaign']) for v in coverage)==sum(v['new_artworks'] for v in summary['by_source'].values())==10259;assert sum(int(v['existing_artworks_linked_this_campaign']) for v in coverage)==len(linked)==1450
 summary['identity_reference_downloads_this_wave']=dict(selected_wikiart_jpeg=0,catalogue_image_attachments=0);summary['verification_method']='Wave80 accepts122 existing Milan holdings from exact saved national records and151 matched native museum objects. All151 claims reviewed:23 probable duplicate records already represented in the museum and6 unresolved versions retained. Each selected object has a distinct native IGB inventory; component paintings count individually, ensemble parents excluded. Native and original descriptions, titles, creator names and dates reconciled, including three comparison-only typo normalizations and one explicitly preserved Inganni date/clothing discrepancy.60 unknown dates remain unchanged. Atomic local transaction protects5545 scoped records and11587 prior campaign artworks.18 offline guards, exact readback and zero-write replay. No new artworks, images, painter links, catalogue dates, status changes or display claims. Milan147linked/87eligible still needs13 eligible dates or additional works for100eligible, and more for preferred200. Broader all-museum goal active.'
 m.save(m.RUN/('verification-'+label+'.json'),summary);print(json.dumps(dict(campaign_new=10259,campaign_links=1450,changes=changes,after=live['summary'],institutions_expanded=summary['institutions_with_new_records_or_reconciled_holdings'],external_changes=len(external),new_external_institutions=len(new))),flush=True)
if __name__=='__main__':main()
