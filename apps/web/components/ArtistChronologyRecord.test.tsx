import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import type { ArtistDetail } from "@/lib/types";
import { ArtistChronologyRecord } from "./ArtistChronologyRecord";
import { useMuseumRequest } from "./museum-state";

vi.mock("./museum-state", () => ({ useMuseumRequest: vi.fn(() => ({ loading: true })) }));
vi.mock("./RecordNavigation", () => ({ useRecordNavigation: () => ({}) }));
vi.mock("./ArtistRecord", () => ({ ArtistRecord: ({ workBrowser }: { workBrowser: (choose: () => void) => ReactNode }) => <>{workBrowser(() => {})}</> }));
const artist = { id: "painter", slug: "painter", display_name: "Painter", timeline_start_year: 1850, timeline_end_year: 1910, artworks: [] } as unknown as ArtistDetail;
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
