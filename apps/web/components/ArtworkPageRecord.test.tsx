import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ArtworkPageRecord } from "./ArtworkPageRecord";
import type { Artwork } from "@/lib/types";

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

it("renders an unillustrated, undated review work and its qualified attribution without loading a collection", () => {
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  const work: Artwork = {
    id: "review-work", slug: "review-work", title: "Unfinished study", status: "review", revision: 1,
    attribution_role: "workshop", date_precision: "unknown", date_display: "Date unknown",
    alternate_title: null, creation_year_start: null, creation_year_end: null,
    work_type: "unknown", medium_text: null, dimensions_text: null, accession_number: null,
    creation_place_unknown_reason: null, creation_place_display: null, current_location_text: null,
    media_url: null, alt_text: null, rights_status: null, attribution_text: null, representative_order: null,
    source_page_url: null, license_label: null, license_url: null, location_checked_at: null, description_md: null,
    citations: [{ field_name: "title", source_name: "Museum catalogue", source_url: "https://example.org/object" }],
  };
  const artist = { id: "painter", slug: "painter", display_name: "Painter", entity_type: "person" };
  const { container } = render(<ArtworkPageRecord artist={artist} work={work} browsePath="/artists/painter?art_images=false&art_year=undated" />);
  expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Unfinished study");
  expect(screen.getByText("Workshop", { exact: true })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Browse Painter artworks" })).toHaveAttribute("href", "/artists/painter?art_images=false&art_year=undated");
  expect(container.querySelector('a[href="https://example.org/object"]')).toHaveTextContent("Museum catalogue");
  expect(container.querySelector("img")).toBeNull();
  expect(fetch).not.toHaveBeenCalled();
});
