import Link from "next/link";
import { notFound } from "next/navigation";
import { discoveryRequest, type SEOEntry } from "@/lib/seo-api";
import { pageMetadata } from "@/lib/seo";
import { researchPreviewEnabled } from "@/lib/research-preview";

type Props = { searchParams: Promise<{ after?: string | string[] }> };
function cursor(value: string | string[] | undefined): string {
  if (value === undefined) return "";
  if (typeof value !== "string" || value.length > 100 || !/^[a-z0-9]+(?:[-_][a-z0-9]+)*$/.test(value)) notFound();
  return value;
}
export async function generateMetadata({ searchParams }: Props) {
  const after = cursor((await searchParams).after);
  return pageMetadata("Artist directory", "Browse published artist profiles, biographies, artworks and sources in Artline’s art history atlas.", `/artists${after ? `?after=${encodeURIComponent(after)}` : ""}`);
}
export default async function ArtistsPage({ searchParams }: Props) {
  const after = cursor((await searchParams).after);
  // Preview-mode profile pages contain review material and carry noindex. Do
  // not advertise them as published directory results until public release.
  const page = researchPreviewEnabled() ? { items: [], next: "" } : await discoveryRequest<{ items: SEOEntry[]; next: string }>(`artists?after=${encodeURIComponent(after)}`);
  if (after && !page.items.length) notFound();
  return <main id="main-content" className="admin-page prose-page">
    <h1>Artist directory</h1>
    <p>Explore artists through their biographies, artworks and recorded sources. Artline connects painters and other creators with the museums, places and periods around them.</p>
    {page.items.length ? <ul>{page.items.map(item => <li key={item.path}><Link href={item.path} prefetch={false}>{item.name}</Link></li>)}</ul> : <p>The catalogue is being reviewed. Published profiles will appear here after their sources and artwork selections have been checked. You can explore the current research preview in the <Link href="/">interactive timeline</Link>.</p>}
    <nav aria-label="Artist directory pages">{after && <Link href="/artists">Back to the beginning</Link>}{page.next && <Link href={`/artists?after=${encodeURIComponent(page.next)}`} prefetch={false}>Next artists →</Link>}</nav>
    <p><Link href="/about">How Artline selects and documents its content</Link></p>
  </main>;
}
