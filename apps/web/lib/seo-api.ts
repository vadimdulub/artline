import "server-only";
export type SEOEntry = { path: string; name: string };

export async function discoveryRequest<T>(path: string): Promise<T> {
  // The Go discovery endpoints always enforce published visibility themselves.
  const url = new URL(`/api/v1/seo/${path}`, process.env.API_INTERNAL_URL ?? "http://localhost:8080");
  const response = await fetch(url, { cache: "no-store", signal: AbortSignal.timeout(10000) });
  if (!response.ok) throw new Error("Search discovery is temporarily unavailable.");
  return response.json();
}
