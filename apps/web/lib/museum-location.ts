import { countryName } from "./api";
import type { Museum } from "./types";

// Keep each city with its own country. A venue must never supply the country
// for an institution's unrelated or incomplete primary location.
export function museumLocations(museum: Pick<Museum, "city" | "country" | "venues">): string[] {
  const locations = [museum, ...museum.venues];
  const complete = locations.filter(location => location.city?.trim() && location.country?.trim());
  const candidates = complete.length ? complete : locations;
  return [...new Set(candidates.map(location => {
    const city = location.city?.trim();
    const country = location.country?.trim();
    return [city, country ? countryName(country.toUpperCase()) : undefined].filter(Boolean).join(", ");
  }).filter(Boolean))];
}
