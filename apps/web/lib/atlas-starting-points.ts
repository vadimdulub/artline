import type { AtlasPreset } from "./atlas";

// Move the previous starting selection with the period, retaining custom geography.
export function startingGeography(next: AtlasPreset | undefined, current: AtlasPreset | undefined, params: URLSearchParams, starting: boolean): Record<string, string | string[] | null> {
  if (!next) return {};
  const countries = params.getAll("country");
  const otherGeography = params.has("continent") || params.has("region");
  const previousDefault = params.get("country_scope") === "artwork" && !otherGeography && countries.length > 0 && countries.length === current?.startingCountries?.length && countries.every(country => current.startingCountries?.includes(country));
  if (!starting && (countries.length || otherGeography) && !previousDefault) return {};
  return { country: next.startingCountries ?? null, country_scope: next.startingCountries?.length ? "artwork" : null, continent: null, region: null };
}
