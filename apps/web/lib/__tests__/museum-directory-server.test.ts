import { afterEach, expect, it, vi } from "vitest";
vi.mock("next/headers", () => ({ cookies: async () => ({ get: (name: string) => name === "artline_session" ? { name, value: "s".repeat(43) } : undefined }) }));
import { getMuseumDirectory } from "../server-api";

afterEach(() => vi.unstubAllGlobals());

it("caches only the first unfiltered page and keeps member headers in its key", async () => {
  const fetch = vi.fn().mockResolvedValue({ status: 200, ok: true, json: async () => ({ items: [], total: 0 }) });
  vi.stubGlobal("fetch", fetch);
  await getMuseumDirectory(new URLSearchParams());
  const options = fetch.mock.calls[0][1];
  expect(options.cache).toBe("force-cache");
  expect(options.next.revalidate).toBe(30);
  expect(options.headers.get("cookie")).toBe(`artline_session=${"s".repeat(43)}`);
  await getMuseumDirectory(new URLSearchParams({ country: "FR" }));
  expect(fetch.mock.calls[1][1].cache).toBe("no-store");
  await getMuseumDirectory(new URLSearchParams({ cursor: "next-page" }));
  expect(fetch.mock.calls[2][1].cache).toBe("no-store");
});
