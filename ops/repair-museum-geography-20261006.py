#!/usr/bin/env python3
"""Add twelve source-verified museum venues; never infer artwork display.

Planning and verification are read-only. Applying requires a pinned per-target
plan, full preimage backups, and a transaction that checks for concurrent edits.
No artworks, holdings, editorial states, or existing place values are changed.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import uuid
from pathlib import Path

from bs4 import BeautifulSoup

spec = importlib.util.spec_from_file_location("audit", Path(__file__).with_name("audit-museum-gaps-20261005.py"))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
r = audit.r
OP = "museum-geography-20261006"
RUN = r.RUN / "venue-geography"
BACKUP = Path.home() / "Library/Application Support/Artline/backups" / OP
EDITOR = "local-european-research"
# Reviewed address fragments from successful official-page captures. The three
# blocked/rate-limited source captures are deliberately excluded from this batch.
ADDRESS = {
    "smithsonian-american-art-museum": "8th and G Streets, NW",
    "wikimedia-museum-q59435": "Museumsplatz 1, 1070 Wien",
    "wikimedia-museum-q639791": "99 Gansevoort Street, New York",
    "wikimedia-museum-q6352575": "1080 Chapel Street, New Haven",
    "wikimedia-museum-q210081": "600 N. Charles St.",
    "ateneum-art-museum": "Kaivokatu 2, 00100 Helsinki",
    "spain-research-museum-q640447": "23, rue Madame de Sévigné, Paris",
    "wikimedia-museum-q59546080": "Avenue Winston-Churchill, 75008 Paris",
    "wikimedia-museum-q857276": "11 avenue du Président Wilson 75116 Paris",
    "wikimedia-museum-q213322": "Cromwell Road, London, SW7 2RL",
    "wikimedia-museum-q371908": "Albertinaplatz",
    "wikimedia-museum-q505873": "1040 Wien, Karlsplatz 8",
}


def uid(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, OP + "/" + key))


def verified_facts():
    facts = []
    for row in r.load(r.RUN / "reviewed-museum-venues.json.gz"):
        if row["institution_slug"] not in ADDRESS:
            continue
        receipt = row["source_receipt"]
        assert receipt["status"] == 200
        body = gzip.decompress((r.ROOT / receipt["body_path"]).read_bytes())
        assert r.sha(body) == receipt["sha256"]
        text = " ".join(BeautifulSoup(body, "html.parser").get_text(" ", strip=True).split())
        fragment = ADDRESS[row["institution_slug"]]
        assert fragment in text, (row["institution_slug"], fragment)
        facts.append({**row, "verified_address_fragment": fragment})
    assert len(facts) == 12
    return facts


def snapshot(db, fact):
    institution = db.execute("SELECT to_jsonb(i) row FROM institutions i WHERE slug=%s", (fact["institution_slug"],)).fetchone()["row"]
    venues = [x["row"] for x in db.execute("SELECT to_jsonb(v) row FROM institution_venues v WHERE institution_id=%s ORDER BY id", (institution["id"],))]
    places = [x["row"] for x in db.execute("SELECT to_jsonb(p) row FROM places p WHERE lower(name)=lower(%s) AND country_code=%s ORDER BY id", (fact["city"], fact["country"]))]
    assert len(places) <= 1, "Ambiguous city identity"
    return {"institution": institution, "venues": venues, "places": places}


def plan(target):
    path = RUN / (target + "-plan.json.gz")
    if path.exists():
        print(target, "existing plan retained")
        return
    rows = []
    with r.connect(target) as db:
        for fact in verified_facts():
            old = snapshot(db, fact)
            assert not old["venues"] and not old["institution"]["canonical_institution_id"]
            assert db.execute("SELECT 1 FROM countries WHERE code=%s", (fact["country"],)).fetchone()
            place_id = old["places"][0]["id"] if old["places"] else uid("place/" + fact["country"] + "/" + fact["city"])
            assert old["institution"]["place_id"] in (None, place_id), "Existing institution geography differs"
            rows.append({"fact": fact, "before": old, "place_id": place_id, "venue_id": uid("venue/" + fact["institution_slug"]), "venue_slug": fact["institution_slug"] + "-verified-venue"})
    r.save_gz(path, {"operation": OP, "target": target, "planned_at": r.now(), "rows": rows})
    print(target, "planned", len(rows), "verified museum venues")


def apply(target):
    path = RUN / (target + "-plan.json.gz")
    data = r.load(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    r.save_gz(BACKUP / (target + "-preimages.json.gz"), data)
    with r.connect(target, readonly=False) as db, db.transaction():
        db.execute("SET LOCAL lock_timeout='3s'")
        db.execute("SELECT pg_advisory_xact_lock(202610061)")
        ids = [row["before"]["institution"]["id"] for row in data["rows"]]
        db.execute("SELECT id FROM institutions WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE", (ids,)).fetchall()
        existing = db.execute("SELECT count(*) n FROM institution_venues WHERE id=ANY(%s::uuid[])", ([row["venue_id"] for row in data["rows"]],)).fetchone()["n"]
        if existing:
            assert existing == len(data["rows"]), "Partial prior application; review required"
            verify_rows(db, data)
            print(target, "already applied", existing)
            return
        for row in data["rows"]:
            assert snapshot(db, row["fact"]) == row["before"], "Museum or place changed after plan"
        db.execute("INSERT INTO sources(id,slug,name,source_type) VALUES(%s,%s,%s,'collection_page')", (uid("source"), OP, "Official museum visitor addresses reviewed October 2026"))
        for row in data["rows"]:
            fact, old = row["fact"], row["before"]
            if not old["places"]:
                db.execute("INSERT INTO places(id,name,normalized_name,country_code) VALUES(%s,%s,%s,%s)", (row["place_id"], fact["city"], r.norm(fact["city"]), fact["country"]))
            if old["institution"]["place_id"] is None:
                db.execute("UPDATE institutions SET place_id=%s,updated_at=now() WHERE id=%s AND place_id IS NULL", (row["place_id"], old["institution"]["id"]))
            db.execute("INSERT INTO institution_venues(id,institution_id,slug,name,place_id,visit_url,source_url,checked_at,status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'review')", (row["venue_id"], old["institution"]["id"], row["venue_slug"], fact["name"], row["place_id"], fact["url"], fact["url"], fact["source_receipt"]["retrieved_at"]))
            note = ("Official visitor page identifies the museum venue in " + fact["city"] + ", " + fact["country"] + ": " + fact["address"] + ". Venue geography only; this does not place individual artworks in the building or assert current display, opening hours or ticket availability. Source capture SHA-256 " + fact["source_receipt"]["sha256"] + "; reviewed plan SHA-256 " + digest + ".")
            db.execute("INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'institution',%s,'verified_venue',%s,%s,%s,%s,%s)", (uid("citation/" + fact["institution_slug"]), old["institution"]["id"], uid("source"), fact["url"], note, fact["source_receipt"]["retrieved_at"], EDITOR))
        after = verify_rows(db, data)
    r.save_gz(BACKUP / (target + "-after.json.gz"), {"plan_sha256": digest, "rows": after})
    print(target, "added", len(after), "verified venues; no artwork or display changes")


def verify_rows(db, data):
    after = []
    for row in data["rows"]:
        cur = snapshot(db, row["fact"])
        old = row["before"]["institution"]
        assert {k: v for k, v in old.items() if k not in {"place_id", "updated_at"}} == {k: v for k, v in cur["institution"].items() if k not in {"place_id", "updated_at"}}
        assert cur["institution"]["place_id"] == row["place_id"]
        assert len(cur["venues"]) == 1
        venue = cur["venues"][0]
        for key, expected in {"id": row["venue_id"], "place_id": row["place_id"], "status": "review", "visit_url": row["fact"]["url"], "source_url": row["fact"]["url"], "name": row["fact"]["name"]}.items():
            assert venue[key] == expected, key
        assert len(cur["places"]) == 1 and cur["places"][0]["country_code"] == row["fact"]["country"]
        assert db.execute("SELECT 1 FROM citations WHERE id=%s AND source_url=%s", (uid("citation/" + row["fact"]["institution_slug"]), row["fact"]["url"])).fetchone()
        assert not db.execute("SELECT 1 FROM artwork_location_assertions WHERE venue_id=%s LIMIT 1", (row["venue_id"],)).fetchone()
        after.append(cur)
    return after


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "apply", "verify"])
    parser.add_argument("--target", required=True, choices=["local", "production"])
    args = parser.parse_args()
    if args.command == "verify":
        with r.connect(args.target) as connection:
            result = verify_rows(connection, r.load(RUN / (args.target + "-plan.json.gz")))
        print(args.target, "verified", len(result), "venues")
    else:
        {"plan": plan, "apply": apply}[args.command](args.target)
