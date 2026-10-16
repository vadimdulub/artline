#!/usr/bin/env python3
"""Complete the official 1830 Charlottenborg catalogue at entry level."""
import argparse
import datetime
import importlib.util
import json
import uuid
from pathlib import Path

from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "docs/research/danish-golden-age-20261013/catalogue-checklists"
DATA = RUN / "charlottenborg-1830-complete.json"
BACKUP = Path.home() / "Library/Application Support/Artline/backups/danish-golden-age-20261013"
EVENT = "41b52f79-6880-5589-8b45-e281d578f670"
OCCURRENCE = "b0c3df03-f67b-5d8b-8fc6-1a1a4a9cac6d"
SOURCE_RECORD_ID = "danish-golden-age-charlottenborg-1830-20261013"
URL = "https://kunstbiblioteket.kb.dk/objekter/udstillingskataloger/Udst_0663.pdf"
SHA256 = "ad6c715927f757f03e2e93de6b9e3aaa0ede02bb67397b75282bcda0ce7987dd"
NS = uuid.UUID("15887edb-0e8e-4a4f-bb1c-462e7bd63349")
OP = "danish-golden-age-charlottenborg-complete-20261013"

spec = importlib.util.spec_from_file_location("catalogue", ROOT / "ops/catalogue-expansion-20261008.py")
catalogue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalogue)


def uid(value):
    # Preserve the IDs used by the first two-entry wave.
    return str(uuid.uuid5(NS, "danish-golden-age-charlottenborg-1830-20261013/" + value))


def snapshot(db, lock=False):
    suffix = " FOR UPDATE" if lock else ""
    source = dict(db.execute(
        "SELECT to_jsonb(s) AS row FROM exhibition_source_records s WHERE source_record_id=%s" + suffix,
        (SOURCE_RECORD_ID,),
    ).fetchone()["row"])
    entries = [dict(row) for row in db.execute(
        """SELECT id::text, catalogue_number, artwork_id::text, source_artwork_id,
                  title_label, creator_label, participation, source_page, evidence, match_basis
           FROM exhibition_entries WHERE source_record_id=%s ORDER BY catalogue_number::int""" + suffix,
        (source["id"],),
    )]
    event = dict(db.execute("SELECT to_jsonb(e) AS row FROM exhibitions e WHERE id=%s" + suffix, (EVENT,)).fetchone()["row"])
    publication = dict(db.execute(
        "SELECT to_jsonb(p) AS row FROM exhibition_publications p WHERE source_record_id=%s" + suffix,
        (source["id"],),
    ).fetchone()["row"])
    coverage = [dict(row["row"]) for row in db.execute(
        "SELECT to_jsonb(c) AS row FROM exhibition_source_coverage c WHERE source_key='royal-danish-library' AND inspected_start_year=1830" + suffix
    )]
    return {"source": source, "entries": entries, "event": event, "publication": publication, "coverage": coverage}


def plan():
    items = json.loads(DATA.read_text())
    assert len(items) == 193 and [item["number"] for item in items] == list(range(1, 194))
    assert all(item["title"] and item["creator"] and 2 <= item["source_page"] <= 15 for item in items)
    with catalogue.connect() as db:
        before = snapshot(db)
    assert len(before["entries"]) == 2
    assert {row["catalogue_number"] for row in before["entries"]} == {"34", "58"}
    assert all(row["artwork_id"] for row in before["entries"])
    payload = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "operation": OP,
        "source_sha256": SHA256,
        "before": before,
        "items": items,
        "totals": {"catalogue_entries": 193, "existing_exact_links": 2, "new_unlinked_entries": 191},
    }
    (RUN / "charlottenborg-1830-complete-plan.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n")
    BACKUP.mkdir(parents=True, exist_ok=True)
    BACKUP.chmod(0o700)
    path = BACKUP / "charlottenborg-1830-complete-before.json"
    assert not path.exists()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n")
    path.chmod(0o600)
    print(payload["totals"])


