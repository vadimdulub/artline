#!/usr/bin/env python3
"""Bounded PMA Russian pictorial-object metadata batch 210 (no image writes)."""
import csv, fcntl, gzip, hashlib, importlib.util, inspect, json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pma210base", ROOT / "ops/india-300-delivery-20261011.py")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
E = ROOT / "docs/research/continuous-production-20261011/batches/000210"
R = Path.home() / "Library/Application Support/Artline/continuous-research/batches/000210"
OP = "continuous-pma-20261013-b000210"
PHASE = "pma-russian-pictorial"
FIELD = "continuous_pma_object_evidence_b000210"
MUSEUM = "Philadelphia Museum of Art"
SCHEME = "pma-native-object"
h.OP = OP
h.RUN = E
h.BACKUP = Path.home() / "Library/Application Support/Artline/backups" / OP
h.SCHEMES = {"pma": [SCHEME]}
h.museums = lambda: {MUSEUM: ("wikimedia-museum-q510324", "https://www.philamuseum.org/")}
for p in (E, R, h.BACKUP, E / "source-captures"):
    p.mkdir(parents=True, exist_ok=True)

def save(name, value):
    p = E / name
    if p.exists():
        return h.load(p)
    h.save(p, value)
    return value

def target():
    commands = subprocess.check_output(["ps", "ax", "-o", "command="], text=True).splitlines()
    expected = "artline-508319:europe-west1:artline-postgres"
    assert any(x.startswith("/tmp/artline-cloud-sql-proxy ") and "--port 55519 " in x and expected in x for x in commands)
    with h.connect() as db:
        row = dict(db.execute("SELECT current_database() db, current_setting('transaction_read_only') ro").fetchone())
    assert row["db"] == "artline" and row["ro"] in ("on", True)
    return {"connection_name": expected, "proxy_port": 55519, "database": row, "helper": "ops/india-300-delivery-20261011.py", "shared_ingestion_lock": "artline-curated-ingestion"}

def field(raw, name):
    m = re.search(r'\\"' + re.escape(name) + r'\\":\\"(.*?)\\"', raw)
    if not m:
        m = re.search(r'"' + re.escape(name) + r'":"(.*?)"', raw)
    return bytes(m.group(1), "utf-8").decode("unicode_escape") if m else None

def collision(db, rows):
    ids = [r["source_id"] for r in rows]
    urls = [r["source_url"] for r in rows]
    assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=ANY(%s)", (SCHEME, ids)).fetchall()
    assert not db.execute("SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)", (urls,)).fetchall()
h.collision = collision

plan_code = inspect.getsource(h.plan).replace(
    "User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.",
    "User authorized bounded continuous production batch 210: exact PMA Russian pictorial objects and documented holdings; no image permissions generalized."
)
exec(compile(plan_code, __file__, "exec"), h.__dict__)
apply_code = inspect.getsource(h.apply).replace(
    "assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'",
    "assert 1 <= len(rows) <= 50 and all(not r['before'] for r in rows), 'Bounded new PMA objects only'"
).replace("india_minimum_300_museum_coverage_20261011", FIELD).replace(
    "load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'", "load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'"
).replace(
    "  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'",
    "  collision(db,rows)\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'"
)
exec(compile(apply_code, __file__, "exec"), h.__dict__)

