export type Book = {
  id: string;
  title: string;
  author: string;
  years: string;
  era: string;
  theme: string;
  description: string;
  coverTone: string;
  coverInk: string;
  coverMark: string;
  cover?: { imageUrl: string; sourceUrl: string; label: string; credit: string; license: string; licenseUrl: string; checkedAt: string };
  startYear: number | null;
  endYear: number | null;
  approximate: boolean;
  creators: { id: string; name: string; description: string; birth: string | null; death: string | null; sourceUrl: string; kind?: string; credit?: string }[];
  sourceUrl: string;
  dateBasis: string;
  selectionBasis: string;
  status: string;
};

export type BookRange = { start: number; end: number };
export type BookFilterOption = { slug: string; name: string };
export type BooksFacets = { languages: BookFilterOption[]; countries: BookFilterOption[]; regions: BookFilterOption[] };
export type BookSuggestion = { key: "language" | "country" | "region" | "author"; value: string; name: string; count: number };
export type TimelineAuthor = Book["creators"][number] & {
  startYear: number | null; endYear: number | null; lifespan: string; approximate: boolean; bookCount: number; credits: string[];
};
export type BooksResponse = {
  items: Book[];
  total: number;
  selectionTotal: number;
  hasMore: boolean;
  nextCursor: string;
  range: BookRange;
  bounds: BookRange;
  undatedTotal: number;
  mode: "individual" | "density";
  density: { start_year: number; end_year: number; count: number }[];
  suggested_filters?: BookSuggestion[];
  authors?: TimelineAuthor[];
  view?: "books" | "authors";
  periods: (BookRange & { label: string })[];
  ticks: { year: number; label: string }[];
};

export function bookYearLabel(year: number): string {
  return year < 0 ? `${Math.abs(year)} BCE` : `${year}`;
}

// Format the server's lifespan envelope compactly on the chart. The drawer
// retains the original birth/death labels, including alternatives and ranges.
export function authorLifespanLabel(author: TimelineAuthor): string {
  if (author.birth && author.death && author.startYear !== null && author.endYear !== null) {
    return `${author.approximate ? "c. " : ""}${bookYearLabel(author.startYear)}–${bookYearLabel(author.endYear)}`;
  }
  return author.lifespan;
}

export function compressedBCE(range: BookRange): boolean { return range.start < 1 && range.end > 1; }

const calendar = (year: number) => year < 0 ? year + 1 : year;
const historicalYear = (value: number) => value <= 0 ? value - 1 : value;
export function compressedBefore1700(range: BookRange): boolean { return range.start < 1700 && range.end > 1700; }

// Fixed historical axis: 5000 BCE / 1 / linearFrom / 2000 anchor 0 / 5 / 25 / 100.
// Books uses 1700; All uses 1400. Selecting years never rescales these anchors.
function bookCoordinate(year: number, linearFrom: number): number {
 const y=calendar(year);
 return y<=1 ? (y+4999)/5000*5 : y<=linearFrom ? 5+(y-1)/(linearFrom-1)*20 : 25+(y-linearFrom)/(2000-linearFrom)*75;
}
function bookCoordinateYear(value: number, linearFrom: number): number {
 const y=value<=5 ? value/5*5000-4999 : value<=25 ? 1+(value-5)/20*(linearFrom-1) : linearFrom+(value-25)/75*(2000-linearFrom);
 return historicalYear(Math.round(y));
}
export function bookTickPosition(year: number, range: BookRange, linearFrom = 1700): number {
 return (bookCoordinate(year,linearFrom)-bookCoordinate(range.start,linearFrom))/(bookCoordinate(range.end,linearFrom)-bookCoordinate(range.start,linearFrom))*100;
}
export function bookYearAtPosition(position: number, range: BookRange, linearFrom = 1700): number {
 const fraction=Math.max(0,Math.min(100,position))/100;
 return bookCoordinateYear(bookCoordinate(range.start,linearFrom)+fraction*(bookCoordinate(range.end,linearFrom)-bookCoordinate(range.start,linearFrom)),linearFrom);
}

// Tick visibility follows pixel spacing, since equal calendar steps are no
// longer equally spaced. Keep the change of scale and both ends legible.
export function visibleBookTicks(ticks: BooksResponse["ticks"], range: BookRange, width: number, linearFrom = 1700) {
  if (!ticks.length) return [];
  const compressed = range.start < linearFrom && range.end > linearFrom;
  const candidates = [...ticks];
  if (compressed && !candidates.some(tick => tick.year === linearFrom)) candidates.push({ year: linearFrom, label: String(linearFrom) });
  candidates.sort((a, b) => a.year - b.year);
  const chosen = [candidates[0], candidates[candidates.length - 1]];
  const boundary = candidates.find(tick => tick.year === linearFrom);
  if (compressed && boundary) chosen.push(boundary);
  for (const tick of candidates) {
    if (chosen.every(other => Math.abs(bookTickPosition(tick.year, range, linearFrom) - bookTickPosition(other.year, range, linearFrom)) * width / 100 >= 70)) chosen.push(tick);
  }
  return [...new Map(chosen.map(tick => [tick.year, tick])).values()].sort((a, b) => a.year - b.year);
}

// Axis labels are presentation only. Date selection still belongs to the API,
// while the complete historical axis stays fixed across range changes.
export function bookAxisTicks(bounds: BookRange, width: number, linearFrom = 1700) {
  const ticks = [{ year: Math.round(bounds.start / 2), label: "BCE" }];
  for (let year = 100; year <= bounds.end; year += 100) ticks.push({ year, label: String(year) });
  return visibleBookTicks(ticks, bounds, width, linearFrom);
}

// Visual layout only; the API owns chronology, filtering and page order.
export function positionBooks<T extends { startYear: number | null; endYear: number | null }>(books: T[], range: BookRange, width: number, linearFrom = 1700) {
  const pixels = Math.max(1, width);
  const lanes: [number, number][][] = [];
  return books.filter((book): book is T & { startYear: number; endYear: number } => book.startYear !== null && book.endYear !== null).map(book => {
    const x = bookTickPosition(Math.max(range.start, book.startYear), range, linearFrom) / 100 * pixels;
    const end = bookTickPosition(Math.min(range.end, book.endYear), range, linearFrom) / 100 * pixels;
    const markWidth = Math.min(pixels, Math.max(8, end - x));
    const left = Math.min(x, pixels - markWidth);
    const labelWidth = Math.min(pixels, 246);
    const labelLeft = Math.max(0, Math.min(left, pixels - labelWidth));
    const occupied: [number, number] = [Math.min(left, labelLeft), Math.max(left + markWidth, labelLeft + labelWidth)];
    let lane = lanes.findIndex(intervals => intervals.every(([a, b]) => occupied[0] >= b + 18 || occupied[1] + 18 <= a));
    if (lane < 0) { lane = lanes.length; lanes.push([]); }
    lanes[lane].push(occupied);
    return { ...book, lane, left: left / pixels * 100, width: markWidth / pixels * 100, labelOffset: labelLeft - left, labelWidth };
  });
}
