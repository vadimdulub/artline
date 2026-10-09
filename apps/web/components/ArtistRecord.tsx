"use client";
import Link from "next/link";
import { artworkDate, displayMetadata } from "@/lib/display-metadata";
import { ArtworkDialog, ArtworkImage, ArtworkViewer, ShareWorkLink } from "./ArtworkViewer";
import { RecordArrows, type RecordNavigation } from "./RecordNavigation";
import { ArtworkLocation } from "./ArtworkLocation";
import { ArtworkDescription } from "./ArtworkDescription";
import { ArtistBiography } from "./ArtistBiography";
import { updateQuery } from "@/lib/url-state";
import { cleanEditorialBiography } from "@/lib/biography";
import { ArtworkFacts } from "./ArtworkFacts";
import { useEffect, useRef, useState, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { countryName, safeSourceURL } from "@/lib/api";
import type { ArtistDetail, Artwork, Citation } from "@/lib/types";

export function SourceList({ citations }: { citations: Citation[] }) {
  return <ul className="source-list">{citations.map((source, index) => <li key={index}><a href={safeSourceURL(source.source_url)} target="_blank" rel="noreferrer">{source.source_name}</a></li>)}</ul>;
}
function WorkBrowserContent({ render, onSelectWork, selectedID }: { render: (choose: (id: string) => void, selectedID?: string) => ReactNode; onSelectWork: (id: string) => void; selectedID?: string }) {
  return render(onSelectWork, selectedID);
}
function ArtistContext({ collapsed, children }: { collapsed: boolean; children: ReactNode }) {
  return collapsed ? <details className="chronology-biography"><summary>About the painter</summary>{children}</details> : children;
}
function PainterArtworkDetails({ artist, work }: { artist: ArtistDetail; work: Artwork }) {
  return <>
        <ArtworkFacts work={work} attribution />
        {work.attribution_text && <p className="image-credit">{work.attribution_text}</p>}
        <ArtworkLocation work={work} />
        <ArtworkDescription key={work.id} work={work} detailPath={`artists/${artist.slug}/works/${work.id}`} />
        {work.location_checked_at && <p className="image-credit">Location checked {new Intl.DateTimeFormat("en", { dateStyle: "medium", timeZone: "UTC" }).format(new Date(work.location_checked_at))}. This does not indicate whether the work is on display.</p>}
        {(work.citations.length > 0 || safeSourceURL(work.source_page_url)) && <details><summary>Artwork sources</summary><SourceList citations={work.citations} />{safeSourceURL(work.source_page_url) && <a href={safeSourceURL(work.source_page_url)} target="_blank" rel="noreferrer">Image source</a>}</details>}
  </>;
}
export function ArtistRecord({ artist, essay, workId, onSelectWork, embedded = false, artworks, linkedWork, defaultWork, workBrowser, workMessage, navigation, pageWork, gallery = false }: { artist: ArtistDetail; essay?: string | null; workId?: string | null; onSelectWork: (id: string) => void; embedded?: boolean; artworks?: Artwork[]; linkedWork?: Artwork; defaultWork?: Artwork; workBrowser?: (choose: (id: string) => void, selectedID?: string) => ReactNode; workMessage?: ReactNode; navigation?: RecordNavigation; pageWork?: Artwork | null; gallery?: boolean; }) {
  const works = artworks ?? artist.artworks;
  // Keep canonical artwork links available in the server-rendered painter page
  // while the complete, bounded chronology is loading.
  const artworkPages = works.length ? works : artist.artworks;
  const collections = artist.collections ?? [];
  const hasBiography = Boolean(artist.reference_biography?.text.trim() || cleanEditorialBiography(artist.biography_md ?? ""));
  const selectedIndex = workId || defaultWork ? works.findIndex((item) => item.id === (workId || defaultWork?.id)) : 0;
  const work = workId ? (linkedWork?.id === workId ? linkedWork : works[selectedIndex]) : defaultWork ?? works[0];
  const headingWork = pageWork === undefined ? (workId ? work : null) : pageWork;
  const creator = <><Link href={`/artists/${artist.slug}`}>{artist.display_name}</Link>{work && work.attribution_role !== "primary" && <small className="artwork-creator-role">{work.attribution_role.replaceAll("_", " ")}</small>}</>;
  const workNavigation = navigation ?? { previous: selectedIndex>0 ? () => onSelectWork(works[selectedIndex-1].id) : undefined, next: selectedIndex>=0 && selectedIndex<works.length-1 ? () => onSelectWork(works[selectedIndex+1].id) : undefined };
  const [viewer, setViewer] = useState({ id: workId, open: Boolean(gallery && workId) });
  const viewerOpen = viewer.id === workId ? viewer.open : Boolean(workId);
  const artworkPanel = useRef<HTMLElement>(null);
  const artworkHeading = useRef<HTMLHeadingElement>(null);
  const pendingWorkFocus = useRef(false);
  const selectedWorks = useRef<HTMLElement>(null);
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
  const background = <section className="painter-background" aria-label="About the painter">
        <div className="record-classification"><span><i style={{ background: artist.movement.color }} />{artist.movement.name}</span>{artist.countries.map(code => <span key={code}>{countryName(code)}</span>)}</div>
        {artist.aliases.length > 0 && <details className="artist-aliases"><summary>Other names ({artist.aliases.length})</summary><p>{artist.aliases.join(", ")}</p></details>}
      {(hasBiography || artist.influences.length > 0) && <ArtistContext collapsed={embedded && Boolean(workBrowser)}><section className={`artist-context${!artist.influences.length ? " research-context" : ""}`} aria-label="Biography and influences">
        <ArtistBiography artist={artist} embedded={embedded} />
        {(["incoming", "outgoing"] as const).map(direction => {
          const claims = artist.influences.filter(item => item.direction === direction);
          if (!claims.length) return null;
          return <div key={direction} className={`influence-column ${direction}`}><h2>{direction === "incoming" ? "Influenced by" : "Later influence"}</h2><ul>{claims.map(claim => <li key={claim.id}>{claim.slug ? <Link href={`/artists/${claim.slug}`}>{claim.name}</Link> : claim.name}<small>{claim.evidence_level.replaceAll("_", " ")}</small><details><summary>Evidence</summary><p>{claim.evidence_note}</p><SourceList citations={claim.citations} /></details></li>)}</ul></div>;
        })}
      </section></ArtistContext>}

      </section>;
  const artworkRecord = !gallery && (!embedded || work || workMessage) ? <aside ref={artworkPanel} className={`artwork-panel${embedded ? " painter-preview" : ""}`} aria-label={embedded ? "Artwork preview" : undefined} aria-labelledby={embedded ? undefined : "artwork-record-title"}>
      {!embedded && <div className="artwork-panel-heading"><h2 className="artwork-creator" ref={artworkHeading} tabIndex={-1} id="artwork-record-title">{creator}</h2>{work && <RecordArrows navigation={workNavigation} noun="artwork" />}</div>}
      {work ? <div className="artwork-details">
        <ArtworkViewer work={work} creator={creator} navigation={workNavigation} />
        {embedded ? <>
          <div className="painter-preview-caption"><div><h3 ref={artworkHeading} tabIndex={-1} aria-live="polite">{work.title}</h3>{artworkDate(work) && <p className="artwork-date">{artworkDate(work)}</p>}</div><RecordArrows navigation={workNavigation} noun="artwork" /></div>
          {work.current_location_text && <p className="painter-preview-holding">Held at {work.current_location_text}</p>}
          <div className="painter-preview-actions"><button type="button" onClick={returnToWorks}>Browse artworks</button><details className="preview-work-details" key={work.id}><summary>Artwork details</summary><div>{work.alternate_title && <p>{work.alternate_title}</p>}<PainterArtworkDetails artist={artist} work={work} /><ShareWorkLink path={`/artists/${artist.slug}/works/${work.id}`} /></div></details></div>
        </> : <>
          <h3 aria-live="polite">{work.title}</h3>{work.alternate_title && <p>{work.alternate_title}</p>}{artworkDate(work) && <p className="artwork-date">{artworkDate(work)}</p>}
          <div className="artwork-panel-actions"><ShareWorkLink key={work.id} path={`/artists/${artist.slug}/works/${work.id}`} /></div>
          {selectedIndex>=0 && <p className="image-credit">{selectedIndex + 1} / {works.length}{workBrowser ? " on this page" : ""}</p>}
          <PainterArtworkDetails artist={artist} work={work} />
        </>}
      </div> : workMessage ?? <div className="artwork-waiting"><span aria-hidden="true">▧</span><h3>A closer look</h3><p>Select an artwork to explore its date, origin, collection, and sources.</p></div>}
    </aside> : null;
  return <div className={`artist-record${gallery ? " artist-gallery-record" : ""}`}>
    <div className="artist-main">
      <header className="artist-heading">
        {!embedded && headingWork ? <><h1 style={{ fontSize: "clamp(1.75rem, 3vw, 2.75rem)", lineHeight: 1.12 }}>{headingWork.title}</h1><p><Link href={`/artists/${artist.slug}`}>{artist.display_name}</Link>{artworkDate(headingWork) && <> · {artworkDate(headingWork)}</>}</p></> : <h1>{artist.display_name}</h1>}<p className="artist-dates">{!embedded && headingWork ? `${artist.display_name}: ${artist.timeline_display}` : artist.timeline_display}</p>
        {embedded && <Link className="text-link full-painter-link" href={`/artists/${artist.slug}`}>Open full painter record <span aria-hidden="true">↗</span></Link>}
      </header>
      {embedded && artworkRecord}
      {gallery && !workId && defaultWork && <section className="painter-key-artwork" aria-label="Key artwork">
        <ArtworkViewer work={defaultWork} creator={creator} />
        <div><p className="eyebrow">Selected artwork</p><h2>{defaultWork.title}</h2>{artworkDate(defaultWork) && <p className="artwork-date">{artworkDate(defaultWork)}</p>}{defaultWork.holding && <p className="painter-preview-holding">{defaultWork.holding.name}</p>}<button type="button" className="text-link" onClick={() => chooseWork(defaultWork.id)}>Explore artwork <span aria-hidden="true">↗</span></button></div>
      </section>}
      {!embedded && <nav className="artist-section-links" aria-label="Artist sections"><a href={`#works-${artist.id}`}>Artworks{artist.artwork_count !== undefined && ` (${artist.artwork_count.toLocaleString("en-GB")})`}</a>{hasBiography && <a href={`#biography-${artist.id}`}>Biography</a>}{collections.length > 0 && <a href={`#collections-${artist.id}`}>Museums</a>}{artist.citations.length > 0 && <a href={`#sources-${artist.id}`}>Sources</a>}</nav>}
      {!embedded && background}
      <section ref={selectedWorks} className="selected-works" aria-labelledby={`works-${artist.id}`}>
        {workBrowser ? <WorkBrowserContent render={workBrowser} onSelectWork={chooseWork} selectedID={gallery ? workId ?? undefined : work?.id} /> : <><div className="section-heading"><h2 id={`works-${artist.id}`}>Selected works</h2><span>{works.length ? `${works.length} records · choose a work for details` : ""}</span></div>
        {works.length ? <div className={embedded ? "works-list" : "works-strip"} style={{ ["--work-columns" as string]: Math.min(5, works.length) }}>{works.map((item, index) => <button key={item.id} className={`work-card${embedded ? " work-row" : ""}${item.id === work?.id ? " is-selected" : ""}`} type="button" aria-pressed={item.id === work?.id} onClick={() => chooseWork(item.id)}><ArtworkImage work={item} number={embedded ? index + 1 : undefined} />{embedded ? <span className="work-row-copy">{artworkDate(item) && <span className="work-date">{artworkDate(item)}</span>}<span className="work-title">{item.title}</span>{displayMetadata(item.creation_place_display) && <span className="work-location">Made in {item.creation_place_display}</span>}{displayMetadata(item.current_location_text) && <span className="work-location">Held at {item.current_location_text}</span>}</span> : <><span className="work-title">{item.title}</span>{artworkDate(item) && <span className="work-date">{artworkDate(item)}</span>}</>}</button>)}</div> : <div className="quiet-empty"><h3>No artworks in this selection</h3><Link href="/catalogue">Explore the catalogue</Link></div>}
        </>}
      </section>
      {embedded && background}
      {!embedded && collections.length > 0 && <section className="artist-collections" id={`collections-${artist.id}`} aria-label="Museum holdings"><h2>Museums & collections</h2>
        <><p>Documented holdings of works attributed to {artist.display_name}. Check the museum’s record for current display information.</p><ul>{collections.map(collection => <li key={collection.id}><div><Link href={`/museums/${collection.slug}?artist=${artist.slug}`} prefetch={false}>{collection.name}</Link><span>{collection.work_count.toLocaleString("en-GB")} recorded {collection.work_count === 1 ? "work" : "works"}</span></div><button type="button" onClick={() => { updateQuery({ art_museum: collection.slug, art_cursor: null, art_year: null, art_q: null, art_type: null, art_images: "false", work: null }, true); selectedWorks.current?.scrollIntoView({ block: "start" }); }}>Browse works</button></li>)}</ul>{(artist.collection_count ?? 0) > collections.length && <Link href={`/museums?artist=${artist.slug}`} prefetch={false}>Explore all recorded collections</Link>}</>
      </section>}
      {!embedded && artworkPages.length > 0 && <noscript><nav className="painter-collections" aria-label="Artwork pages"><h2>Explore artwork records</h2><ul>{artworkPages.map(item => <li key={item.id}><Link href={`/artists/${artist.slug}/works/${item.id}`} prefetch={false}>{item.title}</Link></li>)}</ul></nav></noscript>}
      {essay && <details className="essay-section"><summary>Read the painter essay</summary><article className="essay"><ReactMarkdown remarkPlugins={[remarkGfm]}>{essay}</ReactMarkdown></article></details>}
      {artist.citations.length > 0 && <details className="sources-section" id={`sources-${artist.id}`}><summary>Sources <span>{artist.citations.length}</span></summary><SourceList citations={artist.citations} /></details>}
    </div>
    {!embedded && artworkRecord}
    {gallery && workMessage && <div className="gallery-work-message">{workMessage}</div>}
    {gallery && viewerOpen && work && <ArtworkDialog work={work} creator={creator} navigation={workNavigation} close={() => setViewer({ id: workId, open: false })} details={<><PainterArtworkDetails artist={artist} work={work} /><ShareWorkLink path={`/artists/${artist.slug}/works/${work.id}`} /></>} />}
    {gallery && pageWork && <noscript><article className="artwork-details standalone-artwork"><ArtworkImage work={pageWork} large /><h3>{pageWork.title}</h3>{artworkDate(pageWork) && <p>{artworkDate(pageWork)}</p>}<PainterArtworkDetails artist={artist} work={pageWork} /></article></noscript>}

  </div>;
}
