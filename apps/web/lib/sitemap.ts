import { absoluteURL } from "./seo";
import { guideLanguages } from "./museum-guide-types";

export const publicPages = ["/about", "/artists", "/guides", "/art-history-timeline", ...Object.keys(guideLanguages).filter(locale => locale !== "en").map(locale => `/art-history-timeline/${locale}`)];
export const explorerPages = ["/", "/books", "/events", "/all"];
export function escapeXML(value: string): string { return value.replace(/[<>&"']/g, character => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;", "'": "&apos;" })[character]!); }
export type SitemapEntry = { path: string; lastModified?: string; images?: string[] };
export function sitemapXML(paths: (string | SitemapEntry)[], index = false): string {
  const root = index ? "sitemapindex" : "urlset", item = index ? "sitemap" : "url";
  const hasImages = !index && paths.some(entry => typeof entry !== "string" && entry.images?.length);
  const imageNamespace = hasImages ? ' xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"' : "";
  return `<?xml version="1.0" encoding="UTF-8"?><${root} xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"${imageNamespace}>${paths.map(entry => {
    const data = typeof entry === "string" ? { path: entry } : entry;
    const modified = data.lastModified ? `<lastmod>${escapeXML(data.lastModified)}</lastmod>` : "";
    const images = !index ? [...new Set(data.images ?? [])].slice(0, 1000).map(image => `<image:image><image:loc>${escapeXML(absoluteURL(image))}</image:loc></image:image>`).join("") : "";
    return `<${item}><loc>${escapeXML(absoluteURL(data.path))}</loc>${modified}${images}</${item}>`;
  }).join("")}</${root}>`;
}
export function sitemapResponse(body: string): Response {
  return new Response(body, { headers: { "content-type": "application/xml; charset=utf-8", "cache-control": "no-store", "x-robots-tag": "noindex" } });
}
export function sitemapUnavailable(): Response {
  // A temporary outage must never look like a successfully emptied sitemap.
  return new Response("Sitemap temporarily unavailable", { status: 503, headers: { "retry-after": "60", "cache-control": "no-store" } });
}
