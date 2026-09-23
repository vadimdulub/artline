import { afterEach, beforeEach, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
vi.mock("../seo-api", () => ({ discoveryRequest: vi.fn() }));
import { discoveryRequest } from "../seo-api";
import { GET as index } from "../../app/sitemap.xml/route";
import { GET as shard } from "../../app/[sitemapFile]/route";

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
it("does not expose review-profile sitemaps in preview mode", async () => {
  vi.stubEnv("ARTLINE_PUBLIC_RESEARCH_PREVIEW", "true");
  expect(await (await index()).text()).not.toContain("sitemap-artworks");
  expect(await (await request("sitemap-pages.xml")).text()).not.toContain("<loc>https://artline.example/</loc>");
  expect((await request("sitemap-artists-abc.xml")).status).toBe(404);
  expect(discoveryRequest).not.toHaveBeenCalled();
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
