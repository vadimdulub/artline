import { describe, expect, it } from "vitest";
import { bookTickPosition, bookYearAtPosition, compressedBefore1700, visibleBookTicks } from "../books";

const full = { start: -5000, end: 2000 };

describe("Books timeline scale", () => {
  it("keeps year spacing when translating a window across 1700", () => {
    const before = { start: 1500, end: 1800 };
    const after = {
      start: bookYearAtPosition(bookTickPosition(before.start, full) + 10, full),
      end: bookYearAtPosition(bookTickPosition(before.end, full) + 10, full),
    };
    const spacing = (range: typeof full) => bookTickPosition(1780, range) - bookTickPosition(1760, range);
    expect(spacing(after)).toBeCloseTo(spacing(before), 0);
    expect(after.start).toBeGreaterThan(1700);
  });
  it("reserves three quarters of a broad timeline for 1700 onward", () => {
    expect(bookTickPosition(1700, full)).toBe(25);
    expect(bookTickPosition(1, full)).toBe(5);
    expect(bookTickPosition(1800, full) - bookTickPosition(1700, full)).toBeCloseTo(bookTickPosition(1900, full) - bookTickPosition(1800, full));
    expect(bookTickPosition(2000, full)).toBe(100);
  });

  it("keeps historical years ordered and reversible through both scale boundaries", () => {
    for (const range of [full, { start: 1, end: 2000 }, { start: -5000, end: -1 }, { start: 1200, end: 1700 }, { start: 1731, end: 2000 }]) {
      let previous = -1;
      for (let year = range.start; year <= range.end; year++) {
        if (year === 0) continue;
        const position = bookTickPosition(year, range);
        expect(position).toBeGreaterThan(previous);
        expect(bookYearAtPosition(position, range)).toBe(year);
        previous = position;
      }
      expect(bookYearAtPosition(-10, range)).toBe(range.start);
      expect(bookYearAtPosition(110, range)).toBe(range.end);
    }
  });

  it("restores regular spacing when focused on earlier or modern years", () => {
    for (const range of [{ start: 1200, end: 1700 }, { start: 1700, end: 2000 }, { start: -500, end: -100 }]) {
      expect(compressedBefore1700(range)).toBe(false);
      expect(bookTickPosition((range.start + range.end) / 2, range)).toBeCloseTo(50);
    }
  });

  it("keeps the BCE label, 1700 boundary and recent years readable", () => {
    const candidates = [{ year: -2500, label: "BCE" }, ...Array.from({ length: 20 }, (_, i) => ({ year: (i + 1) * 100, label: String((i + 1) * 100) }))];
    for (const width of [284, 354, 1392]) {
      const ticks = visibleBookTicks(candidates, full, width);
      expect(ticks.map(tick => tick.label)).toEqual(expect.arrayContaining(["BCE", "1700", "2000"]));
      for (let i = 1; i < ticks.length; i++) {
        expect((bookTickPosition(ticks[i].year, full) - bookTickPosition(ticks[i - 1].year, full)) * width / 100).toBeGreaterThan(50);
      }
    }
  });
});
