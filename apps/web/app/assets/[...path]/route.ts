export const dynamic = "force-dynamic";
export const runtime = "nodejs";

let credentials: { token: string; expiresAt: number } | undefined;

async function storageToken(): Promise<string> {
  if (credentials && credentials.expiresAt > Date.now() + 60_000) return credentials.token;
  const response = await fetch(
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
    { headers: { "Metadata-Flavor": "Google" }, cache: "no-store", signal: AbortSignal.timeout(5000) },
  );
  if (!response.ok) throw new Error("Storage credentials unavailable");
  const data = await response.json() as { access_token: string; expires_in: number };
  if (!data.access_token || !Number.isFinite(data.expires_in)) throw new Error("Invalid storage credentials");
  credentials = { token: data.access_token, expiresAt: Date.now() + data.expires_in * 1000 };
  return credentials.token;
}

async function serve(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const bucket = process.env.ARTLINE_IMAGES_BUCKET;
  const { path } = await context.params;
  if (!bucket || !["artworks", "artists"].includes(path[0]) || path.length > 8 ||
      path.some(part => !/^[a-zA-Z0-9][a-zA-Z0-9._-]*$/.test(part) || part.includes("..")) ||
      !/\.(jpe?g|png|webp|avif|gif)$/i.test(path.at(-1) ?? "")) {
    return new Response("Image not found", { status: 404 });
  }
  try {
    const headers = new Headers({ authorization: `Bearer ${await storageToken()}` });
    const etag = request.headers.get("if-none-match");
    if (etag) headers.set("if-none-match", etag);
    const url = `https://storage.googleapis.com/storage/v1/b/${encodeURIComponent(bucket)}/o/${encodeURIComponent(`assets/${path.join("/")}`)}?alt=media`;
    const response = await fetch(url, {
      method: request.method === "HEAD" ? "HEAD" : "GET",
      headers, cache: "no-store", signal: AbortSignal.timeout(15000), redirect: "error",
    });
    if (response.status === 404) return new Response("Image not found", { status: 404 });
    if (!response.ok && response.status !== 304) {
      if (response.status === 401) credentials = undefined;
      await response.body?.cancel();
      throw new Error("Storage request failed");
    }
    const resultHeaders = new Headers({
      "cache-control": "public, max-age=86400",
      "x-content-type-options": "nosniff",
    });
    for (const name of ["content-type", "content-length", "etag", "last-modified"]) {
      const value = response.headers.get(name);
      if (value) resultHeaders.set(name, value);
    }
    return new Response(request.method === "HEAD" || response.status === 304 ? null : response.body,
      { status: response.status, headers: resultHeaders });
  } catch {
    return new Response("Image temporarily unavailable", { status: 503, headers: { "cache-control": "no-store" } });
  }
}

export const GET = serve;
export const HEAD = serve;
