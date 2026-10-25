import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { ArtistDetail, Artwork } from "@/lib/types";
import { ArtistArtworkTimeline } from "./ArtistArtworkTimeline";

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
const artist = { id: "painter", display_name: "Painter", timeline_start_year: 1880,
  timeline_end_year: 1970, timeline_display: "1880–1970", timeline_basis: "life",
  movement: { slug: "modern", name: "Modern", color: "#8f3a29" } } satisfies Partial<ArtistDetail>;
function work(id: string, year: number | null, extra: Partial<Artwork> = {}): Artwork {
  return { id, title: id, creation_year_start: year, creation_year_end: year,
    date_display: year === null ? "Date unknown" : String(year), date_precision: year === null ? "unknown" : "exact",
    media_url: null, medium_text: "Oil on canvas", work_type: "painting", current_location_text: null, ...extra } as Artwork;
}
const early = work("Early canvas", 1901), late = work("Later canvas", 1937), undated = work("Undated study", null);
function show(artworks: Artwork[] = [early, late, undated], extra: Partial<Parameters<typeof ArtistArtworkTimeline>[0]> = {}) {
  const onOpenWork = vi.fn(), onUndated = vi.fn();
  const view = render(<ArtistArtworkTimeline artist={artist} artworks={artworks} onOpenWork={onOpenWork} onUndated={onUndated} {...extra} />);
  return { ...view, onOpenWork, onUndated };
}

it("shows a saved selection and plots only supported dates", () => {
  show(undefined, { initialWorkID: late.id });
  expect(screen.getByRole("heading", { name: "Life and artworks" })).toBeVisible();
  expect(screen.getByRole("heading", { name: late.title })).toBeVisible();
  expect(screen.getByRole("button", { name: "1901: 1 artwork" })).toHaveAttribute("aria-pressed", "false");
  expect(screen.getByRole("button", { name: "1937: 1 artwork" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByText("2 of 3")).toBeVisible();
  expect(screen.queryByRole("button", { name: /unknown|undated.*artwork/i })).not.toBeInTheDocument();
});

it("previews on pointer and keyboard focus without opening a record", () => {
  const { onOpenWork } = show();
  fireEvent.pointerEnter(screen.getByRole("button", { name: "1937: 1 artwork" }));
  expect(screen.getByRole("heading", { name: late.title })).toBeVisible();
  expect(onOpenWork).not.toHaveBeenCalled();
  fireEvent.focus(screen.getByRole("button", { name: "1901: 1 artwork" }));
  expect(screen.getByRole("heading", { name: early.title })).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Open artwork" }));
  expect(onOpenWork).toHaveBeenCalledWith(early.id);
});

it("deduplicates the same physical artwork across saved and paged selections", () => {
  show([early, early, late]);
  expect(screen.getByText("2 artwork previews")).toBeVisible();
  expect(screen.getByRole("button", { name: "1901: 1 artwork" })).toBeVisible();
});

it("keeps distinct same-year works reachable inside a crowded date group", () => {
  show([early, work("Another canvas", 1937), work("Zinc study", 1937)]);
  const group = screen.getByRole("button", { name: "1937: 2 artworks" });
  fireEvent.click(group);
  expect(screen.getByRole("heading", { name: "Another canvas" })).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Next artwork preview" }));
  expect(screen.getByRole("heading", { name: "Zinc study" })).toBeVisible();
  expect(group).toHaveAttribute("aria-pressed", "true");
});

it("supports arrows, Home and End without focus resetting the chosen clustered work", () => {
  show([early, work("Another canvas", 1937), work("Zinc study", 1937)]);
  const first = screen.getByRole("button", { name: "1901: 1 artwork" });
  first.focus();
  fireEvent.keyDown(first, { key: "End" });
  expect(screen.getByRole("heading", { name: "Zinc study" })).toBeVisible();
  const last = screen.getByRole("button", { name: "1937: 2 artworks" });
  expect(last).toHaveFocus();
  fireEvent.keyDown(last, { key: "ArrowLeft" });
  expect(screen.getByRole("heading", { name: "Another canvas" })).toBeVisible();
  fireEvent.keyDown(last, { key: "Home" });
  expect(screen.getByRole("heading", { name: early.title })).toBeVisible();
  expect(first).toHaveFocus();
});

it("keeps undated works outside the ruler and available to browse", () => {
  const { onUndated } = show([undated], { undatedCount: 19 });
  expect(screen.getByText("No dated artworks in this selection.")).toBeVisible();
  expect(screen.getByRole("heading", { name: undated.title })).toBeVisible();
  expect(screen.getByText("Undated", { exact: true })).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "19 undated works" }));
  expect(onUndated).toHaveBeenCalledOnce();
});

it("retains a posthumous physical date beyond the painter's lifetime", () => {
  const { container } = show([work("Posthumous edition", 1980)]);
  const dot = screen.getByRole("button", { name: "1980: 1 artwork" });
  expect(dot.style.left).toBe("100%");
  expect(screen.getByText("Died 1970")).toBeVisible();
  expect(container.querySelector('[class*="lifeBand"]')?.getAttribute("style")).toContain("width: 90%");
});

it("uses the recorded beginning of a range while displaying its full wording", () => {
  show([work("Ranged painting", 1900, { creation_year_end: 1910, date_precision: "circa_range", date_display: "c. 1900–1910" })]);
  expect(screen.getByRole("button", { name: "1900: 1 artwork" })).toBeVisible();
  expect(screen.getByText("c. 1900–1910")).toBeVisible();
  expect(screen.getByText(/Ranges begin at their recorded starting year/)).toBeVisible();
});

it("does not label a documented activity interval as birth and death", () => {
  show([early], { artist: { ...artist, timeline_basis: "activity" } });
  expect(screen.getByRole("heading", { name: "Activity and artworks" })).toBeVisible();
  expect(screen.getByText("From 1880")).toBeVisible();
  expect(screen.queryByText("Born 1880")).not.toBeInTheDocument();
});

it("does not plot an unknown precision or an inverted date range", () => {
  show([work("Unknown precision", 1900, { date_precision: "unknown" }), work("Conflicted range", 1920, { creation_year_end: 1910 })]);
  const ruler = screen.getByRole("group", { name: "Artwork dates for Painter" });
  expect(within(ruler).queryByRole("button")).not.toBeInTheDocument();
});

it("clusters close years responsively rather than adding overlapping touch targets", () => {
  vi.stubGlobal("ResizeObserver", class {
    constructor(private callback: ResizeObserverCallback) {}
    observe() { this.callback([{ contentRect: { width: 300 } } as ResizeObserverEntry], this as unknown as ResizeObserver); }
    disconnect() {}
  });
  show(Array.from({ length: 24 }, (_, i) => work(`Work ${i}`, 1900 + i)));
  const dots = within(screen.getByRole("group", { name: "Artwork dates for Painter" })).getAllByRole("button");
  expect(dots.length).toBeLessThan(7);
  expect(screen.getByText("24 artwork previews")).toBeVisible();
  for (let i = 1; i < dots.length; i++) expect((parseFloat(dots[i].style.left) - parseFloat(dots[i-1].style.left)) / 100 * 300).toBeGreaterThanOrEqual(44);
});

it("handles an empty painter without unusable preview controls", () => {
  show([]);
  expect(screen.getByText("No dated artworks in this selection.")).toBeVisible();
  expect(screen.queryByRole("navigation", { name: "Browse artwork previews" })).not.toBeInTheDocument();
});
