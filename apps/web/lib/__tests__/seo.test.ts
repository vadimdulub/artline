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
