import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { ArtistRecord, SourceList } from "./ArtistRecord";
import { permittedImagePath } from "./ArtworkViewer";
import type { ArtistDetail, Artwork } from "../lib/types";

afterEach(cleanup);
const artwork: Artwork = {
  id: "work-1", slug: "work-1", title: "Study", alternate_title: null,
  date_display: "c. 1890–1892", creation_year_start: 1890, creation_year_end: 1892,
  date_precision: "circa_range", work_type: "painting", medium_text: "Oil on canvas",
  dimensions_text: null, accession_number: null, creation_place_display: null,
  creation_place_unknown_reason: "No place of execution is given in the source.",
  current_location_text: null, media_url: null, alt_text: null, rights_status: null,
  attribution_text: null, representative_order: 1, status: "review", revision: 1,
  attribution_role: "primary", source_page_url: null, license_label: null,
  license_url: null, location_checked_at: null, citations: []
};
const painter: ArtistDetail = {
  id: "painter", slug: "painter", display_name: "Painter", sort_name: "Painter",
  timeline_start_year: 1850, timeline_end_year: 1910, timeline_display: "1850–1910",
  timeline_basis: "life", biography_md: null, status: "review", revision: 1,
  entity_type: "person", aliases: [], influences: [], countries: [],
  movement: { slug: "study", name: "Study", color: "#234e9a" }, artworks: [], citations: []
};
it.each([1, 2, 5])("sizes the canonical work grid for %i actual works", count => {
  const artworks = Array.from({ length: count }, (_, i) => ({ ...artwork, id: "work-" + i, representative_order: i + 1 }));
  const { container } = render(<ArtistRecord artist={{ ...painter, artworks }} onSelectWork={() => {}} />);
  expect(container.querySelectorAll(".work-card")).toHaveLength(count);
  expect((container.querySelector(".works-strip") as HTMLElement).style.getPropertyValue("--work-columns")).toBe(String(count));
  expect(screen.getByText("Approximate date range")).toBeVisible();
  expect(screen.getByText("No place of execution is given in the source.")).toBeVisible();
  expect(screen.getByText("Not recorded in this catalogue")).toBeVisible();
});
it("rejects remote and path-traversal image paths", () => {
  expect(permittedImagePath("/assets/artworks/giotto-kiss-of-judas.jpg")).toBe(true);
  for (const path of [null, "https://example.com/image.jpg", "/assets/../secret.jpg", "/assets/artworks/unsafe.svg", "//example.com/image.jpg"]) expect(permittedImagePath(path)).toBe(false);
});
it("opens a linked artwork without adding it to the representative selection", () => {
  const linked = { ...artwork, id: "outside-selection", title: "Additional recorded work", representative_order: null };
  const { container } = render(<ArtistRecord artist={{ ...painter, artworks: [artwork] }} workId={linked.id} linkedWork={linked} onSelectWork={() => {}} />);
  expect(container.querySelectorAll(".work-card")).toHaveLength(1);
  expect(screen.getByRole("heading", { name: "Additional recorded work" })).toBeVisible();
});
it("renders structured geography evidence as readable research notes", () => {
  render(<SourceList citations={[{
    field_name: "geography",
    source_name: "Country research",
    source_url: "https://example.com/source",
    evidence_note: JSON.stringify({
      country_code: "RU",
      country_evidence: {
        basis: "Explicit painter cultural-affiliation wording.",
        source_description: "Russian and French painter (1884–1967)",
        historical_polity_statements: [{ id: "historical" }],
        wikipedia_country_crosscheck: { source_excerpt: "She was a Russian painter." }
      },
      publication: "Review"
    })
  }]} />);
  expect(screen.getByText("Country affiliation: Russia (RU).")).toBeVisible();
  expect(screen.getByText("Evidence basis: Explicit painter cultural-affiliation wording.")).toBeVisible();
  expect(screen.getByText("Biography cross-check: She was a Russian painter.")).toBeVisible();
  expect(screen.queryByText(/historical_polity_statements/)).not.toBeInTheDocument();
});
