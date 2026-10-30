import { Suspense } from "react";
import { notFound } from "next/navigation";
import Link from "@/components/MemberLink";
import { PreparedMuseumGuides } from "@/components/PreparedMuseumGuides";
import { getPreparedMuseumGuides } from "@/lib/prepared-museum-guides";
import { getMuseumGuideLinks } from "@/lib/museum-guide-links";
import { guidePath } from "@/lib/museum-guide-types";
import { MuseumPageTabs } from "@/components/MuseumPageTabs";
import { MuseumDetail } from "@/components/MuseumDetail";
import { MuseumWebsiteLink } from "@/components/MuseumWebsiteLink";
import { MuseumGuideCallout } from "@/components/MuseumGuideCallout";
import { ArtworkImage } from "@/components/ArtworkViewer";
import { MuseumPublicationCards, PublicationImage } from "@/components/MuseumPublicationView";
import { getMuseum } from "@/lib/server-api";
import { getMuseumPublications, getPublishedMuseum } from "@/lib/museum-publications";
import { publicationPath } from "@/lib/museum-studio";
import { absoluteURL, breadcrumbs, pageMetadata, plainDescription } from "@/lib/seo";
import { StructuredData } from "@/components/StructuredData";
import { safeSourceURL } from "@/lib/api";
import { museumLocations } from "@/lib/museum-location";
import { museumDescription } from "@/lib/display-metadata";
import type { Museum } from "@/lib/types";
import styles from "@/components/MuseumPublic.module.css";
async function museumForPage(slug: string): Promise<Museum | null> {
  const existing = await getMuseum(slug);
  if (existing) return existing;
  const published = await getPublishedMuseum(slug);
  return published ? { ...published, kind: "museum", description: "", status: "review", venues: [], work_count: 0, holding_count: 0, on_view_count: 0, highlight_count: 0, cover: null } : null;
}
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const museum = await museumForPage((await params).slug);
  if (!museum) notFound();
  return pageMetadata(museum.name, plainDescription(museum.description, `Explore ${museum.name}, its artworks, exhibitions and guides in Artline.`), `/museums/${museum.slug}`);
}
async function PublishedArtworks({ slug, hasCatalogue }: { slug: string; hasCatalogue: boolean }) {
  const page = await getMuseumPublications(slug, "artwork").catch(() => null);
  if (!page) return <p role="status">Museum artworks could not be loaded. Reload to try again.</p>;
  if (!page.items.length) return hasCatalogue ? null : <p>Artworks will appear here when the museum publishes them.</p>;
  return <section className={styles.section}><div className={styles.sectionHeader}><h3>Published by the museum</h3><Link href={`/museums/${slug}/publications?kind=artwork`}>View all museum artworks</Link></div><p className={styles.note}>Artworks and information provided by verified museum staff.</p><MuseumPublicationCards slug={slug} items={page.items.slice(0, 6)} /></section>;
}
async function PublishedExhibitions({ slug }: { slug: string }) {
  const page = await getMuseumPublications(slug, "exhibition").catch(() => null);
  if (!page) return <p role="status">Museum exhibitions could not be loaded. Reload to try again.</p>;
  return page.items.length ? <><Link href={`/museums/${slug}/publications?kind=exhibition`}>View all exhibitions</Link><MuseumPublicationCards slug={slug} items={page.items.slice(0, 6)} /></> : <p>Museum announcements will appear here when published.</p>;
}
async function PublishedGuides({ slug }: { slug: string }) {
  const [prepared, published] = await Promise.all([getPreparedMuseumGuides(slug).catch(() => null), getMuseumPublications(slug, "guide").catch(() => null)]);
  return <>
    {prepared ? <PreparedMuseumGuides page={prepared} slug={slug} /> : <p role="status">Artline guides could not be loaded. Reload to try again.</p>}
    {published ? published.items.length ? <><div className={styles.sectionHeader}><h3>Published by the museum</h3><Link href={`/museums/${slug}/publications?kind=guide`}>View all museum guides</Link></div><MuseumPublicationCards slug={slug} items={published.items.slice(0, 6)} /></> : !prepared?.items.length && <p>Museum-authored guides will appear here when published.</p> : <p role="status">Museum guides could not be loaded. Reload to try again.</p>}
  </>;
}
export default async function MuseumPage({ params, searchParams }: { params: Promise<{ slug: string }>; searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { slug } = await params;
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(await searchParams)) {
    for (const item of Array.isArray(value) ? value : value === undefined ? [] : [value]) query.append(key, item);
  }
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || slug.length > 100) notFound();
  const [museum, profilePage, publishedGuides] = await Promise.all([museumForPage(slug), getMuseumPublications(slug, "profile").catch(() => null), getMuseumPublications(slug, "guide").catch(() => null)]);
  if (!museum) notFound();
  const profile = profilePage?.items[0], info = profile?.document;
  const visit = safeSourceURL(info?.visit_url || museum.venues[0]?.visit_url || museum.website_url);
  const description = info?.summary || museumDescription(museum.description);
  const guides = getMuseumGuideLinks(museum.slug);
  const collectionQuery = new URLSearchParams(query);
  collectionQuery.set("tab", "collection");
  return <main id="main-content" className={styles.page}>
    <StructuredData data={{ "@context": "https://schema.org", "@type": "CollectionPage", name: museum.name, description: description || undefined, url: absoluteURL(`/museums/${museum.slug}`) }} />
    <StructuredData data={breadcrumbs([{ name: "Artline", path: "/" }, { name: "Museums", path: "/museums" }, { name: museum.name, path: `/museums/${museum.slug}` }])} />
    <Link className={styles.back} href="/museums">Museums</Link>
    <header className={`${styles.hero} ${!museum.cover && !info?.image_url && !info?.image_id ? styles.heroTextOnly : ""}`}><div className={styles.heroText}><h1>{info?.title || museum.name}<MuseumWebsiteLink url={museum.website_url || visit} name={museum.name} /></h1>{museumLocations(museum).length > 0 && <p className={styles.place}>{museumLocations(museum).join(" / ")}</p>}{description?.split(/\n\s*\n/).map((paragraph, index) => <p key={index}>{paragraph}</p>)}<div className={styles.actions}><Link href={`/museums/${museum.slug}?${collectionQuery}#collection`}>Explore the collection</Link>{visit && visit !== "#" && <a href={visit} target="_blank" rel="noreferrer">Plan your visit</a>}</div></div>
      {(info?.image_url || info?.image_id) && profile ? <figure className={styles.heroImage}><div><PublicationImage item={profile} slug={slug} /></div><figcaption>{info.image_credit}</figcaption></figure> : museum.cover && <figure className={styles.heroImage}><Link href={`/museums/${slug}?work=${museum.cover.id}#collection`}><ArtworkImage work={museum.cover} large /></Link><figcaption>{museum.cover.title}{museum.cover.artists.length > 0 && ` — ${museum.cover.artists.map(a => a.name).join(", ")}`}. <a href={`/museums/${slug}?work=${museum.cover.id}#collection`}>Artwork and source</a></figcaption></figure>}
    </header>
    <MuseumGuideCallout guides={[
      ...guides.map(guide => ({ href: guidePath(guide.slug), title: guide.title, count: guide.count, languages: guide.locales.length })),
      ...(publishedGuides?.items ?? []).map(guide => ({ href: publicationPath(museum.slug, guide.id), title: guide.document.title })),
    ]} />
    {!profilePage && <p role="status">Museum information could not be loaded. Reload to try again.</p>}
    <MuseumPageTabs slug={slug} museumName={museum.name} initialSearch={query.size ? `?${query}` : ""} hasProfile={!!profile} panels={{
      collection: <div className={styles.collection}>
        {museum.work_count > 0 && <><p className={styles.note}>From Artline’s historical catalogue. Documented holdings do not guarantee current display.</p><MuseumDetail key={slug} slug={slug} initialMuseum={museum} embedded guides={guides.map(guide => ({ href: guidePath(guide.slug), title: guide.title }))} /></>}
        <Suspense fallback={<p role="status">Loading museum publications…</p>}><PublishedArtworks slug={slug} hasCatalogue={museum.work_count > 0} /></Suspense>
      </div>,
      exhibitions: <>
        <Suspense fallback={<p role="status">Loading museum exhibitions…</p>}><PublishedExhibitions slug={slug} /></Suspense>
        <p><Link href={`/exhibitions?institution=${museum.id}`}>Explore documented exhibition history</Link></p>
      </>,
      guides: <>
        <Suspense fallback={<p role="status">Loading museum guides…</p>}><PublishedGuides slug={slug} /></Suspense>
        <p><Link href="/guides">Explore Artline guides</Link></p>
      </>,
      visit: <div className={styles.visit}><div>
        {museumLocations(museum).map(location => <p key={location} className={styles.place}>{location}</p>)}
        {info?.body && <p>{info.body}</p>}{info?.address && <p>{info.address}</p>}{info?.hours && <p>{info.hours}</p>}
        {visit && visit !== "#" && <a href={visit} target="_blank" rel="noreferrer">Visit the official museum website</a>}
        <p className={styles.note}>Check the museum’s website for opening hours, tickets, and changes to displays.</p>
      </div><div><h3>Work at {museum.name}?</h3><p>Manage this page, share artworks and exhibitions, and publish guides for your visitors.</p><Link href={`/account/museums?q=${encodeURIComponent(museum.name)}`}>Open museum studio</Link></div></div>,
    }} />
  </main>;
}
