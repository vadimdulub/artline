import { describe, expect, it } from "vitest";
import { timelineRequestKey } from "./timeline-request";

describe("timeline requests", () => {
  it("reuses a response when fitting leaves the effective dates unchanged", () => {
    const defaults = { start: 1300, end: 1650 };
    expect(timelineRequestKey(new URLSearchParams("preset=renaissance&fit=true&type=artwork&type=book"), defaults))
      .toBe(timelineRequestKey(new URLSearchParams("start=1300&type=artwork&type=book&end=1650&preset=renaissance"), defaults));
  });
  it("refetches for changed dates, filters, or pagination", () => {
    const original = new URLSearchParams("start=1300&end=1650&type=artwork");
    for (const [key, value] of [["start", "1400"], ["end", "1600"], ["type", "book"], ["after_artwork", "cursor"]]) {
      const changed = new URLSearchParams(original);
      changed.set(key, value);
      expect(timelineRequestKey(changed)).not.toBe(timelineRequestKey(original));
    }
  });
  it("preserves invalid and repeated parameters for server validation", () => {
    const params = new URLSearchParams("start=bad&start=0&country=france&country=italy");
    const key = new URLSearchParams(timelineRequestKey(params, { start: -12000, end: 2000 }));
    expect(key.getAll("start")).toEqual(["bad", "0"]);
    expect(key.has("end")).toBe(false);
    expect(key.getAll("country")).toEqual(["france", "italy"]);
    expect(params.toString()).toBe("start=bad&start=0&country=france&country=italy");
  });
});
