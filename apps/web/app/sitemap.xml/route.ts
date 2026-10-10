import { discoveryRequest } from "@/lib/seo-api";
import { sitemapResponse, sitemapUnavailable, sitemapXML } from "@/lib/sitemap";

export const dynamic = "force-dynamic";
export async function GET() {
  try {
    const shards = (await discoveryRequest<{ items: string[] }>("sitemaps")).items;
    return sitemapResponse(sitemapXML(["/sitemap-pages.xml", ...shards.filter(shard => /^(artists|artworks)-[0-9a-f]{3}$/.test(shard)).map(shard => `/sitemap-${shard}.xml`)], true));
  } catch { return sitemapUnavailable(); }
}
