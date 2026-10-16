import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CatalogueMap } from "./CatalogueMap";
import { apiRequest } from "@/lib/api";
import type { MapRecord } from "@/lib/map";
vi.mock("next/dynamic", () => ({ default: () => () => <div aria-label="Mock map" /> }));
vi.mock("@/lib/api", () => ({ apiRequest: vi.fn(), errorMessage: (e: Error) => e.message }));
const request = vi.mocked(apiRequest);
const connection = { place: "Geneva", relation: "begun near", precision: "area", lat: 46.2, lon: 6.2, start: 1816, end: 1816, note: "Beginning only", sourceLabel: "Author", sourceUrl: "https://example.org/source" };
const item = { id: "wd-q150827", kind: "book" as const, title: "Frankenstein" };
const props = { items: [item], total: 20, loading: false, onRetry: vi.fn(), range: { start: 1800, end: 1900 }, onOpen: vi.fn() };
beforeEach(() => { vi.clearAllMocks(); });
afterEach(cleanup);
describe("CatalogueMap", () => {
 it("reports page coverage and opens the existing record", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  render(<CatalogueMap {...props} />);
  expect(await screen.findByText("1 of 1 loaded records located · 20 matching records")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Frankenstein" })); expect(props.onOpen).toHaveBeenCalledWith(item);
  expect(request.mock.calls[0][0]).toContain("start=1800&end=1900");
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
 it("keeps unsupported locations accessible in the unlocated list", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [{ ...connection, place: "Historical state", lat: null, lon: null, precision: "unlocated" }], truncated: false }] });
  render(<CatalogueMap {...props} />); fireEvent.click(await screen.findByRole("button", { name: "Unlocated (1)" }));
  expect(screen.getByText(/Historical state · begun near · coordinates unresolved/)).toBeInTheDocument();
 });
});
