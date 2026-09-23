import { bookAxisTicks, bookTickPosition, bookYearLabel, type BookRange } from "./books";

// Calendar coordinates keep 1 BCE and 1 CE one year apart.
const calendar = (year: number) => year < 0 ? year + 1 : year;

export function atlasTimelineScale(range: BookRange, bounds: BookRange, width: number, overview?: {
  position: (year: number) => number;
  ticks: { year: number; label: string }[];
}) {
  const focused = range.start !== bounds.start || range.end !== bounds.end;
  if (!focused) return {
    focused,
    position: overview?.position ?? ((year: number) => bookTickPosition(year, bounds, 1400)),
    ticks: overview?.ticks ?? bookAxisTicks(bounds, width, 1400),
  };

  // A selected interval uses equal year spacing, including across the overview's
  // compression boundaries. Only the overview and navigation slider compress time.
  const span = calendar(range.end) - calendar(range.start);
  const position = (year: number) => (calendar(year) - calendar(range.start)) / span * 100;
  const spacing = Math.max(76, Math.max(bookYearLabel(range.start).length, bookYearLabel(range.end).length) * 7 + 18);
  const desiredStep = span / Math.max(1, Math.floor(width / spacing));
  const magnitude = 10 ** Math.floor(Math.log10(Math.max(1, desiredStep)));
  const step = [1, 2, 5, 10].map(value => value * magnitude).find(value => value >= desiredStep)!;
  const years = [range.start];
  for (let year = Math.ceil(range.start / step) * step; year < range.end; year += step) {
    if (year === 0) continue;
    if ((position(year) - position(years[years.length - 1])) * width / 100 >= spacing &&
        (100 - position(year)) * width / 100 >= spacing) years.push(year);
  }
  years.push(range.end);
  return { focused, position, ticks: years.map(year => ({ year, label: bookYearLabel(year) })) };
}
