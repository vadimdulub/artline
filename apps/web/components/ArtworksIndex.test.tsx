import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ArtworksIndex } from "./ArtworksIndex";
import { useMuseumRequest } from "./museum-state";
vi.mock("./museum-state", () => ({ useMuseumRequest: vi.fn() }));
vi.mock("./AllArtworkDrawer", () => ({ AllArtworkDrawer: ({ id }: { id: string }) => <div role="dialog">Record {id}</div> }));
vi.mock("./ArtworkViewer", () => ({ ArtworkImage: () => <span>Image unavailable</span> }));
vi.mock("./ExplorerFrame", () => ({ useExplorerView: () => null }));
beforeEach(() => {
 window.history.replaceState(null, "", "/artworks");
 window.matchMedia = vi.fn().mockReturnValue({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() });
 vi.mocked(useMuseumRequest).mockReturnValue({ loading: false, error: "", data: { items: [{ id: "orphan-id", title: "Unassigned work", date_display: "", status: "review", creator: "", media_url: null, alt_text: null, rights_status: null, museum: null }], total: 1, next_cursor: "" } } as ReturnType<typeof useMuseumRequest>);
});
afterEach(cleanup);
it("shows incomplete review records by default and opens their details", () => {
 render(<ArtworksIndex />);
 expect(useMuseumRequest).toHaveBeenCalledWith("artworks?limit=24", 0);
 expect(screen.getByRole("button", { name: "Open Unassigned work" })).toBeTruthy();
 expect(screen.queryByText("Date unknown")).toBeNull();
 fireEvent.click(screen.getByRole("button", { name: "Open Unassigned work" }));
 expect(screen.getByRole("dialog").textContent).toContain("orphan-id");
});
it("sends review and undated filters to the server and resets pagination", () => {
 render(<ArtworksIndex />);

 fireEvent.click(screen.getByLabelText("Undated works"));
 expect(useMuseumRequest).toHaveBeenLastCalledWith("artworks?limit=24&undated=true", 0);
 expect(new URLSearchParams(window.location.search).has("cursor")).toBe(false);
});
