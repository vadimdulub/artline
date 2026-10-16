import type { NextRequest } from "next/server";
import { memberRequestHeaders } from "@/lib/session-cookies";
export const dynamic = "force-dynamic";
const uuid = /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/;
async function proxy(request: NextRequest, context: { params: Promise<{ path?: string[] }> }) {
  const { path = [] } = await context.params;
  let methods: string[] = [];
  if (!path.length) methods = ["GET", "POST"];
  else if (path.length === 1 && path[0] === "search") methods = ["GET"];
  else if (uuid.test(path[0])) {
    if (path.length === 1) methods = ["GET", "PATCH", "DELETE"];
    if (path.length === 2 && path[1] === "export") methods = ["GET"];
    if (path.length === 2 && path[1] === "records") methods = ["POST"];
    if (path.length === 4 && path[1] === "records" && ["artwork", "book", "event"].includes(path[2]) && path[3].length <= 160 && /^[a-z0-9]+(?:[-_][a-z0-9]+)*$/.test(path[3])) methods = ["PUT", "DELETE"];
  }
  const privateHeaders = { "cache-control": "private, no-store", "x-robots-tag": "noindex" };
  if (!methods.length) return new Response(null, { status: 404, headers: privateHeaders });
  if (!methods.includes(request.method)) return new Response(null, { status: 405, headers: privateHeaders });
  const target = new URL(`/api/v1/member/studies${path.length ? `/${path.join("/")}` : ""}`, process.env.API_INTERNAL_URL ?? "http://localhost:8080");
  target.search = request.nextUrl.search;
  const headers = memberRequestHeaders(request.cookies);
  for (const name of ["origin", "sec-fetch-site", "content-type"]) { const value = request.headers.get(name); if (value) headers.set(name, value); }
  try {
    let body: Uint8Array<ArrayBuffer> | undefined;
    if (["POST", "PUT", "PATCH"].includes(request.method)) {
      // Bound incoming bodies before buffering or forwarding.
      const reader = request.body?.getReader(); const chunks: Uint8Array[] = []; let size = 0;
      if (reader) for (;;) { const chunk = await reader.read(); if (chunk.done) break; size += chunk.value.byteLength; if (size > 32768) { await reader.cancel(); return new Response(null, { status: 413, headers: privateHeaders }); } chunks.push(chunk.value); }
      body = new Uint8Array(size); let offset = 0; for (const chunk of chunks) { body.set(chunk, offset); offset += chunk.length; }
    }
    const response = await fetch(target, { method: request.method, headers, body, cache: "no-store", redirect: "error", signal: AbortSignal.any([request.signal, AbortSignal.timeout(12000)]) });
    const resultHeaders: Record<string, string> = { ...privateHeaders, "content-type": response.headers.get("content-type") ?? "application/json" };
    const disposition = response.headers.get("content-disposition"); if (disposition) resultHeaders["content-disposition"] = disposition;
    return new Response(response.body, { status: response.status, headers: resultHeaders });
  } catch {
    return Response.json({ error: { message: "Studies are temporarily unavailable. Please try again." } }, { status: 503, headers: privateHeaders });
  }
}
export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
