export type GuideKind = "artist" | "museum" | "using";
export type GuideSearchEntry = {
  slug: string; kind: GuideKind; href: string; title: string; label: string;
  location: string; subtitle: string; image: string; count: number; languages: number;
};
export type GuideSearchPage = {
  items: GuideSearchEntry[]; total: number; matched: number;
  counts: Record<GuideKind | "all", number>; next_cursor: string;
};

export function guideFilters(raw: Record<string, string | string[] | undefined>) {
  const result = new URLSearchParams();
  for (const key of ["q", "kind", "cursor"]) {
    const value = raw[key];
    if (typeof value === "string" && value) result.set(key, value);
    else if (Array.isArray(value)) value.forEach(item => result.append(key, item));
  }
  return result;
}
