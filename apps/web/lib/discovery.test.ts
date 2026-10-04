import { describe, expect, it } from "vitest";
import { discoveryChanges } from "./discovery";

describe("intentional discovery filters", () => {
  it("opens movements beyond the Top 100 and requests fresh date fitting", () => {
    expect(discoveryChanges({ movement: ["pre-raphaelite-brotherhood"] }, "popular")).toMatchObject({ popular: "false", start: null, end: null, fit: "true" });
  });
  it("clears shared and per-layer editorial caps for global search", () => {
    expect(discoveryChanges({ q: "Rossetti" }, "highlights")).toMatchObject({ highlights: "false", artwork_popular: "false", book_top100: "false", event_top100: "false", fit: "true" });
  });
  it("respects explicit highlight toggles, resets, and manual years", () => {
    const cases: Record<string, string | string[] | null>[] = [{ highlights: "true" }, { q: null, highlights: null, start: null, end: null }, { start: "1800", end: "1900" }, { item: "details" }];
    for (const value of cases) {
      expect(discoveryChanges(value, "highlights")).toEqual(value);
    }
  });
});
