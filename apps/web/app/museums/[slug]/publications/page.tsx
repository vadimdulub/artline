import Link from "next/link";
import { notFound } from "next/navigation";
import { getMuseumPublications, getPublishedMuseum } from "@/lib/museum-publications";
import { getMuseum } from "@/lib/server-api";
import { contentLabels, type MuseumContentKind } from "@/lib/museum-studio";
import { MuseumPublicationCards } from "@/components/MuseumPublicationView";
import { noIndex } from "@/lib/seo";
import styles from "@/components/MuseumPublic.module.css";
export const metadata = { title: "Museum publications", robots: noIndex };
export default async function Page({ params, searchParams }: { params: Promise<{ slug: string }>; searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { slug } = await params, query = await searchParams;
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || slug.length > 100) notFound();
  const kind = typeof query.kind === "string" && ["artwork", "exhibition", "guide"].includes(query.kind) ? query.kind as MuseumContentKind : "artwork";
  const cursor = typeof query.cursor === "string" && /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(query.cursor) ? query.cursor : "";
  const q = typeof query.q === "string" ? query.q.slice(0, 200) : "";
  const museum = await getMuseum(slug) ?? await getPublishedMuseum(slug); if (!museum) notFound();
  const page = await getMuseumPublications(slug, kind, cursor, q);
  const href = (next: string) => `/museums/${slug}/publications?${new URLSearchParams({ kind, q, cursor: next })}`;
  return <main id="main-content" className={styles.page}><Link className={styles.back} href={`/museums/${slug}`}>{museum.name}</Link><h1>{contentLabels[kind]}</h1><p>Published by {museum.name}.</p><form className={styles.search}><input type="hidden" name="kind" value={kind} /><label>Search by title<input name="q" type="search" maxLength={200} defaultValue={q} /></label><button>Search</button>{q && <Link href={`/museums/${slug}/publications?kind=${kind}`}>Clear search</Link>}</form>{page.items.length ? <MuseumPublicationCards slug={slug} items={page.items} /> : <p>No published content matches this view.</p>}<nav className={`${styles.pager} catalogue-pagination`} aria-label="Publication pages">{cursor && <Link href={href("")}>First page</Link>}{page.next_cursor && <Link href={href(page.next_cursor)}>Next page</Link>}</nav></main>;
}
