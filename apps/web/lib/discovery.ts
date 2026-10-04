type Changes = Record<string, string | string[] | null>;
const dimensions = new Set(["q", "author", "painter", "movement", "country", "continent", "region", "work_type", "language", "women", "topic", "kind", "creator"]);

// A deliberate filter replaces the editorial starting selection. Explicit
// highlight toggles and manual year edits retain their own meaning.
export function discoveryChanges(values: Changes, highlight: "popular" | "top100" | "highlights"): Changes {
  const filtering = Object.keys(values).some(key => dimensions.has(key.replace(/^(artwork|book|event)_/, "")));
  if (!filtering || Object.hasOwn(values, highlight)) return values;
  return { [highlight]: "false", ...(highlight === "highlights" ? { artwork_popular: "false", book_top100: "false", event_top100: "false" } : {}), start: null, end: null, fit: "true", ...values };
}
