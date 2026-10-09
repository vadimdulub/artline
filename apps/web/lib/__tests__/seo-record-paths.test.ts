import { afterEach, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
import { getArtist, getArtistIdentity, getArtistArtwork } from "../server-api";
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

it.each(["draft", "review", "published"])("reads %s records without preview configuration or credentials", async status => {
  vi.stubEnv("ARTLINE_PUBLIC_RESEARCH_PREVIEW", "false");
  vi.stubEnv("ARTLINE_RESEARCH_PREVIEW_TOKEN", "obsolete-secret");
  const work = { id: "11111111-1111-4111-8111-111111111111", status };
  const fetch = vi.fn().mockImplementation(async (url: URL, options: RequestInit) => {
    expect(url.searchParams.has("preview")).toBe(false);
    expect(new Headers(options.headers).has("authorization")).toBe(false);
    return { status: 200, ok: true, json: async () => url.pathname.includes("/works/") ? work : ({ slug: "giotto", status }) };
  });
  vi.stubGlobal("fetch", fetch);
  expect(await getArtistArtwork("giotto", work.id)).toEqual(work);
  expect(fetch).toHaveBeenCalledOnce();
  expect(String(fetch.mock.calls[0][0])).toContain(`/artists/giotto/works/${work.id}`);
});
it("loads canonical creator identity independently of the full artist summary", async () => {
  const identity = { id: "artist-id", slug: "giotto", display_name: "Giotto", entity_type: "person" };
  const fetch = vi.fn().mockResolvedValue({ status: 200, ok: true, json: async () => identity });
  vi.stubGlobal("fetch", fetch);
  expect(await getArtistIdentity("old-giotto")).toEqual(identity);
  expect(fetch).toHaveBeenCalledOnce();
  expect(String(fetch.mock.calls[0][0])).toContain("/artists/old-giotto/identity");
});
it("returns a missing record without a second visibility lookup", async () => {
  const fetch = vi.fn().mockResolvedValue({ status: 404 });
  vi.stubGlobal("fetch", fetch);
  expect(await getArtist("missing-artist")).toBeNull();
  expect(fetch).toHaveBeenCalledOnce();
});
it("surfaces catalogue outages", async () => {
  const fetch = vi.fn().mockResolvedValue({ status: 503, ok: false });
  vi.stubGlobal("fetch", fetch);
  await expect(getArtist("giotto")).rejects.toThrow("temporarily unavailable");
  expect(fetch).toHaveBeenCalledOnce();
});
