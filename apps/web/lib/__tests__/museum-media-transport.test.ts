import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { GET } from "../../app/api/museum-media/[slug]/[id]/route";
const upstream = vi.fn(), id = "11111111-1111-4111-8111-111111111111";
const context = { params: Promise.resolve({ slug: "the-met", id }) };
beforeEach(() => { vi.stubEnv("API_INTERNAL_URL", "https://api.example"); vi.stubGlobal("fetch", upstream); upstream.mockReset(); });
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });
it("forwards only the authenticated session and preserves private image denial", async () => {
  const token = "a".repeat(43);
  upstream.mockResolvedValue(Response.json({ error: "private" }, { status: 403 }));
  const response = await GET(new NextRequest(`https://artlines.org/api/museum-media/the-met/${id}`, { headers: { cookie: `__Host-artline_session=${token}; unrelated=secret`, authorization: "Bearer forged" } }), context);
  expect(response.status).toBe(403);
  expect(await response.text()).toBe("");
  expect([...upstream.mock.calls[0][1].headers]).toEqual([["cookie", `__Host-artline_session=${token}`]]);
  expect(response.headers.get("cache-control")).toBe("private, no-store");
});
it("streams permitted image bytes without caching", async () => {
  upstream.mockResolvedValue(new Response(new Uint8Array([1, 2, 3]), { headers: { "content-type": "image/png" } }));
  const response = await GET(new NextRequest(`https://artlines.org/api/museum-media/the-met/${id}`), context);
  expect(response.status).toBe(200); expect(response.headers.get("content-type")).toBe("image/png");
  expect(response.headers.get("x-content-type-options")).toBe("nosniff");
  expect(new Uint8Array(await response.arrayBuffer())).toEqual(new Uint8Array([1, 2, 3]));
});
it("rejects unexpected active content and malformed identifiers", async () => {
  upstream.mockResolvedValue(new Response("<script>bad</script>", { headers: { "content-type": "text/html" } }));
  expect((await GET(new NextRequest(`https://artlines.org/api/museum-media/the-met/${id}`), context)).status).toBe(502);
  upstream.mockClear();
  expect((await GET(new NextRequest("https://artlines.org/api/museum-media"), { params: Promise.resolve({ slug: "../private", id }) })).status).toBe(404);
  expect(upstream).not.toHaveBeenCalled();
});
