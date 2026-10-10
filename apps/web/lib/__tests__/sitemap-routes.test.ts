import { afterEach, beforeEach, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
vi.mock("../seo-api", () => ({ discoveryRequest: vi.fn() }));
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
  expect(guidesMetadata().alternates).toMatchObject({ canonical: "https://artline.example/guides" });
  expect(guidesMetadata().robots).toMatchObject({ index: true });
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
it("validates ranges before contacting the API", async () => {
  expect((await request("sitemap-artworks-INVALID.xml")).status).toBe(404);
  expect(discoveryRequest).not.toHaveBeenCalled();
});
