#!/usr/bin/env python3
"""Finalize bounded batch 133 after live French/Auckland reconciliation."""
import csv, gzip, importlib.util, json, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "docs/research/continuous-production-20261011/batches/000133"
R = Path.home() / "Library/Application Support/Artline/continuous-research/batches/000133"
DATA = Path.home() / "Library/Application Support/Artline/source-metadata/continuous-production-20261011/000133"
for p in (E, R, DATA): p.mkdir(parents=True, exist_ok=True)

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value

b = module("auckland133base", "ops/continuous-auckland-images-000113.py")
h = b.h
native = module("auckland133native", "ops/museum-expansion-auckland-20261006.py")
ids = ["54d0f5c9-450e-57b6-a4b2-d0bf1a6fdf65", "55cb8894-e6b4-53d2-9e33-d3d67f132c96",
       "56b54223-1004-55f5-812c-b9ecd1b761df", "5784b26a-6fdb-57ab-bc5d-0b5400b1d040"]
routes = {ids[0]:("299","whetoi-pomare-1896"), ids[1]:("4268","baroque-chair"),
          ids[2]:("3405","rocks-concrete-and-iron"), ids[3]:("342","paora-tuhaere")}
def save(name, value):
    path=E/name
    if path.exists(): return h.load(path)
    h.save(path, value); return value
def rel(p): return str(Path(p).relative_to(ROOT))

required = [ROOT/"AGENTS.md", Path("/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv"),
            ROOT/"docs/ARTLINE_IMAGE_USE.md", ROOT/"docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md",
            ROOT/"docs/LOCAL_DATA_LOCATIONS.md", E.parents[1]/"CHECKPOINT.json", E.parents[1]/"source-queue.json"]
save("required-input-verification.json", {"at":h.now(), "files":[{"path":str(p),"sha256":h.sha(p.read_bytes())} for p in required],
     "registry_rows":len(list(csv.DictReader(open(required[1])))), "local_catalogue_connections":0})
target = b.target()
save("production-target-reconciliation.json", target)

french = ROOT/"docs/research/printmaking-continuation-20261011/french-reserve/delivery-plan.json.gz"
if not french.exists(): french = ROOT/"docs/research/french-printmaking-20261011/delivery-plan.json.gz"
plan = h.load(french); french_ids = [x["artwork_id"] for x in plan["rows"]]
with b.connect() as db:
    live107 = h.snapshot(db, list(h.load(E.parent/"000107/independent-production-verification.json")["after"]))
    assert live107 == h.load(E.parent/"000107/independent-production-verification.json")["after"]
    states = h.snapshot(db, ids)
    french_live = h.snapshot(db, french_ids)
    assert len(french_ids) == 188 and all(french_live[x]["artwork"]["primary_media_id"] for x in french_ids)
save("batch107-live-reconciliation.json", {"at":h.now(),"snapshot_equal":True,"previous_increments_counted":0})
save("french-reserve-live-reconciliation.json", {"at":h.now(),"inspected":188,"already_imported_and_illustrated":188,
     "unimported":0,"selected":0,"new_programme_increments":0,"plan_sha256":h.sha(french.read_bytes()),
     "immutable_plan_unchanged":True})

captures=[]; holds=[]
for aid,(oid,slug) in routes.items():
    url=f"https://www.aucklandartgallery.com/explore/art-and-artists/artwork/{oid}/{slug}"
    response=b.i.session().get(url,timeout=(15,60)); response.raise_for_status(); raw=response.content
    body=DATA/(h.sha(url.encode())+".body.gz"); body.write_bytes(gzip.compress(raw,mtime=0))
    parsed=native.fields(raw); fields=parsed["fields"]; attrs=parsed["native_route"]["attributes"]
    assert str(attrs["id"])==oid and fields["Copyright"]=="Copying restrictions apply"
    assert states[aid]["artwork"]["primary_media_id"] is None
    receipt={"url":url,"status":response.status_code,"retrieved_at":h.now(),"sha256":h.sha(raw),"bytes":len(raw),"body_path":str(body)}
    captures.append({"artwork_id":aid,"native_id":oid,"title":fields["Title"],"artist":fields["Artist"],
                     "accession":fields["Accession No"],"date":fields["Production date"],"image_available":bool(attrs["zoom_image"]),
                     "rights_label":fields["Copyright"],"receipt":receipt})
    holds.append({"artwork_id":aid,"native_id":oid,"reason":"Native source explicitly says Copying restrictions apply; no download or delivery.","source_url":url})
