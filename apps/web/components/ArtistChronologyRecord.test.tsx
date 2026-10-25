import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import type { ArtistDetail, Artwork } from "@/lib/types";
import { ArtistChronologyRecord } from "./ArtistChronologyRecord";
import { useMuseumRequest } from "./museum-state";

vi.mock("./museum-state", () => ({ useMuseumRequest: vi.fn(() => ({ loading: true })) }));
vi.mock("./RecordNavigation", () => ({ useRecordNavigation: () => ({}) }));
vi.mock("./ArtistRecord", () => ({ ArtistRecord: ({ workBrowser, artworkTimeline, onSelectWork }: { workBrowser: (choose: (id: string) => void) => ReactNode; artworkTimeline?: (choose: (id: string) => void) => ReactNode; onSelectWork: (id: string) => void }) => <>{artworkTimeline?.(onSelectWork)}{workBrowser(onSelectWork)}</> }));
const artist = { id: "painter", slug: "painter", display_name: "Painter", timeline_start_year: 1850, timeline_end_year: 1910, timeline_display: "1850–1910", timeline_basis: "life", movement: { slug: "study", name: "Study", color: "#8f3a29" }, artworks: [] } as unknown as ArtistDetail;
beforeEach(() => { window.matchMedia = vi.fn().mockReturnValue({ matches: false, addEventListener() {}, removeEventListener() {} }); });
afterEach(() => { cleanup(); vi.clearAllMocks(); window.history.replaceState(null, "", "/"); });

it.each([true, false])("defaults to pictures for embedded=%s and preserves an explicit opt-out", embedded => {
  render(<ArtistChronologyRecord artist={artist} workId={null} onSelectWork={() => {}} embedded={embedded} />);
  if (embedded) fireEvent.click(screen.getByRole("button", { name: "Artwork filters" }));
  expect(screen.getByRole("checkbox", { name: "With pictures" })).toBeChecked();
  expect(useMuseumRequest).toHaveBeenCalledWith("artists/painter/works?image_only=true", 0);
  fireEvent.click(screen.getByRole("checkbox", { name: "With pictures" }));
  expect(screen.getByRole("checkbox", { name: "With pictures" })).not.toBeChecked();
  expect(useMuseumRequest).toHaveBeenCalledWith("artists/painter/works?image_only=false", 0);
  cleanup();
  render(<ArtistChronologyRecord artist={artist} workId={null} onSelectWork={() => {}} embedded={embedded} />);
  if (embedded) fireEvent.click(screen.getByRole("button", { name: "Artwork filters" }));
  expect(screen.getByRole("checkbox", { name: "With pictures" })).not.toBeChecked();
});

it("adds artwork previews to individual painter pages using already supplied records", () => {
  const onSelectWork = vi.fn();
  const work = { id: "dated", title: "Dated painting", date_display: "1890", date_precision: "exact", creation_year_start: 1890, creation_year_end: 1890, media_url: "/assets/artworks/example.jpg", work_type: "painting", medium_text: null } as Artwork;
  render(<ArtistChronologyRecord artist={{ ...artist, artworks: [work], key_artwork: work }} workId={null} onSelectWork={onSelectWork} embedded={false} />);
  expect(screen.getByRole("heading", { name: "Life and artworks" })).toBeVisible();
  expect(screen.getByRole("button", { name: "1890: 1 artwork" })).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Open artwork" }));
  expect(onSelectWork).toHaveBeenCalledWith(work.id);
  expect(useMuseumRequest).toHaveBeenCalledTimes(2);
});

it("keeps the main timeline's embedded painter record unchanged", () => {
  render(<ArtistChronologyRecord artist={artist} workId={null} onSelectWork={() => {}} embedded />);
  expect(screen.queryByRole("heading", { name: "Life and artworks" })).not.toBeInTheDocument();
});
