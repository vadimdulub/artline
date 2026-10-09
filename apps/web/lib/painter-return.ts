const painterPath = /^\/artists\/([a-z0-9]+(?:[-_][a-z0-9]+)*)(?:\/works\/[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12})?$/;
const filterKeys = ["art_images", "art_year", "art_cursor", "art_q", "art_museum", "art_type", "work"];

// Keep OAuth destinations bounded and restricted to full painter records.
export function painterReturnTo(value: unknown): string | null {
  if (typeof value !== "string" || value.length > 768 || /[\\]|[^\x21-\x7e]/.test(value)) return null;
  const match = painterPath.exec(value.split(/[?#]/, 1)[0]);
  if (!match || match[1].length > 100) return null;
  return value;
}

export function painterRecordPath(slug: string, query: Record<string, string | string[] | undefined>, artworkId?: string): string {
  const path = `/artists/${encodeURIComponent(slug)}${artworkId ? `/works/${encodeURIComponent(artworkId)}` : ""}`;
  const filters = new URLSearchParams();
  // Old cursors were bound to the removed visibility scope. Keep the actual
  // artwork filters, but restart paging when normalizing a legacy link.
  const legacyScope = query.catalogue !== undefined || query.preview !== undefined;
  for (const key of filterKeys) if (typeof query[key] === "string" && !(legacyScope && key === "art_cursor")) filters.set(key, query[key]);
  return painterReturnTo(`${path}${filters.size ? `?${filters}` : ""}`) ?? painterReturnTo(path) ?? "/artists";
}

export function painterSignInPath(destination: string): string {
  const returnTo = painterReturnTo(destination);
  return returnTo ? `/account?${new URLSearchParams({ return_to: returnTo })}` : "/account";
}
