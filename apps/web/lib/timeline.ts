import type { TimelineArtist } from "./types";

export type PositionedArtist = TimelineArtist & {
  lane: number;
  left: number;
  width: number;
  labelOffset: number;
  labelWidth: number;
};

export function positionArtists(
  artists: TimelineArtist[],
  rangeStart: number,
  rangeEnd: number,
  viewportWidth = 1200,
): PositionedArtist[] {
  const span = Math.max(1, rangeEnd - rangeStart);
  const pixels = Math.max(1, viewportWidth);
  const lanes: Array<Array<[number, number]>> = [];

  return [...artists]
    .filter(artist => artist.start_year <= rangeEnd && artist.end_year >= rangeStart)
    .sort((a, b) => a.start_year - b.start_year || a.end_year - b.end_year)
    .map((artist) => {
      const visibleStart = Math.max(rangeStart, artist.start_year);
      const visibleEnd = Math.min(rangeEnd, artist.end_year);
      const rawX = (visibleStart - rangeStart) / span * pixels;
      const markWidth = Math.min(pixels, Math.max(8, (visibleEnd - visibleStart) / span * pixels));
      const x = Math.min(rawX, pixels - markWidth);
      const right = x + markWidth;
      const labelWidth = Math.min(pixels, 220, Math.max(artist.name.length * 7.5, artist.date_display.length * 6.5) + 12);
      const labelLeft = Math.max(0, Math.min(x, pixels - labelWidth));
      const occupied: [number, number] = [Math.min(x, labelLeft), Math.max(right, labelLeft + labelWidth)];
      let lane = lanes.findIndex(intervals => intervals.every(([a, b]) => occupied[0] >= b + 12 || occupied[1] + 12 <= a));
      if (lane === -1) {
        lane = lanes.length;
        lanes.push([]);
      }
      lanes[lane].push(occupied);

      return {
        ...artist,
        lane,
        left: x / pixels * 100,
        width: markWidth / pixels * 100,
        labelOffset: labelLeft - x,
        labelWidth,
      };
    });
}

export function timelineTicks(start: number, end: number): number[] {
  const span = end - start;
  const step = span > 500 ? 100 : span > 200 ? 50 : span > 80 ? 25 : span > 35 ? 10 : span > 10 ? 5 : 1;
  const first = Math.ceil(start / step) * step;
  const ticks: number[] = [];
  for (let year = first; year <= end; year += step) ticks.push(year);
  return ticks;
}

export function normalizeRange(rawStart: string | null, rawEnd: string | null): [number, number] {
  const read = (raw: string | null, fallback: number) => raw && Number.isFinite(Number(raw)) ? Math.max(1100, Math.min(2000, Math.round(Number(raw)))) : fallback;
  let a = read(rawStart, 1100), b = read(rawEnd, 2000);
  if (a > b) [a, b] = [b, a];
  if (a === b) { if (a === 2000) a--; else b++; }
  return [a, b];
}
export function isCurrentPeriod(period: { start_year: number; end_year: number }, start: number, end: number): boolean {
  const [from, to] = normalizeRange(String(period.start_year), String(period.end_year));
  return from === start && to === end;
}
export function presetRange(start: number, end: number, years: number): [number, number] {
  const span = Math.min(900, Math.max(1, years));
  const a = Math.max(1100, Math.min(2000 - span, Math.round((start + end - span) / 2)));
  return [a, a + span];
}
