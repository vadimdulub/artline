import type { Metadata } from "next";
import { safeSourceURL } from "./api";
import { researchPreviewEnabled } from "./research-preview";
import type { ArtistDetail, Artwork } from "./types";

export const siteName = "Artline";
export const siteDescription = "Explore painters, artworks, museums, books and historical events in a shared timeline. Follow the people, places and ideas that connect them.";

// Runtime configuration: never derive canonical URLs from an untrusted Host header.
export function siteURL(): URL {
  const value = process.env.ARTLINE_SITE_URL || "https://artlines.org";
  const url = new URL(value);
  if (!["https:", "http:"].includes(url.protocol) || url.username || url.password || url.pathname !== "/" || url.search || url.hash) {
    throw new Error("ARTLINE_SITE_URL must be an HTTP(S) origin without a path, credentials, query or fragment.");
  }
  return url;
}

export function absoluteURL(path: string): string { return new URL(path, siteURL()).href; }
export const noIndex: Metadata["robots"] = { index: false, follow: true };
export const allowIndex: Metadata["robots"] = { index: true, follow: true, googleBot: { index: true, follow: true, "max-image-preview": "large", "max-snippet": -1, "max-video-preview": -1 } };

export function pageMetadata(title: string, description: string, path: string, options: { index?: boolean; image?: string | null } = {}): Metadata {
  const image = options.image
    ? [{ url: absoluteURL(options.image), alt: title }]
    : [{ url: absoluteURL("/share-image"), alt: "Artline — Art, literature and history in context", width: 1200, height: 630, type: "image/png" }];
  return {
    title, description,
    alternates: { canonical: absoluteURL(path) },
    robots: options.index === false ? noIndex : allowIndex,
    openGraph: { type: "website", locale: "en_US", siteName, title: `${title} — ${siteName}`, description, url: absoluteURL(path), images: image },
    twitter: { card: "summary_large_image", title: `${title} — ${siteName}`, description, images: image },
  };
}

export function explorerMetadata(title: string, description: string, path: string): Metadata {
  return pageMetadata(title, description, path, { index: !researchPreviewEnabled() });
}

export function plainDescription(text: string | null | undefined, fallback: string): string {
  const plain = (text || fallback).replace(/!?\[([^\]]*)\]\([^)]*\)/g, "$1").replace(/<[^>]*>/g, " ").replace(/[#*_`~]/g, "").replace(/\s+/g, " ").trim();
  return plain.length > 160 ? `${plain.slice(0, 157).replace(/\s+\S*$/, "")}…` : plain;
}

export function artistDescription(artist: ArtistDetail): string {
  return plainDescription(artist.biography_md, `Explore ${artist.display_name}: ${artist.timeline_display}. Discover artworks, sources and connections in Artline’s art history atlas.`);
}

export function artworkDescription(work: Artwork, artist: ArtistDetail): string {
  const attribution = work.attribution_role === "primary" ? `by ${artist.display_name}` : `${work.attribution_role.replaceAll("_", " ")} ${artist.display_name}`;
  return plainDescription(work.description_md, `${work.title}, ${attribution}. ${work.date_display}. ${work.medium_text ? `${work.medium_text}. ` : ""}Explore the artwork’s recorded details and sources.`);
}

// Only promote images with an explicit public-domain/open license label. The
// ordinary catalogue viewer retains its existing independent media behavior.
export function shareImage(work: Artwork): string | undefined {
  const path = work.media_url;
  return path && /^\/assets\/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$/.test(path) && ["public_domain", "cc0", "cc_by", "cc_by_sa"].includes(work.rights_status ?? "") ? path : undefined;
}

export function serializeJSONLD(data: unknown): string { return JSON.stringify(data).replace(/</g, "\\u003c"); }

export function breadcrumbs(items: { name: string; path: string }[]) {
  return { "@context": "https://schema.org", "@type": "BreadcrumbList", itemListElement: items.map((item, index) => ({ "@type": "ListItem", position: index + 1, name: item.name, item: absoluteURL(item.path) })) };
}

export function artworkStructuredData(work: Artwork, artist: ArtistDetail) {
  const url = absoluteURL(`/artists/${artist.slug}/works/${work.id}`);
  const image = shareImage(work);
  return {
    "@context": "https://schema.org", "@type": "VisualArtwork", "@id": url, url, name: work.title,
    alternateName: work.alternate_title || undefined, description: artworkDescription(work, artist),
    // A workshop/held attribution must never become an assertion of authorship.
    creator: work.attribution_role === "primary" ? { "@type": artist.entity_type === "person" ? "Person" : "Thing", name: artist.display_name, url: absoluteURL(`/artists/${artist.slug}`) } : undefined,
    artMedium: work.medium_text || undefined,
    // Source date labels remain text on the page; uncertain dates are not ISO dates.
    image: image ? {
      "@type": "ImageObject", contentUrl: absoluteURL(image),
      name: work.title,
      caption: work.alt_text || work.title,
      license: safeSourceURL(work.license_url),
      creditText: work.attribution_text || undefined,
      // Artwork authorship does not establish the photographer or rights owner.
      // Preserve missing image credits and license URLs rather than inventing them.
    } : undefined,
  };
}
