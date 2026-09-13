#!/usr/bin/env python3
"""Produce a guarded correction from pinned SMK creator qualifiers/notes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("resolver", ROOT / "ops/resolve-expanded-research.py")
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)
facts = {}
directory = ROOT / "docs/research/expanded-resolution-20260912/matches-v3"
manifest = json.loads((directory / "manifest.json").read_text())
for c in manifest["chunks"]:
    raw = (directory / c["file"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == c["sha256"]
    for f in json.loads(raw):
        if f["source"] == "smk": facts[f["object_id"]] = f
reviews = []
for path in sorted((ROOT / "content/imports/expanded-resolution-20260912").glob("smk-danish-*.json")):
    if ".snapshot." in path.name: continue
    receipt = resolver.verified(path)
    for work in json.loads(path.read_text())["items"]:
        oid = work["object_number"]
        if oid not in facts: continue
        assert len(work["production"]) == 1
        creator = work["production"][0]
        if not creator.get("notes") and not creator.get("creator_qualifier"): continue
        # Qualifiers require editorial attribution review. KMSsp71 explicitly
        # identifies a copy after Furini in its note, despite no qualifier field.
        hold = bool(creator.get("creator_qualifier")) or oid == "KMSsp71"
        reviews.append({"object_id": oid, "hold": hold, "evidence": {
            "object_url": facts[oid]["object_url"], "source_snapshot": receipt,
            "creator_metadata": creator, "blocks_promotion": hold,
            "review_reason": "Creator qualification/copy caveat requires editorial review" if hold else "Supplemental creator notes retained; source primary attribution unchanged",
        }})
assert len(reviews) == 20 and sum(r["hold"] for r in reviews) == 8
def quote(s): return "'" + s.replace("'", "''") + "'"
values = ",\n".join("(" + quote(r["object_id"]) + "," + quote(json.dumps(r["evidence"], ensure_ascii=False)) + "::jsonb," + str(r["hold"]).lower() + ")" for r in reviews)
sql = """BEGIN;
SELECT pg_advisory_xact_lock(2026090959);
CREATE TEMP TABLE source_creator_review(object_id text PRIMARY KEY,evidence jsonb,hold boolean) ON COMMIT DROP;
INSERT INTO source_creator_review VALUES
""" + values + """;
DO $$ BEGIN
 IF (SELECT count(*) FROM research_resolutions r JOIN source_creator_review s ON r.source_kind='smk' AND r.source_object_id=s.object_id)<>20 THEN RAISE EXCEPTION 'source review scope changed'; END IF;
END $$;
UPDATE research_resolutions r SET review_evidence=s.evidence,
 state=CASE WHEN s.hold THEN 'conflict' ELSE r.state END,
 note=CASE WHEN s.hold THEN 'creator_attribution_review' ELSE r.note END
 FROM source_creator_review s WHERE r.source_kind='smk' AND r.source_object_id=s.object_id
 AND (r.review_evidence IS DISTINCT FROM s.evidence OR (s.hold AND r.state<>'conflict'));
WITH changed AS (
 UPDATE artworks w SET status='archived',revision=revision+1,updated_at=now(),updated_by='local-european-research'
 WHERE w.status='review' AND w.created_by='local-european-research'
 AND EXISTS(SELECT 1 FROM research_resolutions r JOIN source_creator_review s ON s.object_id=r.source_object_id AND r.source_kind='smk' AND s.hold WHERE r.artwork_id=w.id)
 AND EXISTS(SELECT 1 FROM import_records i JOIN import_jobs j ON j.id=i.import_job_id WHERE i.matched_entity_id=w.id AND i.matched_entity_type='artwork' AND i.outcome='created' AND j.adapter_version='expanded-resolution-v1')
 RETURNING id
) SELECT json_build_object('new_artworks_archived',count(*)) FROM changed;
WITH changed AS (
 UPDATE artists a SET status='archived',revision=revision+1,updated_at=now(),updated_by='local-european-research'
 WHERE a.status='review' AND a.created_by='local-european-research' AND a.slug LIKE '%-research-%'
 AND EXISTS(SELECT 1 FROM research_resolutions r JOIN source_creator_review s ON s.object_id=r.source_object_id AND r.source_kind='smk' AND s.hold WHERE r.artist_id=a.id)
 AND NOT EXISTS(SELECT 1 FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id WHERE aa.artist_id=a.id AND w.status<>'archived')
 RETURNING id
) SELECT json_build_object('new_empty_painters_archived',count(*)) FROM changed;
COMMIT;
"""
out = Path(sys.argv[1]); out.write_text(sql)
(ROOT / "docs/research/expanded-resolution-20260912/smk-creator-reviews.json").write_text(json.dumps(reviews, ensure_ascii=False, indent=2))
print(json.dumps({"reviewed": len(reviews), "held": sum(r["hold"] for r in reviews), "sql_sha256": hashlib.sha256(sql.encode()).hexdigest()}))
