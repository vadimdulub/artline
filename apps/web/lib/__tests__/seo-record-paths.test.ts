import { afterEach, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
import { getArtist, getArtistArtwork } from "../server-api";
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

it("resolves stable imported artist slugs accepted by Go", async () => {
  const fetch = vi.fn().mockResolvedValue({ status: 404 });
  vi.stubGlobal("fetch", fetch);
  await getArtist("artist_import");
  expect(fetch).toHaveBeenCalledOnce();
  expect(String(fetch.mock.calls[0][0])).toContain("/artists/artist_import");
});

it("rejects malformed artwork IDs before they can become upstream errors", async () => {
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  expect(await getArtistArtwork("artist", "-".repeat(36))).toBeNull();
  expect(await getArtist("../artist")).toBeNull();
  expect(fetch).not.toHaveBeenCalled();
});

it("narrows public artist and artwork reads during public research preview", async () => {
  vi.stubEnv("ARTLINE_PUBLIC_RESEARCH_PREVIEW", "true");
  const fetch = vi.fn().mockImplementation(async (url: URL) => {
    expect(url.searchParams.get("preview")).toBe("0");
    return { status: 200, ok: true, json: async () => ({ slug: "giotto", status: "published" }) };
  });
  vi.stubGlobal("fetch", fetch);
  await getArtistArtwork("giotto", "11111111-1111-4111-8111-111111111111");
  expect(fetch).toHaveBeenCalledTimes(2);
});
it("retains explicit review fallback only for an unpublished artist", async () => {
  vi.stubEnv("ARTLINE_PUBLIC_RESEARCH_PREVIEW", "true");
  const modes: string[] = [];
  vi.stubGlobal("fetch", vi.fn().mockImplementation(async (url: URL) => {
    modes.push(url.searchParams.get("preview")!);
    return modes.length === 1 ? { status: 404 } : { status: 200, ok: true, json: async () => ({ status: "review" }) };
  }));
  expect(await getArtist("unpublished")).toEqual({ status: "review" });
  expect(modes).toEqual(["0", "1"]);
});
it("never falls back to a review work under a published artist", async () => {
  vi.stubEnv("ARTLINE_PUBLIC_RESEARCH_PREVIEW", "true");
  const fetch = vi.fn().mockResolvedValueOnce({ status: 200, ok: true, json: async () => ({ slug: "giotto", status: "published" }) }).mockResolvedValueOnce({ status: 404 });
  vi.stubGlobal("fetch", fetch);
  expect(await getArtistArtwork("giotto", "22222222-2222-4222-8222-222222222222")).toBeNull();
  expect(fetch).toHaveBeenCalledTimes(2);
  expect(String(fetch.mock.calls[1][0])).toContain("preview=0");
});
it("surfaces an outage instead of silently switching to review visibility", async () => {
  vi.stubEnv("ARTLINE_PUBLIC_RESEARCH_PREVIEW", "true");
  const fetch = vi.fn().mockResolvedValue({ status: 503, ok: false });
  vi.stubGlobal("fetch", fetch);
  await expect(getArtist("giotto")).rejects.toThrow("temporarily unavailable");
  expect(fetch).toHaveBeenCalledOnce();
});
it("opens the full catalogue only through an explicit configured workspace", async () => {
  vi.stubEnv("ARTLINE_PUBLIC_RESEARCH_PREVIEW", "true");
  const fetch = vi.fn().mockImplementation(async (url: URL) => {
    expect(url.searchParams.get("preview")).toBe("1");
    return { status: 200, ok: true, json: async () => ({ slug: "giotto", status: "published" }) };
  });
  vi.stubGlobal("fetch", fetch);
  await getArtistArtwork("giotto", "11111111-1111-4111-8111-111111111111", true);
  expect(fetch).toHaveBeenCalledTimes(2);
});
it("does not enable research access from the workspace flag alone", async () => {
  vi.stubEnv("ARTLINE_PUBLIC_RESEARCH_PREVIEW", "false");
  vi.stubEnv("ARTLINE_RESEARCH_PREVIEW_TOKEN", "");
  const fetch = vi.fn().mockImplementation(async (url: URL) => {
    expect(url.searchParams.get("preview")).toBe("0");
    return { status: 200, ok: true, json: async () => ({ slug: "giotto", status: "published" }) };
  });
  vi.stubGlobal("fetch", fetch);
  await getArtistArtwork("giotto", "11111111-1111-4111-8111-111111111111", true);
  expect(fetch).toHaveBeenCalledTimes(2);
});
