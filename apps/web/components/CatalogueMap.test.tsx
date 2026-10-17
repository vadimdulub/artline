import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CatalogueMap } from "./CatalogueMap";
import { apiRequest } from "@/lib/api";
import type { MapRecord, PlaceGroup } from "@/lib/map";
vi.mock("next/dynamic", () => ({ default: () => ({ selected, groups }: { selected: string; groups: PlaceGroup[] }) => <div aria-label="Mock map" data-selected={selected} data-places={groups.length} /> }));
vi.mock("@/lib/api", () => ({ apiRequest: vi.fn(), errorMessage: (e: Error) => e.message }));
const request = vi.mocked(apiRequest);
const connection = { place: "Geneva", relation: "begun near", precision: "area", lat: 46.2, lon: 6.2, start: 1816, end: 1816, note: "Beginning only", sourceLabel: "Author", sourceUrl: "https://example.org/source" };
const item = { id: "wd-q150827", kind: "book" as const, title: "Frankenstein" };
const props = { items: [item], total: 20, loading: false, onRetry: vi.fn(), range: { start: 1800, end: 1900 }, onOpen: vi.fn() };
beforeEach(() => { vi.clearAllMocks(); window.history.replaceState(null, "", "/"); window.matchMedia = vi.fn().mockReturnValue({ matches: false }); });
afterEach(cleanup);
describe("CatalogueMap", () => {
 it("reports page coverage and opens the existing record", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  render(<CatalogueMap {...props} />);
  expect(await screen.findByText("1 of 1 loaded records located · 20 matching records")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /^Geneva/ }));
  fireEvent.click(screen.getByRole("button", { name: "Frankenstein" })); expect(props.onOpen).toHaveBeenCalledWith(item);
  expect(request.mock.calls[0][0]).toContain("start=1800&end=1900");
 });
 it("keeps selection in the URL and searches only the mapped places on the current page", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection, { ...connection, place: "London", lat: 51.5, lon: -0.1 }], truncated: false }] });
  render(<CatalogueMap {...props} />);
  const search = await screen.findByRole("searchbox", { name: "Find a mapped place on this page" });
  fireEvent.change(search, { target: { value: "London" } });
  expect(screen.queryByRole("button", { name: /^Geneva/ })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /^London/ }));
  expect(new URLSearchParams(window.location.search).get("map_place")).toBe("51.5,-0.1,local");
  expect(screen.getByRole("heading", { name: "London" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "← All places" }));
  expect(new URLSearchParams(window.location.search).has("map_place")).toBe(false);
  expect(screen.getByRole("button", { name: /^Geneva/ })).toBeInTheDocument();
 });
 it("keeps a record usable when its reproduction is unavailable", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  render(<CatalogueMap {...props} items={[{ ...item, image: "/missing.jpg" }]} />);
  fireEvent.click(await screen.findByRole("button", { name: /^Geneva/ }));
  fireEvent.error(screen.getByRole("img", { name: "Frankenstein" }));
  expect(screen.getByText("Image unavailable")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Frankenstein" }));
  expect(props.onOpen).toHaveBeenCalled();
 });
 it("does not misreport a failed location request as zero coverage", async () => {
  request.mockRejectedValue(new Error("Disconnected")); render(<CatalogueMap {...props} />);
  expect(await screen.findByRole("alert")).toHaveTextContent("Disconnected"); expect(screen.queryByText(/0 of 1/)).not.toBeInTheDocument();
 });
 it("ignores stale evidence after the selected years change", async () => {
  let resolveOld!: (value: { records: MapRecord[] }) => void;
  request.mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve; })).mockResolvedValueOnce({ records: [{ id: item.id, connections: [], truncated: false }] });
  const { rerender } = render(<CatalogueMap {...props} />); await waitFor(() => expect(request).toHaveBeenCalledTimes(1));
  rerender(<CatalogueMap {...props} range={{ start: 1901, end: 2000 }} />);
  expect(await screen.findByText("0 of 1 loaded records located · 20 matching records")).toBeInTheDocument();
  await act(async () => resolveOld({ records: [{ id: item.id, connections: [connection], truncated: false }] }));
  expect(screen.queryByText("Geneva")).not.toBeInTheDocument();
 });
 it("includes relationship filters in the evidence request and permits an empty selection", async () => {
  request.mockResolvedValue({ records: [] });
  const artist = { id: "artist-id", kind: "artist" as const, title: "Painter" };
  const { rerender } = render(<CatalogueMap {...props} items={[artist]} relations={["birth"]} />);
  await waitFor(() => expect(request).toHaveBeenCalledTimes(1));
  expect(request.mock.calls[0][0]).toContain("relation=birth");
  rerender(<CatalogueMap {...props} items={[]} relations={[]} />);
  expect(await screen.findByText(/Choose at least one place type above/)).toBeInTheDocument();
  expect(request).toHaveBeenCalledTimes(1);
 });
 it("keeps unsupported locations accessible in the unlocated list", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [{ ...connection, place: "Historical state", lat: null, lon: null, precision: "unlocated" }], truncated: false }] });
  render(<CatalogueMap {...props} />); fireEvent.click(await screen.findByRole("button", { name: "Not mapped (1)" }));
  expect(screen.getByText(/Historical state · Begun near · coordinates unresolved/)).toBeInTheDocument();
 });
});


