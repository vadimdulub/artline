"""Verified production delivery and complete bounded source-decision ledger."""
import csv,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-beziers-more-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);m=a.m;RUN=a.RUN
def main():
 p,digest=a.validate_plan();receipt=m.load(RUN/(a.KEY+'-applied.json'));checks=m.load(RUN/'checks-001.json');assert receipt['plan_sha256']==digest and checks['offline_tests_passed']==12 and checks['atomic_verification_passed'] and checks['replay_zero_writes']
 prior=m.load(m.RUN/'native/beziers-20261009/production-institution-register-001.json.gz');historical={v['id']:v for v in prior['rows']};nextcounts=m.load(RUN/'next-museum-production-counts-001.json');fresh={v['id']:v for v in nextcounts['rows']}
 with a.i.prod.connect() as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY');assert a.counts(db)=={a.IID:dict(linked=241,eligible=186)};register=db.execute('SELECT i.id::text,i.slug,i.name,i.kind,i.status,i.canonical_institution_id::text,i.website_url,p.name city,p.country_code FROM institutions i LEFT JOIN places p ON p.id=i.place_id ORDER BY i.id').fetchall()
 for v in register:
  old=historical.get(v['id'],{});current=receipt['verification']['current_counts'].get(v['id']) or fresh.get(v['id']);v.update(historical_local_linked_works=old.get('historical_local_linked_works'),historical_local_eligible_works=old.get('historical_local_eligible_works'),historical_local_count_at=old.get('historical_local_count_at'),verified_production_works=current.get('linked') if current else old.get('verified_production_works'),verified_production_eligible_works=current.get('eligible') if current else old.get('verified_production_eligible_works'),production_count_state='verified_this_pass' if current else 'inherited_previous_pass' if old.get('verified_production_works') is not None else 'not_refreshed_this_pass',production_count_at=receipt['at'] if v['id']==a.IID else nextcounts['at'] if current else prior['at'] if old.get('verified_production_works') is not None else None)
 m.save(RUN/'production-institution-register-001.json.gz',dict(at=m.now(),rows=register,read_only=True,global_counts_refreshed=False,prior_register=a.reference(m.RUN/'native/beziers-20261009/production-institution-register-001.json.gz')))
 with (RUN/'production-institution-register-001.csv').open('x',newline='') as fp:w=csv.DictWriter(fp,fieldnames=list(register[0]));w.writeheader();w.writerows(register)
 with (RUN/'added-production-artworks-001.csv').open('x',newline='') as fp:
  w=csv.DictWriter(fp,fieldnames=['artwork_id','institution_id','source_id','title','creator_label','date_display','creation_year_start','creation_year_end','date_precision','date_scope','work_type','inventory','source_url','status']);w.writeheader()
  for v in p['records']:
   f=v['facts'];w.writerow(dict(artwork_id=v['artwork_id'],institution_id=a.IID,source_id=f['source_id'],title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],date_scope='eligible' if f['last'] is not None and f['last']<=1970 else 'review',work_type=f['work_type'],inventory=f['inventory'],source_url=f['source_url'],status='review'))
 decisions={d['source_id']:d for d in m.load(a.REVIEW)['decisions']};facts=m.load(RUN/'candidate-facts-001.json.gz');held={v['source_id']:v for v in facts['held']};source=m.load(RUN/'joconde-selected-001.json.gz');assert len(decisions)+len(held)==len(source['rows'])==100 and not facts['existing'] and not source['overlap_previous_ids']
 with (RUN/'all-source-decisions-001.csv').open('x',newline='') as fp:
  w=csv.DictWriter(fp,fieldnames=['source_id','title','inventory','state','reason','source_url']);w.writeheader()
  for v in source['rows']:
   rid=v['Reference'];d=decisions.get(rid);w.writerow(dict(source_id=rid,title=v['Titre'],inventory=v['Numero_inventaire'],state=d['state'] if d else 'source_fact_or_scope_hold',reason=d['basis'] if d else held[rid]['reason'],source_url='https://pop.culture.gouv.fr/notice/joconde/'+rid))
 report=dict(at=m.now(),goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=68,existing_links=0,date_eligible_added=50,after_date_added=18,reviewed_source_records=100,cumulative_distinct_beziers_sources=585,already_catalogued=0,source_fact_or_scope_holds=30,editorial_holds=2,verification=receipt['verification'],museum_before=dict(works=173,eligible_works=136),museum_after=dict(works=241,eligible_works=186),production_campaign_new_artworks=206,production_campaign_museums=2,historical_local_totals_unchanged=dict(new_artworks=11018,existing_links=3036),cross_database_totals_combined=False,production_canonical_museums=sum(v['kind']=='museum' and v['status']!='archived' and not v['canonical_institution_id'] for v in register),global_production_counts_refreshed=False,remaining_finearts_records_not_fetched=335,remaining_finearts_page=source['finearts_next'],source_access='National public tabular API accessible. POP pages were unavailable in web reader, not a confirmed HTTP provider denial; no new provider access hold. Prior provider holds retained.',preserved_queues_checkpoint=a.reference(a.CHECKPOINT),next_museum_queue=a.reference(RUN/'next-museum-production-counts-001.json'))
 m.save(RUN/'delivery-001.json',report)
 text='''# Béziers additional drawings — production expansion, 9 October 2026

Added **68 production artworks in review**, taking the Musée des Beaux-Arts de Béziers from **173 to 241 linked artworks**. The count with creation dates within scope rose from **136 to 186**. These are original Jean Moulin / Romanin drawings: 50 have eligible dates and 18 retain open “after” dates. The real local database remains unchanged at 85 linked / 84 date-eligible works.

- [68 delivered artworks](added-production-artworks-001.csv)
- [All 100 source decisions](all-source-decisions-001.csv)
- [Production institution register](production-institution-register-001.csv)
- [Verification and remaining research](delivery-001.json)
- [Reviewed object identities](editorial-reviewed-001.json.gz)

The [Ministry of Culture's museum record M0467](https://pop.culture.gouv.fr/notice/museo/M0467) and [Béziers municipal collection page](https://www.ville-beziers.fr/culture/musee-fayet) identify the collection. Metadata comes from the national Joconde catalogue's public tabular API. All delivered records carry their individual POP source URL and literal source evidence. Holdings do not establish current display, custody or ownership.

This bounded continuation reviewed Fine Arts positions 201–300, without overlap with the earlier 485 researched records. The cumulative source ledger therefore covers 585 distinct notices. Thirty source/group holds and two additional editorial holds remain on this page; prior holds are unchanged. Another 335 Fine Arts records remain unrequested. Directory coverage is not complete artwork coverage.

Two notices explicitly describe the upper and lower parts of one rejoined sheet; both remain held until their physical identity can be reconciled as one object. Two crowd drawings with identical titles, dimensions and descriptive fields are also held. Sketchbooks and detached sketchbook pages require parent/component reconciliation. Multi-figure drawings and recto/verso sheets count once. The folded refugee document is one independently inventoried sheet, not 35 artworks.

The Montparnasse scenes retain distinct inventories, dimensions and compositions. A recorded “vers 1931” inscription preserves an approximate date; another work retains the questioned lower endpoint of “1925 (?)-1939.” Creation in 1932 is kept separate from the depicted 1900 costumes. Open dates were not shortened using the creator's lifespan, a broad period or the 1975 acquisition date.

Twelve offline policy checks passed. Cloud SQL backup 1791547275836 completed before the atomic insert and readback. A second application verified the same result with zero writes. All 234 existing comparator/museum records and all 138 earlier production additions were preserved. No image attachments, artist-authority links, publication changes or current-display claims were made.

Béziers now exceeds the 200-artwork catalogue target, with 186 works whose dates are within scope. The selected production phase has delivered 206 new artworks across Béziers and Girodet; historical local-only totals remain separate. Eight other museum leads have fresh scoped production counts in the queue. Global production counts remain unrefreshed after prior timeouts; no blanket count was retried. Prior provider holds, archival pins and research queues remain active, and the overall museum goal is unfinished.
'''
 dest=RUN/'README.md';assert not dest.exists();dest.write_text(text);print(json.dumps(dict(added=68,after=241,eligible=186,production_new_total=206,canonical_museums=report['production_canonical_museums'])),flush=True)
if __name__=='__main__':main()
