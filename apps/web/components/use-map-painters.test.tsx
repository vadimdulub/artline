import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { apiRequest } from "@/lib/api";
import { useMapPainters } from "./use-map-painters";

vi.mock("@/lib/api", () => ({ apiRequest: vi.fn(), errorMessage: (error: Error) => error.message }));
const request = vi.mocked(apiRequest);
const painter = { id: "monet", slug: "claude-monet", name: "Claude Monet", date_display: "1840–1926", movement: { name: "Impressionism" } };
beforeEach(() => vi.clearAllMocks());
afterEach(cleanup);

it("retains native lifespans and resolves selected painters outside the timeline window", async () => {
  request.mockResolvedValueOnce({ items: [painter] }).mockResolvedValueOnce({ id: "old", slug: "old-painter", display_name: "Old painter", timeline_display: "900–970" });
  const { result } = renderHook(() => useMapPainters(["claude-monet", "old-painter"], true));
  await waitFor(() => expect(result.current.loading).toBe(false));
  expect(result.current.items.map(item => [item.id, item.years])).toEqual([["monet", "1840–1926"], ["old", "900–970"]]);
  const params = new URLSearchParams(String(request.mock.calls[0][0]).split("?")[1]);
  expect(params.getAll("painter")).toEqual(["claude-monet", "old-painter"]);
  expect(params.get("popular")).toBe("false");
  expect(request.mock.calls[1][0]).toBe("artists/old-painter");
});

it("aborts obsolete painter selections and prevents their results replacing the new selection", async () => {
  let resolveOld!: (value: unknown) => void;
  request.mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve; })).mockResolvedValueOnce({ items: [painter] });
  const { result, rerender } = renderHook(({ values }) => useMapPainters(values, true), { initialProps: { values: ["old-painter"] } });
  const signal = request.mock.calls[0][1]?.signal;
  rerender({ values: ["claude-monet"] });
  await waitFor(() => expect(result.current.loading).toBe(false));
  expect(signal?.aborted).toBe(true);
  await act(async () => resolveOld({ items: [{ ...painter, id: "obsolete", slug: "old-painter" }] }));
  expect(result.current.items.map(item => item.id)).toEqual(["monet"]);
});

it("does not fetch in timeline mode and retries failed map selections", async () => {
  const { result, rerender } = renderHook(({ enabled }) => useMapPainters(["claude-monet"], enabled), { initialProps: { enabled: false } });
  expect(request).not.toHaveBeenCalled();
  request.mockRejectedValueOnce(new Error("Unavailable")).mockResolvedValueOnce({ items: [painter] });
  rerender({ enabled: true });
  await waitFor(() => expect(result.current.error).toBe("Unavailable"));
  act(() => result.current.retry());
  await waitFor(() => expect(result.current.items[0]?.id).toBe("monet"));
  expect(result.current.error).toBeUndefined();
});