def apply():
    planned = json.loads((RUN / "charlottenborg-1830-complete-plan.json").read_text())
    assert json.loads((ROOT / "docs/research/danish-golden-age-20261013/cloud-backup.json").read_text())["status"] == "SUCCESSFUL"
    with catalogue.connect(True) as db, db.transaction():
        db.execute("SET LOCAL lock_timeout='120s'")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute("SELECT pg_advisory_xact_lock(2026101308)")
        current = snapshot(db, lock=True)
        assert current == planned["before"]
        source_id = current["source"]["id"]
        existing = {row["catalogue_number"]: row for row in current["entries"]}
        for item in planned["items"]:
            number = str(item["number"])
            if number in existing:
                continue
            evidence = {
                "official_catalogue_sha256": SHA256,
                "source_range": item["source_range"],
                "raw_ocr": item["raw_ocr"],
                "transcription_state": "source-faithful OCR with reviewed creator and number sequence",
                "creation_cutoff_review": "Catalogued in the 1830 exhibition; therefore created before 1980.",
                "identity_state": "No exact surviving production object established; retained as an unlinked catalogue entry.",
            }
            db.execute(
                """INSERT INTO exhibition_entries(
                       id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,
                       catalogue_number,title_label,creator_label,date_label,participation,source_page,evidence,match_basis)
                   VALUES(%s,%s,%s,%s,NULL,%s,%s,%s,%s,'1830','exhibited',%s,%s,NULL)""",
                (uid("entry/" + number), EVENT, source_id, OCCURRENCE, "Udst_0663:" + number,
                 number, item["title"], item["creator"], str(item["source_page"]), Jsonb(evidence)),
            )
        payload = dict(current["source"]["source_payload"] or {})
        payload.update({"pages": 15, "numbered_through": 193, "catalogue_entries": 193})
        interpretation = dict(current["source"]["interpretation"] or {})
        interpretation.update({
            "scope": "Complete official exhibition catalogue, all numbered entries 1–193.",
            "identity": "Two entries retain exact SMK artwork links; all other rows remain explicit unlinked catalogue evidence pending object-level reconciliation.",
            "correction": "The earlier extent of 165 omitted the catalogue's sculpture, architecture, ornament and applied-art sections; corrected from the complete 15-page document.",
        })
        db.execute(
            "UPDATE exhibition_source_records SET source_payload=%s, interpretation=%s WHERE id=%s",
            (Jsonb(payload), Jsonb(interpretation), source_id),
        )
        evidence = dict(current["publication"]["evidence"] or {})
        evidence.update({"catalogue_number_extent": "1–193", "complete_transcription": True, "entry_count": 193})
        db.execute(
            "UPDATE exhibition_publications SET page_label='15 pages', evidence=%s WHERE id=%s",
            (Jsonb(evidence), current["publication"]["id"]),
        )
        for coverage in current["coverage"]:
            details = dict(coverage["details"] or {})
            details.update({"full_catalogue_inspected": True, "numbered_through": 193,
                            "catalogue_entries_ingested": 193, "exact_object_links_applied": 2,
                            "unlinked_identity_backlog": 191})
            db.execute("UPDATE exhibition_source_coverage SET research_state='source_exhausted', details=%s WHERE id=%s", (Jsonb(details), coverage["id"]))
        db.execute("UPDATE exhibitions SET checklist_state='complete', updated_at=now() WHERE id=%s", (EVENT,))
        totals = dict(db.execute(
            "SELECT count(*) AS entries,count(artwork_id) AS linked,count(*) FILTER(WHERE artwork_id IS NULL) AS unlinked FROM exhibition_entries WHERE source_record_id=%s",
            (source_id,),
        ).fetchone())
        assert totals == {"entries": 193, "linked": 2, "unlinked": 191}
    with catalogue.connect() as db:
        after = snapshot(db)
    assert after["event"]["checklist_state"] == "complete"
    result = {"applied_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "operation": OP,
              "totals": totals, "event_checklist_state": after["event"]["checklist_state"]}
    (RUN / "charlottenborg-1830-complete-applied.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n")
    print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["plan", "apply"])
    globals()[parser.parse_args().phase]()
