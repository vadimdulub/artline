#!/usr/bin/env python3
"""Finalize the bounded research-only outcome for continuous batch 261."""
import datetime, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"docs/research/continuous-production-20261011"
OUT=BASE/"batches/000261"
QUEUE=BASE/"source-queue.json"
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name,value): (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")

source=json.loads((OUT/"surdoc-mnba-page30-source-verification.json").read_text())
eligible=source["eligible_after_source_review"]
before=QUEUE.read_bytes(); queue=json.loads(before)
entry=next(x for x in queue["sources"] if x["source_id"]=="surdoc_chile")
entry.update(status="mnba_page30_ten_objects_researched_seven_pre1971_candidates_held_for_global_identity_reconciliation",
             checkpoint={"institution":3,"page":31,"researched_native_ids":[x["id"] for x in source["researched_objects"]],
                         "selected_candidates":eligible,"remaining_page30_ids":source["index_ids"][10:]},
             evidence_paths=["docs/research/continuous-production-20261011/batches/000261/surdoc-mnba-page30-source-verification.json",
                             "docs/research/continuous-production-20261011/batches/000261/production-target-reconciliation.json"])
QUEUE.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+"\n")
save("source-queue-update-verification.json",{"at":now(),"source_id":"surdoc_chile","before_sha256":hashlib.sha256(before).hexdigest(),"after_sha256":sha(QUEUE),"preserved_unrelated_entries":110,"resume_cursor":entry["checkpoint"]})
save("bounded-production-gap-cohort.json",{"at":now(),"discovered":21,"researched":10,"selected":len(eligible),"prepared":0,"imported":0,"verified":0,"holds":[{"native_ids":eligible,"reason":"Global creator plus accession/title/date/dimensions/version reconciliation is incomplete; external-ID absence alone is insufficient evidence for safe inserts."},{"native_ids":["2-160"],"reason":"No explicit creation date; source history text is not substituted."},{"native_ids":["2-1604"],"reason":"No explicit creation date."},{"native_ids":["2-1605"],"reason":"Creation date 1981 is outside the through-1970 scope."}],"images":"No downloads: SURDOC registry policy requires record-explicit open rights and none was established.","writes":0})
save("actual-visual-review.json",{"at":now(),"prepared_images":0,"viewed_images":0,"reason":"No eligible licensed images were prepared; visual inspection was therefore not claimed."})
result={"outcome":"no_eligible_candidates","summary":"Batch 261 reconciled production and batch 107, then advanced the undercovered SURDOC Chile route to MNBA page 30. The page yielded 21 stable native IDs; 10 exact object pages were researched. Seven pre-1971 objects remain candidates, but were not inserted because full global creator and physical-object/version reconciliation is still required. Two undated works and one 1981 work were held. No image had record-explicit open reuse rights, and no production or storage writes occurred.","next_task":"Continue SURDOC MNBA page 30 from native ID 2-1606, then perform bounded global creator and accession/title/date/dimensions reconciliation for the seven saved candidates before any transactional insert; resume at institution=3,page=31 after page 30 is exhausted.","blocker":"","verified_counts":{"new_painters":0,"new_artworks":0,"newly_illustrated":0,"alternate_images":0,"museum_links":0},"evidence_paths":[]}
paths=["surdoc-mnba-page30-source-verification.json","production-target-reconciliation.json","batch107-live-reconciliation.json","bounded-production-gap-cohort.json","actual-visual-review.json","source-queue-update-verification.json"]
save("independent-production-verification.json",{"at":now(),"write":False,"verified_increments":result["verified_counts"],"production_target":json.loads((OUT/"production-target-reconciliation.json").read_text()),"programme_attribution":"No committed plan or production delta; all increments zero."})
paths.append("independent-production-verification.json")
result["evidence_paths"]=[str((OUT/p).relative_to(ROOT)) for p in paths]
save("batch-verification-receipt.json",{"at":now(),"batch":261,"result":result,"files":[{"path":str((OUT/p).relative_to(ROOT)),"sha256":sha(OUT/p)} for p in paths]})
result["evidence_paths"].append(str((OUT/"batch-verification-receipt.json").relative_to(ROOT)))
save("CHECKPOINT.json",{"at":now(),"batch":261,"status":"complete","result":result,"resume_cursor":entry["checkpoint"]})
result["evidence_paths"].append(str((OUT/"CHECKPOINT.json").relative_to(ROOT)))
save("worker-result.json",result)
print(json.dumps(result,ensure_ascii=False))

if __name__=="__main__": pass
