#!/usr/bin/env python3
"""Match only the supplied research candidates against pinned museum metadata.

No database or images are opened. Literal title/creator/institution/date matches
must identify one source object; collisions remain in the unresolved ledger.
"""
import collections
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parent.parent


def norm(value):
    return " ".join("".join(c for c in unicodedata.normalize("NFD", value or "").casefold()
                           if not unicodedata.combining(c)).split())


def creator_key(value):
    value = re.sub(r"\(\d{4}\s*[-–]\s*\d{4}\)", "", value)
    value = re.sub(r"(?i)\((peintre|painter|artiste)\)", "", value)
    return " ".join(sorted(re.findall(r"[^\W_]+", norm(value))))


def verified(path):
    metadata = json.loads(path.with_name(path.name + ".snapshot.json").read_text())
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    if h.hexdigest() != metadata["sha256"]:
        raise ValueError("changed source: " + str(path))
    metadata["local_path"] = str(path.relative_to(ROOT))
    return metadata


def source_date(s):
    # ISO source birth/death values only, never dates derived from artworks.
    return int(s[:4]) if re.match(r"^\d{4}(?:-|$)", s or "") else None


def main():
    out = Path(sys.argv[1]); out.mkdir(mode=0o700, exist_ok=False)
    stage = ROOT / "docs/research/expanded-20260912-v4"
    report = json.loads((stage / "review.json").read_text())
    entries = {}
    for chunk in report["chunks"]:
        b = (stage / chunk["file"]).read_bytes()
        if hashlib.sha256(b).hexdigest() != chunk["sha256"]:
            raise ValueError("changed staged chunk")
        for r in json.loads(b):
            entries[r["record_id"]] = r["raw"]["csv"]["cells"]
    matches = collections.defaultdict(dict)
    source_root = ROOT / "content/imports/expanded-resolution-20260912"

    # Tate's museum-issued CSV is a historical 2014 snapshot, not a current
    # display record. Artist IDs are source authority IDs, not name hashes.
    tate_artist_path = source_root / "tate-artist_data.csv"
    tate_artwork_path = source_root / "tate-artwork_data.csv"
    ae, we = verified(tate_artist_path), verified(tate_artwork_path)
    with tate_artist_path.open(encoding="utf-8-sig") as f:
        authors = {r["id"]: r for r in csv.DictReader(f)}
    index = collections.defaultdict(list)
    for rid, v in entries.items():
        if v[3] == "Tate": index[(creator_key(v[0]), norm(v[1]), norm(v[2]))].append(rid)
    tate_types = {
        "Oil paint on canvas": "painting", "Oil paint on wood": "painting",
        "Oil paint on board": "painting", "Oil paint on paper": "painting",
        "Oil paint on hardboard": "painting", "Oil paint on cardboard": "painting",
        "Oil paint on mahogany": "painting", "Oil paint on oak": "painting",
        "Acrylic paint on canvas": "painting", "Tempera on canvas": "painting",
        "Watercolour on paper": "watercolor", "Graphite on paper": "drawing",
        "Ink on paper": "drawing", "Etching on paper": "print",
        "Lithograph on paper": "print", "Screenprint on paper": "print",
    }
    with tate_artwork_path.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            a = authors.get(r["artistId"])
            if not a: continue
            parts = r["artist"].split(", ", 1)
            name = " ".join(reversed(parts))
            ids = index.get((creator_key(name), norm(r["title"]), norm(r["dateText"])), [])
            for rid in ids:
                matches[rid]["tate:" + r["id"]] = {
                    "source": "tate", "object_id": r["id"],
                    "object_url": r["url"].replace("http://", "https://"),
                    "title": r["title"], "accession": r["accession_number"],
                    "date_display": r["dateText"], "date_fields": {"year": r["year"]},
                    "work_type": tate_types.get(r["medium"], ""),
                    "type_basis": "Conservative mapping from exact museum medium; unmapped media require review",
                    "medium": r["medium"], "dimensions": r["dimensions"],
                    "painter": {"source_id": a["id"], "name": name, "sort_name": a["name"],
                                "birth": source_date(a["yearOfBirth"]), "death": source_date(a["yearOfDeath"]),
                                "date_display": a["dates"], "role": r["artistRole"],
                                "url": a["url"].replace("http://", "https://")},
                    "institution": {"key": "tate", "name": "Tate", "city": "", "country": "GB", "website": "https://www.tate.org.uk"},
                    "evidence": [we, ae], "source_note": "Museum-owned metadata snapshot last updated October 2014; no current display or venue assignment inferred",
                }
    print("Tate source matching complete", flush=True)

    index = collections.defaultdict(list)
    for rid, v in entries.items():
        if v[3] == "Statens Museum for Kunst (SMK)": index[(norm(v[0]), norm(v[1]), norm(v[2]))].append(rid)
    for path in sorted(source_root.glob("smk-danish-*.json")):
        if ".snapshot." in path.name: continue
        evidence = verified(path)
        for r in json.loads(path.read_text())["items"]:
            p = r.get("production", [])
            dates = r.get("production_date", [])
            if len(p) != 1 or len(dates) != 1: continue
            p, d = p[0], dates[0]
            for t in r.get("titles", []):
                ids = index.get((norm(p.get("creator", "")), norm(t.get("title", "")), norm(d.get("period", ""))), [])
                for rid in ids:
                    oid = r["object_number"]
                    matches[rid]["smk:" + oid] = {
                        "source": "smk", "object_id": oid,
                        "object_url": r.get("frontend_url") or "https://open.smk.dk/artwork/image/" + oid,
                        "title": t["title"], "accession": oid,
                        "date_display": d.get("period", ""),
                        "date_fields": {"start": d.get("start"), "end": d.get("end"), "notes": r.get("production_dates_notes", [])},
                        "work_type": "painting" if any(n["name"] == "Maleri" for n in r.get("object_names", [])) else "",
                        "type_basis": "SMK object_names: Maleri", "medium": "; ".join(r.get("techniques", [])),
                        "dimensions": json.dumps(r.get("dimensions", []), ensure_ascii=False),
                        "painter": {"source_id": p.get("creator_lref", ""),
                                    "name": " ".join(v for v in [p.get("creator_forename"), p.get("creator_surname")] if v) or p.get("creator", ""),
                                    "sort_name": p.get("creator", ""),
                                    "birth": source_date(p.get("creator_date_of_birth")), "death": source_date(p.get("creator_date_of_death")),
                                    "date_display": "", "role": p.get("creator_role", "artist"),
                                    "url": r.get("object_url") or "https://api.smk.dk/api/v1/art/?object_number=" + oid},
                        "institution": {"key": "smk-statens-museum-for-kunst", "name": "Statens Museum for Kunst (SMK)", "city": "Copenhagen", "country": "DK", "website": "https://www.smk.dk"},
                        "evidence": [evidence], "source_note": "Object and creator metadata from SMK; on_display and image fields deliberately not imported",
                    }
                    if p.get("creator_qualifier") or p.get("notes"):
                        matches[rid]["smk:" + oid]["object_context"] = {
                            "creator_qualifier": p.get("creator_qualifier", ""),
                            "creator_notes": p.get("notes", ""),
                        }
    print("SMK source matching complete", flush=True)

    # Joconde notice creation/acquisition dates are deliberately not read as
    # artwork dates. Deposit locations are not silently substituted for holdings.
    index = collections.defaultdict(list)
    for rid, v in entries.items():
        if " — " in v[3]: index[(creator_key(v[0]), norm(v[1]), norm(v[3]))].append(rid)
    path = ROOT / "content/imports/joconde-20260910/joconde.csv"
    evidence = verified(path)
    with path.open() as f:
        for r in csv.DictReader(f, delimiter="|"):
            museum = r["Nom_officiel_musee"] + " — " + r["Ville"]
            ids = index.get((creator_key(r["Auteur"]), norm(r["Titre"]), norm(museum)), [])
            for rid in ids:
                oid = r["Reference"]
                domain = set(x.strip().lower() for x in r["Domaine"].split(";"))
                kind = "painting" if "peinture" in domain else "drawing" if "dessin" in domain else "print" if "estampe" in domain else ""
                m = re.fullmatch(r"(.+?)\s*\((\d{4})-(\d{4})\)", r["Auteur"])
                name = m[1] if m else r["Auteur"]
                matches[rid]["joconde:" + oid] = {
                    "source": "joconde", "object_id": oid,
                    "object_url": "https://www.pop.culture.gouv.fr/notice/joconde/" + oid,
                    "title": r["Titre"], "accession": r["Numero_inventaire"],
                    "date_display": r["Millesime_de_creation"] or r["Periode_de_creation"],
                    "date_fields": {"millesime_de_creation": r["Millesime_de_creation"], "periode_de_creation": r["Periode_de_creation"]},
                    "work_type": kind, "type_basis": "Joconde Domaine: " + r["Domaine"],
                    "medium": r["Materiaux_techniques"], "dimensions": r["Mesures"],
                    "object_context": {"denomination": r["Denomination"], "missing": r["MANQUANT"],
                                       "missing_note": r["MANQUANT_COM"], "deposit": r["Lieu_de_depot"],
                                       "localisation": r["Localisation"]},
                    "painter": {"source_id": "", "name": name, "sort_name": name,
                                "birth": int(m[2]) if m else None, "death": int(m[3]) if m else None,
                                "date_display": r["Auteur"], "role": "artist", "url": "https://www.pop.culture.gouv.fr/notice/joconde/" + oid},
                    "institution": {"key": "joconde-" + r["Code_Museofile"].lower(), "name": museum, "city": r["Ville"], "country": "FR", "website": "https://www.pop.culture.gouv.fr/notice/museo/" + r["Code_Museofile"]},
                    "evidence": [evidence], "source_note": "Creator authority still requires reconciliation; source deposit: " + r["Lieu_de_depot"],
                }
    print("Joconde source matching complete", flush=True)
    resolved, unresolved = [], []
    counts = collections.Counter()
    for rid, v in sorted(entries.items()):
        candidates = matches.get(rid, {})
        if len(candidates) == 1:
            fact = next(iter(candidates.values()))
            fact["research_record_id"] = rid
            fact["csv_cells"] = v
            resolved.append(fact); counts[fact["source"]] += 1
        else:
            unresolved.append({"research_record_id": rid, "reason": "source_collision" if candidates else "no_exact_source_match", "candidates": list(candidates)})
    chunks = []
    for offset in range(0, len(resolved), 500):
        file = f"resolved-{offset//500+1:03d}.json"
        b = (json.dumps(resolved[offset:offset+500], ensure_ascii=False, indent=2) + "\n").encode()
        (out / file).write_bytes(b)
        chunks.append({"file": file, "sha256": hashlib.sha256(b).hexdigest(), "records": min(500, len(resolved)-offset)})
    (out / "unresolved.json").write_text(json.dumps(unresolved, indent=2))
    summary = {"input_sha256": report["input_sha256"], "source_counts": dict(counts), "resolved_entries": len(resolved), "unresolved_entries": len(unresolved), "chunks": chunks}
    (out / "manifest.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k != "chunks"}), flush=True)


if __name__ == "__main__":
    main()
