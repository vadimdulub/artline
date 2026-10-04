import { describe, expect, it } from "vitest";
import { rangeHandlePositions } from "../range-handles";

describe("range handle spacing", () => {
  it("leaves separated dates at their actual positions", () => {
    expect(rangeHandlePositions(20, 90, 100)).toEqual({ start: 20, end: 90 });
  });
  it.each([[0, 1, 0, 32], [99, 100, 68, 100], [49, 50, 33.5, 65.5]])(
    "separates %s–%s without pushing either handle past an endpoint", (start, end, left, right) => {
      expect(rangeHandlePositions(start, end, 100)).toEqual({ start: left, end: right });
    },
  );
  it("handles a track before measurement and in a tiny container", () => {
    expect(rangeHandlePositions(0, 0, 0)).toEqual({ start: 0, end: 0 });
    expect(rangeHandlePositions(8, 9, 10)).toEqual({ start: 0, end: 10 });
  });
});
