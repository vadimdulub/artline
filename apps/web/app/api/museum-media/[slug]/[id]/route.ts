import type { NextRequest } from "next/server";
import { memberRequestHeaders } from "@/lib/session-cookies";
export const dynamic = "force-dynamic";
export async function GET(request: NextRequest, context: { params: Promise<{ slug: string; id: string }> }) {
  const { slug, id } = await context.params;
  const headers = { "cache-control": "private, no-store", "x-content-type-options": "nosniff", "x-robots-tag": "noindex", "content-security-policy": "default-src 'none'; sandbox" };
  if (!/^[a-z0-9]+(?:[-_][a-z0-9]+)*$/.test(slug) || slug.length > 100 || !/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(id)) return new Response(null, { status: 404, headers });
  try {
    const response = await fetch(new URL(`/api/v1/museum-media/${slug}/${id}`, process.env.API_INTERNAL_URL ?? "http://localhost:8080"), { headers: memberRequestHeaders(request.cookies), cache: "no-store", redirect: "error", signal: AbortSignal.any([request.signal, AbortSignal.timeout(12000)]) });
    if (!response.ok) return new Response(null, { status: response.status, headers });
    const type = response.headers.get("content-type");
    if (type !== "image/jpeg" && type !== "image/png") return new Response(null, { status: 502, headers });
    return new Response(response.body, { headers: { ...headers, "content-type": type } });
  } catch { return new Response(null, { status: 503, headers }); }
}
