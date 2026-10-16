import { discoveryRequest, type SEOEntry } from "@/lib/seo-api";
import { explorerPages, publicPages, sitemapResponse, sitemapUnavailable, sitemapXML } from "@/lib/sitemap";
import { getGuideIndex, getMuseumGuide } from "@/lib/museum-guides";
import { museumGuideSitemapEntry } from "@/lib/museum-guide-seo";

export const dynamic = "force-dynamic";
export async function GET(_request: Request, { params }: { params: Promise<{ sitemapFile: string }> }) {
  const { sitemapFile } = await params;
  if (sitemapFile === "sitemap-pages.xml") {
    const guides = getGuideIndex().flatMap(guide => guide.locales.map(locale => {
      const edition = getMuseumGuide(guide.slug, locale);
      if (!edition) throw new Error("Indexed museum guide edition is missing");
      return museumGuideSitemapEntry(edition);
    }));
    return sitemapResponse(sitemapXML([...publicPages, ...explorerPages, ...guides]));
  }
  const match = /^sitemap-(artists|artworks)-([0-9a-f]{3})\.xml$/.exec(sitemapFile);
  if (!match) return new Response("Not found", { status: 404 });
  try {
    const page = await discoveryRequest<{ items: SEOEntry[] }>(`sitemaps/${match[1]}/${match[2]}`);
    return sitemapResponse(sitemapXML(page.items.map(item => item.path)));
  } catch { return sitemapUnavailable(); }
}
