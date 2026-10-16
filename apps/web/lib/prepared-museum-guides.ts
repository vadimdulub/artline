import "server-only";
import type { GuideSearchPage } from "./guide-search";

export async function getPreparedMuseumGuides(slug: string): Promise<GuideSearchPage> {
  const url = new URL("/api/v1/guides", process.env.API_INTERNAL_URL ?? "http://localhost:8080");
  url.searchParams.set("institution", slug);
  const response = await fetch(url, { cache: "no-store", redirect: "error", signal: AbortSignal.timeout(8000) });
  if (!response.ok) throw new Error("Artline guides could not be loaded.");
  return response.json();
}
