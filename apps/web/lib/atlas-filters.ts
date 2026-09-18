import type { AtlasType } from "./atlas";

export const entityFields: Record<AtlasType, string[]> = {
  artwork: ["q", "painter", "movement", "region", "country", "work_type", "women", "popular"],
  book: ["q", "author", "region", "country", "language", "women", "top100"],
  event: ["q", "topic", "kind", "region", "country", "top100"],
};
export const allEntityKeys = Object.entries(entityFields).flatMap(([type, fields]) => fields.map(field => `${type}_${field}`));
export function readEntityFilters(type: AtlasType, source: URLSearchParams) {
  const result = new URLSearchParams();
  for (const field of entityFields[type]) for (const value of source.getAll(`${type}_${field}`)) result.append(field, value);
  const top = type === "artwork" ? "popular" : "top100";
  if (!result.has(top)) result.set(top, "true");
  return result;
}
export function entityUpdates(type: AtlasType, filters?: URLSearchParams): Record<string, string[] | null> {
  return Object.fromEntries(entityFields[type].map(field => [`${type}_${field}`, filters?.has(field) ? filters.getAll(field) : null]));
}
