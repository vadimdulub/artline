import Image from "next/image";
import Link from "@/components/MemberLink";
import { notFound } from "next/navigation";
import { AtlasPageHeader } from "@/components/AtlasPageHeader";
import { getArtworkExhibitions, getExhibitionArtwork } from "@/lib/exhibitions-server";
import { exhibitionDates, exhibitionSource, participationLabel } from "@/lib/exhibitions";
import { pageMetadata } from "@/lib/seo";
import styles from "../../exhibitions.module.css";

type Props = { params: Promise<{ id: string }>; searchParams: Promise<{ after?: string }> };

export async function generateMetadata({ params }: Props) {
  const { id } = await params;
  const artwork = await getExhibitionArtwork(id);
  return pageMetadata(artwork?.title ?? "Exhibition artwork", "Artwork details and documented exhibition history.", `/exhibitions/artworks/${id}`, { index: false });
}

export default async function ExhibitionArtworkPage({ params, searchParams }: Props) {
  const { id } = await params;
  const { after = "" } = await searchParams;
  const artwork = await getExhibitionArtwork(id);
  if (!artwork) notFound();
  const appearances = await getArtworkExhibitions(id, after);
  if (!appearances) return <main id="main-content" className={styles.page}><h1>Check the exhibition history link</h1><Link href={`/exhibitions/artworks/${id}`}>Return to the artwork</Link></main>;
  return <main id="main-content" className={styles.page}>
    <p className={styles.meta}>Exhibition artwork</p>
    <AtlasPageHeader title={artwork.title || "Title not recorded"} description={artwork.creator || "Creator not recorded"} />
    <div className={styles.artworkOverview}>
      <div>
        {artwork.image && <figure className={styles.artworkFigure}><Image src={artwork.image} width={1000} height={800} alt={artwork.title || "Documented artwork"} unoptimized /><figcaption>{artwork.imageCredit}{artwork.imageLicense ? ` · ${artwork.imageLicense}` : ""}</figcaption></figure>}
        {!artwork.image && <p className={styles.lede}>Image not yet available for this artwork.</p>}
        <div className={styles.sources}>{artwork.artworkId && <Link href={`/all?selection=true&type=artwork&highlights=false&artwork_id=${artwork.artworkId}&item=${artwork.artworkId}&itemType=artwork`} prefetch={false}>Open in the artwork catalogue</Link>}<a href="#exhibition-history">Exhibition history ↓</a></div>
      </div>
      <aside className={styles.recordFacts} aria-label="Artwork details"><dl>
        <div><dt>Date</dt><dd>{artwork.date || "Date not recorded"}</dd></div>
        <div><dt>Medium</dt><dd>{artwork.medium || "Medium not recorded"}</dd></div>
        {artwork.dimensions && <div><dt>Dimensions</dt><dd>{artwork.dimensions}</dd></div>}
        {artwork.attribution && <div><dt>Object classification</dt><dd>{artwork.attribution}</dd></div>}
        <div><dt>Documented exhibitions</dt><dd>{artwork.appearanceCount}<small>Connections collected in this selection; this is not a complete lifetime exhibition history.</small></dd></div>
      </dl></aside>
    </div>
    {artwork.artists.length > 0 && <section className={styles.section} aria-labelledby="creators"><h2 id="creators">Artists &amp; makers</h2><ul className={styles.people}>{artwork.artists.map(person => <li key={person.id}><div><h3>{person.artist_slug ? <Link href={`/artists/${person.artist_slug}`} prefetch={false}>{person.name}</Link> : person.name}</h3><p className={styles.meta}>{person.role === "primary" ? "Artist" : person.role.replaceAll("_", " ")}</p><div className={styles.personActions}><Link href={`/exhibitions?${person.artist_id ? `artist=${person.artist_id}` : `person=${person.id}`}`} prefetch={false}>Artist’s exhibitions</Link></div></div></li>)}</ul></section>}
    <section className={styles.section} aria-labelledby="exhibition-history"><div className={styles.sectionHeading}><h2 id="exhibition-history">Exhibition history</h2><span>{appearances.total} documented {appearances.total === 1 ? "connection" : "connections"}</span></div>
      <ul className={styles.artworkHistory}>{appearances.items.map(item => <li key={item.id}><div className={styles.historyDate}>{item.startYear}</div><div><p className={styles.meta}>{participationLabel(item.participation)}{item.format === "online" ? " · Online exhibition" : ""}</p><h3><Link href={`/exhibitions/${item.exhibitionId}`} prefetch={false}>{item.title}</Link></h3><p>{exhibitionDates(item)}</p>{item.venues.length > 0 && <div className={styles.meta}>Exhibition venues{item.venues.map((venue, i) => <div key={i}>{venue.name}{venue.start_date ? ` · ${exhibitionDates({ startDate: venue.start_date, endDate: venue.end_date ?? null, dates: venue.start_date })}` : ""}</div>)}</div>}<p className={styles.note}>{item.evidence.note}</p></div></li>)}</ul>
      <nav className={styles.paging} aria-label="Artwork exhibition history pages">{after && <Link href={`/exhibitions/artworks/${id}#exhibition-history`} prefetch={false}>First exhibitions</Link>}{appearances.hasMore && <Link href={`/exhibitions/artworks/${id}?after=${encodeURIComponent(appearances.nextCursor)}#exhibition-history`} prefetch={false}>More exhibitions →</Link>}</nav>
    </section>
    <section className={styles.section} aria-labelledby="source-record"><h2 id="source-record">Catalogue record</h2><p className={styles.note}>{exhibitionSource(artwork.provider)} · Object {artwork.sourceArtworkID}</p><p className={styles.note}>{artwork.identityBasis}</p>{artwork.sourceCaption && <details className={styles.caption}><summary>Original catalogue caption</summary><p>{artwork.sourceCaption}</p></details>}</section>
  </main>;
}
