"""Translate the revised guide prose; retain established names, titles and evidence.

Uses the existing Artline Cloud Translation service. Cached responses are keyed
by exact source text and locale. Does not read or write a catalogue database.
"""

raise SystemExit("Disabled by user instruction on 12 October 2026: do not use Google services, including Cloud Translation.")

import concurrent.futures
import hashlib
import html
import json
import re
import subprocess
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
GUIDES = ROOT / "apps/web/content/articles/museum-guides"
EVIDENCE = ROOT / "docs/research/guide-prose-20261011"
CACHE = EVIDENCE / "translations-llm"
CACHE.mkdir(parents=True, exist_ok=True)
DATES = json.loads((EVIDENCE / "date-wording-changes.json").read_text())
DATE_IDS = {row["id"] for row in DATES}
LOCALES = ["ru", "it", "de", "zh", "fr", "es", "pt", "ja", "ar"]
MODEL = "projects/artline-508319/locations/us-central1/models/general/translation-llm"
token = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
HEADERS = {"Authorization": "Bearer " + token, "x-goog-user-project": "artline-508319"}


def translate(pair):
    source_path, locale = pair
    source = json.loads(source_path.read_text())
    destination = source_path.with_name(locale + ".json")
    edition = json.loads(destination.read_text())
    assert [w["id"] for w in source["works"]] == [w["id"] for w in edition["works"]]
    items = []
    for key in ["title", "subtitle", "introduction", "visitNote", "selectionNote"]:
        items.append(([key], source[key]))
    for i, work in enumerate(source["works"]):
        for key in ["description", "importance"]:
            items.append((["works", i, key], work[key]))
        if work["id"] in DATE_IDS:
            items.append((["works", i, "date"], work["date"]))
    for i, book in enumerate(source["books"]):
        items.append((["books", i, "note"], book["note"]))
    for key in ["contextNote", "all", "allHint", "painters", "paintersHint"]:
        items.append((["labels", key], source["labels"][key]))
    # Limit both characters and segment count, preserving paragraph context.
    batches, batch, size = [], [], 0
    for item in items:
        if batch and (size + len(item[1]) > 22000 or len(batch) >= 90):
            batches.append(batch)
            batch, size = [], 0
        batch.append(item)
        size += len(item[1])
    if batch:
        batches.append(batch)
    for batch in batches:
        texts = [item[1] for item in batch]
        digest = hashlib.sha256(json.dumps([MODEL, locale, texts], ensure_ascii=False).encode()).hexdigest()
        cached = CACHE / (digest + ".json")
        if cached.exists():
            result = json.loads(cached.read_text())
        else:
            for attempt in range(5):
                response = requests.post(
                    "https://translation.googleapis.com/v3/projects/artline-508319/locations/us-central1:translateText",
                    headers=HEADERS,
                    json={"model": MODEL, "contents": texts, "mimeType": "text/plain", "sourceLanguageCode": "en", "targetLanguageCode": locale},
                    timeout=240,
                )
                if response.ok or response.status_code not in [429, 500, 502, 503, 504]:
                    break
                time.sleep(2 ** attempt + 1)
            response.raise_for_status()
            result = response.json()
            cached.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        assert len(result["translations"]) == len(batch)
        for (keys, _), translated in zip(batch, result["translations"]):
            target = edition
            for key in keys[:-1]:
                target = target[key]
            target[keys[-1]] = html.unescape(translated["translatedText"])
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(edition, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(destination)
    return {"slug": source["slug"], "locale": locale, "fields": len(items), "sourceCharacters": sum(len(value) for _, value in items)}


def apply_editorial_edits():
    """Apply recorded edits after translation, without changing source evidence."""
    overrides = json.loads((EVIDENCE / "editorial-overrides.json").read_text())
    for destination in sorted(GUIDES.glob("*/*.json")):
        if destination.stem == "en":
            continue
        edition = json.loads(destination.read_text())
        def plain(value):
            return re.sub(r"\*([^*]+)\*", r"\1", value)
        for key in ["title", "subtitle", "introduction", "visitNote", "selectionNote"]:
            edition[key] = plain(edition[key])
        edition["title"] = edition["title"].rstrip(".。")
        for work in edition["works"]:
            for key in ["description", "importance", "title"]:
                work[key] = plain(work[key])
            work["title"] = work["title"].rstrip(".。")
        for book in edition["books"]:
            book["note"] = plain(book["note"])
        for row in overrides:
            if row["slug"] != edition["slug"] or row["locale"] != edition["locale"]:
                continue
            target = edition
            for key in row["path"][:-1]:
                target = target[key]
            target[row["path"][-1]] = row["value"]
        destination.write_text(json.dumps(edition, ensure_ascii=False, indent=2) + "\n")
    glossary = json.loads((EVIDENCE / "material-glossary.json").read_text())
    terms = {term["en"]: term for term in glossary["terms"]}
    for source_path in sorted(GUIDES.glob("*/en.json")):
        source = json.loads(source_path.read_text())
        for locale in glossary["locales"]:
            destination = source_path.with_name(locale + ".json")
            edition = json.loads(destination.read_text())
            for i, work in enumerate(source["works"]):
                if not work["medium"]:
                    continue
                canonical = glossary["aliases"].get(work["medium"], work["medium"])
                edition["works"][i]["medium"] = terms[canonical][locale]
            destination.write_text(json.dumps(edition, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    import sys
    if "--editorial-only" in sys.argv:
        apply_editorial_edits()
        raise SystemExit(0)
    pairs = [(source, locale) for source in sorted(GUIDES.glob("*/en.json")) for locale in LOCALES]
    report = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(translate, pairs):
            report.append(result)
            print(json.dumps(result), flush=True)
    (EVIDENCE / "translation-run.json").write_text(json.dumps(report, indent=2) + "\n")
    apply_editorial_edits()
