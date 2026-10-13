import { safeSourceURL } from "./api";
import { absoluteURL } from "./seo";
import { guidePath, type MuseumGuide } from "./museum-guide-types";
import type { SitemapEntry } from "./sitemap";

// Use the guide's recorded editorial date, never the request or build time.
function editorialDate(value: string): string | undefined {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return undefined;
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value ? value : undefined;
}

export function museumGuideSitemapEntry(guide: MuseumGuide): SitemapEntry {
  return {
    path: guidePath(guide.slug, guide.locale),
    lastModified: editorialDate(guide.updated),
    // These are the approved reproductions already displayed in this edition.
    images: [...new Set(guide.works.map(work => work.image).filter(Boolean))],
  };
}

export function museumGuideStructuredData(guide: MuseumGuide) {
  const url = absoluteURL(guidePath(guide.slug, guide.locale));
  return {
    "@context": "https://schema.org",
    "@type": "Article",
    "@id": `${url}#article`,
    url,
    mainEntityOfPage: { "@type": "WebPage", "@id": url },
    headline: guide.title,
    description: guide.subtitle,
    inLanguage: guide.locale,
    dateModified: editorialDate(guide.updated),
    isAccessibleForFree: true,
    publisher: { "@type": "Organization", name: "Artline", url: absoluteURL("/") },
    image: guide.works.filter(work => work.image).slice(0, 3).map(work => ({
      "@type": "ImageObject",
      contentUrl: absoluteURL(work.image),
      caption: `${work.title} — ${work.artist}`,
      creditText: work.credit || undefined,
      license: safeSourceURL(work.licenseUrl),
    })),
    // No invented publication date, named author, museum endorsement or display status.
  };
}
