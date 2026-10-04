import { discoveryRequest, type SEOEntry } from "@/lib/seo-api";
import { researchPreviewEnabled } from "@/lib/research-preview";
import { explorerPages, publicPages, sitemapResponse, sitemapUnavailable, sitemapXML } from "@/lib/sitemap";

export const dynamic = "force-dynamic";
export async function GET(_request: Request, { params }: { params: Promise<{ sitemapFile: string }> }) {
  const { sitemapFile } = await params;
  if (sitemapFile === "sitemap-pages.xml") return sitemapResponse(sitemapXML([...publicPages, ...(researchPreviewEnabled() ? [] : explorerPages)]));
  const match = /^sitemap-(artists|artworks|museums)-([0-9a-f]{3})\.xml$/.exec(sitemapFile);
  if (!match || (researchPreviewEnabled() && match[1] === "museums")) return new Response("Not found", { status: 404 });
  try {
    const page = await discoveryRequest<{ items: SEOEntry[] }>(`sitemaps/${match[1]}/${match[2]}`);
    return sitemapResponse(sitemapXML(page.items.map(item => item.path)));
  } catch { return sitemapUnavailable(); }
}
