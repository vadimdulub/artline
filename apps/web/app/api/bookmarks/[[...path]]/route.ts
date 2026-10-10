import type { NextRequest } from "next/server";
import { memberRequestHeaders } from "@/lib/session-cookies";
export const dynamic = "force-dynamic";
async function proxy(request: NextRequest, context: { params: Promise<{ path?: string[] }> }) {
  const { path = [] } = await context.params;
  const read = path.length === 0 || (path.length === 1 && path[0] === "state");
  const write = path.length === 2 && ["artist", "artwork"].includes(path[0]) && /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i.test(path[1]);
  if (!read && !write) return new Response(null, { status: 404 });
  if (read ? request.method !== "GET" : !["PUT", "DELETE"].includes(request.method)) return new Response(null, { status: 405 });
  const target = new URL(`/api/v1/member/bookmarks${path.length ? `/${path.join("/")}` : ""}`, process.env.API_INTERNAL_URL ?? "http://localhost:8080");
  target.search = request.nextUrl.search;
  const headers = memberRequestHeaders(request.cookies);
  for (const name of ["origin", "sec-fetch-site"]) { const value = request.headers.get(name); if (value) headers.set(name, value); }
  try {
    const response = await fetch(target, { method: request.method, headers, cache: "no-store", redirect: "error", signal: AbortSignal.any([request.signal, AbortSignal.timeout(12000)]) });
    return new Response(response.body, { status: response.status, headers: { "content-type": "application/json", "cache-control": "private, no-store", "x-robots-tag": "noindex" } });
  } catch {
    return Response.json({ error: { code: "BOOKMARKS_UNAVAILABLE", message: "Your bookmarks are temporarily unavailable. Please try again." } }, { status: 503, headers: { "cache-control": "private, no-store" } });
  }
}
export const GET = proxy;
export const PUT = proxy;
export const DELETE = proxy;
