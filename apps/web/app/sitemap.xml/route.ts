import { discoveryRequest } from "@/lib/seo-api";
import { researchPreviewEnabled } from "@/lib/research-preview";
import { sitemapResponse, sitemapUnavailable, sitemapXML } from "@/lib/sitemap";

export const dynamic = "force-dynamic";
export async function GET() {
  try {
    const shards = (await discoveryRequest<{ items: string[] }>("sitemaps")).items.filter(shard => !researchPreviewEnabled() || !shard.startsWith("museums-"));
    return sitemapResponse(sitemapXML(["/sitemap-pages.xml", ...shards.map(shard => `/sitemap-${shard}.xml`)], true));
  } catch { return sitemapUnavailable(); }
}
