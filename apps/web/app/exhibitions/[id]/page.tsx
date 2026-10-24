import { ExhibitionImage } from "@/components/ExhibitionImage";
import { ExhibitionParticipant } from "@/components/ExhibitionParticipant";
import Link from "@/components/MemberLink";
import { notFound } from "next/navigation";
import { AtlasPageHeader } from "@/components/AtlasPageHeader";
import { getExhibition, getExhibitionEntries } from "@/lib/exhibitions-server";
import { exhibitionDates, exhibitionSource, exhibitionState, participationLabel, exhibitionArtworkPath } from "@/lib/exhibitions";
import { pageMetadata } from "@/lib/seo";
import styles from "../exhibitions.module.css";

type Props = { params: Promise<{ id: string }>; searchParams: Promise<{ after?: string; participation?: string }> };
export async function generateMetadata({ params, searchParams }: Props) {
  const { id } = await params; const exhibition = await getExhibition(id);
  return pageMetadata(exhibition?.title ?? "Exhibition", "Explore the artworks, artists and ideas of this exhibition.", `/exhibitions/${id}`, { index: Boolean(exhibition) && !exhibition?.localStudy && !(await searchParams).after });
}
export default async function ExhibitionPage({ params, searchParams }: Props) {
  const { id } = await params; const { after = "", participation = "" } = await searchParams;
  const exhibition = await getExhibition(id);
  if (!exhibition) notFound();
  const entries = await getExhibitionEntries(id, after, participation);
  if (!entries) return <main id="main-content" className={styles.page}><h1>Check the artwork page link</h1><Link href={`/exhibitions/${id}`}>Return to the exhibition</Link></main>;
  const research = exhibition.research;
  const artworkQuery = new URLSearchParams(participation ? { participation } : {});
  const firstArtworks = `/exhibitions/${id}${artworkQuery.size ? `?${artworkQuery}` : ""}#artworks`;
  artworkQuery.set("after", entries.nextCursor);
  return <main id="main-content" className={styles.page}>
    <AtlasPageHeader title={exhibition.title} description={exhibitionDates(exhibition)} />
    <nav className={styles.sectionNav} aria-label="On this exhibition page"><a href="#artworks">Artworks <span>{exhibition.entryCount}</span></a><a href="#overview">About</a><a href="#participants">Artists <span>{exhibition.participantCount}</span></a><a href="#references">Record notes</a></nav>
    <section className={styles.gallerySection} aria-labelledby="artworks">
      <h2 id="artworks" className="sr-only">Artworks in the exhibition</h2>
      {exhibition.participationCounts && <nav className={styles.artworkFilters} aria-label="Artwork evidence"><Link href={`/exhibitions/${id}#artworks`} aria-current={!participation ? "page" : undefined} prefetch={false}>All documented <span>{exhibition.entryCount}</span></Link><Link href={`/exhibitions/${id}?participation=exhibited#artworks`} aria-current={participation === "exhibited" ? "page" : undefined} prefetch={false}>Recorded as exhibited <span>{exhibition.participationCounts.exhibited ?? 0}</span></Link></nav>}
      <ul className={styles.gallery}>{entries.items.map((entry, index) => { const href = exhibitionArtworkPath(entry); const picture = <ExhibitionImage src={entry.image} width={entry.imageWidth || 700} height={entry.imageHeight || 700} alt={entry.title || "Exhibition artwork"} eager={index < 3} />; return <li key={entry.id} id={`work-${entry.id}`}>
        <figure><div className={styles.galleryImage}>{href ? <Link href={href} prefetch={false} aria-label={`View ${entry.title || "artwork"}`}>{picture}</Link> : picture}</div></figure>
        <div className={styles.entryText}><p className={styles.meta}>{entry.creator || "Creator not recorded"}</p><h3>{href ? <Link href={href} prefetch={false}>{entry.title || "Title not recorded"}</Link> : entry.title || "Title not recorded"}</h3><p className={styles.meta}>{entry.date || "Date not recorded"}</p></div>
        <details className={styles.caption}><summary>Details &amp; image credit</summary>{entry.medium && <p>{entry.medium}</p>}<p>{participationLabel(entry.participation)}{entry.catalogueNumber ? ` · Catalogue ${entry.catalogueNumber}` : ""}{entry.sourcePage ? ` · Page ${entry.sourcePage}` : ""}</p>{entry.participationEvidence && <p>{entry.participationEvidence.note}</p>}{entry.sourceCaption && <p>{entry.sourceCaption}</p>}{entry.image && <p>{entry.imageCredit}{entry.imageLicense ? ` · ${entry.imageLicense}` : ""}</p>}</details>
      </li>; })}</ul>
      {!entries.items.length && <p className={styles.note}>{participation ? "Object-level exhibition evidence has not yet been established for these works. Choose All documented to see the exhibition list." : "An artwork list has not yet been collected for this exhibition."}</p>}
      <nav className={styles.paging} aria-label="Exhibited artwork pages">{after && <Link href={firstArtworks} prefetch={false}>First artwork page</Link>}{entries.hasMore && <Link href={`/exhibitions/${id}?${artworkQuery}#artworks`} prefetch={false}>More artworks →</Link>}</nav>
    </section>
    <div id="overview" className={styles.overview}>
      <section aria-labelledby="ideas"><h2 id="ideas">About the exhibition</h2>
        {research ? <><p className={styles.lede}>{research.overview}</p>{research.excerpt && <blockquote className={styles.quote}><p>“{research.excerpt}”</p><cite>Exhibition description · {exhibitionSource(exhibition.sources[0]?.provider || "")}</cite></blockquote>}
          {research.concepts.length > 0 && <div className={styles.topics}>{research.concepts.map(topic => <Link key={topic} href={`/exhibitions?theme=${encodeURIComponent(topic)}`} prefetch={false}>{topic}</Link>)}</div>}
        </> : <p className={styles.note}>The archive documents this exhibition’s dates and participants. A curatorial description has not yet been added.</p>}
        {exhibition.state !== "held" && <p className={styles.note}>The event’s occurrence or dates require further verification. {exhibition.stateBasis}</p>}
        {exhibition.alternateTitles.length > 0 && <p className={styles.note}>Also recorded as: {exhibition.alternateTitles.join(" · ")}</p>}
      </section>
      <aside className={styles.recordFacts} aria-label="Exhibition details"><dl><div><dt>Event</dt><dd>{exhibitionState(exhibition.state)}{exhibition.format === "online" ? " online" : ""}</dd></div><div><dt>Venue &amp; presenter</dt><dd>{exhibition.venues.length ? exhibition.venues.map((venue, i) => <div key={venue.id ?? i}>{venue.museum_slug ? <Link href={`/museums/${venue.museum_slug}`} prefetch={false}>{venue.name}</Link> : venue.name || "Venue not identified"}<small>{[venue.city, venue.country].filter(Boolean).join(", ")}</small>{venue.start_date && <small>{exhibitionDates({ startDate: venue.start_date, endDate: venue.end_date ?? null, dates: venue.start_date })}</small>}</div>) : research?.presenter || "Venue not recorded"}</dd></div><div><dt>Artwork coverage</dt><dd>{research?.publicListComplete ? `${research.publicListTotal} of ${research.publicListTotal} public listings` : exhibition.checklistState === "complete" ? "Complete checklist" : "Partial exhibition record"}<small>{research?.scope || "The final exhibition checklist has not been established."}</small></dd></div></dl></aside>
    </div>
    <section className={styles.section} aria-labelledby="participants"><div className={styles.sectionHeading}><h2 id="participants">Artists &amp; people</h2><span>{exhibition.participantCount.toLocaleString("en-US")} participants</span></div><ul className={styles.people}>{exhibition.participants.map(person => <ExhibitionParticipant key={person.id} person={person} showHistory={exhibition.expandedStudy || exhibition.localStudy} />)}</ul>{!exhibition.participants.length && <p className={styles.note}>Participants have not yet been identified in this record.</p>}{exhibition.participantCount > exhibition.participants.length && <p className={styles.note}>Showing {exhibition.participants.length} of {exhibition.participantCount.toLocaleString("en-US")} participant records.</p>}</section>
    {Boolean(exhibition.related?.length) && <section className={styles.section} aria-labelledby="related"><h2 id="related">More exhibitions with these artists</h2><ul className={styles.related}>{exhibition.related!.map(item => <li key={item.id}><span>{item.startYear}</span><Link href={`/exhibitions/${item.id}`} prefetch={false}>{item.title}</Link></li>)}</ul></section>}
    <section id="references" className={styles.section} aria-label="Record notes"><details className={styles.evidence}><summary>Exhibition record &amp; evidence</summary><p>“Recorded as exhibited” follows an object’s exhibition history. “Listed in exhibition” follows a public artwork listing. Exhibition participation, ownership and present display are separate facts.</p>{research?.conceptBasis && <p>{research.conceptBasis}</p>}<ul>{exhibition.sources.map(source => <li key={`${source.provider}-${source.source_record_id}`}>{exhibitionSource(source.provider)} · Record {source.source_record_id}{source.retrieved_at && <small>Checked {source.retrieved_at.slice(0, 10)}</small>}</li>)}</ul>{exhibition.publications.length > 0 && <ul className={styles.publications}>{exhibition.publications.map((publication, i) => <li key={i}>{publication.title || publication.kind.replaceAll("_", " ")}{publication.author && <span>{publication.author}</span>}</li>)}</ul>}</details></section>
  </main>;
}
