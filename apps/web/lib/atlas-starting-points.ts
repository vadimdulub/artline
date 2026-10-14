import type { AtlasPreset } from "./atlas";

// Fully specified shared views can load alongside the preset labels. Incomplete
// views must wait for the preset's default filters and date window.
export function atlasNeedsPresetMetadata(params: URLSearchParams): boolean {
  return Boolean(params.get("preset")) && !(params.get("preset_filters") === "custom" && params.has("start") && params.has("end"));
}

// Matches the API's ApplyStartingFilters. All filtering remains on the server.
export function resolvedStartingFilters(params: URLSearchParams, preset?: AtlasPreset): URLSearchParams {
  const result = new URLSearchParams(params);
  if (!preset || params.get("preset_filters") === "custom") return result;
  if (!["country", "continent", "region", "artwork_country", "artwork_region"].some(key => params.has(key)) && preset.startingCountries?.length) {
    preset.startingCountries.forEach(value => result.append("country", value));
    result.set("country_scope", "artwork");
  }
  if (!["creator", "artwork_painter", "book_author"].some(key => params.has(key))) {
    preset.startingCreators?.forEach(value => result.append("creator", value));
  }
  if (!params.has("highlights")) result.set("highlights", String(preset.startingHighlights));
  return result;
}

export function startingFilters(next?: AtlasPreset): Record<string, string | string[] | null> {
  if (!next) return {};
  return {
    country: next.startingCountries ?? null,
    country_scope: next.startingCountries?.length ? "artwork" : null,
    continent: null, region: null,
    creator: next.startingCreators ?? null,
    highlights: String(next.startingHighlights),
    book_top100: null, event_top100: null,
    preset_filters: "custom",
  };
}
