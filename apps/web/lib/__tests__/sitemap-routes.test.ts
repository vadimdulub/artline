import { afterEach, beforeEach, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
vi.mock("../seo-api", () => ({ discoveryRequest: vi.fn() }));
import { getGuideIndex } from "../museum-guides";
import { discoveryRequest } from "../seo-api";
import { GET as index } from "../../app/sitemap.xml/route";
import { GET as shard } from "../../app/[sitemapFile]/route";
import { generateMetadata as guideMetadata } from "../../app/art-history-timeline/page";
import { generateMetadata as guidesMetadata } from "../../app/guides/page";

beforeEach(() => {
  vi.stubEnv("ARTLINE_SITE_URL", "https://artline.example");
  vi.stubEnv("ARTLINE_PUBLIC_RESEARCH_PREVIEW", "false");
  vi.stubEnv("ARTLINE_RESEARCH_PREVIEW_TOKEN", "");
});
afterEach(() => { vi.unstubAllEnvs(); vi.resetAllMocks(); });
const request = (file: string) => shard(new Request(`https://artline.example/${file}`), { params: Promise.resolve({ sitemapFile: file }) });

it("links bounded public sitemaps from the root index", async () => {
  vi.mocked(discoveryRequest).mockResolvedValue({ items: ["artists-abc", "artworks-def"] });
  const response = await index();
  expect(response.status).toBe(200);
  expect(await response.text()).toContain("https://artline.example/sitemap-artworks-def.xml");
});
it("advertises public pages and artworks while omitting member pages", async () => {
  vi.stubEnv("ARTLINE_PUBLIC_RESEARCH_PREVIEW", "true");
  vi.mocked(discoveryRequest).mockResolvedValueOnce({ items: ["artists-abc", "artworks-def", "museums-123"] });
  const root = await (await index()).text();
  expect(root).toContain("sitemap-artists-abc.xml");
  expect(root).toContain("sitemap-artworks-def.xml");
  expect(root).not.toContain("sitemap-museums");
  const pages = await (await request("sitemap-pages.xml")).text();
  expect(pages).toContain("<loc>https://artline.example/</loc>");
  expect(pages).toContain("<loc>https://artline.example/art-history-timeline</loc>");
  expect(pages).toContain("<loc>https://artline.example/guides</loc>");
  expect(guideMetadata().robots).toMatchObject({ index: true });
  expect((await guidesMetadata({ searchParams: Promise.resolve({}) })).alternates).toMatchObject({ canonical: "https://artline.example/guides" });
  expect((await guidesMetadata({ searchParams: Promise.resolve({}) })).robots).toMatchObject({ index: true });
  expect(pages).not.toContain("/museums");
  vi.mocked(discoveryRequest).mockResolvedValueOnce({ items: [{ path: "/artists/giotto", name: "Giotto" }] });
  expect(await (await request("sitemap-artists-abc.xml")).text()).toContain("/artists/giotto");
  expect((await request("sitemap-museums-123.xml")).status).toBe(404);
});
it("reports outages as retryable failures rather than empty successful sitemaps", async () => {
  vi.mocked(discoveryRequest).mockRejectedValue(new Error("offline"));
  for (const response of [await index(), await request("sitemap-artworks-abc.xml")]) {
    expect(response.status).toBe(503);
    expect(response.headers.get("retry-after")).toBe("60");
    expect(response.headers.get("cache-control")).toBe("no-store");
  }
});
it("keeps all public artist and museum guide editions and their selected images discoverable without the catalogue API", async () => {
  const response = await request("sitemap-pages.xml");
  const xml = new DOMParser().parseFromString(await response.text(), "application/xml");
  expect(xml.querySelector("parsererror")).toBeNull();
  const urls = [...xml.getElementsByTagName("url")];
  const guides = urls.filter(url => url.getElementsByTagName("loc")[0].textContent?.includes("/guides/"));
  expect(guides).toHaveLength(getGuideIndex().reduce((n, guide) => n + guide.locales.length, 0) + 10);
  for (const slug of ["artemisia-gentileschi", "mary-cassatt", "frida-kahlo"]) {
    expect(guides.some(guide => guide.getElementsByTagName("loc")[0].textContent === `https://artline.example/guides/${slug}/ru`)).toBe(true);
  }
  for (const guide of guides) {
    expect(guide.getElementsByTagName("lastmod")[0].textContent).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(guide.getElementsByTagNameNS("http://www.google.com/schemas/sitemap-image/1.1", "image").length).toBeGreaterThanOrEqual(guide.getElementsByTagName("loc")[0].textContent?.includes("islamic-patterns") ? 6 : 20);
  }
  expect(discoveryRequest).not.toHaveBeenCalled();
});
it("validates ranges before contacting the API", async () => {
  expect((await request("sitemap-artworks-INVALID.xml")).status).toBe(404);
  expect(discoveryRequest).not.toHaveBeenCalled();
});

it("keeps filtered guide searches out of indexing with the directory canonical", async () => {
  const metadata = await guidesMetadata({ searchParams: Promise.resolve({ q: "Louvre" }) });
  expect(metadata.robots).toMatchObject({ index: false, follow: true });
  expect(metadata.alternates).toMatchObject({ canonical: "https://artline.example/guides" });
});
