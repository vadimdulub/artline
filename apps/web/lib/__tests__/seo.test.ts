import { afterEach, describe, expect, it, vi } from "vitest";
import { artworkStructuredData, explorerMetadata, pageMetadata, serializeJSONLD, shareImage, siteURL } from "../seo";
import { sitemapXML } from "../sitemap";
import type { ArtistDetail, Artwork } from "../types";

afterEach(() => vi.unstubAllEnvs());

describe("search metadata", () => {
  it("uses the configured canonical origin and rejects URL contamination", () => {
    vi.stubEnv("ARTLINE_SITE_URL", "https://artline.example");
    const metadata = pageMetadata("An artwork", "A description", "/artists/a/works/1");
    expect(metadata.alternates?.canonical).toBe("https://artline.example/artists/a/works/1");
    expect(metadata.openGraph).toMatchObject({ url: "https://artline.example/artists/a/works/1" });
    for (const bad of ["https://artline.example/path", "https://name:password@artline.example", "javascript:alert(1)", "https://artline.example?preview=1"]) {
      vi.stubEnv("ARTLINE_SITE_URL", bad);
      expect(siteURL).toThrow();
    }
  });

  it("keeps research previews out of search while leaving approved release pages indexable", () => {
    vi.stubEnv("ARTLINE_PUBLIC_RESEARCH_PREVIEW", "true");
    expect(explorerMetadata("Atlas", "Description", "/").robots).toMatchObject({ index: false, follow: true });
    vi.stubEnv("ARTLINE_PUBLIC_RESEARCH_PREVIEW", "false");
    vi.stubEnv("ARTLINE_RESEARCH_PREVIEW_TOKEN", "");
    expect(explorerMetadata("Atlas", "Description", "/").robots).toMatchObject({ index: true });
  });

  it("provides a brand sharing image without overriding a permitted artwork image", () => {
    vi.stubEnv("ARTLINE_SITE_URL", "https://artline.example");
    expect(pageMetadata("Guide", "Description", "/art-history-timeline").openGraph).toMatchObject({
      images: [{ url: "https://artline.example/share-image", width: 1200, height: 630 }],
    });
    expect(pageMetadata("Work", "Description", "/artists/a/works/1", { image: "/assets/artworks/work.jpg" }).openGraph).toMatchObject({
      images: [{ url: "https://artline.example/assets/artworks/work.jpg" }],
    });
  });

  it("describes image permissions only from recorded evidence", () => {
    vi.stubEnv("ARTLINE_SITE_URL", "https://artline.example");
    const artist = { slug: "artist", display_name: "An Artist", entity_type: "person" } as ArtistDetail;
    const work = { id: "work", title: "A painting", date_display: "Date unknown", attribution_role: "primary", media_url: "/assets/artworks/work.jpg", rights_status: "cc_by", license_url: "https://creativecommons.org/licenses/by/4.0/", attribution_text: "Photograph: Example Museum", alt_text: "A landscape with a river" } as Artwork;
    const image = artworkStructuredData(work, artist).image;
    expect(image).toMatchObject({ "@type": "ImageObject", contentUrl: "https://artline.example/assets/artworks/work.jpg", license: work.license_url, creditText: work.attribution_text, caption: work.alt_text });
    expect(image).not.toHaveProperty("creator");
    expect(image).not.toHaveProperty("copyrightNotice");
    expect(image).not.toHaveProperty("acquireLicensePage");
    const unknown = artworkStructuredData({ ...work, license_url: "javascript:alert(1)", attribution_text: null }, artist).image;
    expect(unknown?.license).toBeUndefined();
    expect(unknown?.creditText).toBeUndefined();
    expect(artworkStructuredData({ ...work, rights_status: "restricted" }, artist).image).toBeUndefined();
  });

  it("escapes script-breaking content without changing the structured value", () => {
    const data = { name: '</script><script>alert("x")</script>' };
    const serialized = serializeJSONLD(data);
    expect(serialized).not.toContain("<");
    expect(JSON.parse(serialized)).toEqual(data);
  });

  it("does not turn uncertain dates, attributions or holdings into unsupported claims", () => {
    const artist = { slug: "some-artist", display_name: "Some Artist", entity_type: "person" } as ArtistDetail;
    const work = { id: "work", title: "An icon", date_display: "circa 1600–1650", date_precision: "circa_range", attribution_role: "attributed_to", media_url: "/assets/artworks/icon.jpg", rights_status: "restricted" } as Artwork;
    const data = artworkStructuredData(work, artist);
    expect(data.creator).toBeUndefined();
    expect(data).not.toHaveProperty("dateCreated");
    expect(data).not.toHaveProperty("location");
    expect(data.image).toBeUndefined();
    expect(shareImage({ ...work, rights_status: "public_domain" })).toBe(work.media_url);
    expect(artworkStructuredData({ ...work, attribution_role: "primary" }, artist).creator?.name).toBe(artist.display_name);
  });

  it("XML-escapes query URLs and does not manufacture modification dates", () => {
    vi.stubEnv("ARTLINE_SITE_URL", "https://artline.example");
    const xml = sitemapXML(["/artists?after=a&next=b"]);
    expect(xml).toContain("https://artline.example/artists?after=a&amp;next=b");
    expect(xml).not.toContain("lastmod");
    expect(sitemapXML(["/sitemap-pages.xml"], true)).toContain("<sitemapindex");
  });
});
