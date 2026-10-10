#!/usr/bin/env python3
"""Read-only verification of the selected museum data and live image delivery."""
import argparse
import concurrent.futures
import hashlib
import importlib.util
import io
import json
import uuid
from pathlib import Path

import requests
from PIL import Image

spec = importlib.util.spec_from_file_location("audit", Path(__file__).with_name("audit-museum-gaps-20261005.py"))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
r = audit.r
OUT = r.RUN / "verification-20261006"


def selected():
    assets = {}
    plans = [r.load(r.ROOT / "docs/research/louvre-image-coverage-20261005/repair-plan.json.gz"), r.load(r.RUN / "national-image-repair-plan.json.gz")]
    for plan in plans:
        for claim in plan["claims"]:
            snap = plan["targets"]["local"]
            media = snap["preimages"][snap["id_map"][claim["source_id"]]]["media"]
            assets[media["id"]] = {"path": media["storage_path"], "bytes": media["byte_size"], "sha256": media["checksum_sha256"], "width": media["width"], "height": media["height"]}
    images = [r.load(path) for path in sorted((r.RUN / "open-images-01/images").glob("*/*.json"))]
    for im in images:
        assets[im["media_id"]] = im
    cma = r.load(r.RUN / "new-cma-works/plan.json.gz")
    for work in cma["works"]:
        assets[work["media_id"]] = r.load(r.RUN / "new-cma-works/images" / (str(work["object"]["id"]) + ".json.gz"))
    icons = r.load(r.RUN / "icon-paths/plan.json.gz")
    for row in icons["changes"]:
        media = next(x for x in icons["preimages"]["local"] if x["id"] == row["id"])
        assets[row["id"]] = {**row, "path": row["new"], "width": media["width"], "height": media["height"]}
    assert len(images) == 13 and sum(len(p["claims"]) for p in plans) == 26 and len(cma["works"]) == 6
    return assets, plans, images, cma, icons


def assets_live():
    assets, *_ = selected()
    def one(item):
        mid, media = item
        response = requests.get("https://artlines.org" + media["path"], timeout=35)
        response.raise_for_status()
        raw = response.content
        assert response.headers.get("content-type", "").startswith("image/")
        assert len(raw) == media["bytes"] <= 100000
        assert hashlib.sha256(raw).hexdigest() == media["sha256"]
        with Image.open(io.BytesIO(raw)) as image:
            assert image.size == (media["width"], media["height"])
            image.verify()
        return {"media_id": mid, "path": media["path"], "bytes": len(raw), "sha256": media["sha256"], "status": response.status_code}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        result = list(pool.map(one, assets.items()))
    r.save(OUT / "live-assets.json", {"checked_at": r.now(), "assets": result})
    print("Live files verified:", len(result), "all <=100KB with matching checksums and dimensions")


