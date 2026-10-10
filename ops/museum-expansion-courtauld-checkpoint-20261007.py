#!/usr/bin/env python3
"""Read-only verification and complete bounded Courtauld continuation queue."""
import collections,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-courtauld-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m;RUN=a.RUN

HOLDS={
 'p-2000-xx-3':'Bonington Beach Scene with Figures lead lacks enough physical metadata to exclude a translated/version identity.',
 'p-1947-lf-80':'Crome Edge of the Forest lead requires physical-object comparison.',
 'p-1978-pg-81':'Daddi Madonna and Child Enthroned with Saints lead has a nearby 1339 date and missing physical metadata; resolve before adding.',
 'p-1932-sc-157':'Gainsborough wife portraits and Margaret holding a Theorbo need version review.',
 'p-1966-gp-161':'Existing Garofalo Holy Family with infant John and Elizabeth, dated1520, is a strong duplicate lead.',
 'p-1975-xx-187':'Self-portrait has1054 global exact-title leads; creator identity/aliases need final targeted review.',
 'p-1978-pg-433':'Native title says after Francesco Bassano while the Maker field says after Jacopo Bassano; preserve the conflict.',
 'p-1947-lf-50':'Source creator label Germany19th century/copy/former Bruyn attribution conflicts with production1550; do not substitute prototype date.',
 'p-1982-lb-177':'Gotlib production1942–1943 conflicts with provenance exhibition1934.',
 'p-1932-sc-100':'Native Late1760s date and narrative completion by Dupont after Gainsborough death need separate-phase review.',
 'p-1935-rf-392':'Provenance field includes unrelated Rembrandt and Degas object labels; preserve literal content and review field contamination.',
 'p-1947-lf-31':'Two separately accessioned Blanchard fragments originally formed one painting and are reunited; determine object grouping before counting.',
 'p-1999-xx-1':'Second Blanchard fragment of the same reunited Allegory of Charity; do not count as an independent whole without grouping review.'}

def main():
 plan,digest=a.validate_plan();added={r['facts']['source_id'] for r in plan['records']};cs={r['source_id']:r for r in m.load(a.COMPARISONS)['records']};queue=[];account=[]
 for row in m.load(a.CANDIDATES)['rows']:
  sid=row['source_id'];cm=cs.get(sid);reason=None
  if sid in added:state='added_review_only'
  elif row['state']=='source_hold':state='source_hold';reason='; '.join(row['reasons'])
  elif row['grouping']['component_number']:state='component_grouping_hold';reason='Do not count panel/face alongside a parent work; resolve whole/part scope.'
  elif cm and (cm['source_hits'] or any(x['relevant'] for x in cm['inventory_hits'])):state='existing_identity_lead';reason='Source URL or relevant inventory already occurs in the catalogue; verify holding rather than add another record.'
  elif sid in HOLDS:state='editorial_hold';reason=HOLDS[sid]
  else:state='editorial_review_pending';reason='Additional title, creator, physical-object or version review required; no import approval.'
  account.append(dict(source_id=sid,inventory=row['facts']['inventory'],state=state))
  if sid not in added:queue.append(dict(state=state,reason=reason,candidate=row,comparison=cm))
 loans=[]
 for n in range(1,5):
  p=RUN/f'painting-index-sorted-{n:03}.json.gz'
  loans += [dict(row=r,index_reference=a.reference(p),state='loan_index_lead_not_approved') for r in m.load(p)['parsed']['rows'] if r['source_path'].startswith('/object-lp-')]
 counts=dict(collections.Counter(x['state'] for x in account));assert len(account)==196 and len(queue)==106 and len(loans)==12 and counts['added_review_only']==90
 m.save(RUN/'followup-queue-001.json.gz',dict(at=m.now(),rows=queue,loan_leads=loans,accounting=account,counts=counts,total_index_rows=208,retained_object_records=196,unadded_retained_objects=106,plan_reference=a.reference(a.PLAN),candidate_reference=a.reference(a.CANDIDATES),next_request=m.load(RUN/'painting-index-sorted-004.json.gz')['parsed']['next_request'],policy='Research queue, not import approval. Refresh public navigation if its search token expires. Rebase identity comparisons after the90 additions; preserve original snapshots. Parent/child, loans, missing objects, dates and creator conflicts remain explicit.'))
 with m.connect() as db:
  result=a.verify(db,plan,digest);rows=db.execute("SELECT id::text,status,accession_number FROM artworks WHERE current_institution_id=%s AND status<>'archived' ORDER BY id",(a.IID,)).fetchall();invs=[a.i.compact(r['accession_number']) for r in rows if r['accession_number']]
  result.update(distinct_normalized_inventories=len(set(invs)),nonempty_inventories=len(invs),unknown_inventory_count=len(rows)-len(invs),all_linked_status_counts=dict(collections.Counter(x['status'] for x in rows)),preserved_artist_links=len(plan['before']['artists']),preserved_media_links=len(plan['before']['media']),preserved_identifiers=len(plan['before']['identifiers']),preserved_location_assertions=len(plan['before']['assertions']))
  assert result['current_counts']==dict(linked=106,eligible=105) and len(invs)==len(set(invs))==106
 m.save(RUN/'minimum-100-verification.json',dict(at=m.now(),plan_sha256=digest,local_only=True,verification=result,limitation='SQL counts do not freshly validate all16 legacy linked object identities or repair the one unknown legacy date. All23 pre-existing linked/pending records and relations remain unchanged. Preferred200 target and wider goal are unfinished.'))
 log=Path('/tmp/artline-courtauld-replay-20261007.log').read_text();assert log=='Unchanged replay: 90 records;zero inserts\n'
 m.save(RUN/'replay-001.json',dict(at=m.now(),plan_sha256=digest,result=log.strip(),verification=result,policy='Actual apply replay completed with zero inserts and full read-back.'))
 print(json.dumps(dict(accounting=counts,verification=result)),flush=True)

if __name__=='__main__':main()
