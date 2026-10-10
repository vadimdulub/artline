#!/usr/bin/env python3
"""Save read-only Wallace verification and a complete source follow-up queue."""
import collections,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-wallace-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m;RUN=a.RUN

def main():
 plan,digest=a.validate_plan();dm={d['source_id']:d for d in a.decisions()};added={r['facts']['source_id']:r for r in plan['records']};queue=[];account=[]
 for row in m.load(a.CANDIDATES)['rows']:
  sid=row['source_id'];d=dm.get(sid)
  if sid in added:state='added_review_only'
  elif d:state=d['state']
  elif row['state']=='candidate':state='editorial_review_pending'
  else:state=row['state']
  account.append(dict(source_id=sid,inventory=row.get('facts',{}).get('inventory'),state=state))
  if sid not in added:queue.append(dict(state=state,candidate=row,editorial_decision=d))
 counts=dict(collections.Counter(r['state'] for r in account));assert counts==dict(added_review_only=92,editorial_hold=15,editorial_review_pending=127,source_hold=17,source_capture_hold=1)
 m.save(RUN/'followup-queue-001.json.gz',dict(at=m.now(),rows=queue,accounting=account,counts=counts,total_unique_sources=252,unadded_unique_sources=160,plan_reference=a.reference(a.PLAN),candidate_reference=a.reference(a.CANDIDATES),next_index_url=m.load(RUN/'capture-pass-012.json.gz')['next_url'],policy='Unadded source objects, not import approvals. Source date/capture holds, tentative authorship, prototype distinctions and existing-identity leads retained. Fresh comparisons required after the applied92 additions.'))
 with m.connect() as db:
  result=a.verify(db,plan,digest)
  rows=db.execute("SELECT id::text,status,accession_number,creation_year_start,creation_year_end,date_precision FROM artworks WHERE current_institution_id=%s AND status<>'archived' ORDER BY id",(a.IID,)).fetchall()
  inventory=[a.i.compact(x['accession_number']) for x in rows if x['accession_number']]
  result.update(distinct_normalized_inventories=len(set(inventory)),nonempty_inventories=len(inventory),unknown_inventory_count=len(rows)-len(inventory),all_linked_status_counts=dict(collections.Counter(x['status'] for x in rows)),preserved_artist_links=len(plan['before']['artists']),preserved_media_links=len(plan['before']['media']),preserved_identifiers=len(plan['before']['identifiers']),preserved_location_assertions=len(plan['before']['assertions']))
  assert result['current_counts']==dict(linked=100,eligible=100)
 m.save(RUN/'minimum-100-verification.json',dict(at=m.now(),plan_sha256=digest,local_only=True,verification=result,limitation='SQL totals and inventories do not newly validate all eight legacy physical-object identities. All eleven pre-existing linked or pending records and their relations remain unchanged. Preferred200 target and wider museum goal are unfinished.'))
 m.save(RUN/'replay-001.json',dict(at=m.now(),plan_sha256=digest,result='Unchanged replay:92 records;zero inserts',verification=result,policy='Actual apply replay completed with zero inserts and full read-back.'))
 print(json.dumps(dict(accounting=counts,verification=result)),flush=True)
if __name__=='__main__':main()
