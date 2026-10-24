import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ApiError, apiRequest } from "@/lib/api";
import { useCatalogueRequest } from "./museum-state";
import { clearMuseumPageCache } from "@/lib/museum-page-cache";
vi.mock("@/lib/api", async original => ({ ...await original<typeof import("@/lib/api")>(), apiRequest: vi.fn() }));
beforeEach(() => { vi.useFakeTimers(); clearMuseumPageCache(); vi.mocked(apiRequest).mockReset(); });
afterEach(() => { cleanup(); vi.useRealTimers(); });
const initial = { slug: "museum", name: "Server-rendered museum" };
it("reuses server data, refreshes on revision, and retains it on transient failure", async () => {
  const { result, rerender } = renderHook(({ revision }) => useCatalogueRequest("museums/museum", revision, initial, true), { initialProps: { revision: 0 } });
  await act(() => vi.advanceTimersByTimeAsync(200));
  expect(apiRequest).not.toHaveBeenCalled();
  expect(result.current.data).toEqual(initial);
  vi.mocked(apiRequest).mockRejectedValueOnce(new ApiError("Unavailable", 503));
  rerender({ revision: 1 });
  await act(() => vi.advanceTimersByTimeAsync(200));
  expect(apiRequest).toHaveBeenCalledTimes(1);
  expect(result.current.error).toBe("Unavailable");
  expect(result.current.previousData).toEqual(initial);
});
it.each([401,403,404])("discards unavailable server data on HTTP %s", async status => {
  vi.mocked(apiRequest).mockRejectedValue(new ApiError("Unavailable",status));
  const { result, rerender } = renderHook(({ revision }) => useCatalogueRequest("museums/museum", revision, initial, true), { initialProps: { revision: 0 } });
  rerender({ revision: 1 });
  await act(() => vi.advanceTimersByTimeAsync(200));
  expect(result.current.previousData).toBeUndefined();
});

it("restores a visited directory page immediately without another request", async () => {
  const filtered = { slug: "filtered", name: "Filtered collections" };
  vi.mocked(apiRequest).mockResolvedValueOnce(filtered);
  const { result, rerender } = renderHook(({ path }) => useCatalogueRequest(path, 0, initial, true, true), { initialProps: { path: "museums?" } });
  await act(() => vi.advanceTimersByTimeAsync(200));
  rerender({ path: "museums?country=FR" });
  expect(result.current.loading).toBe(true);
  expect(result.current.previousData).toEqual(initial);
  await act(() => vi.advanceTimersByTimeAsync(200));
  expect(result.current.data).toEqual(filtered);
  rerender({ path: "museums?" });
  expect(result.current.loading).toBe(false);
  expect(result.current.data).toEqual(initial);
  await act(() => vi.advanceTimersByTimeAsync(200));
  expect(apiRequest).toHaveBeenCalledTimes(1);
});

it("refreshes cached directory pages on explicit retry and clears denied data", async () => {
  const { result, rerender } = renderHook(({ revision }) => useCatalogueRequest("museums?", revision, initial, true, true), { initialProps: { revision: 0 } });
  await act(() => vi.advanceTimersByTimeAsync(200));
  vi.mocked(apiRequest).mockRejectedValueOnce(new ApiError("Sign in", 401));
  rerender({ revision: 1 });
  await act(() => vi.advanceTimersByTimeAsync(200));
  expect(result.current.data).toBeUndefined();
  expect(result.current.previousData).toBeUndefined();
  rerender({ revision: 0 });
  expect(result.current.loading).toBe(true);
});
