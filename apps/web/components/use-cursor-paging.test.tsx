import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useCursorPaging } from "./use-cursor-paging";

describe("bounded cursor navigation", () => {
  it("returns to the preceding cursor and resets across filters", () => {
    const change = vi.fn();
    const { result, rerender } = renderHook(({ scope, cursor }) => useCursorPaging(scope, cursor, change), { initialProps: { scope: "museum-a", cursor: "" } });
    act(() => result.current.next("page-two"));
    expect(change).toHaveBeenLastCalledWith("page-two");
    rerender({ scope: "museum-a", cursor: "page-two" });
    expect(result.current.number).toBe(2);
    act(() => result.current.previous());
    expect(change).toHaveBeenLastCalledWith(null);
    rerender({ scope: "museum-a|monet", cursor: "" });
    expect(result.current.canPrevious).toBe(false);
    expect(result.current.number).toBe(1);
  });
  it("does not invent a page number for a bookmarked cursor", () => {
    const change = vi.fn();
    const { result, rerender } = renderHook(({ cursor }) => useCursorPaging("museum", cursor, change), { initialProps: { cursor: "opaque" } });
    expect(result.current.number).toBe(null);
    act(() => result.current.next("next"));
    rerender({ cursor: "next" });
    expect(result.current.number).toBe(null);
    expect(result.current.canPrevious).toBe(true);
    act(() => result.current.first());
    rerender({ cursor: "" });
    expect(result.current.number).toBe(1);
  });
});
