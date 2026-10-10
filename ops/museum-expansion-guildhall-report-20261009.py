"""Wave86 coverage, separating local additions from unrelated catalogue changes."""
import copy,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-guildhall-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);m=a.m;io=a.module('io','museum-expansion-detroit-final-report-20261007.py')
def main():
 label='after-wave-86';assert not(m.RUN/('verification-'+label+'.json')).exists();p,digest=a.validate_plan();a.verify_baseline()
 with m.connect() as db:verified=a.verify(db,p,digest)
 live=m.load(m.RUN/(label+'.json'));summary=copy.deepcopy(m.load(m.RUN/'verification-after-wave-85.json'));coverage=io.read_csv(m.RUN/'museum-coverage-after-wave-85.csv');liveby={v['id']:v for v in live['institutions']};oldids={v['id'] for v in coverage};assert oldids<=set(liveby);new=[v for v in live['institutions'] if v['id'] not in oldids]
 for v in new:
  row={k:'' for k in coverage[0]};row.update(v);row.update(works_before=v['works'],eligible_before=v['eligible_works'],added_this_campaign=0,existing_artworks_linked_this_campaign=0,research_state='external_registry_addition_not_reviewed_by_this_campaign',native_source_probe_status='not_reviewed_by_this_campaign',coverage_baseline_label='first_observed_after_wave_86');coverage.append(row)
 changes=[];external=[]
 for row in coverage:
  v=liveby[row['id']]
  if row['id']==a.IID:
   old=p['before_counts'];assert int(row['works'])==old['linked'] and int(row['eligible_works'])==old['eligible'];assert v['works']==old['linked']+a.N and v['eligible_works']==old['eligible']+a.N;assert v['illustrated_works']==int(row['illustrated_works']) and v['pending_associations']==int(row['pending_associations'])
   changes.append(dict(institution_id=row['id'],name=row['name'],new=a.N,existing_linked=0,linked_before=old['linked'],linked_after=v['works'],eligible_before=old['eligible'],eligible_after=v['eligible_works']));row.update(added_this_campaign=int(row['added_this_campaign'])+a.N,research_state=row['research_state']+'; guildhall_22_selected_museum_published_additions',native_source_probe_status='museum_published_objects_and_physical_versions_reviewed',campaign_state='minimum_100_remaining_'+str(max(0,100-v['eligible_works'])))
  elif row['id'] in oldids:
   delta={k:dict(before=int(row[k]),after=v[k]) for k in ['works','eligible_works','illustrated_works','pending_associations'] if int(row[k])!=v[k]}
   if delta:external.append(dict(institution_id=row['id'],name=row['name'],changes=delta))
  for k,value in v.items():
   if k!='campaign_state':row[k]=value
 growth=a.RUN/'coverage-registry-growth-001.json';assert not growth.exists();m.save(growth,dict(at=m.now(),live_audit_reference=a.reference(m.RUN/(label+'.json')),previous_coverage_reference=a.reference(m.RUN/'museum-coverage-after-wave-85.csv'),added_institutions=new,existing_institution_changes=external,policy='External changes remain separate from this campaign.'));io.write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
 for name in ['reconciled-artworks','gac-date-enrichments']:io.write_csv(m.RUN/(name+'-'+label+'.csv'),io.read_csv(m.RUN/(name+'-after-wave-85.csv')))
 added=io.read_csv(m.RUN/'added-artworks-after-wave-85.csv');museum=liveby[a.IID]
 for v in p['records']:
  f=v['facts'];added.append(dict(artwork_id=v['artwork_id'],museum=museum['name'],museum_slug=museum['slug'],title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],accession=f['inventory'],source_url=f['source_url'],status='review'))
 assert len(added)==len({v['artwork_id'] for v in added})==10417;io.write_csv(m.RUN/('added-artworks-'+label+'.csv'),added)
 summary.update(at=m.now(),verified_new_artworks=10417,verified_existing_artworks_linked=2297,after=live['summary'],guildhall_additions=verified,guildhall_museum_changes=changes,unrelated_coverage_changes_since_prior_report=external,newly_observed_institutions=new,external_registry_growth_reference=a.reference(growth),global_coverage_snapshot_at=live['summary']['at'])
 summary['by_source'][a.KEY]=dict(new_artworks=a.N,existing_artworks_linked=0,institutions_expanded=1,newly_expanded_institutions=0,reviewed_objects=40,editorial_holds=17,already_catalogued=1,museum_changes=changes,plan_sha256=digest)
 summary['verification_components'] += [a.reference(m.RUN/'verification-after-wave-85.json'),a.reference(a.CHECKPOINT),a.reference(a.PLAN),a.reference(a.RUN/(a.KEY+'-applied.json'))];summary['institutions_with_new_records_or_reconciled_holdings']=sum(int(v['added_this_campaign'])+int(v['existing_artworks_linked_this_campaign'])>0 for v in coverage)
 for threshold in [100,200]:summary['museums_crossing_'+str(threshold)]=[dict(name=v['name'],before=int(v['works_before']),after=int(v['works'])) for v in coverage if v['kind']=='museum' and v['status']!='archived' and not v['canonical_institution_id'] and int(v['works_before'])<threshold<=int(v['works'])]
 assert sum(int(v['added_this_campaign']) for v in coverage)==sum(v['new_artworks'] for v in summary['by_source'].values())==10417;assert sum(int(v['existing_artworks_linked_this_campaign']) for v in coverage)==2297
 summary['identity_reference_downloads_this_wave']=dict(selected_wikiart_jpeg=0,catalogue_image_attachments=0);summary['verification_method']='Wave86 reviews40 selected Guildhall object leads;22 eligible artworks added in review,17 held,one Lavery already catalogued. Exact museum-published object pages,collection history and physical-version evidence. Clytemnestra1882 distinct from Worcester1914; full-size Constable sketch tied to explicit Guildhall lender credit,not publisher-based attribution. Fresh identity scope4362 artworks and8927 citations; all12692 prior campaign records preserved. Atomic readback and zero-write replay. Guildhall115linked/86eligible; all-museum minimum100/preferred200 goal remains active. No images,artist links,legacy metadata edits or current-display claims.'
 m.save(m.RUN/('verification-'+label+'.json'),summary);print(json.dumps(dict(campaign_new=10417,campaign_links=2297,changes=changes,after=live['summary'],institutions_expanded=summary['institutions_with_new_records_or_reconciled_holdings'],external_changes=len(external),new_external_institutions=len(new))),flush=True)
if __name__=='__main__':main()
