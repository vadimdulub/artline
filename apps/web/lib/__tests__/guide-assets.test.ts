import { afterEach, expect, it, vi } from "vitest";
import { GET, HEAD } from "@/app/assets/[...path]/route";
afterEach(()=>{vi.unstubAllGlobals();vi.unstubAllEnvs();});
it("serves credited guide images from the existing image bucket",async()=>{
 vi.stubEnv("ARTLINE_IMAGES_BUCKET","guide-test-bucket");
 const fetch=vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({access_token:"test-token",expires_in:3600}))).mockResolvedValueOnce(new Response("image",{headers:{"content-type":"image/webp","etag":"abc"}}));vi.stubGlobal("fetch",fetch);
 const response=await GET(new Request("https://artlines.org/assets/guides/islamic-patterns/mihrab-640.webp"),{params:Promise.resolve({path:["guides","islamic-patterns","mihrab-640.webp"]})});
 expect(response.status).toBe(200);expect(await response.text()).toBe("image");expect(fetch.mock.calls[1][0]).toContain("assets%2Fguides%2Fislamic-patterns%2Fmihrab-640.webp");expect(response.headers.get("cache-control")).toContain("public");
});
it("rejects other namespaces, traversal and non-images before fetching",async()=>{
 vi.stubEnv("ARTLINE_IMAGES_BUCKET","guide-test-bucket");const fetch=vi.fn();vi.stubGlobal("fetch",fetch);
 for(const path of [["private","secret.webp"],["guides","..","image.webp"],["guides","islamic-patterns","index.html"],["guides","bad/path.webp"]]) {
  expect((await HEAD(new Request("https://artlines.org/assets/x",{method:"HEAD"}),{params:Promise.resolve({path})})).status).toBe(404);
 }
 expect(fetch).not.toHaveBeenCalled();
});

it("keeps fingerprinted reproductions immutable while bounding legacy image caching", async () => {
 vi.stubEnv("ARTLINE_IMAGES_BUCKET", "artwork-test-bucket");
 vi.stubGlobal("fetch", vi.fn(async (url: string) => url.startsWith("http://metadata.")
  ? new Response(JSON.stringify({ access_token: "test-token", expires_in: 3600 }))
  : new Response("image", { headers: { "content-type": "image/jpeg" } })));
 for (const [filename, immutable] of [["painting-82fe72a1ba637b04.jpg", true], ["223afa6b-b800-5e94-ad65-42a8365d9567.jpg", false]] as const) {
  const response = await GET(new Request(`https://artlines.org/assets/artworks/${filename}`), { params: Promise.resolve({ path: ["artworks", filename] }) });
  expect(response.status).toBe(200);
  expect(response.headers.get("cache-control")).toBe(immutable ? "public, max-age=31536000, immutable" : "public, max-age=86400");
 }
});
