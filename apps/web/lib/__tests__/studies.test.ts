import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { GET, POST, PUT, PATCH, DELETE } from "../../app/api/studies/[[...path]]/route";
import { memberReturnTo, memberSignInPath, requiresMember } from "../member-return";
import { safeStudyLink, studyYearError } from "../studies";
const id = "11111111-1111-4111-8111-111111111111";
const context = (path?: string[]) => ({ params: Promise.resolve({ path }) });
const upstream = vi.fn();
beforeEach(() => { vi.stubGlobal("fetch", upstream); vi.stubEnv("API_INTERNAL_URL", "https://api.example"); upstream.mockReset(); });
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

it("requires membership and retains study destinations through sign-in", () => {
  for (const path of ["/studies", `/studies/${id}?view=gallery`, "/bookmarks"]) { expect(requiresMember(path)).toBe(true); expect(memberReturnTo(path)).toBe(path); expect(memberSignInPath(path)).toContain("return_to="); }
  expect(requiresMember("/artists/monet")).toBe(false); expect(memberReturnTo("/studies/../auth")).toBeNull(); expect(memberReturnTo("//evil.example/studies")).toBeNull();
});
it("preserves authenticated bodies and CSRF evidence without forwarding other credentials", async () => {
  upstream.mockResolvedValue(Response.json({ id }));
  const body = JSON.stringify({ link: { kind: "book", url: "https://example.org/book", title: "A book" } });
  const token = "a".repeat(43);
  const response = await POST(new NextRequest(`https://artlines.org/api/studies/${id}/records`, { method: "POST", body, headers: { "content-type": "application/json", cookie: `__Host-artline_session=${token}; editor=ignored`, origin: "https://artlines.org", "sec-fetch-site": "same-origin", authorization: "Bearer ignored" } }), context([id, "records"]));
  const [url, options] = upstream.mock.calls[0]; expect(url.href).toBe(`https://api.example/api/v1/member/studies/${id}/records`); expect(new TextDecoder().decode(options.body)).toBe(body); expect(options.headers.get("cookie")).toBe(`__Host-artline_session=${token}`); expect(options.headers.has("authorization")).toBe(false); expect(options.headers.get("origin")).toBe("https://artlines.org"); expect(response.headers.get("cache-control")).toBe("private, no-store");
});
it("rejects unbounded bodies, unsupported paths and wrong methods", async () => {
  expect((await POST(new NextRequest("https://artlines.org/api/studies", { method: "POST", body: "x".repeat(32769) }), context())).status).toBe(413);
  expect((await GET(new NextRequest("https://artlines.org/api/studies/auth"), context(["..", "auth"]))).status).toBe(404);
  expect((await PUT(new NextRequest("https://artlines.org/api/studies", { method: "PUT" }), context())).status).toBe(405);
  expect((await PATCH(new NextRequest("https://artlines.org/api/studies/search", { method: "PATCH" }), context(["search"]))).status).toBe(405);
  expect((await DELETE(new NextRequest(`https://artlines.org/api/studies/${id}/records`, { method: "DELETE" }), context([id, "records"]))).status).toBe(405);
  expect(upstream).not.toHaveBeenCalled();
});
it("keeps exports private and preserves unauthorized responses", async () => {
  upstream.mockResolvedValue(new Response("Title,Notes", { headers: { "content-type": "text/csv", "content-disposition": 'attachment; filename="artline-study.csv"' } }));
  const exported = await GET(new NextRequest(`https://artlines.org/api/studies/${id}/export?format=csv`), context([id, "export"]));
  expect(exported.headers.get("content-disposition")).toContain("artline-study.csv"); expect(exported.headers.get("content-type")).toBe("text/csv"); expect(exported.headers.get("cache-control")).toBe("private, no-store");
  upstream.mockResolvedValue(Response.json({ error: { code: "AUTH_REQUIRED" } }, { status: 401 })); expect((await GET(new NextRequest("https://artlines.org/api/studies"), context())).status).toBe(401);
});
it("validates year ranges and renders only safe source links", () => {
  expect(studyYearError("1877", "1877")).toBe(""); expect(studyYearError("-500", "1900")).toBe("");
  for (const [from, to] of [["0", "1900"], ["1880", "1870"], ["19.5", "1900"], ["abc", ""], ["", "2001"]]) expect(studyYearError(from, to)).not.toBe("");
  for (const unsafe of ["javascript:alert(1)", "data:text/html,test", "https://user:pass@example.org", "//example.org", "/\\evil.example"]) expect(safeStudyLink(unsafe)).toBeUndefined();
  expect(safeStudyLink("https://example.org/book")).toBe("https://example.org/book"); expect(safeStudyLink("/artists/monet")).toBe("/artists/monet");
});
