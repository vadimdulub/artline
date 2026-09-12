import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const fetchMock = vi.fn();
beforeEach(() => {
  vi.resetModules();
  vi.stubEnv("ARTLINE_IMAGES_BUCKET", "artline-images");
  vi.stubGlobal("fetch", fetchMock);
  fetchMock.mockReset();
});
afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); });
const context = (path: string[]) => ({ params: Promise.resolve({ path }) });
const token = () => new Response(JSON.stringify({ access_token: "private-storage-token", expires_in: 3600 }));

describe("private bucket image delivery", () => {
  it("rejects non-image and traversal paths before requesting credentials", async () => {
    const { GET } = await import("../../app/assets/[...path]/route");
    for (const path of [["artworks", "..", "secret.jpg"], ["artworks", ".env"], ["backups", "db.jpg"], ["artworks", "receipt.json"]]) {
      expect((await GET(new Request("https://artline.example/assets/test"), context(path))).status).toBe(404);
    }
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("streams the requested object and never returns its storage credentials", async () => {
    fetchMock.mockResolvedValueOnce(token()).mockResolvedValueOnce(new Response(new Uint8Array([1, 2, 3]), {
      headers: { "content-type": "image/jpeg", etag: '"image-v1"' },
    }));
    const { GET } = await import("../../app/assets/[...path]/route");
    const response = await GET(new Request("https://artline.example/assets/artworks/work.jpg"), context(["artworks", "work.jpg"]));
    expect(response.status).toBe(200);
    expect([...new Uint8Array(await response.arrayBuffer())]).toEqual([1, 2, 3]);
    expect(response.headers.get("etag")).toBe('"image-v1"');
    expect(response.headers.get("authorization")).toBeNull();
    expect(response.headers.get("cache-control")).toContain("max-age=86400");
    expect(fetchMock.mock.calls[1][0]).toBe("https://storage.googleapis.com/storage/v1/b/artline-images/o/assets%2Fartworks%2Fwork.jpg?alt=media");
    expect(fetchMock.mock.calls[1][1].headers.get("authorization")).toBe("Bearer private-storage-token");
  });

  it("preserves conditional requests and empty 304 responses", async () => {
    fetchMock.mockResolvedValueOnce(token()).mockResolvedValueOnce(new Response(null, { status: 304, headers: { etag: '"image-v1"' } }));
    const { GET } = await import("../../app/assets/[...path]/route");
    const response = await GET(new Request("https://artline.example/assets/artworks/work.jpg", { headers: { "if-none-match": '"image-v1"' } }), context(["artworks", "work.jpg"]));
    expect(response.status).toBe(304);
    expect(await response.text()).toBe("");
    expect(fetchMock.mock.calls[1][1].headers.get("if-none-match")).toBe('"image-v1"');
  });

  it("does not expose upstream errors or cache failures", async () => {
    fetchMock.mockResolvedValueOnce(token()).mockResolvedValueOnce(new Response("sensitive upstream error", { status: 403 }));
    const { GET } = await import("../../app/assets/[...path]/route");
    const response = await GET(new Request("https://artline.example/assets/artworks/work.jpg"), context(["artworks", "work.jpg"]));
    expect(response.status).toBe(503);
    expect(await response.text()).toBe("Image temporarily unavailable");
    expect(response.headers.get("cache-control")).toBe("no-store");
  });
});
