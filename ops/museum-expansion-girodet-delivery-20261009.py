"""Separate production delivery from the historical local-only museum campaign."""
import csv,hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-girodet-apply-v3-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);m=a.m;RUN=a.RUN
def main():
 p,digest=a.validate_plan();receipt=m.load(RUN/(a.KEY+'-applied.json'));assert receipt['plan_sha256']==digest
 checks=m.load(RUN/'checks-001.json');assert checks['offline_tests_passed']==12 and checks['atomic_verification_passed'] and checks['replay_zero_writes']
 base=m.load(RUN/'production-initial-scope-001.json.gz');mu=base['snapshot']['museums'][0];b=dict(id=a.IID,name=mu['name'],works=89,eligible_works=82,illustrated_works=sum(v['primary_media_id'] is not None for v in base['snapshot']['artworks']));c=dict(b,works=139,eligible_works=113);assert receipt['verification']['current_counts'][a.IID]==dict(linked=139,eligible=113);register=m.load(RUN/'production-institution-register-001.json.gz')

 fields=['artwork_id','institution_id','museum','source_id','title','creator_label','date_display','creation_year_start','creation_year_end','date_precision','date_scope','work_type','inventory','source_url','review_status']
 with (RUN/'added-production-artworks-001.csv').open('x',newline='') as fp:
  w=csv.DictWriter(fp,fieldnames=fields);w.writeheader()
  for v in p['records']:
   f=v['facts'];w.writerow(dict(artwork_id=v['artwork_id'],institution_id=a.IID,museum=c['name'],source_id=f['source_id'],title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],date_scope='eligible' if f['last'] is not None and f['last']<=1970 else 'unknown' if f['last'] is None else 'crossing_1970_review',work_type=f['work_type'],inventory=f['inventory'],source_url=f['source_url'],review_status='review'))
 decisions={d['source_id']:d for d in m.load(a.REVIEW)['decisions']};facts=m.load(RUN/'candidate-facts-001.json.gz');held={v['source_id']:v for v in facts['held']};source=m.load(RUN/'joconde-current-003.json.gz')['rows'];assert len(source)==205 and len(decisions)+len(held)==205
 with (RUN/'all-source-decisions-001.csv').open('x',newline='') as fp:
  w=csv.DictWriter(fp,fieldnames=['source_id','title','inventory','state','reason','source_url']);w.writeheader()
  for v in sorted(source,key=lambda v:v['Reference']):
   rid=v['Reference'];d=decisions.get(rid);w.writerow(dict(source_id=rid,title=v['Titre'],inventory=v['Numero_inventaire'],state=d['state'] if d else 'source_fact_or_scope_hold',reason=d['basis'] if d else held[rid]['reason'],source_url='https://pop.culture.gouv.fr/notice/joconde/'+rid))
 report=dict(at=m.now(),goal_complete=False,production_only=True,local_unchanged=True,plan_sha256=digest,added=50,existing_links=0,date_eligible_added=31,unknown_date_added=11,crossing1970_added=8,reviewed_source_records=205,already_catalogued=84,editorial_holds=4,source_fact_or_scope_holds=67,verification=receipt['verification'],museum_before=b,museum_after=c,production_institution_register=a.reference(RUN/'production-institution-register-001.json.gz'),global_production_count_refresh='deferred after two read-only timeouts',local_campaign_checkpoint=a.reference(a.CHECKPOINT),local_campaign_totals_unchanged=dict(new_artworks=11018,existing_links=3036),policy='Historical campaign totals are local-only and are not summed into production counts. Production institution directory captured; fresh global production counts remain unverified after two read-only timeouts. No local database writes, existing artwork changes, image attachments, artist links or display claims.')
 m.save(RUN/'delivery-001.json',report)
 text=f'''# Musée Girodet — production museum expansion, 9 October 2026

Added **50 new production review artworks**, bringing this museum from **89 to 139 linked works**. Dates within the pre-1971 scope increased from **82 to 113**: 31 additions have eligible dates, 11 are undated and eight retain Joconde's twentieth-century range (1901–2000). Creator lifetimes were not substituted for artwork dates. The real local catalogue remains unchanged at 89 linked / 82 eligible works.

- [50 delivered artworks](added-production-artworks-001.csv)
- [All 205 source-record decisions](all-source-decisions-001.csv)
- [Production institution register and explicit count gaps](production-institution-register-001.csv)
- [Verification and museum counts](delivery-001.json)
- [Reviewed source and identity evidence](editorial-reviewed-001.json.gz)

The official [Ministry of Culture museum record](https://pop.culture.gouv.fr/notice/museo/M0284) identifies the collection. Its current Joconde dataset returned 205 museum-scoped records in two bounded pages. Of these, 84 were already catalogued, 50 were accepted, four remain held after individual review and 67 require separate source, physical-object or scope review. No exhaustive artwork or image download was performed.

New works include Girodet drawings and oil studies, Luce drawings and a lithograph, Charpentier's plaster portrait relief and individually inventoried Triqueti models and tarsias. Counterproofs, preparatory works and recto/verso sheets retain their identities; three head studies on one sheet count as one object. Museum holdings do not imply current display, physical custody or legal ownership, including historical usufruct qualifications. Matching confidence is an editorial assessment, not a calibrated probability.

The four individual holds are the two Janssens gallery pendants (one ambiguous existing record lacks an inventory), the full-size Ferdinand d'Orléans plaster (1842/1844 source conflict), and an anonymous portrait with conflicting support descriptions. Bound sketchbooks and separately described pages were not multiplied. The missing Circassienne, deposits, photographs, correspondence, lithographic stone matrix and other scope cases remain in the full ledger. Historical records were preserved.

Twelve offline date and source-boundary tests passed. The batch used a pinned plan, successful Cloud SQL backup **1791542644400**, an atomic transaction with readback, unchanged-existing-record comparisons and a zero-write replay. The review examined 4,136 existing production artworks and 8,928 citations. No new images, artist-authority links, publication or current-display claims were added. One approved WikiArt comparator image was inspected solely for identity research.

The target remains unfinished. Girodet needs another **61 linked works** to reach 200, or 87 more with eligible dates to reach 200 eligible works. The complete production institution directory is retained, but a fresh global count refresh is **not complete**: both the whole-catalogue query and a bounded 50-institution count query exceeded their 120-second statement timeout. Exact Girodet counts were verified separately. The register labels historical local counts explicitly; they are not presented as current production counts. Further count-query diagnostics and representative load testing remain open.


Earlier provider-access holds and research queues remain in the [wave 100 checkpoint](../augustiner-20261009/delivery-checkpoint-001.json). Public Girodet guides were accessible; the teacher PDF lead returned 404. Continue independent object sources and other underfilled museums without retrying held providers or creating quota placeholders.
'''
 dest=RUN/'README.md';assert not dest.exists();dest.write_text(text);print(json.dumps(dict(added=50,before=89,after=139,eligible=113)),flush=True)
if __name__=='__main__':main()
