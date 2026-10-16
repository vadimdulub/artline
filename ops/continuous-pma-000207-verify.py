#!/usr/bin/env python3
"""Independent live/source/audit/public verification and queue checkpoint for batch 207."""
import fcntl, gzip, importlib.util, json, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("pma207",ROOT/"ops/continuous-pma-000207.py")
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);h=b.h

with (b.R/"worker.lock").open("a+") as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p,pin=h.pinned(b.PHASE);ids=[r["artwork_id"] for r in p["records"]];n=len(ids);assert n==29
 prepath=h.BACKUP/b.PHASE/"locked-before.json.gz";pre=h.load(prepath);assert pre["artworks"]=={} and pre["plan_sha256"]==pin
 sources=[]
 for r in p["records"]:
  ep=ROOT/r["evidence_file"];raw=gzip.decompress(ep.read_bytes());text=raw.decode(errors="replace")
  assert h.sha(ep.read_bytes())==r["evidence"]["sha256"] and r["title"] in text and r["accession_number"] in text
  assert r["last"]<=1970 and r["source_id"] in r["source_url"] and not r["before"]
  sources.append({"artwork_id":r["artwork_id"],"source_id":r["source_id"],"source_url":r["source_url"],"capture_sha256":r["evidence"]["sha256"],"accession":r["accession_number"],"verified":True})
 with h.connect() as db,db.transaction():
  db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
  after=h.snapshot(db,ids);assert len(after)==n
  notes=[dict(x) for x in db.execute("SELECT entity_id::text,source_id::text,source_record_id,source_url,evidence_note::jsonb note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,b.FIELD))];assert len(notes)==n
  holdids=[]
  for r in p["records"]:
   state=after[r["artwork_id"]];a=state["artwork"];note=next(x for x in notes if x["entity_id"]==a["id"])
   for k,v in {"title":r["title"],"accession_number":r["accession_number"],"creation_year_start":r["first"],"creation_year_end":r["last"],"date_precision":r["precision"],"date_display":r["date_display"],"medium_text":r["medium"],"status":"review","primary_media_id":None,"current_institution_id":p["institutions"][b.MUSEUM]["id"],"research_candidate":True,"published_at":None}.items():assert a[k]==v,(a["id"],k)
   assert not state["attachments"] and len(state["holdings"])==1
   hold=state["holdings"][0];holdids.append(hold["id"]);assert hold["claim_type"]=="holding" and hold["context"]=="collection" and hold["review_state"]=="accepted" and hold["display_state"] is None
   hev=json.loads(hold["evidence_note"]);assert hev["confidence"]>=.8 and hev["source_sha256"]==r["evidence"]["sha256"] and hev["inventory"]==r["accession_number"]
   assert note["note"]["plan_sha256"]==pin and note["note"]["evidence"]["sha256"]==r["evidence"]["sha256"] and note["source_record_id"]==r["source_id"] and note["source_url"]==r["source_url"]
   own=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(b.SCHEME,r["source_id"])).fetchall();assert len(own)==1 and own[0]["entity_id"]==a["id"]
   if r["artist_id"]:assert len(state["creators"])==1 and state["creators"][0]["artist_id"]==r["artist_id"]
   else:assert not state["creators"]
  events=[dict(x) for x in db.execute("SELECT entity_id::text,entity_type,action,before_json,after_json,created_at FROM audit_log WHERE entity_id=ANY(%s::uuid[]) AND action='insert'",(ids+holdids,))];assert len(events)==2*n and all(x["before_json"] is None for x in events)
  assert db.execute("SELECT count(*) n FROM artwork_search_documents WHERE id=ANY(%s::uuid[])",(ids,)).fetchone()["n"]==n
  receipt107=h.load(b.E.parent/"000107/batch-verification-receipt.json");ids107=receipt107["production_ids"]
  batch107=db.execute("SELECT count(*) n FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids107,)).fetchone()["n"];assert batch107==12
  media107=db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND primary_media_id IS NOT NULL",(ids107,)).fetchone()["n"];assert media107==12
  totals=dict(db.execute("SELECT count(*) artworks,count(*) FILTER (WHERE primary_media_id IS NOT NULL) illustrated FROM artworks WHERE status<>'archived'").fetchone())
 b.save("independent-source-verification.json",{"at":h.now(),"plan_sha256":pin,"records":sources,"native_images_selected":0,"visual_review_claimed":False})
 b.save("independent-production-verification.json",{"at":h.now(),"plan_sha256":pin,"verified_new_artworks":n,"verified_museum_links":n,"production_ids":ids,"live_totals":totals,"locked_preimage":{"path":str(prepath),"sha256":h.sha(prepath.read_bytes())},"local_catalogue_connections":0})
 b.save("independent-audit-history-verification.json",{"at":h.now(),"events":h.safe(events),"empty_artwork_preimages":True,"insert_events":len(events),"programme_plan_checksum_verified":True})
 b.save("batch107-live-reconciliation.json",{"at":h.now(),"live_citation_matches":batch107,"verified_primary_media":media107,"prior_receipt_sha256":h.sha((b.E.parent/"000107/batch-verification-receipt.json").read_bytes()),"previous_increments_counted":0,"stale_prior_aggregate":172,"basis":"Fresh row-scoped read-only reconciliation across the 12 persisted batch-107 IDs found exactly 12 identity citations and 12 primary media. The earlier 172 aggregate was not row-scoped and is superseded here; batch 107 was not replayed."})
 public=[]
 for r in p["records"]:
  url="https://artlines.org/api/backend/v1/atlas/artworks/"+r["artwork_id"]
  with urllib.request.urlopen(url,timeout=45) as res: body=res.read();status=res.status
  assert status==200 and r["title"].encode() in body and b.MUSEUM.encode() in body
  public.append({"artwork_id":r["artwork_id"],"url":url,"status":status,"sha256":h.sha(body),"title_and_holding_present":True})
 b.save("independent-public-verification.json",{"at":h.now(),"records":public,"verified":n})
 b.save("actual-visual-review.json",{"at":h.now(),"prepared_images":0,"actually_viewed_files":[],"claim":"No image was prepared or delivered; file checks were not represented as visual review.","native_image_leads_preserved":n})
 counts={"new_painters":0,"new_artworks":n,"newly_illustrated":0,"alternate_images":0,"museum_links":n}
 b.save("batch-verification-receipt.json",{"at":h.now(),"verified_counts":counts,"production_ids":ids,"plan_sha256":pin,"locked_preimage_sha256":h.sha(prepath.read_bytes()),"production_target":"artline-508319:europe-west1:artline-postgres","shared_ingestion_lock":"artline-curated-ingestion","attribution":"Empty locked artwork preimages plus unique PMA native identifiers, own citation field, plan checksum, 58 insert audit events, fresh production/public reads. Earlier campaigns excluded.","images_and_storage_writes":0})
 queue_path=b.E.parents[1]/"source-queue.json";queue=h.load(queue_path);entry=next(x for x in queue["sources"] if x["source_id"]=="philadelphia_museum_art")
 entry.update(status="29_russian_pictorial_artworks_and_holdings_verified_images_held_per_object",checkpoint="docs/research/continuous-production-20261011/batches/000207/CHECKPOINT.json",last_checked_at=h.now(),access_status="Official catalogue and 30 exact object pages HTTP 200; 29 new eligible pictorial objects delivered, one title/date version held.",policy_reference="Original 111-source registry; docs/ARTLINE_IMAGE_USE.md")
 entry["resume_cursor"]={"route":"russian_pictorial_place_filter","algolia_page":0,"examined_native_ids":[x["source_id"] for x in sources]+["54325"],"delivered_native_ids":[x["source_id"] for x in sources],"held_native_ids":["54325"],"next_page":1,"next_step":"Rotate to a Greek/Byzantine or Russian-icon institution, then continue PMA Russia page 1 without repeating these 30 identities. Review native public-domain image flags individually before any download."}
 entry["verified_counts"]=counts
 queue_bytes=json.dumps(queue,ensure_ascii=False,indent=2).encode()+b"\n";queue_path.write_bytes(queue_bytes)
 b.save("source-queue-update-verification.json",{"at":h.now(),"source_id":"philadelphia_museum_art","queue_sha256":h.sha(queue_bytes),"unrelated_entries_preserved":True,"resume_cursor":entry["resume_cursor"]})
 checkpoint={"at":h.now(),"batch":207,"stage":"independently_verified_complete","discovered":30,"selected":29,"prepared":29,"imported":29,"verified":29,"verified_counts":counts,"production_writes":138,"next_task":"Research a distinct undercovered Greek, Byzantine, post-Byzantine or Russian-icon registry route with stable object identifiers and explicit image reuse; do not repeat PMA page 0. PMA Russia can later resume at page 1, with per-object rights review for images.","blocker":"","evidence":["docs/research/continuous-production-20261011/batches/000207/independent-source-verification.json","docs/research/continuous-production-20261011/batches/000207/independent-production-verification.json","docs/research/continuous-production-20261011/batches/000207/independent-audit-history-verification.json","docs/research/continuous-production-20261011/batches/000207/independent-public-verification.json","docs/research/continuous-production-20261011/batches/000207/batch-verification-receipt.json","docs/research/continuous-production-20261011/batches/000207/source-queue-update-verification.json"]}
 b.save("CHECKPOINT.json",checkpoint)
 with h.connect() as db:assert h.snapshot(db,ids)==after
 b.save("independent-final-reconciliation.json",{"at":h.now(),"plan_sha256":pin,"live_rows_equal_verified_snapshot":True,"replay_increments":{k:0 for k in counts},"verified_counts":counts})
 print(json.dumps(counts))
