import { afterEach, beforeEach, expect, it, vi } from "vitest";
vi.mock("next/headers", () => ({ cookies: vi.fn() }));
vi.mock("next/navigation", () => ({ redirect: vi.fn((path: string) => { throw new Error(`redirect:${path}`); }) }));
import { cookies } from "next/headers";
import { getMemberSession, requireMemberSession } from "../member-session";

const upstream = vi.fn();
beforeEach(() => {
  vi.stubEnv("API_INTERNAL_URL", "https://api.example");
  vi.stubGlobal("fetch", upstream);
  upstream.mockReset();
  vi.mocked(cookies).mockResolvedValue({ get: () => undefined } as never);
});
afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); });

it("verifies cookies with Go and does not cache member access between requests", async () => {
  const token = "a".repeat(43);
  vi.mocked(cookies).mockResolvedValue({ get: (name: string) => name === "__Host-artline_session" ? { name, value: token } : undefined } as never);
  upstream.mockResolvedValue(new Response(JSON.stringify({ user: { id: "member" } })));
  await expect(requireMemberSession("/museums/the-met")).resolves.toBeUndefined();
  const [url, options] = upstream.mock.calls[0];
  expect(url.href).toBe("https://api.example/api/v1/auth/session");
  expect(options.headers.get("cookie")).toBe(`__Host-artline_session=${token}`);
  expect(options.cache).toBe("no-store");
  expect(options.redirect).toBe("error");
});

it("redirects anonymous and expired sessions back through sign-in with the museum filters", async () => {
  upstream.mockResolvedValue(new Response(JSON.stringify({ user: null })));
  await expect(requireMemberSession("/museums/the-met?artist=monet"))
    .rejects.toThrow("redirect:/account?return_to=%2Fmuseums%2Fthe-met%3Fartist%3Dmonet");
});

it("uses the API's local debug session without requiring cookies or Google", async () => {
  upstream.mockResolvedValue(new Response(JSON.stringify({ user: { id: "local-debug" }, local_debug: true, all_features: true })));
  await expect(requireMemberSession("/museums/the-met")).resolves.toBeUndefined();
  expect(upstream.mock.calls[0][1].headers.has("cookie")).toBe(false);
});

it("fails closed when the session service is unavailable", async () => {
  upstream.mockResolvedValue(new Response(null, { status: 503 }));
  await expect(getMemberSession()).rejects.toThrow("Sign-in is temporarily unavailable");
});
