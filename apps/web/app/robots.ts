import type { MetadataRoute } from "next";
import { absoluteURL } from "@/lib/seo";

export const dynamic = "force-dynamic";

export default function robots(): MetadataRoute.Robots {
  return {
    // Search and AI crawlers use the same public HTML. Leave pages crawlable so
    // crawlers can read noindex on account and internal pages.
    rules: { userAgent: "*", allow: "/" },
    sitemap: absoluteURL("/sitemap.xml"),
  };
}
