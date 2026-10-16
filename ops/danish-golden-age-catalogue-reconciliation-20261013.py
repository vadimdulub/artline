#!/usr/bin/env python3
"""Reconcile source-specific Danish Golden Age exhibition catalogue rows.

Every accepted link requires a unique creator/title/date candidate plus object-level
corroboration from the catalogue's holder and dimensions. Repeated titles and
version conflicts remain unlinked.
"""
import argparse
import datetime
import importlib.util
import json
from pathlib import Path

from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "docs/research/danish-golden-age-20261013/catalogue-checklists"
BACKUP = Path.home() / "Library/Application Support/Artline/backups/danish-golden-age-20261013"
OP = "danish-golden-age-catalogue-reconciliation-20261013"

spec = importlib.util.spec_from_file_location("catalogue", ROOT / "ops/catalogue-expansion-20261008.py")
catalogue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalogue)

# Source catalogue number -> (production artwork, source object corroboration).
LINKS = {
    "getty": {
        "1": ("77592d29-06c7-578d-be83-6698ef692a9b", "Getty accession 85.PA.43; exact creator, title, 1841 date and object dimensions"),
    },
    "gardens": {
        "3": ("318f4958-8e96-4d13-9dc9-d576154ef4af", "Cleveland 1977.116; exact 43.5 x 34.6 cm object"),
        "8": ("324cc656-b7fa-4f56-8d4e-6b3e950f75ba", "Met 15.30.24; exact 17.1 x 21.3 cm object"),
        "15": ("139b2896-c8e0-4b02-8a18-bea0bac84981", "NGA 1983.1.32; exact 81.3 x 65.1 cm object"),
        "18": ("5d5074ea-7596-418e-acf5-6c32b170ec58", "AIC 1933.1153; exact 60.2 x 73.3 cm object"),
        "23": ("250f7fa5-175b-44c0-bd78-1f40b0d5b7d9", "Tate N04413; exact 76.2 x 99.4 cm object"),
        "26": ("aa1e43ec-3f19-4ffe-b111-38dacaca51a5", "SMK KMS3570; exact 79.5 x 63.5 cm object"),
        "32": ("df064321-b2f5-5ccc-af9f-500be48c771c", "National Gallery of Victoria; exact creator, title, 1882 date and 92.8 x 73.5 cm object"),
        "50": ("84ca7617-d3cc-4374-9776-324ab6fe1deb", "Met 59.142; exact 72.7 x 54.3 cm object; distinguished from private-collection no. 49"),
        "51": ("1e26c3d4-d6e6-443d-9f15-fdd0883e6404", "Met 64.156; exact 60 x 73 cm object"),
        "56": ("e6b8ea80-bf3f-5ae0-b1bf-994976397e3a", "Carmen Thyssen-Bornemisza collection; exact 35.5 x 49 cm object"),
        "62": ("78df5778-dfa5-4155-abcd-8b3a82897c85", "NGA 1970.17.54; exact 73.4 x 92.1 cm object"),
        "66": ("f3552d55-7e52-49c7-a67b-ff0fac8d7436", "Cleveland 1950.582; exact holder and object identity; catalogue reports framed dimensions"),
        "94": ("088f5c26-f073-54a2-ad91-c8fe29ccf3d2", "Thyssen CTB.1993.6; exact 75.7 x 100 cm object"),
        "96": ("da6e9738-adfe-5d6c-9c4d-338389eb7c1e", "Carmen Thyssen-Bornemisza collection; exact 92.3 x 73.3 cm object"),
    },
}

SOURCE_RECORDS = {
    "getty": "danish-golden-age-catalogue-checklists-20261013/beyond-the-light",
    "gardens": "danish-golden-age-impressionist-gardens-20261013",
}


def rows(db, lock=False):
    result = {}
    suffix = " FOR UPDATE" if lock else ""
    for group, source_record_id in SOURCE_RECORDS.items():
        numbers = list(LINKS[group])
        query = """SELECT ee.id::text, ee.catalogue_number, ee.artwork_id::text,
                          ee.title_label, ee.creator_label, ee.date_label,
                          ee.match_basis, ee.evidence,
                          esr.id::text AS source_record_uuid
                   FROM exhibition_entries ee
                   JOIN exhibition_source_records esr ON esr.id=ee.source_record_id
                   WHERE esr.source_record_id=%s AND ee.catalogue_number=ANY(%s)
                   ORDER BY ee.catalogue_number""" + suffix
        found = [dict(row) for row in db.execute(query, (source_record_id, numbers))]
        assert len(found) == len(numbers), (group, len(found), len(numbers))
        result[group] = found
    return result


