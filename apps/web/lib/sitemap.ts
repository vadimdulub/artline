import { absoluteURL } from "./seo";

export const publicPages = ["/about", "/artists", "/art-history-timeline"];
export const explorerPages = ["/", "/museums", "/books", "/events", "/all"];
export function escapeXML(value: string): string { return value.replace(/[<>&"']/g, character => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;", "'": "&apos;" })[character]!); }
export function sitemapXML(paths: string[], index = false): string {
  const root = index ? "sitemapindex" : "urlset", item = index ? "sitemap" : "url";
  return `<?xml version="1.0" encoding="UTF-8"?><${root} xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${paths.map(path => `<${item}><loc>${escapeXML(absoluteURL(path))}</loc></${item}>`).join("")}</${root}>`;
}
export function sitemapResponse(body: string): Response {
  return new Response(body, { headers: { "content-type": "application/xml; charset=utf-8", "cache-control": "no-store", "x-robots-tag": "noindex" } });
}
export function sitemapUnavailable(): Response {
  // A temporary outage must never look like a successfully emptied sitemap.
  return new Response("Sitemap temporarily unavailable", { status: 503, headers: { "retry-after": "60", "cache-control": "no-store" } });
}
