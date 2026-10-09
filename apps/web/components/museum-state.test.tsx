import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ApiError, apiRequest } from "@/lib/api";
import { useCatalogueRequest } from "./museum-state";
vi.mock("@/lib/api", async original => ({ ...await original<typeof import("@/lib/api")>(), apiRequest: vi.fn() }));
beforeEach(() => { vi.useFakeTimers(); vi.mocked(apiRequest).mockReset(); });
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
