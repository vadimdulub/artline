import { afterEach, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
import { getArtist, getArtistArtwork } from "../server-api";
afterEach(() => vi.unstubAllGlobals());

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
