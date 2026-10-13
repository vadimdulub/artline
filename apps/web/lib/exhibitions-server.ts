import "server-only";
import { cache } from "react";
import type { ExhibitionDetail, ExhibitionPage, ExhibitionEntries, ExhibitionArtwork, ArtworkAppearances } from "./exhibitions";

async function request<T>(path: string): Promise<T | null> {
  let base = process.env.API_INTERNAL_URL ?? "http://localhost:8080";
  // A separate source-backed local research service; never a production switch.
  if (process.env.NODE_ENV === "development" && process.env.EXHIBITIONS_REVIEW_API_URL) {
    const preview = new URL(process.env.EXHIBITIONS_REVIEW_API_URL);
    if (preview.protocol !== "http:" || !["127.0.0.1", "[::1]"].includes(preview.hostname) || preview.username || preview.password) throw new Error("Exhibition review requires a loopback service.");
    base = preview.origin;
  }
  const url = new URL(`/api/v1/exhibitions${path}`, base);
  const response = await fetch(url, { cache: "no-store", signal: AbortSignal.timeout(10000) });
  if (response.status === 400 || response.status === 404) return null;
  if (!response.ok) throw new Error("The exhibition catalogue is temporarily unavailable.");
  return response.json();
}
export const getExhibition = cache(async (id: string) => {
  if (!/^[a-f0-9]{8}(-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i.test(id)) return null;
  return request<ExhibitionDetail>(`/${id}`);
});
export function getExhibitions(query: URLSearchParams) { return request<ExhibitionPage>(`?${query}`); }
export function getExhibitionEntries(id: string, after: string, participation = "") {
  return request<ExhibitionEntries>(`/${encodeURIComponent(id)}/entries?${new URLSearchParams({ after, limit: "50", participation })}`);
}
export const getExhibitionArtwork = cache(async (id: string) => {
  if (!/^[a-f0-9]{8}(-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i.test(id)) return null;
  return request<ExhibitionArtwork>(`/artworks/${id}`);
});
export function getArtworkExhibitions(id: string, after: string) {
  return request<ArtworkAppearances>(`/artworks/${encodeURIComponent(id)}/exhibitions?${new URLSearchParams({ after, limit: "40" })}`);
}
