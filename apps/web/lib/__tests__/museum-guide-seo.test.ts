import { afterEach, expect, it, vi } from "vitest";
import { museumGuideSitemapEntry, museumGuideStructuredData } from "../museum-guide-seo";
import { getMuseumGuide } from "../museum-guides";
import { sitemapXML } from "../sitemap";

afterEach(() => vi.unstubAllEnvs());

it("describes the exact public language edition without inventing authorship or publication", () => {
  vi.stubEnv("ARTLINE_SITE_URL", "https://artline.example");
  const guide = getMuseumGuide("prado", "es")!;
  const article = museumGuideStructuredData(guide);
  expect(article).toMatchObject({
    "@type": "Article", url: "https://artline.example/guides/prado/es",
    headline: guide.title, inLanguage: "es", isAccessibleForFree: true,
    dateModified: guide.updated, mainEntityOfPage: { "@id": "https://artline.example/guides/prado/es" },
    publisher: { name: "Artline" },
  });
  expect(article).not.toHaveProperty("author");
  expect(article).not.toHaveProperty("datePublished");
  expect(article).not.toHaveProperty("location");
  expect(article.image[0]).toMatchObject({ contentUrl: guide.works[0].image, creditText: guide.works[0].credit });
});

it("omits unknown or invalid editorial dates and unsupported license links", () => {
  const guide = getMuseumGuide("louvre")!;
  for (const updated of ["unknown", "2026-02-30", "2026-13-11", "11 October 2026"]) {
    expect(museumGuideStructuredData({ ...guide, updated }).dateModified).toBeUndefined();
    expect(museumGuideSitemapEntry({ ...guide, updated }).lastModified).toBeUndefined();
  }
  const work = { ...guide.works[0], credit: "", licenseUrl: "javascript:alert(1)" };
  const image = museumGuideStructuredData({ ...guide, works: [work] }).image[0];
  expect(image.creditText).toBeUndefined();
  expect(image.license).toBeUndefined();
  expect(image).not.toHaveProperty("creator");
});

it("emits valid image sitemap XML while preserving ordinary pages and escaping URL data", () => {
  vi.stubEnv("ARTLINE_SITE_URL", "https://artline.example");
  const image = '/assets/a.jpg?caption="art"&detail=1';
  const xml = sitemapXML(["/about", { path: "/guides/example", lastModified: "2026-10-10", images: [image, image] }]);
  const doc = new DOMParser().parseFromString(xml, "application/xml");
  expect(doc.querySelector("parsererror")).toBeNull();
  expect(doc.getElementsByTagName("url").length).toBe(2);
  expect(doc.getElementsByTagName("lastmod").length).toBe(1);
  const images = doc.getElementsByTagNameNS("http://www.google.com/schemas/sitemap-image/1.1", "loc");
  expect(images.length).toBe(1);
  expect(images[0].textContent).toBe(new URL(image, "https://artline.example").href);
  expect(sitemapXML(["/sitemap-pages.xml"], true)).not.toContain("xmlns:image");
});

it("includes only images actually selected in the guide and keeps the image sitemap bound", () => {
  const guide = getMuseumGuide("louvre")!;
  const entry = museumGuideSitemapEntry(guide);
  expect(entry.images).toEqual([...new Set(guide.works.map(work => work.image))]);
  const xml = sitemapXML([{ path: "/guide", images: Array.from({ length: 1001 }, (_, i) => `/assets/${i}.jpg`) }]);
  const doc = new DOMParser().parseFromString(xml, "application/xml");
  expect(doc.getElementsByTagNameNS("http://www.google.com/schemas/sitemap-image/1.1", "image").length).toBe(1000);
});