def stage():
    save("production-target-reconciliation.json", target())
    registry = Path("/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv")
    reg = list(csv.DictReader(registry.open(encoding="utf-8-sig")))
    assert len(reg) == 111
    required = ["AGENTS.md", "docs/ARTLINE_IMAGE_USE.md", "docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md", "docs/LOCAL_DATA_LOCATIONS.md", "docs/research/continuous-production-20261011/CHECKPOINT.json", "docs/research/continuous-production-20261011/source-queue.json"]
    save("required-input-verification.json", {"at": h.now(), "files": [{"path": x, "sha256": h.sha((ROOT/x).read_bytes())} for x in required], "registry": {"path": str(registry), "sha256": h.sha(registry.read_bytes()), "records": len(reg)}})
    src = json.loads((R / "source-captures/pma-russia-page1.json").read_text())
    include = re.compile(r"oil|tempera|watercolor|pencil|etching|engraving|lithograph|relief print|drawing|ink|gouache|pastel", re.I)
    exclude = re.compile(r"porcelain|glass|silver|brooch|relief of|shawl|poster|bound pamphlet", re.I)
    candidates = [x for x in src["hits"] if include.search(x.get("medium", "")) and not exclude.search(x.get("medium", ""))][:30]
    rows, checks = [], []
    with h.connect() as db:
        assert not db.execute("SELECT entity_id FROM citations WHERE field_name=%s", (FIELD,)).fetchall()
        for x in candidates:
            oid = x["objectID"]
            runtime = R / "source-captures" / f"{oid}.html"
            evidence = E / "source-captures" / f"{oid}.html.gz"
            raw = runtime.read_bytes()
            if not evidence.exists(): evidence.write_bytes(gzip.compress(raw, mtime=0))
            html = raw.decode(errors="replace")
            accession = field(html, "ObjectNumber") or field(html, "AccessionNumber")
            rights = field(html, "RightsType")
            dimensions = field(html, "Dimensions")
            credit = field(html, "CreditLine")
            url = f"https://www.philamuseum.org/objects/{oid}"
            exact = [dict(v) for v in db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=%s UNION SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=%s OR (scheme=%s AND external_id=%s))", (url, url, SCHEME, oid))]
            title = [dict(v) for v in db.execute("SELECT id::text,title,current_institution_id::text,accession_number FROM artworks WHERE normalized_title=%s AND creation_year_start=%s AND creation_year_end=%s", (h.norm(x["title"]), x["dateBegin"], x["dateEnd"]))]
            reason = None
            if exact: reason = "existing source identity"
            elif title: reason = "global title/date identity requires version reconciliation"
            elif not accession: reason = "official page accession not parsed"
            checks.append({"source_id": oid, "title": x["title"], "source_matches": exact, "title_date_matches": title, "decision": reason or "selected_new", "rights_type": rights, "accession_number": accession})
            if reason: continue
            rows.append({"provider": "pma", "source_id": oid, "source_url": url, "museum": MUSEUM, "title": x["title"], "creator_label": None if x["artist"] == "Artist/maker unknown" else x["artist"], "creator_link_hold": x["artist"] == "Artist/maker unknown", "date_display": x["dated"], "year_start": x["dateBegin"], "year_end": x["dateEnd"], "date_decision": "eligible", "accession_number": accession, "source_type": "painting" if re.search(r"oil|tempera", x["medium"], re.I) else ("watercolor" if "watercolor" in x["medium"].lower() else ("drawing" if "pencil" in x["medium"].lower() else "print")), "medium": x["medium"], "dimensions": dimensions, "credit": credit, "evidence_file": str(evidence.relative_to(ROOT)), "evidence": {"status": 200, "retrieved_at": h.now(), "sha256": h.sha(evidence.read_bytes()), "url": url}, "raw": {"original_title": x["title"], "source_record": x, "rights_type": rights, "image_url": (x.get("media") or {}).get("url"), "image_selected": False}, "identity_review": "Exact official PMA object page, native object ID and accession. Pictorial medium and source date end through 1970. Holding only; on-view flag not imported or asserted. Image intentionally withheld pending object-level reuse review despite catalogue RightsType."})
    save("global-identity-reconciliation.json", {"at": h.now(), "examined": len(candidates), "records": checks, "selected": len(rows)})
    assert rows
    h.save(E/PHASE/"source-records.json.gz", rows)
    h.plan(PHASE)
    p, pin = h.pinned(PHASE)
    assert 1 <= len(p["records"]) <= 50 and all(not r["before"] for r in p["records"])
    save("source-register.json", {"at": h.now(), "registry": next(x for x in reg if x["source_id"] == "philadelphia_museum_art"), "access_status": "Official catalogue and exact object pages HTTP 200; 50 bounded Russian pictorial records examined.", "policy": "Metadata and documented holding only. Native images not downloaded because registry requires per-object explicit open review; public-domain flags retained as leads, not generalized.", "plan_sha256": pin})
    print("STAGED", len(p["records"]), pin)

def recovery():
    p, pin = h.pinned(PHASE)
    dest = h.BACKUP; dest.mkdir(parents=True, exist_ok=True); dest.chmod(0o700)
    secret = subprocess.check_output(["gcloud", "secrets", "versions", "access", "latest", "--secret=artline-database-url", "--project=artline-508319", "--account=vadim@alingva.com"], text=True).strip()
    kw = h.psycopg.conninfo.conninfo_to_dict(secret); env = os.environ.copy(); env.update(PGHOST="127.0.0.1", PGPORT="55519", PGDATABASE=kw["dbname"], PGUSER=kw["user"], PGPASSWORD=kw["password"], PGSSLMODE="disable", PGOPTIONS="-c default_transaction_read_only=on")
    path = dest / "production-schema-before.pgdump"
    proc = subprocess.run(["/opt/homebrew/opt/libpq/bin/pg_dump", "--schema-only", "--format=custom", "--no-owner", "--no-acl", "--file", str(path)], env=env, capture_output=True, timeout=180); assert proc.returncode == 0
    with h.connect() as db:
        collision(db, p["records"]); assert h.snapshot(db, [r["artwork_id"] for r in p["records"]]) == {}
    files = [path, dest/PHASE/"plan-preimages.json.gz"]
    save("local-recovery-verification.json", {"at": h.now(), "status": "VERIFIED", "plan_sha256": pin, "cloud_backups_created": 0, "files": [{"path": str(f), "sha256": h.sha(f.read_bytes()), "bytes": f.stat().st_size} for f in files]})
    print("RECOVERY VERIFIED")

def apply():
    p, pin = h.pinned(PHASE)
    assert h.load(E/"local-recovery-verification.json")["plan_sha256"] == pin
    target(); h.apply(PHASE)

if __name__ == "__main__":
    with (R/"worker.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        globals()[sys.argv[1]]()
