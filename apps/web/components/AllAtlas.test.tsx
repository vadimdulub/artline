import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { apiRequest } from "@/lib/api";
import type { AtlasMetadata, AtlasResponse } from "@/lib/atlas";
import { updateQuery } from "@/lib/url-state";
import { AllAtlas } from "./AllAtlas";

vi.mock("@/lib/api", async original => ({ ...await original<typeof import("@/lib/api")>(), apiRequest: vi.fn() }));
vi.mock("./use-atlas-creators", () => ({ useAtlasCreators: () => ({ options: [] }) }));
vi.mock("./RecordNavigation", () => ({ useRecordNavigation: () => undefined }));
vi.mock("./AllArtworkGallery", () => ({ AllArtworkGallery: () => <div>Loaded artwork gallery</div>, GalleryScrollButtons: () => null }));
const range = { start: 1300, end: 1650 };
const metadata: AtlasMetadata = { bounds: { start: -12000, end: 2000 }, presets: [{ id: "renaissance", name: "The Renaissance", group: "History", description: "", startingScope: "Europe", startingHighlights: false, period: range, context: range, sources: [] }], types: [], regions: [], continents: [], defaultPreset: "" };
const response: AtlasResponse = { range, bounds: metadata.bounds, total: 1, ticks: [], lanes: [{ key: "artwork", name: "Artworks", singular: "Artwork", dateLabel: "Created", cutoff: 1970, color: "#abc", total: 1, mode: "individual", items: [{ id: "work", type: "artwork", title: "Test work", startYear: 1500, endYear: 1500, years: "1500", context: "", approximate: false }], density: [], nextCursor: "" }] };
function deferred<T>() {
 let resolve!: (value: T) => void, reject!: (error: Error) => void;
 const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
 return { promise, resolve, reject };
}
beforeEach(() => {
 window.history.replaceState(null, "", "/all?preset=renaissance&selection=true&type=artwork");
 vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
 window.matchMedia = vi.fn().mockReturnValue({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() });
});
afterEach(() => { cleanup(); vi.mocked(apiRequest).mockReset(); vi.unstubAllGlobals(); });
function mockRequests(content: Promise<AtlasResponse>, presets = Promise.resolve(metadata)) {
 vi.mocked(apiRequest).mockImplementation((path) => (path === "atlas/presets" ? presets : path === "atlas/geography" ? Promise.resolve({ countries: [] }) : content) as ReturnType<typeof apiRequest>);
}
it("shows a visible spinner before metadata and the first content response, then removes it", async () => {
 const content = deferred<AtlasResponse>(), presets = deferred<AtlasMetadata>();
 mockRequests(content.promise, presets.promise);
 const { container } = render(<AllAtlas />);
 expect(screen.getByText("Loading the timeline…")).toBeVisible();
 expect(container.querySelector('.all-content-loading[role="status"] .loading-spinner')).toBeTruthy();
 expect(container.querySelector('.timeline-stage')).toHaveAttribute("aria-busy", "true");
 await act(async () => presets.resolve(metadata));
 await waitFor(() => expect(apiRequest).toHaveBeenCalledWith(expect.stringMatching(/^atlas\?/), expect.anything()));
 expect(screen.getByText("Loading the timeline…")).toBeVisible();
 await act(async () => content.resolve(response));
 expect(await screen.findByText("Loaded artwork gallery")).toBeVisible();
 expect(screen.queryByText("Loading the timeline…")).toBeNull();
 expect(container.querySelector('.timeline-stage')).toHaveAttribute("aria-busy", "false");
});
it("replaces previous content with a spinner when filters change", async () => {
 mockRequests(Promise.resolve(response));
 render(<AllAtlas />);
 await screen.findByText("Loaded artwork gallery");
 const pending = deferred<AtlasResponse>();
 mockRequests(pending.promise);
 act(() => updateQuery({ q: "new query" }));
 expect(screen.getByText("Loading the timeline…")).toBeVisible();
 expect(screen.queryByText("Loaded artwork gallery")).toBeNull();
});
it("replaces a failed request with an error and lets Retry load content", async () => {
 const pending = deferred<AtlasResponse>();
 mockRequests(pending.promise);
 const { container } = render(<AllAtlas />);
 await waitFor(() => expect(apiRequest).toHaveBeenCalledWith(expect.stringMatching(/^atlas\?/), expect.anything()));
 await act(async () => pending.reject(new Error("Unavailable")));
 expect(screen.getByRole("heading", { name: "We couldn’t load this view" })).toBeVisible();
 expect(screen.queryByText("Loading the timeline…")).toBeNull();
 expect(container.querySelector('.timeline-stage')).toHaveAttribute("aria-busy", "false");
 mockRequests(Promise.resolve(response));
 fireEvent.click(screen.getByRole("button", { name: /^Retry$/ }));
 expect(screen.getByText("Loading the timeline…")).toBeVisible();
 expect(await screen.findByText("Loaded artwork gallery")).toBeVisible();
});
it("does not leave an endless spinner if required preset metadata fails", async () => {
 const presets = deferred<AtlasMetadata>();
 mockRequests(new Promise(() => {}), presets.promise);
 render(<AllAtlas />);
 await act(async () => presets.reject(new Error("Unavailable")));
 expect(screen.getByText("Period information could not be loaded.")).toBeVisible();
 expect(screen.queryByText("Loading the timeline…")).toBeNull();
});
