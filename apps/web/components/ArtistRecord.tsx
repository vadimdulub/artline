"use client";
import Link from "next/link";
import { ArtworkDialog, ArtworkImage, ArtworkViewer, ShareWorkLink } from "./ArtworkViewer";
import { RecordArrows, type RecordNavigation } from "./RecordNavigation";
import { ArtworkLocation } from "./ArtworkLocation";
import { ArtworkDescription } from "./ArtworkDescription";
import { EvidenceNote } from "./EvidenceNote";
import { useEffect, useRef, useState, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { countryName, safeSourceURL } from "@/lib/api";
import type { ArtistDetail, Artwork, Citation } from "@/lib/types";

export function SourceList({ citations }: { citations: Citation[] }) {
  return <ul className="source-list">{citations.map((source, index) => <li key={index}><a href={safeSourceURL(source.source_url)} target="_blank" rel="noreferrer">{source.source_name}</a><span>{source.field_name.replaceAll("_", " ")}</span>{source.evidence_note && <EvidenceNote note={source.evidence_note} />}</li>)}</ul>;
}
function WorkBrowserContent({ render, onSelectWork, selectedID }: { render: (choose: (id: string) => void, selectedID?: string) => ReactNode; onSelectWork: (id: string) => void; selectedID?: string }) {
  return render(onSelectWork, selectedID);
}
function ArtistContext({ collapsed, children }: { collapsed: boolean; children: ReactNode }) {
  return collapsed ? <details className="chronology-biography"><summary>About the painter and influences</summary>{children}</details> : children;
}
function PainterArtworkDetails({ artist, work }: { artist: ArtistDetail; work: Artwork }) {
  return <>
        <dl><div><dt>Dating</dt><dd>{({ exact: "Exact year", exact_year: "Exact year", circa: "Approximate", range: "Date range", circa_range: "Approximate date range", decade: "Within this decade", century: "Within this century", before: "Before this date", after: "After this date", unknown: "Uncertain" } as Record<string, string>)[work.date_precision] ?? work.date_precision.replaceAll("_", " ")}</dd></div><div><dt>Made in</dt><dd>{work.creation_place_display ?? "Not yet established"}{!work.creation_place_display && work.creation_place_unknown_reason && <small className="metadata-note">{work.creation_place_unknown_reason}</small>}</dd></div><div><dt>Held at</dt><dd>{work.current_location_text ?? "Location not recorded"}</dd></div><div><dt>Medium</dt><dd>{work.medium_text ?? work.work_type.replaceAll("_", " ")}</dd></div><div><dt>Dimensions</dt><dd>{work.dimensions_text ?? "Not recorded in this catalogue"}</dd></div>{work.accession_number && <div><dt>Collection no.</dt><dd>{work.accession_number}</dd></div>}<div><dt>Attribution</dt><dd>{({ primary: "By the artist", workshop: "Workshop", attributed_to: "Attributed to the artist", follower_of: "Follower of the artist", formerly_attributed_to: "Formerly attributed to the artist", circle_of: "Circle of the artist" } as Record<string, string>)[work.attribution_role] ?? work.attribution_role.replaceAll("_", " ")}</dd></div><div><dt>Image rights</dt><dd>{work.license_label ?? work.rights_status?.replaceAll("_", " ") ?? "Not recorded"}{work.license_url && <a className="license-link" href={safeSourceURL(work.license_url)} target="_blank" rel="noreferrer">License details</a>}</dd></div></dl>
        {work.attribution_text && <p className="image-credit">{work.attribution_text}</p>}
        <ArtworkLocation work={work} />
        <ArtworkDescription key={work.id} work={work} detailPath={`artists/${artist.slug}/works/${work.id}`} />
        {work.location_checked_at && <p className="image-credit">Location checked {new Intl.DateTimeFormat("en", { dateStyle: "medium", timeZone: "UTC" }).format(new Date(work.location_checked_at))}. This does not indicate whether the work is on display.</p>}
        <details><summary>Artwork sources</summary><SourceList citations={work.citations} />{safeSourceURL(work.source_page_url) && <a href={safeSourceURL(work.source_page_url)} target="_blank" rel="noreferrer">Image source</a>}</details>
  </>;
}
export function ArtistRecord({ artist, essay, workId, onSelectWork, embedded = false, artworks, linkedWork, workBrowser, workMessage, navigation, pageWork, gallery = false }: { artist: ArtistDetail; essay?: string | null; workId?: string | null; onSelectWork: (id: string) => void; embedded?: boolean; artworks?: Artwork[]; linkedWork?: Artwork; workBrowser?: (choose: (id: string) => void, selectedID?: string) => ReactNode; workMessage?: ReactNode; navigation?: RecordNavigation; pageWork?: Artwork | null; gallery?: boolean }) {
  const works = artworks ?? artist.artworks;
  // Keep canonical artwork links available in the server-rendered painter page
  // while the complete, bounded chronology is loading.
  const artworkPages = works.length ? works : artist.artworks;
  const collections = [...new Map(works.flatMap(work => work.holding ? [[work.holding.id, work.holding] as const] : [])).values()];
  const selectedIndex = workId ? works.findIndex((item) => item.id === workId) : 0;
  const work = workId ? (linkedWork?.id === workId ? linkedWork : works[selectedIndex]) : works[0];
  const headingWork = pageWork === undefined ? (workId ? work : null) : pageWork;
  const creator = <><Link href={`/artists/${artist.slug}`}>{artist.display_name}</Link>{work && work.attribution_role !== "primary" && <small className="artwork-creator-role">{work.attribution_role.replaceAll("_", " ")}</small>}</>;
  const workNavigation = navigation ?? { previous: selectedIndex>0 ? () => onSelectWork(works[selectedIndex-1].id) : undefined, next: selectedIndex>=0 && selectedIndex<works.length-1 ? () => onSelectWork(works[selectedIndex+1].id) : undefined };
  const [viewer, setViewer] = useState({ id: workId, open: Boolean(gallery && workId) });
  const viewerOpen = viewer.id === workId ? viewer.open : Boolean(workId);
  const [fullBiography, setFullBiography] = useState(!embedded);
  const artworkPanel = useRef<HTMLElement>(null);
  const artworkHeading = useRef<HTMLHeadingElement>(null);
  const pendingWorkFocus = useRef(false);
  const selectedWorks = useRef<HTMLElement>(null);
  const shortBiography = artist.biography_md?.split(/(?<=\.)\s+/).slice(0, 2).join(" ") ?? "";
  function chooseWork(id: string) {
    if (gallery) { setViewer({ id, open: true }); onSelectWork(id); return; }
    pendingWorkFocus.current = true;
    onSelectWork(id);
    // Selecting the current work does not change props, but still opens its record.
    if (id === work?.id) focusWork();
  }
  function focusWork() {
    pendingWorkFocus.current = false;
    artworkHeading.current?.focus({ preventScroll: true });
    artworkPanel.current?.scrollIntoView({ block: "start", behavior: "instant" });
  }
  useEffect(() => {
    if (pendingWorkFocus.current) focusWork();
  }, [work?.id]);
  function returnToWorks() {
    (selectedWorks.current?.querySelector<HTMLButtonElement>(".work-card[aria-pressed=true]") ?? selectedWorks.current?.querySelector<HTMLElement>("h2"))?.focus({ preventScroll: true });
    selectedWorks.current?.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth", block: "start" });
  }
  return <div className={`artist-record${gallery ? " artist-gallery-record" : ""}`}>
    <div className="artist-main">
      <header className="artist-heading">
        {!embedded && headingWork ? <><h1 style={{ fontSize: "clamp(1.75rem, 3vw, 2.75rem)", lineHeight: 1.12 }}>{headingWork.title}</h1><p><Link href={`/artists/${artist.slug}`}>{artist.display_name}</Link> · {headingWork.date_display}</p></> : <h1>{artist.display_name}</h1>}<p className="artist-dates">{!embedded && headingWork ? `${artist.display_name}: ${artist.timeline_display}` : artist.timeline_display}</p>
        {embedded && <Link className="text-link full-painter-link" href={`/artists/${artist.slug}`}>Open full painter record <span aria-hidden="true">↗</span></Link>}
      </header>
      <section ref={selectedWorks} className="selected-works" aria-labelledby={`works-${artist.id}`}>
        {workBrowser ? <WorkBrowserContent render={workBrowser} onSelectWork={chooseWork} selectedID={gallery ? workId ?? undefined : work?.id} /> : <><div className="section-heading"><h2 id={`works-${artist.id}`}>Selected works</h2><span>{works.length ? `${works.length} records · choose a work for details` : "Selection in progress"}</span></div>
        {works.length ? <div className={embedded ? "works-list" : "works-strip"} style={{ ["--work-columns" as string]: Math.min(5, works.length) }}>{works.map((item, index) => <button key={item.id} className={`work-card${embedded ? " work-row" : ""}${item.id === work?.id ? " is-selected" : ""}`} type="button" aria-pressed={item.id === work?.id} onClick={() => chooseWork(item.id)}><ArtworkImage work={item} number={embedded ? index + 1 : undefined} />{embedded ? <span className="work-row-copy"><span className="work-date">{item.date_display}</span><span className="work-title">{item.title}</span><span className="work-location">{item.creation_place_display ? `Made in ${item.creation_place_display}` : "Creation place not established"}</span><span className="work-location">{item.current_location_text ? `Held at ${item.current_location_text}` : "Current location not recorded"}</span></span> : <><span className="work-title">{item.title}</span><span className="work-date">{item.date_display}</span></>}</button>)}</div> : <div className="quiet-empty"><h3>A selection takes shape</h3><p>Works will appear here as dates, locations, and sources are reviewed.</p><Link href="/catalogue">Explore the catalogue</Link></div>}
        </>}
      </section>
      <section className="painter-background" aria-label="About the painter">
        <div className="record-classification"><span><i style={{ background: artist.movement.color }} />{artist.movement.name}</span>{artist.countries.map(code => <span key={code}>{countryName(code)}</span>)}</div>
        {artist.aliases.length > 0 && <details className="artist-aliases"><summary>Other names ({artist.aliases.length})</summary><p>{artist.aliases.join(", ")}</p></details>}
      <ArtistContext collapsed={Boolean(workBrowser)}><section className={`artist-context${!artist.influences.length ? " research-context" : ""}`} aria-label="Biography and influences">
        <div className="biography">{artist.biography_md ? <><ReactMarkdown remarkPlugins={[remarkGfm]}>{fullBiography ? artist.biography_md : shortBiography}</ReactMarkdown>{shortBiography !== artist.biography_md && <button className="biography-toggle" aria-expanded={fullBiography} onClick={() => setFullBiography(value => !value)}>{fullBiography ? "Show less" : "Read full biography"}</button>}</> : <p className="research-note">Biography and influences are still being researched.</p>}</div>
        {artist.influences.length > 0 ? (["incoming", "outgoing"] as const).map(direction => {
          const claims = artist.influences.filter(item => item.direction === direction);
          return <div key={direction} className={`influence-column ${direction}`}><h2>{direction === "incoming" ? "Influenced by" : "Later influence"}</h2>{claims.length ? <ul>{claims.map(claim => <li key={claim.id}>{claim.slug ? <Link href={`/artists/${claim.slug}`}>{claim.name}</Link> : claim.name}<small>{claim.evidence_level.replaceAll("_", " ")}</small><details><summary>Evidence</summary><p>{claim.evidence_note}</p><SourceList citations={claim.citations} /></details></li>)}</ul> : <p className="muted">Connections are still being researched.</p>}</div>;
        }) : artist.biography_md ? <p className="research-note influence-research">Influences are still being researched; no connections are asserted yet.</p> : null}
      </section></ArtistContext>
      {collections.length > 0 && <nav className="painter-collections museum-tags" aria-label="Collections for these artworks"><h2>Explore these collections</h2><ul>{collections.map(collection => <li key={collection.id}><Link href={`/museums/${collection.slug}?artist=${artist.slug}`}>{collection.name}</Link></li>)}</ul></nav>}
      </section>
      {!embedded && artworkPages.length > 0 && <nav className="painter-collections" aria-label="Artwork pages"><h2>Explore artwork records</h2><ul>{artworkPages.map(item => <li key={item.id}><Link href={`/artists/${artist.slug}/works/${item.id}`} prefetch={false}>{item.title}</Link></li>)}</ul></nav>}
      {essay && <details className="essay-section"><summary>Read the painter essay</summary><article className="essay"><ReactMarkdown remarkPlugins={[remarkGfm]}>{essay}</ReactMarkdown></article></details>}
      <details className="sources-section"><summary>Sources & research notes <span>{artist.citations.length}</span></summary><SourceList citations={artist.citations} /></details>
    </div>
    {!gallery && (!embedded || work || workMessage) && <aside ref={artworkPanel} className="artwork-panel" aria-labelledby="artwork-record-title">
      <div className="artwork-panel-heading"><h2 className="artwork-creator" ref={artworkHeading} tabIndex={-1} id="artwork-record-title"><span className="sr-only">Artwork record: </span>{creator}</h2>{work && <RecordArrows navigation={workNavigation} noun="artwork" />}</div>
      {work ? <div className="artwork-details">
        <ArtworkViewer work={work} creator={creator} navigation={workNavigation} />
        <h3 aria-live="polite">{work.title}</h3>{work.alternate_title && <p>{work.alternate_title}</p>}<p className="artwork-date">{work.date_display}</p>
        <div className="artwork-panel-actions">{embedded && <button type="button" onClick={returnToWorks}>{workBrowser ? "← Artworks by year" : "← Selected works"}</button>}<ShareWorkLink key={work.id} path={`/artists/${artist.slug}/works/${work.id}`} /></div>
        {selectedIndex>=0 && <p className="image-credit">{selectedIndex + 1} / {works.length}{workBrowser ? " on this page" : ""}</p>}
        <PainterArtworkDetails artist={artist} work={work} />
      </div> : workMessage ?? <div className="artwork-waiting"><span aria-hidden="true">▧</span><h3>A closer look</h3><p>Select an artwork to explore its date, origin, collection, and sources.</p></div>}
    </aside>}
    {gallery && workMessage && <div className="gallery-work-message">{workMessage}</div>}
    {gallery && viewerOpen && work && <ArtworkDialog work={work} creator={creator} navigation={workNavigation} close={() => setViewer({ id: workId, open: false })} details={<><PainterArtworkDetails artist={artist} work={work} /><ShareWorkLink path={`/artists/${artist.slug}/works/${work.id}`} /></>} />}
    {gallery && pageWork && <noscript><article className="artwork-details standalone-artwork"><ArtworkImage work={pageWork} large /><h3>{pageWork.title}</h3><p>{pageWork.date_display}</p><PainterArtworkDetails artist={artist} work={pageWork} /></article></noscript>}

  </div>;
}
