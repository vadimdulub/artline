import { describe, expect, it } from "vitest";
import { normalizeRange, positionArtists, presetRange, timelineTicks } from "../timeline";
import type { TimelineArtist } from "../types";

const movement = { slug: "test", name: "Test", color: "#234e9a" };

describe("positionArtists", () => {
  function painter(id: number, start: number, end: number): TimelineArtist {
    return { id: String(id), slug: "painter-" + id, name: "A painter with a particularly long name " + id, start_year: start, end_year: end, date_display: start + "–" + end, movement, countries: [], artwork_count: 0, status: "review" };
  }
  it("keeps right-edge labels and short activity intervals inside a phone viewport", () => {
    const result = positionArtists([painter(1, 1999, 2000), painter(2, 2000, 2000)], 1100, 2000, 284);
    for (const mark of result) {
      const left = mark.left / 100 * 284;
      expect(left + mark.width / 100 * 284).toBeLessThanOrEqual(284);
      expect(left + mark.labelOffset).toBeGreaterThanOrEqual(0);
      expect(left + mark.labelOffset + mark.labelWidth).toBeLessThanOrEqual(284);
    }
    expect(result[0].lane).not.toBe(result[1].lane);
  });
  it("packs dense labels without overlapping in the same lane", () => {
    for (const width of [284, 732, 1384]) {
      const result = positionArtists(Array.from({ length: 28 }, (_, i) => painter(i, 1200 + i * 27, 1270 + i * 27)), 1100, 2000, width);
      for (let i = 0; i < result.length; i++) {
        const a = result[i], aStart = a.left / 100 * width + Math.min(0, a.labelOffset);
        const aEnd = a.left / 100 * width + Math.max(a.width / 100 * width, a.labelOffset + a.labelWidth);
        for (const b of result.slice(i + 1).filter(b => b.lane === a.lane)) {
          const bStart = b.left / 100 * width + Math.min(0, b.labelOffset);
          const bEnd = b.left / 100 * width + Math.max(b.width / 100 * width, b.labelOffset + b.labelWidth);
          expect(aEnd + 11.99 <= bStart || bEnd + 11.99 <= aStart).toBe(true);
        }
      }
    }
  });
  it("clips to the selected period and removes artists outside it", () => {
    const result = positionArtists([painter(1, 1750, 1820), painter(2, 1950, 2000)], 1800, 1900, 1000);
    expect(result).toHaveLength(1);
    expect(result[0].left).toBe(0);
    expect(result[0].width).toBe(20);
  });
  it("keeps overlapping painters in separate lanes", () => {
    const items: TimelineArtist[] = [
      { id: "1", slug: "one", name: "One", start_year: 1800, end_year: 1850, date_display: "1800–1850", movement, countries: [], artwork_count: 0, status: "review" },
      { id: "2", slug: "two", name: "Two", start_year: 1820, end_year: 1870, date_display: "1820–1870", movement, countries: [], artwork_count: 0, status: "review" },
    ];
    const result = positionArtists(items, 1800, 1900);
    expect(result[0].lane).toBe(0);
    expect(result[1].lane).toBe(1);
  });
});

describe("bookmark and zoom ranges", () => {
  it("normalizes reversed and malformed bookmarks", () => {
    expect(normalizeRange("2000", "1100")).toEqual([1100, 2000]);
    expect(normalizeRange("wrong", null)).toEqual([1100, 2000]);
    expect(normalizeRange("2000", "2000")).toEqual([1999, 2000]);
  });
  it("preserves preset width at either end of the atlas", () => {
    expect(presetRange(1990, 2000, 100)).toEqual([1900, 2000]);
    expect(presetRange(1100, 1110, 50)).toEqual([1100, 1150]);
  });
  it("provides ticks in a one-year window", () => {
    expect(timelineTicks(1999, 2000)).toEqual([1999, 2000]);
  });
});

describe("timelineTicks", () => {
  it("includes century ticks for the full range", () => {
    expect(timelineTicks(1100, 2000)).toContain(1500);
  });
});
