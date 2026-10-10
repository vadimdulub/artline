"""Wave82 verified coverage and separate external catalogue changes."""
import collections,copy,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-britain-five-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);m=a.m;io=a.module('io','museum-expansion-detroit-final-report-20261007.py')
def main():
 label='after-wave-82';assert not (m.RUN/('verification-'+label+'.json')).exists();p,digest=a.validate_plan();a.verify_baseline()
 with m.connect() as db:verified=a.verify(db,p,digest)
 live=m.load(m.RUN/(label+'.json'));summary=copy.deepcopy(m.load(m.RUN/'verification-after-wave-81.json'));coverage=io.read_csv(m.RUN/'museum-coverage-after-wave-81.csv');liveby={v['id']:v for v in live['institutions']};oldids={v['id'] for v in coverage};assert oldids<=set(liveby);new=[v for v in live['institutions'] if v['id'] not in oldids]
 for v in new:
  row={k:'' for k in coverage[0]};row.update(v);row.update(works_before=v['works'],eligible_before=v['eligible_works'],added_this_campaign=0,existing_artworks_linked_this_campaign=0,research_state='external_registry_addition_not_reviewed_by_this_campaign',native_source_probe_status='not_reviewed_by_this_campaign',coverage_baseline_label='first_observed_after_wave_82');coverage.append(row)
 changes=[];external=[]
 for row in coverage:
  v=liveby[row['id']]
  if row['id'] in a.IIDS:
   picked=[h for h in p['holdings'] if h['institution_id']==row['id']];count=len(picked);eligible=sum(h['facts']['date_precision']!='unknown' for h in picked);old=p['before_counts'][row['id']];assert int(row['works'])==old['linked'] and int(row['eligible_works'])==old['eligible'];assert v['works']==old['linked']+count and v['eligible_works']==old['eligible']+eligible
   picked_ids={h['artwork_id'] for h in picked};previously_illustrated=sum(bool(art['primary_media_id']) for art in p['before']['artworks'] if art['id'] in picked_ids);assert v['illustrated_works']==int(row['illustrated_works'])+previously_illustrated and v['pending_associations']==int(row['pending_associations'])-count
   changes.append(dict(institution_id=row['id'],name=row['name'],new=0,existing_linked=count,linked_before=old['linked'],linked_after=v['works'],eligible_before=old['eligible'],eligible_after=v['eligible_works']));row.update(existing_artworks_linked_this_campaign=int(row['existing_artworks_linked_this_campaign'])+count,research_state=row['research_state']+'; britain_five_'+str(count)+'_existing_holdings_accepted',native_source_probe_status='saved_referenced_wikidata_and_selected_native_evidence_reviewed',campaign_state=('minimum_100_met_eligible_'+str(v['eligible_works'])+'_preferred_200_remaining') if v['eligible_works']>=100 else ('minimum_100_remaining_'+str(100-v['eligible_works'])))
  elif row['id']==a.s.NETWORK:
   refinements=[h for h in p['holdings'] if h['decision']['previous_network_assertion_id']];assert v['works']==int(row['works'])-len(refinements) and v['eligible_works']==int(row['eligible_works'])-sum(h['facts']['date_precision']!='unknown' for h in refinements)
   row.update(research_state=row['research_state']+'; supported_perth_branch_refinements_history_preserved');changes.append(dict(institution_id=row['id'],name=row['name'],new=0,existing_linked=0,branch_refinements_out=len(refinements),linked_before=int(row['works']),linked_after=v['works'],eligible_before=int(row['eligible_works']),eligible_after=v['eligible_works']))
  elif row['id'] in oldids:
   delta={k:dict(before=int(row[k]),after=v[k]) for k in ['works','eligible_works','illustrated_works','pending_associations'] if int(row[k])!=v[k]}
   if delta:external.append(dict(institution_id=row['id'],name=row['name'],changes=delta))
  for k,value in v.items():
   if k!='campaign_state':row[k]=value
 growth=a.RUN/'coverage-registry-growth-001.json';assert not growth.exists();m.save(growth,dict(at=m.now(),live_audit_reference=a.reference(m.RUN/(label+'.json')),previous_coverage_reference=a.reference(m.RUN/'museum-coverage-after-wave-81.csv'),added_institutions=new,existing_institution_changes=external,policy='External changes remain distinct from this campaign.'))
 io.write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
 for name in ['added-artworks','gac-date-enrichments']:io.write_csv(m.RUN/(name+'-'+label+'.csv'),io.read_csv(m.RUN/(name+'-after-wave-81.csv')))
 linked=io.read_csv(m.RUN/'reconciled-artworks-after-wave-81.csv')
 for v in p['holdings']:linked.append(dict(artwork_id=v['artwork_id'],institution_id=v['institution_id'],source_url=v['facts']['source_url'],verified_existing_metadata_unchanged=True,confidence=v['decision']['confidence'],evidence_basis=v['decision']['basis'],source_limitation=v['decision']['limitation']))
 assert len(linked)==len({v['artwork_id'] for v in linked})==1668+a.HCOUNT;io.write_csv(m.RUN/('reconciled-artworks-'+label+'.csv'),linked)
 summary.update(at=m.now(),verified_new_artworks=10259,verified_existing_artworks_linked=1668+a.HCOUNT,after=live['summary'],britain_five_holdings=verified,britain_five_museum_changes=changes,unrelated_coverage_changes_since_prior_report=external,newly_observed_institutions=new,external_registry_growth_reference=a.reference(growth),global_coverage_snapshot_at=live['summary']['at'])
 summary['by_source'][a.KEY]=dict(new_artworks=0,existing_artworks_linked=a.HCOUNT,previously_unlinked=verified['previously_unlinked'],network_to_branch_refinements=verified['network_to_branch_refinements'],institutions_expanded=2,newly_expanded_institutions=2,reviewed_objects=244,editorial_holds=244-a.HCOUNT,unknown_dates_preserved=verified['unknown_date_records_preserved'],museum_changes=changes,plan_sha256=digest)
 summary['verification_components'] += [a.reference(m.RUN/'verification-after-wave-81.json'),a.reference(a.CHECKPOINT),a.reference(a.PLAN),a.reference(a.RUN/(a.KEY+'-applied.json'))]
 summary['institutions_with_new_records_or_reconciled_holdings']=sum(int(v['added_this_campaign'])+int(v['existing_artworks_linked_this_campaign'])>0 for v in coverage)
 for threshold in [100,200]:summary['museums_crossing_'+str(threshold)]=[dict(name=v['name'],before=int(v['works_before']),after=int(v['works'])) for v in coverage if v['kind']=='museum' and v['status']!='archived' and not v['canonical_institution_id'] and int(v['works_before'])<threshold<=int(v['works'])]
 assert sum(int(v['added_this_campaign']) for v in coverage)==sum(v['new_artworks'] for v in summary['by_source'].values())==10259;assert sum(int(v['existing_artworks_linked_this_campaign']) for v in coverage)==len(linked)==1668+a.HCOUNT
 summary['identity_reference_downloads_this_wave']=dict(selected_wikiart_jpeg=0,catalogue_image_attachments=0);summary['verification_method']='Wave82 reviews244 Williamson/Perth pending associations using exact saved objects,creator authorities,museum-scoped inventory,native metadata and physical-version comparisons. Williamson native pages and retained museum-supplied MDS objects corroborate explicit facts. CPK-to-Perth branch refinements are identified editorial inferences from exact fine-art objects,the official2023 gallery transition including Fergusson Collection,and specific referenced branch claims. Original network history and other review assertions remain. Undated works,qualified/conflicting makers,modern dates,source conflations and unresolved physical versions remain explicit. Atomic local readback and zero-write replay preserve metadata,images,creator links,status and prior campaign artworks. No new artwork or display claim. Both museum targets and all-museum goal remain active toward200.'


 m.save(m.RUN/('verification-'+label+'.json'),summary);print(json.dumps(dict(campaign_new=10259,campaign_links=1668+a.HCOUNT,changes=changes,after=live['summary'],institutions_expanded=summary['institutions_with_new_records_or_reconciled_holdings'],external_changes=len(external),new_external_institutions=len(new))),flush=True)
if __name__=='__main__':main()
