import "server-only";
import { cache } from "react";
import type { MuseumContentKind, MuseumPublication, MuseumPublicationPage, StudioMuseum } from "./museum-studio";
async function read<T>(path: string): Promise<T | null> {
  const response = await fetch(new URL(`/api/v1/museum-publications/${path}`, process.env.API_INTERNAL_URL ?? "http://localhost:8080"), { cache: "no-store", redirect: "error", signal: AbortSignal.timeout(12000) });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("Museum publications are temporarily unavailable.");
  return response.json();
}
export const getMuseumPublications = cache(async (slug: string, kind: MuseumContentKind, cursor = "", query = ""): Promise<MuseumPublicationPage> => (await read<MuseumPublicationPage>(`${encodeURIComponent(slug)}?${new URLSearchParams({ kind, cursor, q: query })}`)) ?? { items: [], next_cursor: "" });
export const getMuseumPublication = cache((slug: string, id: string) => read<MuseumPublication>(`${encodeURIComponent(slug)}/${encodeURIComponent(id)}`));
export const getPublishedMuseum = cache((slug: string) => read<StudioMuseum>(`${encodeURIComponent(slug)}/museum`));
