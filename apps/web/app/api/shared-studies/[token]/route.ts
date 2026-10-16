import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";
const headers = { "cache-control": "private, no-store", "x-robots-tag": "noindex, nofollow", "referrer-policy": "no-referrer" };

export async function GET(request: NextRequest, context: { params: Promise<{ token: string }> }) {
  const { token } = await context.params;
  if (!/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(token)) return new Response(null, { status: 404, headers });
  const target = new URL(`/api/v1/shared/studies/${token}`, process.env.API_INTERNAL_URL ?? "http://localhost:8080");
  target.search = request.nextUrl.search;
  try {
    // Sharing is independent of member authentication. Never forward cookies.
    const response = await fetch(target, { cache: "no-store", redirect: "error", signal: AbortSignal.any([request.signal, AbortSignal.timeout(12000)]) });
    return new Response(response.body, { status: response.status, headers: { ...headers, "content-type": "application/json" } });
  } catch {
    return Response.json({ error: { message: "This study could not be loaded. Please try again." } }, { status: 503, headers });
  }
}

function readOnly() { return Response.json({ error: { message: "Shared studies are read only." } }, { status: 405, headers: { ...headers, allow: "GET" } }); }
export const POST = readOnly;
export const PUT = readOnly;
export const PATCH = readOnly;
export const DELETE = readOnly;
export const HEAD = readOnly;
