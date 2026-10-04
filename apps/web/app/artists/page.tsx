import Link from "next/link";
import { notFound } from "next/navigation";
import { discoveryRequest, type SEOEntry } from "@/lib/seo-api";
import { pageMetadata } from "@/lib/seo";
import styles from "./directory.module.css";

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
  // Discovery always applies published visibility in Go, including during preview.
  const page = await discoveryRequest<{ items: SEOEntry[]; next: string }>(`artists?after=${encodeURIComponent(after)}`);
  if (after && !page.items.length) notFound();
  return <main id="main-content" className="admin-page prose-page">
    <h1>Artists, up close</h1>
    <p>Explore selected works, the lives behind them and the collections that hold them. Each profile brings together a sourced biography, artistic influences and five works to look at more closely.</p>
    {page.items.length ? <ul className={styles.artists}>{page.items.map(item => <li key={item.path}><Link href={item.path} prefetch={false}><span>{item.name}</span><span className={styles.arrow} aria-hidden="true">↗</span></Link></li>)}</ul> : <p>Explore the available painters and their artworks in the <Link href="/">interactive timeline</Link>.</p>}
    <nav aria-label="Artist directory pages">{after && <Link href="/artists">Back to the beginning</Link>}{page.next && <Link href={`/artists?after=${encodeURIComponent(page.next)}`} prefetch={false}>Next artists →</Link>}</nav>
    <p>Follow more connections in the <Link href="/">interactive art history timeline</Link>.</p>
    <p><Link href="/art-history-timeline">How to explore an art history timeline</Link></p>
    <p><Link href="/about">How Artline selects and documents its content</Link></p>
  </main>;
}
