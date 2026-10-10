import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { GET, PUT, DELETE } from "../../app/api/bookmarks/[[...path]]/route";
const upstream = vi.fn();
const context = (path?: string[]) => ({ params: Promise.resolve({ path }) });
beforeEach(() => { vi.stubGlobal("fetch", upstream); vi.stubEnv("API_INTERNAL_URL", "https://api.example"); upstream.mockReset(); });
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });
it("forwards the member cookie and CSRF evidence for idempotent writes", async () => {
  upstream.mockResolvedValue(Response.json({ saved: true }));
  const id = "11111111-1111-4111-8111-111111111111", token = "a".repeat(43);
  const response = await PUT(new NextRequest(`https://artlines.org/api/bookmarks/artwork/${id}`, { method: "PUT", headers: { cookie: `__Host-artline_session=${token}; editor=ignored`, origin: "https://artlines.org", "sec-fetch-site": "same-origin", authorization: "Bearer ignored" } }), context(["artwork", id]));
  const [url, options] = upstream.mock.calls[0];
  expect(url.href).toBe(`https://api.example/api/v1/member/bookmarks/artwork/${id}`);
  expect(options.method).toBe("PUT"); expect(options.cache).toBe("no-store"); expect(options.redirect).toBe("error");
  expect([...options.headers]).toEqual([["cookie", `__Host-artline_session=${token}`], ["origin", "https://artlines.org"], ["sec-fetch-site", "same-origin"]]);
  expect(response.headers.get("cache-control")).toBe("private, no-store");
});
it("does not turn a read into a save or forward unknown paths", async () => {
  const id = "11111111-1111-4111-8111-111111111111";
  expect((await GET(new NextRequest(`https://artlines.org/api/bookmarks/artist/${id}`), context(["artist", id]))).status).toBe(405);
  expect((await DELETE(new NextRequest("https://artlines.org/api/bookmarks", { method: "DELETE" }), context())).status).toBe(405);
  expect((await GET(new NextRequest("https://artlines.org/api/bookmarks/../auth"), context(["..", "auth"]))).status).toBe(404);
  expect(upstream).not.toHaveBeenCalled();
});
it("preserves unauthenticated responses instead of caching a successful empty list", async () => {
  upstream.mockResolvedValue(Response.json({ error: { code: "AUTH_REQUIRED" } }, { status: 401 }));
  const response = await GET(new NextRequest("https://artlines.org/api/bookmarks?kind=artist"), context());
  expect(response.status).toBe(401);
  expect(upstream.mock.calls[0][0].search).toBe("?kind=artist");
  expect(response.headers.get("x-robots-tag")).toBe("noindex");
});

it.each(["book", "event"])("proxies %s saves with bounded catalogue identifiers", async kind => {
  upstream.mockResolvedValue(Response.json({ saved: true }));
  const request = new NextRequest(`https://artlines.org/api/bookmarks/${kind}/record-q123`, { method: "PUT" });
  expect((await PUT(request, context([kind, "record-q123"]))).status).toBe(200);
  expect(upstream.mock.calls[0][0].pathname).toBe(`/api/v1/member/bookmarks/${kind}/record-q123`);
  expect((await PUT(request, context([kind, "../auth"]))).status).toBe(404);
  expect((await PUT(request, context([kind, "x".repeat(161)]))).status).toBe(404);
  expect(upstream).toHaveBeenCalledTimes(1);
});
