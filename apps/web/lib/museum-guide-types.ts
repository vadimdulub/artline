export const guideLanguages = { en: "English", ru: "Русский", it: "Italiano", de: "Deutsch", zh: "简体中文", fr: "Français", es: "Español", pt: "Português", ja: "日本語", ar: "العربية" } as const;
export type GuideLocale = keyof typeof guideLanguages;
export type GuideWork = {
  id: string; title: string; catalogueTitle: string; artist: string; artists: { slug: string; name: string; role: string }[];
  // A guide can identify a creator before the catalogue relationship exists.
  // Explicit null uses the ID-based view; absent preserves older guide links.
  catalogueArtistSlug?: string | null;
  date: string; start: number | null; end: number | null; medium: string; accession: string;
  image: string; imageSource: string; credit: string; license: string; licenseUrl: string;
  source: string; description: string; importance: string; museum: string;
};
export type GuideBook = { title: string; author: string; note: string; url: string; access: string };
export type MuseumGuide = {
  kind?: "museum" | "artist";
  artist?: { name: string; slug: string; lifeDates: string };
  comparisonArtists?: { slug: string; name: string }[];
  slug: string; locale: GuideLocale; title: string; museum: string; city: string; country: string;
  subtitle: string; introduction: string; visitNote: string; selectionNote: string;
  closingSections?: { title: string; paragraphs: string[] }[];
  website: string; officialGuide: string; updated: string; works: GuideWork[]; books: GuideBook[];
  context: { start: number; end: number }; labels: Record<string, string>;
};
export type GuideSummary = Pick<MuseumGuide, "slug" | "museum" | "city" | "country" | "title" | "subtitle" | "updated" | "kind" | "artist"> & { image: string; count: number; locales: GuideLocale[] };
export function guideSubject(guide: Pick<MuseumGuide, "museum" | "artist">) { return guide.artist?.name || guide.museum; }
export function guideLocation(guide: Pick<MuseumGuide, "city" | "country" | "artist">) { return guide.artist?.lifeDates || [guide.city, guide.country].filter(Boolean).join(", "); }
export function guidePath(slug: string, locale: GuideLocale = "en") { return `/guides/${slug}${locale === "en" ? "" : `/${locale}`}`; }
export function guideWorkPath(work: Pick<GuideWork, "id" | "artists" | "catalogueArtistSlug">) {
  const slug = work.catalogueArtistSlug === undefined ? work.artists[0]?.slug : work.catalogueArtistSlug;
  return slug ? `/artists/${slug}/works/${work.id}` : `/all?selection=true&type=artwork&highlights=false&artwork_id=${work.id}&item=${work.id}&itemType=artwork`;
}
export function guidePortalLinks(guide: Pick<MuseumGuide, "works" | "context" | "comparisonArtists"> & Partial<Pick<MuseumGuide, "slug" | "locale">>) {
  const { start, end } = guide.context;
  const years = { start: String(start), end: String(end) };
  const all = new URLSearchParams({ ...years, selection: "true", highlights: "false", artwork_popular: "false", book_top100: "true", event_top100: "true" });
  for (const type of ["artwork", "book", "event"]) all.append("type", type);
  for (const work of guide.works) all.append("artwork_id", work.id);
  const painters = new URLSearchParams({ start: String(Math.max(1100, start - 60)), end: String(Math.min(2000, end + 40)), popular: "false" });
  for (const slug of [...new Set([...guide.works.flatMap(work => work.artists.map(artist => artist.slug)), ...(guide.comparisonArtists || []).map(artist => artist.slug)])].slice(0, 32)) painters.append("painter", slug);
  // Presentation context only: these parameters never enter catalogue requests.
  if (guide.slug) for (const params of [all, painters]) {
    params.set("guide", guide.slug);
    params.set("guide_lang", guide.locale ?? "en");
  }
  const context = new URLSearchParams({ ...years, top100: "true" });
  return { all: `/all?${all}`, painters: `/?${painters}`, events: `/events?${context}`, books: `/books?${context}` };
}
