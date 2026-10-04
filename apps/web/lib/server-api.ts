import "server-only";
import { cache } from "react";
import type { ArtistDetail, ArtistBrowsePage, Artwork, Museum } from "./types";
import { researchPreviewEnabled, researchPreviewToken } from "./research-preview";
export { researchPreviewEnabled, researchPreviewToken } from "./research-preview";

export const getArtist = cache(async (slug: string, fullCatalogue = false): Promise<ArtistDetail | null> => {
  if (slug.length > 100 || !/^[a-z0-9]+(?:[-_][a-z0-9]+)*$/.test(slug)) return null;
  const token = researchPreviewToken();
  const url = new URL(`/api/v1/artists/${encodeURIComponent(slug)}`, process.env.API_INTERNAL_URL ?? "http://localhost:8080");
  url.searchParams.set("preview", fullCatalogue && researchPreviewEnabled() ? "1" : "0");
  const options = (): RequestInit => ({ cache: "no-store" as const, headers: token ? { authorization: `Bearer ${token}` } : {}, signal: AbortSignal.timeout(8000) });
  let response = await fetch(url, options());
  if (response.status === 404 && researchPreviewEnabled() && !fullCatalogue) {
    url.searchParams.set("preview", "1");
    response = await fetch(url, options());
  }
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("The catalogue is temporarily unavailable.");
  return response.json();
});

export const getMuseum = cache(async (slug: string): Promise<Museum | null> => {
  if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(slug) || slug.length > 100) return null;
  const token = researchPreviewToken();
  const url = new URL(`/api/v1/museums/${encodeURIComponent(slug)}`, process.env.API_INTERNAL_URL ?? "http://localhost:8080");
  if (researchPreviewEnabled()) url.searchParams.set("preview", "1");
  const response = await fetch(url, { cache: "no-store", headers: token ? { authorization: `Bearer ${token}` } : {}, signal: AbortSignal.timeout(8000) });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("The museum catalogue is temporarily unavailable.");
  return response.json();
});

export const getArtistArtwork = cache(async (slug: string, id: string, fullCatalogue = false): Promise<Artwork | null> => {
  if (slug.length > 100 || !/^[a-z0-9]+(?:[-_][a-z0-9]+)*$/.test(slug) || !/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i.test(id)) return null;
  const token = researchPreviewToken();
  const artist = await getArtist(slug, fullCatalogue);
  if (!artist) return null;
  const url = new URL(`/api/v1/artists/${encodeURIComponent(artist.slug)}/works/${id}`, process.env.API_INTERNAL_URL ?? "http://localhost:8080");
  url.searchParams.set("preview", (fullCatalogue && researchPreviewEnabled()) || artist.status !== "published" ? "1" : "0");
  const response = await fetch(url, { cache: "no-store", headers: token ? { authorization: `Bearer ${token}` } : {}, signal: AbortSignal.timeout(8000) });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("The artwork is temporarily unavailable.");
  return response.json();
});

export async function getArtistDirectory(params: URLSearchParams): Promise<ArtistBrowsePage | null> {
  const url = new URL("/api/v1/artists", process.env.API_INTERNAL_URL ?? "http://localhost:8080");
  url.search = params.toString();
  url.searchParams.set("preview", researchPreviewEnabled() ? "1" : "0");
  const token = researchPreviewToken();
  const response = await fetch(url, { cache: "no-store", headers: token ? { authorization: `Bearer ${token}` } : {}, signal: AbortSignal.timeout(10000) });
  if (response.status === 400) return null;
  if (!response.ok) throw new Error("The artist directory is temporarily unavailable.");
  return response.json();
}
