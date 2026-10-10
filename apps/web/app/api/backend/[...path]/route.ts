import type { NextRequest } from "next/server";
import { memberRequestHeaders } from "@/lib/session-cookies";
import { acceptsGzip } from "@/lib/response-compression";
export const dynamic = "force-dynamic";
async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (path[0] !== "v1" || path.some((part) => !/^[a-zA-Z0-9_-]+$/.test(part))) {
    return Response.json({ error: { code: "INVALID_PROXY_PATH", message: "Unknown API path." } }, { status: 404 });
  }
  const target = new URL(`/api/${path.map(encodeURIComponent).join("/")}`, process.env.API_INTERNAL_URL ?? "http://localhost:8080");
  target.search = request.nextUrl.search;
  const headers = memberRequestHeaders(request.cookies);
  // Old bookmarks use the same catalogue; no preview credentials are forwarded.
  target.searchParams.delete("preview");
  target.searchParams.delete("status");
  try {
    // Cancel superseded reads, leaving headroom for the atlas query budget.
    const timeout = AbortSignal.timeout(path[1] === "atlas" ? 25000 : 12000);
    const signal = AbortSignal.any([request.signal, timeout]);
    const response = await fetch(target, { headers, cache: "no-store", signal });
    const responseHeaders = new Headers({ "content-type": response.headers.get("content-type") ?? "application/json", "cache-control": "private, no-store" });
    const cacheStatus = response.headers.get("x-artline-cache");
    if (cacheStatus) responseHeaders.set("x-artline-cache", cacheStatus);
    responseHeaders.set("vary", "Accept-Encoding");
    const compress = request.method === "GET" && response.ok && response.body &&
      responseHeaders.get("content-type")?.includes("application/json") && acceptsGzip(request.headers.get("accept-encoding"));
    if (compress) responseHeaders.set("content-encoding", "gzip");
    return new Response(compress ? response.body!.pipeThrough(new CompressionStream("gzip")) : response.body, { status: response.status, headers: responseHeaders });
  } catch {
    return Response.json({ error: { code: "SERVICE_UNAVAILABLE", message: "The catalogue is temporarily unavailable. Try again shortly." } }, { status: 503 });
  }
}
export const GET = proxy;
