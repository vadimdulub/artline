import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { GET, POST, PUT } from "../../app/api/museum-studio/[[...path]]/route";
const upstream = vi.fn();
beforeEach(() => { vi.stubEnv("API_INTERNAL_URL", "https://api.example"); vi.stubGlobal("fetch", upstream); upstream.mockReset(); });
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });
it("forwards only session and origin evidence, and preserves a denied museum claim", async () => {
  upstream.mockResolvedValue(Response.json({ error: { code: "MUSEUM_ACCESS" } }, { status: 403 }));
  const token = "a".repeat(43);
  const response = await POST(new NextRequest("https://artlines.org/api/museum-studio/the-met/claim", { method: "POST", headers: { origin: "https://artlines.org", "sec-fetch-site": "same-origin", cookie: `__Host-artline_session=${token}; editor=secret`, "x-museum-id": "forged", authorization: "Bearer forged" } }), { params: Promise.resolve({ path: ["the-met", "claim"] }) });
  const [url, init] = upstream.mock.calls[0];
  expect(url.href).toBe("https://api.example/api/v1/member/museum-studio/the-met/claim");
  expect([...init.headers]).toEqual([["cookie", `__Host-artline_session=${token}`], ["origin", "https://artlines.org"], ["sec-fetch-site", "same-origin"]]);
  expect(response.status).toBe(403);
  expect(response.headers.get("cache-control")).toBe("private, no-store");
});
it.each([["the-met", "domains"], ["the-met", "content", "not-a-uuid"], ["the-met", "claim", "extra"]])("rejects unsupported studio paths %s", async (...path) => {
  expect((await GET(new NextRequest("https://artlines.org/api/museum-studio"), { params: Promise.resolve({ path }) })).status).toBe(404);
  expect(upstream).not.toHaveBeenCalled();
});
it("bounds museum document payloads before forwarding", async () => {
  const response = await PUT(new NextRequest("https://artlines.org/api/museum-studio/the-met/content/11111111-1111-4111-8111-111111111111", { method: "PUT", body: "x".repeat(262145) }), { params: Promise.resolve({ path: ["the-met", "content", "11111111-1111-4111-8111-111111111111"] }) });
  expect(response.status).toBe(413); expect(upstream).not.toHaveBeenCalled();
});
it("accepts bounded binary uploads and forwards their media type", async () => {
  upstream.mockResolvedValue(Response.json({ id: "upload-id" }));
  const bytes = new Uint8Array(300000).fill(12);
  const response = await POST(new NextRequest("https://artlines.org/api/museum-studio/the-met/images", { method: "POST", body: bytes, headers: { origin: "https://artlines.org", "content-type": "image/png" } }), { params: Promise.resolve({ path: ["the-met", "images"] }) });
  expect(response.status).toBe(200);
  const [url, init] = upstream.mock.calls[0];
  expect(url.pathname).toBe("/api/v1/member/museum-studio/the-met/images");
  expect(init.headers.get("content-type")).toBe("image/png");
  expect(init.body).toEqual(bytes);
});
it("rejects oversized images before forwarding", async () => {
  const response = await POST(new NextRequest("https://artlines.org/api/museum-studio/the-met/images", { method: "POST", body: new Uint8Array(10 * 1024 * 1024 + 1) }), { params: Promise.resolve({ path: ["the-met", "images"] }) });
  expect(response.status).toBe(413); expect(upstream).not.toHaveBeenCalled();
});
it("routes artwork searches and resolution to the museum-scoped API", async () => {
  upstream.mockImplementation(() => Promise.resolve(Response.json({ items: [] })));
  await GET(new NextRequest("https://artlines.org/api/museum-studio/the-met/artworks?scope=collection&q=Monet&images=1"), { params: Promise.resolve({ path: ["the-met", "artworks"] }) });
  expect(upstream.mock.calls[0][0].search).toBe("?scope=collection&q=Monet&images=1");
  await POST(new NextRequest("https://artlines.org/api/museum-studio/the-met/artworks/resolve", { method: "POST", body: "[]" }), { params: Promise.resolve({ path: ["the-met", "artworks", "resolve"] }) });
  expect(upstream.mock.calls[1][0].pathname).toBe("/api/v1/member/museum-studio/the-met/artworks/resolve");
});
