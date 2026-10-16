#!/usr/bin/env python3
"""Attach Royal Danish Library records for exact pre-1980 catalogues."""
import argparse
import datetime
import importlib.util
import json
import re
import uuid
from pathlib import Path

from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "docs/research/danish-golden-age-20261013/catalogue-checklists"
DATA = RUN / "royal-library-pre1980-selection.json"
BACKUP = Path.home() / "Library/Application Support/Artline/backups/danish-golden-age-20261013"
OP = "danish-golden-age-royal-library-pre1980-20261014"
NS = uuid.UUID("f341e74e-a848-46e5-babd-aa64907546e4")

spec = importlib.util.spec_from_file_location("catalogue", ROOT / "ops/catalogue-expansion-20261008.py")
catalogue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalogue)


def uid(value):
    return str(uuid.uuid5(NS, OP + "/" + value))


def snapshot(db, records, lock=False):
    ids = [record["exhibition_id"] for record in records]
    suffix = " FOR SHARE" if lock else ""
    events = [dict(row["row"]) for row in db.execute(
        "SELECT to_jsonb(e) AS row FROM exhibitions e WHERE id=ANY(%s::uuid[]) ORDER BY id" + suffix, (ids,))]
    sources = [dict(row["row"]) for row in db.execute(
        "SELECT to_jsonb(s) AS row FROM exhibition_source_records s WHERE source_key='royal-danish-library-catalogue' AND source_record_id=ANY(%s) ORDER BY source_record_id" + suffix,
        ([record["record_id"] for record in records],),
    )]
    publications = [dict(row["row"]) for row in db.execute(
        "SELECT to_jsonb(p) AS row FROM exhibition_publications p WHERE exhibition_id=ANY(%s::uuid[]) ORDER BY id" + suffix, (ids,))]
    return {"events": events, "sources": sources, "publications": publications}


def plan():
    records = json.loads(DATA.read_text())["records"]
    assert len(records) == 8 and sum(record["new_publication"] for record in records) == 4
    with catalogue.connect() as db:
        before = snapshot(db, records)
    assert len(before["events"]) == 8 and not before["sources"]
    for record in records:
        catalogues = [row for row in before["publications"] if row["exhibition_id"] == record["exhibition_id"] and row["publication_type"] == "catalogue"]
        assert bool(catalogues) != record["new_publication"], record["record_id"]
    payload = {"generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "operation": OP,
               "records": records, "before": before,
               "totals": {"library_records": 8, "new_catalogue_publications": 4, "corroborated_publications": 4, "readable_checklists": 0}}
    (RUN / "royal-library-pre1980-plan.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n")
    BACKUP.mkdir(parents=True, exist_ok=True)
    BACKUP.chmod(0o700)
    path = BACKUP / "royal-library-pre1980-before.json"
    assert not path.exists()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n")
    path.chmod(0o600)
    print(payload["totals"])


def first(display, key):
    values = display.get(key) or []
    return values[0] if values else None


def clean_creator(value):
    if not value:
        return None
    return re.sub(r"\$\$.*", "", value).strip() or None


def apply():
    planned = json.loads((RUN / "royal-library-pre1980-plan.json").read_text())
    records = planned["records"]
    assert json.loads((ROOT / "docs/research/danish-golden-age-20261013/cloud-backup.json").read_text())["status"] == "SUCCESSFUL"
    with catalogue.connect(True) as db, db.transaction():
        db.execute("SET LOCAL lock_timeout='120s'")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute("SELECT pg_advisory_xact_lock(2026101402)")
        current = snapshot(db, records, lock=True)
        assert current == planned["before"]
        for record in records:
            pnx = record["pnx"]
            display = pnx["display"]
            source_id = uid("source/" + record["record_id"])
            full_url = "https://soeg.kb.dk/discovery/fulldisplay?docid=" + record["record_id"] + "&context=L&vid=45KBDK_KGL:KGL"
            db.execute(
                """INSERT INTO exhibition_source_records(
                       id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,
                       capture_url,capture_sha256,source_payload,interpretation)
                   VALUES(%s,%s,'royal-danish-library-catalogue',%s,%s,%s,%s,%s,%s,%s)""",
                (source_id, record["exhibition_id"], record["record_id"], full_url,
                 record["retrieved_at"], record["query_url"], record["capture_sha256"], Jsonb(pnx),
                 Jsonb({"scope": "Exact Royal Danish Library catalogue record.",
                        "identity": "Exhibition title, date and venue or institutional context match the Artline exhibition.",
                        "access": "Physical catalogue holding; no readable checklist file exposed by the discovery record. No artwork participation inferred."})),
            )
            evidence = {"royal_danish_library_record": record["record_id"],
                        "mms": first(display, "mms"), "holdings": display.get("lds24"),
                        "catalogue_notes": display.get("lds25"), "checklist_access": "physical_holding_only"}
            if record["new_publication"]:
                db.execute(
                    """INSERT INTO exhibition_publications(
                           id,exhibition_id,source_record_id,publication_type,title_label,author_label,
                           publication_date_label,url,source_identifier,page_label,evidence)
                       VALUES(%s,%s,%s,'catalogue',%s,%s,%s,%s,%s,%s,%s)""",
                    (uid("publication/" + record["record_id"]), record["exhibition_id"], source_id,
                     first(display, "title"), clean_creator(first(display, "creator")), first(display, "creationdate"),
                     full_url, record["record_id"], first(display, "format"), Jsonb(evidence)),
                )
            else:
                publication = next(row for row in current["publications"] if row["exhibition_id"] == record["exhibition_id"] and row["publication_type"] == "catalogue")
                merged = dict(publication["evidence"] or {})
                merged.update(evidence)
                db.execute("UPDATE exhibition_publications SET evidence=%s WHERE id=%s", (Jsonb(merged), publication["id"]))
    with catalogue.connect() as db:
        after = snapshot(db, records)
    assert len(after["sources"]) == 8
    result = {"applied_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "operation": OP,
              "library_records": 8, "new_catalogue_publications": 4, "readable_checklists": 0, "artwork_links": 0}
    (RUN / "royal-library-pre1980-applied.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["plan", "apply"])
    globals()[parser.parse_args().phase]()
