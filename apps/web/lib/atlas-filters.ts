import type { AtlasType } from "./atlas";

export const allAtlasKinds: AtlasType[] = ["artwork", "book", "event"];
const startingFilters = ["preset", "q", "creator", "country", "continent", "region", "start", "end", "highlights", "artwork_image_only"];

export function atlasLayers(params: URLSearchParams): string[] {
  const explicit = params.getAll("type");
  if (explicit.length) return explicit;
  // Removing every layer is an intentional empty canvas. A new filter action
  // can populate it again; reload and history must preserve the explicit choice.
  if (params.get("selection") === "true") return [];
  return startingFilters.some(key => params.getAll(key).some(value => value.trim())) ? allAtlasKinds : [];
}

export function layersAfterFilter(layers: string[], updates: Record<string, string | string[] | null>): string[] {
  const starts = Object.values(updates).some(value => Array.isArray(value) ? value.length > 0 : Boolean(value?.trim()));
  return layers.length || !starts ? layers : allAtlasKinds;
}

export const entityFields: Record<AtlasType, string[]> = {
  artwork: ["q", "painter", "movement", "region", "country", "work_type", "women", "popular", "image_only"],
  book: ["q", "author", "region", "country", "language", "women", "top100"],
  event: ["q", "topic", "kind", "region", "country", "top100"],
};
export const allEntityKeys = Object.entries(entityFields).flatMap(([type, fields]) => fields.map(field => `${type}_${field}`));
export function readEntityFilters(type: AtlasType, source: URLSearchParams) {
  const result = new URLSearchParams();
  for (const field of entityFields[type]) for (const value of source.getAll(`${type}_${field}`)) result.append(field, value);
  const top = type === "artwork" ? "popular" : "top100";
  if (!result.has(top)) result.set(top, String(type !== "artwork" && source.get("highlights") !== "false"));
  if (type === "artwork") result.set("image_only", "true");
  return result;
}
export function entityUpdates(type: AtlasType, filters?: URLSearchParams): Record<string, string[] | null> {
  return Object.fromEntries(entityFields[type].map(field => [`${type}_${field}`, filters?.has(field) ? filters.getAll(field) : null]));
}