def database(target):
    assets, plans, images, cma, icons = selected()
    checked = []
    with r.connect(target) as db:
        for plan in plans:
            snap = plan["targets"][target]
            for claim in plan["claims"]:
                aid = snap["id_map"][claim["target_id"]]
                old = snap["preimages"][aid]["artwork"]
                row = db.execute("SELECT to_jsonb(a) row FROM artworks a WHERE id=%s", (aid,)).fetchone()["row"]
                for key in ["title", "creation_year_start", "creation_year_end", "date_display", "date_precision", "status", "unlinked_creator_label"]:
                    assert row[key] == old[key], (aid, key)
                assert row["primary_media_id"] == claim["media_id"]
                assert db.execute("SELECT 1 FROM artwork_media WHERE artwork_id=%s AND media_id=%s", (aid, claim["media_id"])).fetchone()
                checked.append(aid)
        for im in images:
            found = db.execute("SELECT a.id::text,a.primary_media_id::text,a.status,a.title,a.date_display FROM artworks a JOIN external_identifiers e ON e.entity_id=a.id AND e.entity_type='artwork' WHERE e.scheme=%s AND e.external_id=%s", (im["scheme"], im["external_id"])).fetchall()
            assert len(found) == 1
            work = found[0]
            assert work["primary_media_id"] == im["media_id"] and work["title"] == im["title"] and work["date_display"] == im["date_display"] and work["status"] == "review"
            checked.append(work["id"])
        orsay = r.load(r.RUN / "orsay-acquisitions/plan.json.gz")
        new_ids = []
        for work in cma["works"]:
            w = work["object"]
            new_ids.append(work["artwork_id"])
            row = db.execute("SELECT to_jsonb(a) row FROM artworks a WHERE id=%s", (work["artwork_id"],)).fetchone()["row"]
            assert row["title"] == w["title"] and row["creation_year_start"] == w["creation_date_earliest"] and row["creation_year_end"] == w["creation_date_latest"]
            assert row["primary_media_id"] == work["media_id"] and row["current_institution_id"] == cma["targets"][target]["institution"]["id"]
            creators = db.execute("SELECT artist_id::text FROM artwork_artists WHERE artwork_id=%s", (row["id"],)).fetchall()
            if work["artist_slug"]:
                assert creators == [{"artist_id": cma["targets"][target]["artists"][work["artist_slug"]]["id"]}]
            else:
                assert not creators and row["unlinked_creator_label"] == w["creators"][0]["description"].split(" (")[0]
            checked.append(row["id"])
        for work in orsay["facts"]["records"]:
            aid = str(uuid.uuid5(uuid.NAMESPACE_URL, "orsay-acquisitions-20261005/work/" + work["object_id"]))
            new_ids.append(aid)
            row = db.execute("SELECT to_jsonb(a) row FROM artworks a WHERE id=%s", (aid,)).fetchone()["row"]
            assert row["title"] == work["title"] and row["creation_year_start"] == work["start"] and row["creation_year_end"] == work["end"] and row["date_precision"] == work["precision"]
            assert row["primary_media_id"] is None and row["current_institution_id"] == orsay["targets"][target]["institution"]["id"]
            assert db.execute("SELECT artist_id::text FROM artwork_artists WHERE artwork_id=%s", (aid,)).fetchall() == [{"artist_id": orsay["targets"][target]["artists"][work["artist_slug"]]["id"]}]
        assert len(new_ids) == 8
        assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND status='review' AND research_candidate AND creation_year_end<=1970", (new_ids,)).fetchone()["n"] == 8
        assert db.execute("SELECT count(*) n FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[]) AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL", (new_ids,)).fetchone()["n"] == 8
        assert not db.execute("SELECT 1 FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[]) AND claim_type='display'", (new_ids,)).fetchone()
        for mid, expected in assets.items():
            row = db.execute("SELECT to_jsonb(m) row FROM media_assets m WHERE id=%s", (mid,)).fetchone()["row"]
            assert row["storage_path"] == expected["path"] and row["checksum_sha256"] == expected["sha256"] and row["byte_size"] == expected["bytes"] <= 100000
            assert row["rights_status"] in {"cc0", "public_domain", "cc_by"}
            assert db.execute("SELECT 1 FROM media_rights_evidence WHERE media_id=%s", (mid,)).fetchone()
        problems = db.execute("""SELECT
          (SELECT count(*) FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.status<>'archived' AND (m.byte_size>100000 OR m.checksum_sha256 IS NULL OR m.storage_path IS NULL OR m.storage_path !~ '^/assets/[a-zA-Z0-9/_-]+\\.(jpg|jpeg|png|webp|avif)$')) invalid_media,
          (SELECT count(*) FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE i.canonical_institution_id IS NOT NULL) stranded_alias_works,
          (SELECT count(*) FROM institutions i JOIN institutions c ON c.id=i.canonical_institution_id WHERE c.canonical_institution_id IS NOT NULL) alias_chains,
          (SELECT count(*) FROM artworks a LEFT JOIN artwork_location_assertions h ON h.artwork_id=a.id AND h.claim_type='holding' AND h.review_state='accepted' AND h.superseded_by IS NULL WHERE a.current_institution_id IS DISTINCT FROM h.institution_id) inconsistent_holdings
        """).fetchone()
        assert all(v == 0 for v in problems.values()), problems
        stats = db.execute("SELECT count(*) works,count(primary_media_id) images,count(*) FILTER(WHERE status='review') review,count(*) FILTER(WHERE status='published') published FROM artworks WHERE status<>'archived'").fetchone()
        museums = db.execute("SELECT i.slug,count(*) works,count(a.primary_media_id) images FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE i.slug=ANY(%s) AND a.status<>'archived' GROUP BY i.slug ORDER BY i.slug", (["musee-du-louvre", "musee-orsay", "cleveland-museum-of-art"],)).fetchall()
    assert len(checked) == len(set(checked)) == 45
    r.save(OUT / (target + "-data.json"), {"checked_at": r.now(), "selected_attachments": len(checked), "new_artworks": len(new_ids), "selected_media": len(assets), "problems": problems, "stats": stats, "museums": museums})
    print(json.dumps({"target": target, "attachments_verified": len(checked), "new_artworks": len(new_ids), "problems": problems, "museums": museums}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["assets", "database"])
    parser.add_argument("--target", choices=["local", "production"])
    args = parser.parse_args()
    if args.command == "assets":
        assets_live()
    else:
        assert args.target
        database(args.target)
