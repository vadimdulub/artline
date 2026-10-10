#!/usr/bin/env python3
"""Wave52: frozen historical verification plus a freshly verified explicit delta."""
import argparse,copy,csv,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-detroit-final-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m
def read_csv(path):
 with path.open(newline='') as fp:return list(csv.DictReader(fp))
def write_csv(path,rows):
 assert rows and not path.exists()
 with path.open('x',newline='') as fp:
  w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def report(label):
 assert not (m.RUN/('verification-'+label+'.json')).exists();plan,digest=a.validate_plan();receipt=m.load(a.RUN/(a.KEY+'-applied.json'));assert receipt['plan_sha256']==digest
 a.verify_baseline()
 with m.connect() as db:verified=a.verify(db,plan,digest)
 m.audit(label);live=m.load(m.RUN/(label+'.json'));prior=m.load(m.RUN/'verification-after-wave-51.json');summary=copy.deepcopy(prior)
 coverage=read_csv(m.RUN/'museum-coverage-after-wave-51.csv');liveby={r['id']:r for r in live['institutions']};assert set(liveby)=={r['id'] for r in coverage}
 external=[]
 for row in coverage:
  current=liveby[row['id']]
  if row['id']!=a.IID:
   changes={k:dict(before=int(row[k]),after=current[k]) for k in ['works','eligible_works','illustrated_works','pending_associations'] if int(row[k])!=current[k]}
   if changes:external.append(dict(institution_id=row['id'],changes=changes))
  for k,v in current.items():
   if k!='campaign_state':row[k]=v
 detroit=next(r for r in coverage if r['id']==a.IID);assert (detroit['works'],detroit['eligible_works'],detroit['pending_associations'])==(100,100,15)
 detroit.update(added_this_campaign='98',existing_artworks_linked_this_campaign='2',research_state='native_selection_reviewed_minimum_100_met',native_source_probe_status='117_complete_objects_one_timeout_held_no_retry',campaign_state='minimum_100_met_preferred_200_requires_more_research')
 write_csv(m.RUN/('museum-coverage-'+label+'.csv'),coverage)
 added=read_csv(m.RUN/'added-artworks-after-wave-51.csv')
 for r in plan['records']:
  v=r['facts'];added.append(dict(artwork_id=r['artwork_id'],museum='Detroit Institute of Arts',museum_slug='museum-authority-q1201549',title=v['title'],creator_label=v['creator_label'],date_display=v['date_display'],creation_year_start=v['first'],creation_year_end=v['last'],accession=v['inventory'],source_url=v['source_url'],status='review'))
 assert len(added)==len({r['artwork_id'] for r in added})==5426
 write_csv(m.RUN/('added-artworks-'+label+'.csv'),sorted(added,key=lambda r:(r['museum'],r['title'])))
 reconciled=read_csv(m.RUN/'reconciled-artworks-after-wave-51.csv');hs=[]
 for r in plan['holdings']:
  h=dict(artwork_id=r['artwork_id'],institution_id=a.IID,source_url=r['facts']['source_url'],verified_existing_metadata_unchanged=True,confidence=r['decision']['confidence'],evidence_basis=r['decision']['basis'],source_limitation=r['decision']['limitation']);hs.append(h);reconciled.append(h)
 assert len(reconciled)==len({r['artwork_id'] for r in reconciled})==767
 write_csv(m.RUN/('reconciled-artworks-'+label+'.csv'),reconciled)
 write_csv(m.RUN/('gac-date-enrichments-'+label+'.csv'),read_csv(m.RUN/'gac-date-enrichments-after-wave-51.csv'))
 summary.update(at=m.now(),verified_new_artworks=5426,verified_existing_artworks_linked=767,after=live['summary'],detroit_minimum_100=verified,unrelated_coverage_changes_since_prior_report=external)
 summary['existing_holding_verifications']+=hs
 summary['by_source'][a.KEY]=dict(new_artworks=92,existing_artworks_linked=2,institutions_expanded=0,previously_expanded_institution_continuation=True,captured_followup_reviewed=112,captured_holds=18,uncaptured_holds=1,linked_records=100,eligible_records=100,remaining_to_200=100,plan_sha256=digest)
 summary['verification_components'] += [a.reference(m.RUN/'verification-after-wave-51.json'),a.reference(a.CHECKPOINT),a.reference(a.PLAN),a.reference(a.RUN/(a.KEY+'-applied.json'))]
 summary['verification_method']='Wave51 full historical verification remains immutable and source-pinned. Wave52 checks the exact allowed holding delta and all new records, with fresh content digests proving all6099 prior campaign artwork rows and associated artist/media/identifier/citation/assertion rows unchanged from the immediate preflight. Historical total-count assertions are not rerun with new totals or silently weakened. Global museum coverage is a fresh read-only audit.'
 for threshold in [100,200]:summary['museums_crossing_'+str(threshold)]=[dict(name=r['name'],before=int(r['works_before']),after=int(r['works'])) for r in coverage if r['kind']=='museum' and r['status']!='archived' and not r['canonical_institution_id'] and int(r['works_before'])<threshold<=int(r['works'])]
 assert sum(int(r['added_this_campaign']) for r in coverage)==sum(x['new_artworks'] for x in summary['by_source'].values())==5426
 assert sum(int(r['existing_artworks_linked_this_campaign']) for r in coverage)==767
 summary['identity_reference_downloads_this_wave']=dict(selected_wikiart_jpeg=1,selected_primary_educational_pdf=1,catalogue_image_attachments=0)
 m.save(m.RUN/('verification-'+label+'.json'),summary)
 print(json.dumps({k:summary[k] for k in ['verified_new_artworks','verified_existing_artworks_linked','institutions_with_new_records_or_reconciled_holdings','source_pass_museums','source_pass_institutions','after','unrelated_coverage_changes_since_prior_report']}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--label',default='after-wave-52');report(p.parse_args().label)
