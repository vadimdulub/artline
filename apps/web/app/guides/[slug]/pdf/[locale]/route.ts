import fs from "node:fs/promises";
import { guidePDFPath } from "@/lib/museum-guides";
export async function GET(_request: Request, { params }: { params: Promise<{ slug: string; locale: string }> }) {
  const { slug, locale } = await params;
  const filename = guidePDFPath(slug, locale);
  if (!filename) return new Response("Guide not found", { status: 404 });
  let data: Buffer;
  try { data = await fs.readFile(filename); }
  catch { return new Response("PDF temporarily unavailable", { status: 503, headers: { "Retry-After": "60" } }); }
  return new Response(new Uint8Array(data), { headers: { "Content-Type": "application/pdf", "Content-Disposition": `attachment; filename="artline-${slug}-${locale}.pdf"`, "Content-Length": String(data.byteLength), "Cache-Control": "public, max-age=3600", "X-Robots-Tag": "noindex", "X-Content-Type-Options": "nosniff" } });
}
