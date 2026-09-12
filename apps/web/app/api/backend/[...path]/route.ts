import type { NextRequest } from "next/server";
import { researchPreviewToken } from "@/lib/server-api";
export const dynamic = "force-dynamic";
async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (path[0] !== "v1" || path.some((part) => !/^[a-zA-Z0-9_-]+$/.test(part))) {
    return Response.json({ error: { code: "INVALID_PROXY_PATH", message: "Unknown API path." } }, { status: 404 });
  }
  const target = new URL(`/api/${path.map(encodeURIComponent).join("/")}`, process.env.API_INTERNAL_URL ?? "http://localhost:8080");
  target.search = request.nextUrl.search;
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const authorization = request.headers.get("authorization");
  if (contentType) headers.set("content-type", contentType);
  if (authorization) headers.set("authorization", authorization);
  const previewToken = researchPreviewToken();
  if (request.method === "GET" && previewToken && !authorization) {
    headers.set("authorization", `Bearer ${previewToken}`);
    target.searchParams.set("preview", "1");
  }
  let body: Uint8Array | undefined;
  if (request.body) {
    const reader = request.body.getReader();
    const chunks: Uint8Array[] = [];
    let length = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      length += value.byteLength;
      if (length > 1024 * 1024) {
        await reader.cancel();
        return Response.json({ error: { code: "BODY_TOO_LARGE", message: "The request exceeds 1 MB." } }, { status: 413 });
      }
      chunks.push(value);
    }
    body = new Uint8Array(length);
    let offset = 0;
    for (const chunk of chunks) { body.set(chunk, offset); offset += chunk.byteLength; }
  }
  try {
    const response = await fetch(target, { method: request.method, headers, body: body as BodyInit | undefined, cache: "no-store", signal: AbortSignal.timeout(12000) });
    return new Response(response.body, { status: response.status, headers: { "content-type": response.headers.get("content-type") ?? "application/json", "cache-control": "private, no-store" } });
  } catch {
    return Response.json({ error: { code: "SERVICE_UNAVAILABLE", message: "The catalogue is temporarily unavailable. Try again shortly." } }, { status: 503 });
  }
}
export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
