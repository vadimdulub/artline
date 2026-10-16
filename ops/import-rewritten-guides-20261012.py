#!/usr/bin/env python3
"""Import the reviewed all-guides manuscript into file-backed site editions.

The importer changes editorial guide files only. It validates every guide,
locale, selected artwork and correction before writing; it never opens the
catalogue database.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "apps/web/content/articles"
LOCALES = ("en", "ru", "it", "de", "zh", "fr", "es", "pt", "ja", "ar")
UPDATED = "2026-10-12"
MARKER = re.compile(r"<!-- guide_slug: ([a-z0-9-]+); locale: ([a-z]{2}) -->")


def paragraphs(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", value) if part.strip() and not part.strip().startswith("<a ")]


def clean_work_copy(value: str) -> str:
    value = re.sub(r"<!-- artwork_id: [0-9a-f-]+ -->", "", value)
    value = re.sub(r"^\[[^]\n]+\]\([^\n]+\)\s*$", "", value, flags=re.MULTILINE)
    value = re.split(r"\n<a id=", value, maxsplit=1)[0]
    value = re.split(r"\n## \d+\.", value, maxsplit=1)[0]
    return "\n\n".join(paragraphs(value))


def parse_manuscript(path: Path) -> tuple[dict[tuple[str, str], dict], list[dict]]:
    text = path.read_text()
    corrections_at = text.index("## Metadata and factual corrections")
    source_notes_at = text.index("## Source-review notes")
    body = text[:corrections_at]
    matches = list(MARKER.finditer(body))
    assert len(matches) == 900, f"Expected 900 language editions, found {len(matches)}"
    editions: dict[tuple[str, str], dict] = {}
    for index, match in enumerate(matches):
        slug, locale = match.groups()
        assert locale in LOCALES, (slug, locale)
        segment = body[match.end() : matches[index + 1].start() if index + 1 < len(matches) else len(body)]
        segment = segment.split("\n---\n", 1)[0]
        title_match = re.search(r"^#### (.+)$", segment, re.MULTILINE)
        assert title_match, (slug, locale, "missing title")
        title = title_match.group(1).strip()
        remainder = segment[title_match.end() :]
        headings = list(re.finditer(r"^##### (.+)$", remainder, re.MULTILINE))
        assert headings, (slug, locale, "missing sections")
        opening = paragraphs(remainder[: headings[0].start()])
        assert len(opening) >= 2, (slug, locale, "deck/introduction missing")
        sections = []
        for section_index, heading in enumerate(headings):
            raw = remainder[heading.end() : headings[section_index + 1].start() if section_index + 1 < len(headings) else len(remainder)]
            artwork = re.search(r"<!-- artwork_id: ([0-9a-f-]+) -->", raw)
            copy = clean_work_copy(raw)
            assert copy, (slug, locale, heading.group(1), "empty copy")
            sections.append({"title": heading.group(1).strip(), "artworkId": artwork.group(1) if artwork else None, "paragraphs": paragraphs(copy)})
        editions[slug, locale] = {
            "slug": slug,
            "locale": locale,
            "title": title,
            "subtitle": opening[0],
            "introduction": opening[1:],
            "sections": sections,
        }

    correction_rows = []
    correction_text = text[corrections_at:source_notes_at]
    for line in correction_text.splitlines():
        if not line.startswith("| ") or line.startswith("| ---") or "Guide | Artwork ID" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        assert len(cells) == 6, cells
        correction_rows.append({
            "slug": cells[0],
            "artworkId": cells[1].strip("`"),
            "field": cells[2],
            "prior": cells[3],
            "revised": cells[4],
        })
    assert len(correction_rows) == 56, f"Expected 56 corrections, found {len(correction_rows)}"
    return editions, correction_rows


def guide_paths() -> dict[str, Path]:
    result = {}
    for family in ("artist-guides", "museum-guides"):
        for path in (CONTENT / family).glob("*/en.json"):
            assert path.parent.name not in result, path.parent.name
            result[path.parent.name] = path.parent
    assert len(result) == 89, len(result)
    return result


def date_bounds(label: str) -> tuple[int | None, int | None]:
    if label.startswith("exhibited ") or "current Thyssen record" in label or "century" in label.casefold():
        return None, None
    years = [int(year) for year in re.findall(r"(?<!\d)(1\d{3}|20\d{2})(?!\d)", label)]
    return (min(years), max(years)) if years else (None, None)


def apply_correction(work: dict, correction: dict) -> None:
    field, value = correction["field"], correction["revised"]
    if field in {"object_source", "source_url"}:
        work["source"] = value
    elif field == "date":
        work["date"] = value
        work["start"], work["end"] = date_bounds(value)
    elif field == "collection":
        work["museum"] = value
    elif field == "medium":
        work["medium"] = value
    elif field == "title":
        work["catalogueTitle"] = value
    elif field == "description":
        # The replacement manuscript already contains the corrected full commentary.
        pass
    elif field == "artist":
        if correction["artworkId"] == "12d94e28-a350-56cc-a70b-7e7fef605e97":
            work["artist"] = "Titian"
            work["artists"] = [{"name": "Titian", "role": "primary", "slug": "titian-q47551"}]
            work["catalogueArtistSlug"] = None
        elif correction["artworkId"] == "ebfed71f-664e-5f17-ba32-2b4450eaa613":
            work["artist"] = value
            work["artists"] = [
                {"name": "Giovanni Bellini", "role": "primary", "slug": "giovanni-bellini-q17169"},
                {"name": "Titian", "role": "later landscape alterations", "slug": "titian-q47551"},
            ]
        else:
            raise AssertionError(correction)
    elif field == "artist_attribution":
        work["artist"] = value
        work["artists"] = [{"name": "Ferdinand Bol", "role": "attributed", "slug": "ferdinand-bol-q374039"}]
    else:
        raise AssertionError(correction)


def write_json(path: Path, value: object, check: bool) -> None:
    output = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if check:
        assert path.exists() and path.read_text() == output, f"Stale generated file: {path}"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output)


def import_guides(manuscript: Path, check: bool) -> None:
    editions, corrections = parse_manuscript(manuscript)
    paths = guide_paths()
    expected = {(slug, locale) for slug in paths for locale in LOCALES} | {("art-history-timeline", locale) for locale in LOCALES}
    assert set(editions) == expected, (len(editions), len(expected), sorted(set(editions) ^ expected)[:10])
    correction_lookup: dict[tuple[str, str], list[dict]] = {}
    for correction in corrections:
        assert correction["slug"] in paths, correction
        correction_lookup.setdefault((correction["slug"], correction["artworkId"]), []).append(correction)

    total_works = 0
    summaries: dict[str, dict] = {}
    for slug, folder in paths.items():
        en_ids = None
        for locale in LOCALES:
            manuscript_edition = editions[slug, locale]
            guide_path = folder / f"{locale}.json"
            guide = json.loads(guide_path.read_text())
            work_sections = [section for section in manuscript_edition["sections"] if section["artworkId"]]
            closing_sections = [section for section in manuscript_edition["sections"] if not section["artworkId"]]
            ids = [section["artworkId"] for section in work_sections]
            current_ids = [work["id"] for work in guide["works"]]
            assert ids == current_ids, (slug, locale, "artwork identity/order mismatch")
            assert closing_sections and manuscript_edition["sections"][-len(closing_sections):] == closing_sections, (slug, locale, "closing section interleaved")
            en_ids = en_ids or ids
            assert ids == en_ids, (slug, locale, "localized selection mismatch")
            guide.update(
                title=manuscript_edition["title"],
                subtitle=manuscript_edition["subtitle"],
                introduction="\n\n".join(manuscript_edition["introduction"]),
                closingSections=[{"title": section["title"], "paragraphs": section["paragraphs"]} for section in closing_sections],
                updated=UPDATED,
            )
            for work, section in zip(guide["works"], work_sections, strict=True):
                work["title"] = section["title"].removeprefix(re.match(r"^\d+\s+", section["title"]).group(0)) if re.match(r"^\d+\s+", section["title"]) else section["title"]
                work["description"] = "\n\n".join(section["paragraphs"])
                work["importance"] = ""
                for correction in correction_lookup.get((slug, work["id"]), []):
                    apply_correction(work, correction)
            total_works += len(guide["works"])
            write_json(guide_path, guide, check)
            if locale == "en":
                summaries[slug] = {"title": guide["title"], "subtitle": guide["subtitle"], "updated": UPDATED}

    assert total_works == 17_950, total_works
    for family in ("artist-guides", "museum-guides"):
        index_path = CONTENT / family / "index.json"
        index = json.loads(index_path.read_text())
        for entry in index:
            entry.update(summaries[entry["slug"]])
        write_json(index_path, index, check)

    timeline_root = CONTENT / "timeline-guide"
    for locale in LOCALES:
        edition = editions["art-history-timeline", locale]
        assert all(not section["artworkId"] for section in edition["sections"])
        write_json(timeline_root / f"{locale}.json", {
            "slug": "art-history-timeline",
            "locale": locale,
            "title": edition["title"],
            "subtitle": edition["subtitle"],
            "introduction": edition["introduction"],
            "sections": [{"title": section["title"], "paragraphs": section["paragraphs"]} for section in edition["sections"]],
            "updated": UPDATED,
        }, check)
    print(f"{'Verified' if check else 'Imported'} 900 editions and {total_works} localized artwork commentaries")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manuscript", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    import_guides(args.manuscript, args.check)
