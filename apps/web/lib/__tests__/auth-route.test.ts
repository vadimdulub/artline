import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { GET, POST } from "../../app/api/auth/[...path]/route";

const upstream = vi.fn();
const context = (path: string[]) => ({ params: Promise.resolve({ path }) });
beforeEach(() => { vi.stubEnv("API_INTERNAL_URL", "https://api.example"); vi.stubGlobal("fetch", upstream); upstream.mockReset(); });
afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); });

describe("same-origin authentication transport", () => {
  it("preserves multiple cookies and browser redirect without following Google", async () => {
    const headers = new Headers({ location: "https://accounts.google.com/o/oauth2/v2/auth", "content-type": "text/html" });
    headers.append("set-cookie", "__Host-artline_oauth=flow; Path=/; Secure; HttpOnly");
    headers.append("set-cookie", "__Host-artline_session=session; Path=/; Secure; HttpOnly");
    upstream.mockResolvedValue(new Response(null, { status: 303, headers }));
    const response = await POST(new NextRequest("https://artlines.org/api/auth/google/start", { method: "POST", headers: { origin: "https://artlines.org", cookie: "existing=value", authorization: "Bearer editor-must-not-forward" } }), context(["google", "start"]));
    expect(response.status).toBe(303);
    expect(response.headers.getSetCookie()).toHaveLength(2);
    expect(response.headers.get("cache-control")).toBe("private, no-store");
    const [url, options] = upstream.mock.calls[0];
    expect(url.href).toBe("https://api.example/api/v1/auth/google/start");
    expect(options.redirect).toBe("manual");
    expect(options.headers.get("origin")).toBe("https://artlines.org");
    expect(options.headers.get("cookie")).toBe("existing=value");
    expect(options.headers.has("authorization")).toBe(false);
  });

  it("preserves callback parameters", async () => {
    upstream.mockResolvedValue(new Response(null, { status: 303, headers: { location: "https://artlines.org/account" } }));
    await GET(new NextRequest("https://artlines.org/api/auth/google/callback?state=abc&code=xyz"), context(["google", "callback"]));
    expect(upstream.mock.calls[0][0].search).toBe("?state=abc&code=xyz");
  });

  it("forwards the selected painter to the OAuth start endpoint", async () => {
    upstream.mockResolvedValue(new Response(null, { status: 303, headers: { location: "https://accounts.google.com/auth" } }));
    const query = new URLSearchParams({ return_to: "/artists/monet?catalogue=all&art_year=1900" });
    await POST(new NextRequest(`https://artlines.org/api/auth/google/start?${query}`, { method: "POST", headers: { origin: "https://artlines.org" } }), context(["google", "start"]));
    expect(upstream.mock.calls[0][0].searchParams.get("return_to")).toBe("/artists/monet?catalogue=all&art_year=1900");
  });

  it("blocks unknown routes and wrong methods before contacting upstream", async () => {
    expect((await GET(new NextRequest("https://artlines.org/api/auth/logout"), context(["logout"]))).status).toBe(405);
    expect((await GET(new NextRequest("https://artlines.org/api/auth/unknown"), context(["unknown"]))).status).toBe(404);
    expect(upstream).not.toHaveBeenCalled();
  });

  it("does not reveal transport errors", async () => {
    upstream.mockRejectedValue(new Error("secret upstream details"));
    const response = await GET(new NextRequest("https://artlines.org/api/auth/session"), context(["session"]));
    expect(response.status).toBe(503);
    expect(await response.text()).not.toContain("secret");
  });
});
