import type { BookRange, BookFilterOption } from "./books";

export type HistoricalEvent = {
  id: string; sourceId: string; sourceRevision: number; sourceUrl: string;
  title: string; description: string; significance: string; years: string;
  descriptionSource?: { name: string; url: string; kind: "wikipedia" | "wikidata" | "editorial"; language?: string; title?: string; revision?: number; license?: string; licenseUrl?: string; notice: string };
  startYear: number | null; endYear: number | null; approximate: boolean;
  dateBasis: string; kind: "Event" | "Period" | "Movement";
  topics: string[]; countries: string[]; regions: string[]; geographyBasis: string;
  locations: { name: string; url: string }[]; people: { name: string; url: string }[];
  sources: { name: string; url: string }[]; connections: string[];
  top100: boolean; selectionBasis: string; status: string;
};
export type EventSuggestion = { key: "topic" | "country" | "region" | "kind"; value: string; name: string; count: number };
export type EventsFacets = { topics: BookFilterOption[]; countries: BookFilterOption[]; regions: BookFilterOption[]; kinds: BookFilterOption[] };
export type EventsResponse = {
  items: HistoricalEvent[]; total: number; selectionTotal: number; undatedTotal: number;
  hasMore: boolean; nextCursor: string; range: BookRange; bounds: BookRange;
  ticks: { year: number; label: string }[]; mode: "individual" | "density";
  density: { start_year: number; end_year: number; count: number }[];
  suggested_filters: EventSuggestion[];
};
