"""Wave91 Imperial War Museums counts preserve unknown dates and other campaign totals."""
import collections,copy,csv,importlib.util,json,types
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-iwm-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);m=a.m
def read_csv(path):
 with path.open(newline='') as fp:return list(csv.DictReader(fp))
def write_csv(path,rows):
 assert rows and not path.exists()
 with path.open('x',newline='') as fp:
  w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
io=types.SimpleNamespace(read_csv=read_csv,write_csv=write_csv)

def main():
 label='after-wave-91';assert not(m.RUN/('verification-'+label+'.json')).exists();p,digest=a.validate_plan();a.verify_baseline()
 with m.connect() as db:verified=a.verify(db,p,digest)
 live=m.load(m.RUN/(label+'.json'));summary=copy.deepcopy(m.load(m.RUN/'verification-after-wave-90.json'));coverage=io.read_csv(m.RUN/'museum-coverage-after-wave-90.csv');liveby={v['id']:v for v in live['institutions']};oldids={v['id'] for v in coverage};assert oldids<=set(liveby);new=[v for v in live['institutions'] if v['id'] not in oldids];changes=[];external=[];newly=0
 for v in new:
  row={k:'' for k in coverage[0]};row.update(v);row.update(works_before=v['works'],eligible_before=v['eligible_works'],added_this_campaign=0,existing_artworks_linked_this_campaign=0,research_state='external_registry_addition_not_reviewed_by_this_campaign',native_source_probe_status='not_reviewed_by_this_campaign',coverage_baseline_label='first_observed_after_wave_91');coverage.append(row)
 for row in coverage:
  v=liveby[row['id']];holds=[h for h in p['holdings'] if h['institution_id']==row['id']]
  if row['id'] in a.IIDS:
   old=p['before_counts'][row['id']];assert int(row['works'])==old['linked'] and int(row['eligible_works'])==old['eligible'];assert v['works']==old['linked']+len(holds) and v['eligible_works']==old['eligible']+sum(h['facts']['date_precision']!='unknown' for h in holds);picked={h['artwork_id'] for h in holds};assert v['illustrated_works']==int(row['illustrated_works'])+sum(bool(art['primary_media_id']) for art in p['before']['artworks'] if art['id'] in picked);pending={h['artwork_id'] for h in holds if h['decision']['supersede_assertion_ids']};assert v['pending_associations']==int(row['pending_associations'])-len(pending)
   if holds:
    newly+=int(int(row['added_this_campaign'])+int(row['existing_artworks_linked_this_campaign'])==0);changes.append(dict(institution_id=row['id'],name=row['name'],new=0,existing_linked=len(holds),linked_before=old['linked'],linked_after=v['works'],eligible_before=old['eligible'],eligible_after=v['eligible_works']));row.update(existing_artworks_linked_this_campaign=int(row['existing_artworks_linked_this_campaign'])+len(holds),research_state=row['research_state']+'; iwm_network_object_and_version_review',native_source_probe_status='retained_primary_and_referenced_secondary_evidence_reviewed_iwm403_hold')
  elif row['id'] in oldids:
   delta={k:dict(before=int(row[k]),after=v[k]) for k in ['works','eligible_works','illustrated_works','pending_associations'] if int(row[k])!=v[k]}
   if delta:external.append(dict(institution_id=row['id'],name=row['name'],changes=delta))
  row.update(v)
 growth=a.RUN/'coverage-registry-growth-001.json';m.save(growth,dict(at=m.now(),live_audit_reference=a.reference(m.RUN/(label+'.json')),previous_coverage_reference=a.reference(m.RUN/'museum-coverage-after-wave-90.csv'),added_institutions=new,existing_institution_changes=external,policy='External changes separate from campaign.'));io.write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
 for name in ['added-artworks','gac-date-enrichments']:io.write_csv(m.RUN/(name+'-'+label+'.csv'),io.read_csv(m.RUN/(name+'-after-wave-90.csv')))
 linked=io.read_csv(m.RUN/'reconciled-artworks-after-wave-90.csv')
 for v in p['holdings']:linked.append(dict(artwork_id=v['artwork_id'],institution_id=v['institution_id'],source_url=v['facts']['source_url'],verified_existing_metadata_unchanged=True,confidence=v['decision']['confidence'],evidence_basis=v['decision']['basis'],source_limitation=v['decision']['limitation']))
 assert len(linked)==len({v['artwork_id'] for v in linked})==2726;io.write_csv(m.RUN/('reconciled-artworks-'+label+'.csv'),linked);summary.update(at=m.now(),verified_new_artworks=10472,verified_existing_artworks_linked=2726,after=live['summary'],iwm_holdings=verified,iwm_museum_changes=changes,unrelated_coverage_changes_since_prior_report=external,newly_observed_institutions=new,external_registry_growth_reference=a.reference(growth),global_coverage_snapshot_at=live['summary']['at']);summary['by_source'][a.KEY]=dict(new_artworks=0,existing_artworks_linked=99,institutions_expanded=1,newly_expanded_institutions=newly,reviewed_objects=103,editorial_holds=4,existing_network_holdings_preserved=34,existing_london_holdings_preserved=13,unresolved_london_assertions_preserved=88,museum_changes=changes,plan_sha256=digest);summary['verification_components']+=[a.reference(m.RUN/'verification-after-wave-90.json'),a.reference(a.CHECKPOINT),a.reference(a.PLAN),a.reference(a.RUN/(a.KEY+'-applied.json'))];summary['institutions_with_new_records_or_reconciled_holdings']=sum(int(v['added_this_campaign'])+int(v['existing_artworks_linked_this_campaign'])>0 for v in coverage)
 for threshold in [100,200]:summary['museums_crossing_'+str(threshold)]=[dict(name=v['name'],before=int(v['works_before']),after=int(v['works'])) for v in coverage if v['kind']=='museum' and v['status']!='archived' and not v['canonical_institution_id'] and int(v['works_before'])<threshold<=int(v['works'])]
 assert sum(int(v['added_this_campaign']) for v in coverage)==sum(v['new_artworks'] for v in summary['by_source'].values())==10472;assert sum(int(v['existing_artworks_linked_this_campaign']) for v in coverage)==2726;summary['identity_reference_downloads_this_wave']=dict(selected_images=0,selected_source_pdfs=0,catalogue_image_attachments=0);summary['verification_method']='Wave91 reviews103 exact IWM objects and links99 existing artworks to the wider network:96 date-eligible and3unknown.15 retained native pages,referenced secondary object statements,fresh maker authorities and selected Commons descriptions support object identities.13 existing London and34 network holdings preserved. Four physical-version holds; all88 unresolved London-specific claims unchanged.15 same-network pending assertions superseded.96 raw bodies verified; fresh identity5500 artworks/11914 citations. IWM403 stops provider; no source hold bypass or images. Dates,attributions,creator links,images,status and descriptive metadata preserved. Full goal active.';m.save(m.RUN/('verification-'+label+'.json'),summary);print(json.dumps(dict(campaign_new=10472,campaign_links=2726,changes=changes,after=live['summary'],institutions_expanded=summary['institutions_with_new_records_or_reconciled_holdings'],newly_expanded=newly,external_changes=len(external))),flush=True)
if __name__=='__main__':main()
