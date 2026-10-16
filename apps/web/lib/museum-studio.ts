export type MuseumContentKind = "artwork" | "exhibition" | "guide" | "profile";
export type StudioMuseum = { id: string; slug: string; name: string; website_url: string; managed: boolean; eligible: boolean };
export type MuseumArtworkRef = { kind: "catalogue" | "museum"; id: string; note: string };
export type MuseumArtworkChoice = MuseumArtworkRef & { title: string; creator: string; date: string; image_url: string; image_alt: string; credit: string; href: string; available: boolean; published: boolean };
export type MuseumArtworkPage = { items: MuseumArtworkChoice[]; next_cursor: string };
export type MuseumDocument = {
  image_id: string; artworks: MuseumArtworkRef[]; body_format: "" | "markdown";
  title: string; summary: string; body: string; creator: string; date_label: string;
  year_start: number | null; year_end: number | null; medium: string; dimensions: string; inventory: string;
  start_date: string; end_date: string; venue: string; language: string;
  image_url: string; image_alt: string; image_credit: string; source_url: string;
  visit_url: string; address: string; hours: string;
};
export type MuseumPublication = { resolved_artworks?: MuseumArtworkChoice[]; id: string; kind: MuseumContentKind; document: MuseumDocument; version?: number; published: boolean; has_changes?: boolean; updated_at: string };
export type MuseumPublicationPage = { items: MuseumPublication[]; next_cursor: string };
export const contentLabels: Record<MuseumContentKind, string> = { artwork: "Artworks", exhibition: "Exhibitions", guide: "Guides", profile: "Museum page" };
export const contentSingular: Record<MuseumContentKind, string> = { artwork: "artwork", exhibition: "exhibition", guide: "guide", profile: "museum page" };
export function emptyMuseumDocument(): MuseumDocument {
  return { image_id: "", artworks: [], body_format: "", title: "", summary: "", body: "", creator: "", date_label: "", year_start: null, year_end: null, medium: "", dimensions: "", inventory: "", start_date: "", end_date: "", venue: "", language: "", image_url: "", image_alt: "", image_credit: "", source_url: "", visit_url: "", address: "", hours: "" };
}
export function publicationPath(slug: string, id: string) { return `/museums/${encodeURIComponent(slug)}/publications/${id}`; }
export async function studioRequest<T>(path = "", init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/museum-studio${path}`, { ...init, cache: "no-store", headers: { "content-type": "application/json", ...init?.headers } });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error?.message || "Museum publishing is temporarily unavailable.");
  return data;
}

export function museumImageURL(slug: string, document: Pick<MuseumDocument, "image_id" | "image_url">) {
  return document.image_id ? `/api/museum-media/${encodeURIComponent(slug)}/${document.image_id}` : document.image_url;
}
