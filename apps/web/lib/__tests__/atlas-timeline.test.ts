import { describe, expect, it } from "vitest";
import { atlasTimelineScale } from "../atlas-timeline";
import { bookAxisTicks, bookTickPosition, positionBooks } from "../books";

const bounds = { start: -12000, end: 2000 };
const ranges = [
  { start: 1939, end: 1945 }, { start: 1933, end: 1955 },
  { start: 1350, end: 1600 }, { start: 1300, end: 1650 },
  { start: -12000, end: -11999 }, { start: -500, end: -100 },
  { start: -2, end: 2 }, { start: -1, end: 1 },
  { start: 1, end: 2 }, { start: 1999, end: 2000 },
  { start: -12000, end: 1999 }, { start: 1399, end: 1401 },
];

describe("All timeline zoom", () => {
  for (const width of [0, 100, 284, 354, 1392]) {
    it(`retains the compressed overview at ${width}px`, () => {
      const scale = atlasTimelineScale(bounds, bounds, width);
      expect(scale.focused).toBe(false);
      expect(scale.ticks).toEqual(bookAxisTicks(bounds, width, 1400));
      for (const year of [-12000, -5000, -1, 1, 1400, 1800, 2000]) {
        expect(scale.position(year)).toBe(bookTickPosition(year, bounds, 1400));
      }
    });
    for (const range of ranges) it(`fits ${range.start} to ${range.end} at ${width}px`, () => {
      const scale = atlasTimelineScale(range, bounds, width);
      expect(scale.focused).toBe(true);
      expect(scale.position(range.start)).toBe(0);
      expect(scale.position(range.end)).toBe(100);
      expect(scale.ticks[0].year).toBe(range.start);
      expect(scale.ticks.at(-1)!.year).toBe(range.end);
      expect(new Set(scale.ticks.map(tick => tick.year)).size).toBe(scale.ticks.length);
      expect(scale.ticks.length).toBeLessThanOrEqual(Math.max(2, Math.floor(width / 76) + 1));
      for (let index = 0; index < scale.ticks.length; index++) {
        const tick = scale.ticks[index];
        expect(tick.year).not.toBe(0);
        expect(Number.isInteger(tick.year)).toBe(true);
        expect(scale.position(tick.year)).toBeGreaterThanOrEqual(0);
        expect(scale.position(tick.year)).toBeLessThanOrEqual(100);
        expect(tick.label.includes("BCE")).toBe(tick.year < 0);
        if (index > 0 && width >= 100) {
          expect((scale.position(tick.year) - scale.position(scale.ticks[index - 1].year)) * width / 100).toBeGreaterThanOrEqual(76);
        }
      }
    });
  }

  it("uses equal year spacing through the Renaissance and the BCE boundary", () => {
    for (const range of [{ start: 1300, end: 1650 }, { start: -5, end: 5 }]) {
      const scale = atlasTimelineScale(range, bounds, 1000);
      const years = Array.from({ length: range.end - range.start + 1 }, (_, index) => range.start + index).filter(year => year !== 0);
      const spacing = 100 / (years.length - 1);
      for (let index = 1; index < years.length; index++) {
        expect(scale.position(years[index]) - scale.position(years[index - 1])).toBeCloseTo(spacing);
      }
    }
  });

  for (const width of [284, 1392]) it(`clips spanning entries and keeps end labels inside ${width}px`, () => {
    const range = { start: 1939, end: 1945 };
    const { position } = atlasTimelineScale(range, bounds, width);
    const marks = positionBooks([
      { startYear: 1900, endYear: 2000 },
      { startYear: 1939, endYear: 1939 },
      { startYear: 1942, endYear: 1942 },
      { startYear: 1945, endYear: 1945 },
    ], range, width, 1400, position);
    expect(marks[0].left).toBe(0);
    expect(marks[0].width).toBe(100);
    expect(marks[1].left).toBe(0);
    expect(marks[2].left).toBe(50);
    expect(marks[3].left + marks[3].width).toBeCloseTo(100);
    for (const mark of marks) {
      expect(mark.left).toBeGreaterThanOrEqual(0);
      expect(mark.left + mark.width).toBeLessThanOrEqual(100.000001);
      const labelLeft = mark.left / 100 * width + mark.labelOffset;
      expect(labelLeft).toBeGreaterThanOrEqual(-0.000001);
      expect(labelLeft + mark.labelWidth).toBeLessThanOrEqual(width + 0.000001);
    }
  });
});
