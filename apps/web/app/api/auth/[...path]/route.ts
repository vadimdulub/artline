import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

const methods: Record<string, string> = {
  "google/start": "POST",
  "google/callback": "GET",
  session: "GET",
  logout: "POST",
};

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const path = (await context.params).path.join("/");
  const requiredMethod = methods[path];
  if (!requiredMethod || request.method !== requiredMethod) {
    return new Response(null, { status: requiredMethod ? 405 : 404, headers: { "Cache-Control": "private, no-store" } });
  }
  const target = new URL(`/api/v1/auth/${path}`, process.env.API_INTERNAL_URL ?? "http://localhost:8080");
  target.search = request.nextUrl.search;
  const headers = new Headers();
  for (const name of ["cookie", "origin", "sec-fetch-site"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  try {
    const response = await fetch(target, {
      method: request.method, headers, redirect: "manual", cache: "no-store",
      signal: AbortSignal.timeout(12000),
    });
    const outgoing = new Headers({ "Cache-Control": "private, no-store", "Referrer-Policy": "no-referrer", "X-Robots-Tag": "noindex" });
    for (const name of ["content-type", "location"]) {
      const value = response.headers.get(name);
      if (value) outgoing.set(name, value);
    }
    for (const cookie of response.headers.getSetCookie()) outgoing.append("set-cookie", cookie);
    return new Response(response.body, { status: response.status, headers: outgoing });
  } catch {
    return Response.json({ error: "Sign-in is temporarily unavailable. Please try again." }, { status: 503, headers: { "Cache-Control": "private, no-store" } });
  }
}

export const GET = proxy;
export const POST = proxy;
