import { memberReturnTo } from "./member-return";
const filterKeys = ["art_images", "art_year", "art_cursor", "art_q", "art_museum", "art_type", "work"];

export function painterRecordPath(slug: string, query: Record<string, string | string[] | undefined>, artworkId?: string): string {
  const path = `/artists/${encodeURIComponent(slug)}${artworkId ? `/works/${encodeURIComponent(artworkId)}` : ""}`;
  const filters = new URLSearchParams();
  // Old cursors were bound to the removed visibility scope. Keep the actual
  // artwork filters, but restart paging when normalizing a legacy link.
  const legacyScope = query.catalogue !== undefined || query.preview !== undefined;
  for (const key of filterKeys) if (typeof query[key] === "string" && !(legacyScope && key === "art_cursor")) filters.set(key, query[key]);
  return memberReturnTo(`${path}${filters.size ? `?${filters}` : ""}`) ?? memberReturnTo(path) ?? "/artists";
}
