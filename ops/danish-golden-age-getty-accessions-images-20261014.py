#!/usr/bin/env python3
"""Link exact Getty checklist accessions and attach reviewed Met CC0 images."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import uuid
from pathlib import Path

from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "docs/research/danish-golden-age-20261013/catalogue-checklists"
IMAGES = RUN / "getty-met-images-20261014.json"
BACKUP = Path.home() / "Library/Application Support/Artline/backups/danish-golden-age-20261013"
SOURCE_RECORD = "danish-golden-age-catalogue-checklists-20261013/beyond-the-light"
MET_SOURCE = "e9d31deb-98ad-4d21-b71a-ec10005434bf"
OP = "danish-golden-age-getty-accessions-images-20261014"
ACTOR = "local-european-research"
POLICY = "https://www.metmuseum.org/about-the-met/policies-and-documents/open-access"
CC0 = "https://creativecommons.org/publicdomain/zero/1.0/"
NS = uuid.UUID("83c61428-b3d2-4e98-a50e-0b02988fe32c")

LINKS = {
    "1": ("6e808ce9-296e-55df-8833-0565baca562f", "85.PA.43"),
    "2": ("cc18633f-275b-5a41-9f66-02bd28c36104", "2018.59"),
    "5": ("7269f61c-c121-5371-85ca-b310ad886ca0", "2004.369"),
    "6": ("09927935-96fd-59d9-986a-9f16cef0e957", "2007.164.7"),
    "9": ("f8b8800c-057e-54b7-8780-da463a4bd401", "2009.285"),
    "10": ("823d6aa3-ee9c-5558-bc86-af080f45b5c9", "2009.400.64"),
    "11": ("f15152fa-b3ea-5d07-9d85-49f36dfff64c", "2015.12"),
    "12": ("3f60d134-ba45-5e79-b9b5-9827b99f9f6e", "2016.678"),
    "14": ("825901a6-1b3b-596b-b4b0-5593bbae29c5", "2018.280"),
}
OBJECTS = {
    "365663": LINKS["5"][0], "438952": LINKS["6"][0],
    "440727": LINKS["9"][0], "440343": LINKS["10"][0],
    "651676": LINKS["11"][0], "780292": LINKS["14"][0],
}

spec = importlib.util.spec_from_file_location("catalogue", ROOT / "ops/catalogue-expansion-20261008.py")
catalogue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalogue)


def media_id(object_id):
    return str(uuid.uuid5(NS, "met-object/" + object_id))


def snapshot(db, lock=False):
    suffix = " FOR UPDATE" if lock else ""
    entries = [dict(r) for r in db.execute(
        """SELECT ee.id::text,ee.catalogue_number,ee.artwork_id::text,ee.title_label,
                  ee.creator_label,ee.evidence,ee.match_basis
           FROM exhibition_entries ee JOIN exhibition_source_records s ON s.id=ee.source_record_id
           WHERE s.source_record_id=%s AND ee.catalogue_number=ANY(%s)
           ORDER BY ee.catalogue_number::int""" + suffix, (SOURCE_RECORD, list(LINKS)))]
    arts = [dict(r) for r in db.execute(
        """SELECT id::text,title,accession_number,creation_year_start,creation_year_end,
                  primary_media_id::text,status,unlinked_creator_label
           FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id""" + suffix,
        ([x[0] for x in LINKS.values()],))]
    mids = [media_id(x) for x in OBJECTS]
    media = [dict(r) for r in db.execute(
        "SELECT id::text FROM media_assets WHERE id=ANY(%s::uuid[]) ORDER BY id" + suffix, (mids,))]
    attachments = [dict(r) for r in db.execute(
        "SELECT artwork_id::text,media_id::text,sort_order,view_label FROM artwork_media WHERE media_id=ANY(%s::uuid[]) ORDER BY media_id" + suffix,
        (mids,))]
    return {"entries": entries, "artworks": arts, "media": media, "attachments": attachments}


def plan():
    image_doc = json.loads(IMAGES.read_text())
    assert len(image_doc["images"]) == 6 and image_doc["held"] == [{"object_id": "730794", "reason": "Official object page exposes a restricted image endpoint; no image downloaded."}]
    for im in image_doc["images"]:
        raw = (ROOT / im["file_path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == im["checksum_sha256"] and len(raw) == im["bytes"]
    with catalogue.connect() as db:
        before = snapshot(db)
    assert len(before["entries"]) == len(LINKS) and len(before["artworks"]) == len(LINKS)
    assert not before["media"] and not before["attachments"]
    by_number = {x["catalogue_number"]: x for x in before["entries"]}
    assert by_number["1"]["artwork_id"] == "77592d29-06c7-578d-be83-6698ef692a9b"
    assert all(by_number[n]["artwork_id"] is None for n in LINKS if n != "1")
    by_art = {x["id"]: x for x in before["artworks"]}
    assert all(by_art[aid]["accession_number"] == accession for aid, accession in LINKS.values())
    assert all(by_art[aid]["status"] != "archived" for aid, _ in LINKS.values())
    assert all(by_art[aid]["creation_year_end"] <= 1970 for aid, _ in LINKS.values())
    assert all(by_art[aid]["primary_media_id"] is None for aid in OBJECTS.values())
    payload = {"generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "operation": OP,
               "before": before, "links": LINKS, "objects": OBJECTS, "images": image_doc,
               "totals": {"exact_links": 9, "new_links": 8, "corrected_duplicate_link": 1, "new_images": 6, "restricted_image_holds": 1}}
    (RUN / "getty-accessions-images-plan.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n")
    BACKUP.mkdir(parents=True, exist_ok=True); BACKUP.chmod(0o700)
    path = BACKUP / "getty-accessions-images-before.json"
    assert not path.exists()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n"); path.chmod(0o600)
    print(payload["totals"])


def apply():
    p = json.loads((RUN / "getty-accessions-images-plan.json").read_text())
    assert json.loads((ROOT / "docs/research/danish-golden-age-20261013/cloud-backup.json").read_text())["status"] == "SUCCESSFUL"
    images = {x["object_id"]: x for x in p["images"]["images"]}
    with catalogue.connect(True) as db, db.transaction():
        db.execute("SET LOCAL lock_timeout='120s'")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute("SELECT pg_advisory_xact_lock(2026101401)")
        current = snapshot(db, lock=True)
        assert current == p["before"]
        art = {x["id"]: x for x in current["artworks"]}
        for entry in current["entries"]:
            aid, accession = LINKS[entry["catalogue_number"]]
            ev = dict(entry["evidence"] or {})
            ev["accession_reconciliation_20261014"] = {
                "operation": OP, "accession": accession,
                "basis": "Exact museum accession in the official Getty checklist and the production museum-native object.",
                "previous_artwork_id": entry["artwork_id"],
                "correction": "Checklist no. 1 now points to the Getty-native object rather than its duplicate WikiArt record." if entry["catalogue_number"] == "1" else None,
            }
            db.execute("UPDATE exhibition_entries SET artwork_id=%s,match_basis=%s,evidence=%s WHERE id=%s",
                       (aid, "Exact museum accession " + accession, Jsonb(ev), entry["id"]))
        for object_id, aid in OBJECTS.items():
            im = images[object_id]; a = art[aid]; mid = media_id(object_id)
            creator = a["unlinked_creator_label"] or "Unknown creator"
            db.execute("""INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,
                mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,
                creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
                VALUES(%s,'local',%s,%s,'The Metropolitan Museum of Art','image/jpeg',%s,%s,%s,%s,%s,
                       'cc0','CC0 1.0',%s,%s,%s,%s,now(),%s)""",
                (mid, im["storage_path"], im["source_page_url"], im["width"], im["height"], im["bytes"],
                 im["checksum_sha256"], a["title"] + " — " + creator, CC0, creator,
                 f"{a['title']}. {creator}. The Metropolitan Museum of Art. CC0 1.0.", im["retrieved_at"], ACTOR))
            db.execute("""INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,
                source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,now(),%s)""",
                (mid, MET_SOURCE, object_id, im["checksum_sha256"], im["source_image_url"], POLICY,
                 "Exact official museum object image under The Met Open Access CC0 policy.", OP, Jsonb(im)))
            db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,'Museum primary reproduction')", (aid, mid))
            db.execute("UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL", (mid, ACTOR, aid))
    with catalogue.connect() as db:
        after = snapshot(db)
        source_totals = dict(db.execute("""SELECT count(*) entries,count(artwork_id) linked,
            count(*) FILTER(WHERE artwork_id IS NULL) unlinked FROM exhibition_entries ee
            JOIN exhibition_source_records s ON s.id=ee.source_record_id WHERE s.source_record_id=%s""", (SOURCE_RECORD,)).fetchone())
        catalogue_totals = dict(db.execute("""SELECT count(*) entries,count(artwork_id) linked,
            count(*) FILTER(WHERE artwork_id IS NULL) unlinked,
            count(DISTINCT artwork_id) FILTER(WHERE artwork_id IS NOT NULL) distinct_artworks
            FROM exhibition_entries ee JOIN exhibition_source_records s ON s.id=ee.source_record_id
            WHERE s.source_record_id=ANY(%s)""", ([SOURCE_RECORD,
            "danish-golden-age-impressionist-gardens-20261013",
            "danish-golden-age-charlottenborg-1830-20261013"],)).fetchone())
    assert len(after["media"]) == 6 and len(after["attachments"]) == 6
    assert all(x["primary_media_id"] == media_id(oid) for oid, aid in OBJECTS.items() for x in after["artworks"] if x["id"] == aid)
    out = {"applied_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "operation": OP,
           "totals": p["totals"], "getty_source_totals": source_totals,
           "three_catalogue_totals": catalogue_totals, "after": after}
    (RUN / "getty-accessions-images-applied.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str) + "\n")
    print(out["totals"], source_totals, catalogue_totals)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("phase", choices=["plan", "apply"])
    globals()[ap.parse_args().phase]()