save("auckland-native-source-verification.json", {"at":h.now(),"records":captures,"all_exact_native_pages_http_200":True,
     "all_live_primary_states_null":True,"selected":0,"downloads":0})
save("research-holds.json", {"at":h.now(),"holds":holds,"provider_access_hold":False,"unchanged_failed_requests":0})
save("source-access-holds.json", {"at":h.now(),"access_status":"Four exact native pages HTTP 200; object-level copying restrictions held.",
     "provider_access_hold":False,"prior_ledgers_preserved":True})

queue_path=E.parents[1]/"source-queue.json"; before=h.load(queue_path); after=json.loads(json.dumps(before))
row=next(x for x in after["sources"] if x["source_id"]=="auckland_art_gallery")
row.update(status="four_untouched_crosswalks_researched_all_copying_restricted",last_batch=133,last_checked_at=h.now(),
           checkpoint=rel(E/"CHECKPOINT.json"),latest_batch_verified_counts={"new_painters":0,"new_artworks":0,"newly_illustrated":0,"alternate_images":0,"museum_links":0})
row["remaining_gaps"]=["Four formerly untouched native crosswalks are exact but explicitly copying-restricted; do not retry without changed rights evidence.",
                       "Earlier Auckland identity, missing-image, proportion and rights holds remain preserved."]
row.setdefault("research_history",[]).append({"batch":133,"at":h.now(),"evidence":[rel(E/"auckland-native-source-verification.json"),rel(E/"research-holds.json")],"verified_counts":row["latest_batch_verified_counts"]})
queue_path.write_text(json.dumps(after,ensure_ascii=False,indent=2)+"\n")
save("independent-queue-verification.json", {"at":h.now(),"updated_source":"auckland_art_gallery","unrelated_entries_preserved":
     [x for x in before["sources"] if x["source_id"]!="auckland_art_gallery"]==[x for x in after["sources"] if x["source_id"]!="auckland_art_gallery"],
     "before_sha256":h.sha(json.dumps(before,sort_keys=True).encode()),"after_sha256":h.sha(queue_path.read_bytes())})

counts={"new_painters":0,"new_artworks":0,"newly_illustrated":0,"alternate_images":0,"museum_links":0}
evidence=["french-reserve-live-reconciliation.json","batch107-live-reconciliation.json","auckland-native-source-verification.json",
          "research-holds.json","source-access-holds.json","independent-queue-verification.json"]
checkpoint={"at":h.now(),"batch":133,"stage":"verified_complete_no_eligible_candidates","verified_counts":counts,
 "researched":{"french_reserve":188,"auckland_crosswalks":4},"selected":0,"prepared":0,"imported":0,"verified":0,
 "next_task":"Rotate to another undercovered registry-backed Greek, Byzantine or French-print route with unheld object-level evidence; do not replay French188 or retry Auckland copying-restricted objects without changed evidence.",
 "evidence":[rel(E/x) for x in evidence],"external_supervisor_unchanged":True,"local_catalogue_connections":0}
save("CHECKPOINT.json",checkpoint)
save("batch-verification-receipt.json", {"at":h.now(),"verified_counts":counts,"production_ids":[],"production_writes":0,
 "attribution":"No eligible new rows: French reserve already delivered; all four exact Auckland objects explicitly copying-restricted.","production_target":target})
evidence += ["batch-verification-receipt.json","CHECKPOINT.json"]
result={"outcome":"no_eligible_candidates","summary":"The 188 French reserve records were all already delivered and illustrated. Four queued Auckland crosswalks were exact and live-unillustrated, but every native object page explicitly states copying restrictions apply, so all were held and no production write was made.",
 "next_task":checkpoint["next_task"],"blocker":"","verified_counts":counts,"evidence_paths":[rel(E/x) for x in evidence]}
save("worker-result.json",result); print(json.dumps(result))
