#!/usr/bin/env python3
"""Prepare a transactional correction of this task's v2 research upload to v4.

No database connection is opened. The generated SQL only removes newly staged
regional/collective creator labels; existing catalogue and prior research survive.
Run the reviewed SQL with psql ON_ERROR_STOP against each backed-up target.
"""
import hashlib
import json
from pathlib import Path
import re
import sys


def inventory(root):
    report = json.loads((root / "review.json").read_text())
    rows = {}
    mapping = {}
    for chunk in report["chunks"]:
        path = root / chunk["file"]
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != chunk["sha256"]:
            raise ValueError("changed review chunk")
        for row in json.loads(data):
            key = row["record_id"]
            if not re.fullmatch("[a-f0-9]{64}", key) or key in rows:
                raise ValueError("invalid or repeated identity")
            rows[key] = row
            mapping[key] = chunk["sha256"]
    return report, rows, mapping


def main():
    root = Path(__file__).resolve().parent.parent / "docs/research"
    old, before, _ = inventory(root / "expanded-20260912-v2")
    new, after, mapping = inventory(root / "expanded-20260912-v4")
    if old["input_sha256"] != new["input_sha256"] or old["source_url"] != new["source_url"]:
        raise ValueError("different research source")
    if not set(after) < set(before) or any(after[k] != before[k] for k in after):
        raise ValueError("correction must only remove entries, never add or rewrite facts")
    removed = sorted(set(before) - set(after))
    if any(not re.match(r"^(Pittore |Various artists$)", before[k]["raw"]["csv"]["cells"][0]) for k in removed):
        raise ValueError("unreviewed creator removal")
    quote = lambda v: "'" + v.replace("'", "''") + "'"
    old_shas = ",".join(quote(c["sha256"]) for c in old["chunks"])
    new_shas = ",".join(quote(c["sha256"]) for c in new["chunks"])
    parts = ["BEGIN;", "SET LOCAL statement_timeout='120s';",
             "SELECT pg_advisory_xact_lock(2026090911);",
             "CREATE TEMP TABLE previous_review_ids ON COMMIT DROP AS SELECT id FROM research_snapshots WHERE sha256 IN (" + old_shas + ");",
             "DO $$ BEGIN IF (SELECT count(*) FROM previous_review_ids) <> " + str(len(old["chunks"])) + " OR (SELECT count(*) FROM research_records WHERE snapshot_id IN (SELECT id FROM previous_review_ids)) <> " + str(len(before)) + " THEN RAISE EXCEPTION 'Previous reviewed snapshot mismatch'; END IF; END $$;",
             "CREATE TEMP TABLE desired_review (record_id text PRIMARY KEY, sha text) ON COMMIT DROP;",
             "COPY desired_review(record_id,sha) FROM stdin;"]
    parts.extend(k + "\t" + mapping.get(k, "\\N") for k in sorted(before))
    parts.append("\\.")
    parts.append("DO $$ BEGIN IF EXISTS (SELECT 1 FROM research_records r WHERE r.snapshot_id IN (SELECT id FROM previous_review_ids) AND (r.source_url <> " + quote(old["source_url"]) + " OR NOT EXISTS (SELECT 1 FROM desired_review d WHERE d.record_id=r.source_record_id))) THEN RAISE EXCEPTION 'Research identity mismatch'; END IF; END $$;")
    for c in new["chunks"]:
        parts.append("INSERT INTO research_snapshots(sha256,snapshot_name,record_count) VALUES(" + quote(c["sha256"]) + "," + quote("Expanded CSV 2026-09-12 v4 " + c["file"]) + "," + str(c["records"]) + ") ON CONFLICT(sha256) DO NOTHING;")
    parts.extend([
        "DELETE FROM research_records r USING desired_review d WHERE r.snapshot_id IN (SELECT id FROM previous_review_ids) AND r.source_record_id=d.record_id AND d.sha IS NULL;",
        "UPDATE research_records r SET snapshot_id=s.id FROM desired_review d JOIN research_snapshots s ON s.sha256=d.sha WHERE r.snapshot_id IN (SELECT id FROM previous_review_ids) AND r.source_record_id=d.record_id AND r.snapshot_id<>s.id;",
        "DELETE FROM research_snapshots WHERE id IN (SELECT id FROM previous_review_ids) AND sha256 NOT IN (" + new_shas + ");",
        "DO $$ BEGIN IF (SELECT count(*) FROM research_records r JOIN research_snapshots s ON s.id=r.snapshot_id JOIN desired_review d ON d.record_id=r.source_record_id AND d.sha=s.sha256) <> " + str(len(after)) + " THEN RAISE EXCEPTION 'Corrected snapshot count mismatch'; END IF; END $$;",
        "COMMIT;"])
    output = Path(sys.argv[1])
    with output.open("x") as f:
        f.write("\n".join(parts) + "\n")
    print(json.dumps({"removed_entries": len(removed), "retained_entries": len(after), "sql_file": str(output)}))


if __name__ == "__main__":
    main()
