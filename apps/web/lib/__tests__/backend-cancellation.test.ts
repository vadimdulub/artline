// @vitest-environment node
import { afterEach, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

vi.mock("@/lib/server-api", () => ({ researchPreviewToken: () => undefined }));
import { GET } from "@/app/api/backend/[...path]/route";

afterEach(() => vi.unstubAllGlobals());

it("cancels an abandoned timeline read upstream while a newer request succeeds", async () => {
  let began!: () => void;
  const started = new Promise<void>(resolve => { began = resolve; });
  let upstreamCancelled = false;
  vi.stubGlobal("fetch", vi.fn((url: URL, options: RequestInit) => {
    if (url.searchParams.get("start") === "1901") {
      return Promise.resolve(Response.json({ range: { start: 1901, end: 1941 }, lanes: [], total: 0 }));
    }
    return new Promise((_resolve, reject) => {
      options.signal!.addEventListener("abort", () => {
        upstreamCancelled = true;
        reject(options.signal!.reason);
      }, { once: true });
      began();
    });
  }));
  const controller = new AbortController();
  const context = { params: Promise.resolve({ path: ["v1", "atlas"] }) };
  const stale = GET(new NextRequest("http://localhost/api/backend/v1/atlas?start=1900&end=1940", { signal: controller.signal }), context);
  await started;
  controller.abort();
  expect(upstreamCancelled).toBe(true);
  await stale;
  const latest = await GET(new NextRequest("http://localhost/api/backend/v1/atlas?start=1901&end=1941"), context);
  expect(latest.status).toBe(200);
  expect((await latest.json()).range).toEqual({ start: 1901, end: 1941 });
  expect(latest.headers.get("cache-control")).toBe("private, no-store");
});
