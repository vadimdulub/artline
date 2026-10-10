import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { GET } from "../../app/api/backend/[...path]/route";
import { memberRequestHeaders } from "../session-cookies";
const upstream = vi.fn();
beforeEach(() => { vi.stubEnv("API_INTERNAL_URL", "https://api.example"); vi.stubGlobal("fetch", upstream); upstream.mockReset(); });
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });
it("forwards only member cookies and preserves an authentication denial", async () => {
  upstream.mockResolvedValue(Response.json({ error: { code: "AUTH_REQUIRED" } }, { status: 401 }));
  const token = "a".repeat(43);
  const response = await GET(new NextRequest("https://artlines.org/api/backend/v1/museums", { headers: { cookie: `__Host-artline_session=${token}; artline_oauth=private; editor=secret`, authorization: "Bearer ignored", "x-user-id": "forged" } }), { params: Promise.resolve({ path: ["v1", "museums"] }) });
  const headers = upstream.mock.calls[0][1].headers as Headers;
  expect([...headers]).toEqual([["cookie", `__Host-artline_session=${token}`]]);
  expect(response.status).toBe(401);
  expect(response.headers.get("cache-control")).toBe("private, no-store");
  expect(await response.json()).toEqual({ error: { code: "AUTH_REQUIRED" } });
});
it("does not forward malformed tokens", () => {
  expect([...memberRequestHeaders({ get: name => ({ name, value: "a".repeat(42) + ";" }) })]).toEqual([]);
});