describe("following a record on the map", () => {
 const first = { ...connection, key: "writing" };
 const second = { ...connection, key: "publication", place: "London", relation: "first published in", lat: 51.5, lon: -0.1, start: 1818, end: 1818 };
 const unresolved = { ...connection, key: "unknown", place: "Historical country", lat: null, lon: null, start: null, end: null };
 it("steps through server-ordered connections and keeps unresolved places off the map", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [first, second, unresolved], truncated: false }] });
  render(<CatalogueMap {...props} />);
  fireEvent.click(await screen.findByRole("button", { name: "Records (1)" }));
  fireEvent.click(screen.getByRole("button", { name: /BookFrankenstein3 connections/ }));
  expect(screen.getByRole("button", { name: "Previous connection" })).toBeDisabled();
  expect(screen.getByRole("heading", { name: "Geneva" })).toHaveFocus();
  fireEvent.click(screen.getByRole("button", { name: "Next connection" }));
  expect(screen.getByRole("heading", { name: "London" })).toHaveFocus();
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-selected", "51.5,-0.1,local");
  expect(new URLSearchParams(location.search).get("map_stop")).toBe("publication");
  fireEvent.click(screen.getByRole("button", { name: "Next connection" }));
  expect(screen.getByText("Location unresolved · no map marker")).toBeInTheDocument();
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-selected", "");
  expect(screen.getByRole("button", { name: "Next connection" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Open full record" }));
  expect(props.onOpen).toHaveBeenCalledWith(item);
  expect(request).toHaveBeenCalledTimes(1);
 });
 it("restores a linked connection and explicitly handles it leaving the year selection", async () => {
  window.history.replaceState(null, "", "/?map_panel=records&map_record=book:wd-q150827&map_stop=publication&map_place=46.2,6.2,local");
  request.mockResolvedValueOnce({ records: [{ id: item.id, connections: [first, second], truncated: false }] }).mockResolvedValueOnce({ records: [{ id: item.id, connections: [first], truncated: false }] });
  const { rerender } = render(<CatalogueMap {...props} />);
  expect(await screen.findByRole("heading", { name: "London" })).toBeInTheDocument();
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-selected", "51.5,-0.1,local");
  rerender(<CatalogueMap {...props} range={{ start: 1816, end: 1816 }} />);
  expect(await screen.findByText(/That connection is outside this selection/)).toBeInTheDocument();
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-selected", "");
 });
 it("distinguishes a missing page record from an empty catalogue", async () => {
  window.history.replaceState(null, "", "/?map_panel=records&map_record=book:another-page&map_stop=writing");
  request.mockResolvedValue({ records: [{ id: item.id, connections: [first], truncated: false }] });
  render(<CatalogueMap {...props} />);
  expect(await screen.findByText(/This record is not on the current page/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /BookFrankenstein1 connections/ })).toBeInTheDocument();
 });
});
