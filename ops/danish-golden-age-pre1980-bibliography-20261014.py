#!/usr/bin/env python3
"""Attach exact bibliographic records for pre-1980 exhibition catalogues."""
import argparse
import datetime
import importlib.util
import json
import uuid
from pathlib import Path

from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "docs/research/danish-golden-age-20261013/catalogue-checklists"
DATA = RUN / "pre1980-catalogue-bibliography.json"
BACKUP = Path.home() / "Library/Application Support/Artline/backups/danish-golden-age-20261013"
OP = "danish-golden-age-pre1980-bibliography-20261014"
NS = uuid.UUID("53d87008-f0ac-4999-bfc5-b35922bdcdab")

spec = importlib.util.spec_from_file_location("catalogue", ROOT / "ops/catalogue-expansion-20261008.py")
catalogue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalogue)


def uid(value):
    return str(uuid.uuid5(NS, OP + "/" + value))


def snapshot(db, records, lock=False):
    event_ids = [record["exhibition_id"] for record in records]
    suffix = " FOR SHARE" if lock else ""
    events = [dict(row["row"]) for row in db.execute(
        "SELECT to_jsonb(e) AS row FROM exhibitions e WHERE id=ANY(%s::uuid[]) ORDER BY id" + suffix,
        (event_ids,),
    )]
    sources = [dict(row["row"]) for row in db.execute(
        "SELECT to_jsonb(s) AS row FROM exhibition_source_records s WHERE source_key='openlibrary' AND source_record_id=ANY(%s) ORDER BY source_record_id" + suffix,
        ([record["edition_id"] for record in records],),
    )]
    publications = [dict(row["row"]) for row in db.execute(
        "SELECT to_jsonb(p) AS row FROM exhibition_publications p WHERE exhibition_id=ANY(%s::uuid[]) ORDER BY id" + suffix,
        (event_ids,),
    )]
    return {"events": events, "sources": sources, "publications": publications}


def plan():
    data = json.loads(DATA.read_text())
    records = data["records"]
    assert len(records) == 4 and len({record["edition_id"] for record in records}) == 4
    assert all(len(record["capture_sha256"]) == 64 for record in records)
    with catalogue.connect() as db:
        before = snapshot(db, records)
    assert len(before["events"]) == 4 and not before["sources"]
    existing_catalogues = [row for row in before["publications"] if row["publication_type"] == "catalogue"]
    assert not existing_catalogues
    payload = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "operation": OP,
        "records": records,
        "before": before,
        "totals": {"catalogues": 4, "readable_checklists": 0, "new_artwork_links": 0},
    }
    (RUN / "pre1980-catalogue-bibliography-plan.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n")
    BACKUP.mkdir(parents=True, exist_ok=True)
    BACKUP.chmod(0o700)
    path = BACKUP / "pre1980-catalogue-bibliography-before.json"
    assert not path.exists()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n")
    path.chmod(0o600)
    print(payload["totals"])


def text(value):
    if isinstance(value, dict):
        return value.get("value")
    return value


def apply():
    planned = json.loads((RUN / "pre1980-catalogue-bibliography-plan.json").read_text())
    assert json.loads((ROOT / "docs/research/danish-golden-age-20261013/cloud-backup.json").read_text())["status"] == "SUCCESSFUL"
    records = planned["records"]
    with catalogue.connect(True) as db, db.transaction():
        db.execute("SET LOCAL lock_timeout='120s'")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute("SELECT pg_advisory_xact_lock(2026101401)")
        assert snapshot(db, records, lock=True) == planned["before"]
        for record in records:
            payload = record["payload"]
            source_id = uid("source/" + record["edition_id"])
            source_url = "https://openlibrary.org/books/" + record["edition_id"]
            db.execute(
                """INSERT INTO exhibition_source_records(
                       id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,
                       capture_url,capture_sha256,source_payload,interpretation)
                   VALUES(%s,%s,'openlibrary',%s,%s,%s,%s,%s,%s,%s)""",
                (source_id, record["exhibition_id"], record["edition_id"], source_url,
                 record["retrieved_at"], record["url"], record["capture_sha256"], Jsonb(payload),
                 Jsonb({
                     "scope": "Exact edition-level bibliographic identity for the exhibition catalogue.",
                     "checklist_access": "No public scan or readable checklist text exposed; bibliographic metadata does not establish individual artwork participation.",
                     "matching": "Title, year, publisher/venue context and exhibition note or subtitle match the Artline exhibition.",
                 })),
            )
            authors = payload.get("by_statement")
            if not authors:
                authors = "; ".join(contribution for contribution in payload.get("contributions", []) if contribution) or None
            identifiers = []
            identifiers.extend("ISBN " + value for value in payload.get("isbn_10", []))
            identifiers.extend("LCCN " + value for value in payload.get("lccn", []))
            identifiers.extend("OCLC " + value for value in payload.get("oclc_numbers", []))
            evidence = {
                "openlibrary_work": record["work_id"],
                "openlibrary_edition": record["edition_id"],
                "publisher": payload.get("publishers"),
                "publication_place": payload.get("publish_places"),
                "subtitle": payload.get("subtitle"),
                "notes": text(payload.get("notes")),
                "identifiers": identifiers,
                "checklist_access": "bibliographic_only",
            }
            db.execute(
                """INSERT INTO exhibition_publications(
                       id,exhibition_id,source_record_id,publication_type,title_label,author_label,
                       publication_date_label,url,source_identifier,page_label,evidence)
                   VALUES(%s,%s,%s,'catalogue',%s,%s,%s,%s,%s,%s,%s)""",
                (uid("publication/" + record["edition_id"]), record["exhibition_id"], source_id,
                 payload.get("title"), authors, payload.get("publish_date"), source_url,
                 "; ".join(identifiers) or record["edition_id"], payload.get("pagination"), Jsonb(evidence)),
            )
    with catalogue.connect() as db:
        after = snapshot(db, records)
    assert len(after["sources"]) == 4
    inserted = [row for row in after["publications"] if row["source_record_id"] in {row["id"] for row in after["sources"]}]
    assert len(inserted) == 4
    result = {"applied_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "operation": OP,
              "catalogues": 4, "readable_checklists": 0, "artwork_links": 0}
    (RUN / "pre1980-catalogue-bibliography-applied.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["plan", "apply"])
    globals()[parser.parse_args().phase]()
