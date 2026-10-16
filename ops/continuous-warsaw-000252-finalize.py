#!/usr/bin/env python3
import copy, fcntl, importlib.util, json, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('w252',ROOT/'ops/continuous-warsaw-batch-000252.py'); w=importlib.util.module_from_spec(s); s.loader.exec_module(w); b=w.b; h=w.h; E=w.E.parent
receipt=h.load(w.E/'batch-verification-receipt.json'); counts=receipt['verified_counts']; now=h.now()
Q=E.parents[1]/'source-queue.json'; before=h.load(Q); after=copy.deepcopy(before)
row=next(x for x in after['sources'] if x['source_id']=='national_museum_warsaw'); unrelated=[x for x in before['sources'] if x['source_id']!='national_museum_warsaw']
ev=[str((w.E/x).relative_to(ROOT)) for x in ['batch-verification-receipt.json','independent-production-verification.json','independent-storage-verification.json','independent-public-verification.json','actual-visual-review.json','global-identity-reconciliation.json']]
row.update(status='page1_three_held_versions_resolved_and_verified',checkpoint=str((E/'CHECKPOINT.json').relative_to(ROOT)),last_checked_at=now,verified_counts=counts,access_status='Official saved object metadata and image bytes verified; all three prior version holds resolved as distinct physical icons.',evidence_paths=list(dict.fromkeys(row.get('evidence_paths',[])+ev)))
cur=row.setdefault('resume_cursor',{}); cur['page1_continuation_delivered_native_ids']=list(dict.fromkeys(cur.get('page1_continuation_delivered_native_ids',[])+['498663','498667','498653'])); cur['page1_version_review_holds']=[]
cur['next_step']='Rotate to another undercovered eligible registry route; Warsaw page-one recovery holds are resolved. Continue bounded icon/Byzantine/Greek or Russian coverage without repeating delivered native IDs.'
row['remaining_gaps']=['Full National Museum in Warsaw collection coverage remains incomplete; continue from the saved catalogue cursor without repeating delivered native identifiers.']
assert [x for x in after['sources'] if x['source_id']!='national_museum_warsaw']==unrelated and len(after['sources'])==111
with Q.with_suffix('.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX); tmp=Q.with_suffix('.batch252.tmp'); tmp.write_text(json.dumps(after,ensure_ascii=False,indent=2)); os.replace(tmp,Q)
h.save(E/'source-queue-update-verification.json',dict(at=now,modified_source_ids=['national_museum_warsaw'],unrelated_routes_preserved=110,exact_unrelated_structures_equal=True,after_sha256=h.sha(Q.read_bytes()),delivered_native_ids=['498663','498667','498653'],held_native_ids=[]))
evidence=ev+[str((E/'source-queue-update-verification.json').relative_to(ROOT)),str((E/'prior-batch-live-reconciliation.json').relative_to(ROOT))]
cp=dict(at=now,batch=252,stage='production_and_public_delivery_independently_verified',outcome='progress',researched=3,selected=3,prepared=3,imported=3,verified=3,verified_counts=counts,production_ids=receipt['production_ids'],next_task=cur['next_step'],blocker='',evidence_paths=evidence,external_supervisor_unchanged=True,production_writes=3,local_catalogue_connections=0,limitations=['No named painter created; qualified workshop labels remain object-level.','Small inscriptions and unavailable reverse sides were not claimed as visually inspected.'])
h.save(E/'CHECKPOINT.json',cp); h.save(w.R/'CHECKPOINT.json',cp)
result=dict(outcome='progress',summary='Batch 252 resolved three prior Warsaw same-title holds as distinct inventory-level painted icons and independently verified three new review artworks, three authentic primary images, and three accepted museum holdings. All originals and derivatives were individually viewed; storage and public bytes were checksum-verified.',next_task=cur['next_step'],blocker='',verified_counts=counts,evidence_paths=[str((w.E/x).relative_to(ROOT)) for x in ['batch-verification-receipt.json','independent-production-verification.json','independent-storage-verification.json','independent-public-verification.json','actual-visual-review.json']]+[str((E/'source-queue-update-verification.json').relative_to(ROOT)),str((E/'CHECKPOINT.json').relative_to(ROOT))])
h.save(E/'worker-result.json',result); print(json.dumps(result))