def artworks(db):
    ids = [artwork_id for group in LINKS.values() for artwork_id, _ in group.values()]
    found = [dict(row) for row in db.execute(
        """SELECT a.id::text, a.title, a.creation_year_start, a.creation_year_end,
                  a.status, a.accession_number, a.dimensions_text, i.name AS institution
           FROM artworks a LEFT JOIN institutions i ON i.id=a.current_institution_id
           WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id""", (ids,))]
    assert len(found) == len(set(ids))
    assert all(row["status"] != "archived" for row in found)
    return found


def plan():
    with catalogue.connect() as db:
        before = rows(db)
        works = artworks(db)
    assert all(row["artwork_id"] is None for group in before.values() for row in group)
    payload = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "operation": OP,
        "entries_before": before,
        "artworks": works,
        "links": LINKS,
        "totals": {"links": sum(map(len, LINKS.values())), "getty": len(LINKS["getty"]), "gardens": len(LINKS["gardens"])},
        "held": {
            "reason": "Repeated titles, holder/version conflicts, year conflicts, or missing object-level corroboration remain unlinked.",
            "examples": ["Impressionist Gardens nos. 49, 79 and 80", "Getty checklist rows without a unique accession/object concordance"],
        },
    }
    (RUN / "catalogue-reconciliation-plan.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n")
    BACKUP.mkdir(parents=True, exist_ok=True)
    BACKUP.chmod(0o700)
    backup = BACKUP / "catalogue-reconciliation-before.json"
    assert not backup.exists()
    backup.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n")
    backup.chmod(0o600)
    print(payload["totals"])


def apply():
    plan_data = json.loads((RUN / "catalogue-reconciliation-plan.json").read_text())
    assert json.loads((ROOT / "docs/research/danish-golden-age-20261013/cloud-backup.json").read_text())["status"] == "SUCCESSFUL"
    with catalogue.connect(True) as db, db.transaction():
        db.execute("SET LOCAL lock_timeout='120s'")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute("SELECT pg_advisory_xact_lock(2026101307)")
        current = rows(db, lock=True)
        assert current == plan_data["entries_before"]
        assert artworks(db) == plan_data["artworks"]
        for group, entries in current.items():
            for entry in entries:
                artwork_id, basis = LINKS[group][entry["catalogue_number"]]
                evidence = dict(entry["evidence"] or {})
                evidence["reconciliation_20261013"] = {
                    "operation": OP,
                    "basis": basis,
                    "safeguard": "Unique creator/title/date candidate corroborated by catalogue holder and/or exact dimensions; no title-only match.",
                }
                db.execute(
                    """UPDATE exhibition_entries
                       SET artwork_id=%s, match_basis=%s, evidence=%s
                       WHERE id=%s AND artwork_id IS NULL""",
                    (artwork_id, basis, Jsonb(evidence), entry["id"]),
                )
        assert db.execute(
            "SELECT count(*) AS n FROM exhibition_entries WHERE id=ANY(%s::uuid[]) AND artwork_id IS NOT NULL",
            ([entry["id"] for group in current.values() for entry in group],),
        ).fetchone()["n"] == plan_data["totals"]["links"]
    with catalogue.connect() as db:
        after = rows(db)
        totals = dict(db.execute(
            """SELECT count(*) AS entries, count(artwork_id) AS linked,
                      count(*) FILTER (WHERE artwork_id IS NULL) AS unlinked
               FROM exhibition_entries ee JOIN exhibition_source_records esr ON esr.id=ee.source_record_id
               WHERE esr.source_record_id=ANY(%s)""", (list(SOURCE_RECORDS.values()),)).fetchone())
    output = {"applied_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "operation": OP, "updated": plan_data["totals"], "source_totals": totals, "entries_after": after}
    (RUN / "catalogue-reconciliation-applied.json").write_text(json.dumps(output, ensure_ascii=False, indent=2, default=str) + "\n")
    print(output["updated"], output["source_totals"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["plan", "apply"])
    globals()[parser.parse_args().phase]()
