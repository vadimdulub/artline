"use client";
import Link from "next/link";
import { ArtworkImage, ArtworkViewer, ShareWorkLink } from "./ArtworkViewer";
import { ArtworkLocation } from "./ArtworkLocation";
import { ArtworkDescription } from "./ArtworkDescription";
import { useEffect, useRef, useState, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { countryName, safeSourceURL } from "@/lib/api";
import type { ArtistDetail, Artwork, Citation } from "@/lib/types";

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : null;
}

function readableEvidence(note: string) {
  try {
    const parsed = JSON.parse(note) as unknown;
    const evidence = asRecord(parsed);
    if (!evidence) return null;
    const countryEvidence = asRecord(evidence.country_evidence);
    const crosscheck = asRecord(countryEvidence?.wikipedia_country_crosscheck);
    const lines: string[] = [];
    const code = typeof evidence.country_code === "string" ? evidence.country_code : typeof countryEvidence?.country_code === "string" ? countryEvidence.country_code : null;
    if (code) lines.push(`Country affiliation: ${countryName(code)} (${code}).`);
    const basis = typeof countryEvidence?.basis === "string" ? countryEvidence.basis : typeof evidence.description === "string" ? evidence.description : null;
    if (basis) lines.push(`Evidence basis: ${basis}`);
    if (typeof countryEvidence?.source_description === "string") lines.push(`Source description: ${countryEvidence.source_description}`);
    if (typeof crosscheck?.source_excerpt === "string") lines.push(`Biography cross-check: ${crosscheck.source_excerpt}`);
    if (Array.isArray(countryEvidence?.historical_polity_statements) && countryEvidence.historical_polity_statements.length) lines.push(`Historical-polity statements: ${countryEvidence.historical_polity_statements.length} recorded for discovery context only.`);
    if (evidence.publication_status === "review" || evidence.publication === "Review") lines.push("Publication state: review.");
    if (!lines.length) return null;
    return lines;
  } catch {
    return null;
  }
}

function EvidenceNote({ note }: { note: string }) {
  const lines = readableEvidence(note);
  if (!lines) return <p>{note}</p>;
  return <div className="structured-evidence">{lines.map((line, index) => <p key={index}>{line}</p>)}</div>;
}

export function SourceList({ citations }: { citations: Citation[] }) {
  return <ul className="source-list">{citations.map((source, index) => <li key={index}><a href={safeSourceURL(source.source_url)} target="_blank" rel="noreferrer">{source.source_name}</a><span>{source.field_name.replaceAll("_", " ")}</span>{source.evidence_note && <EvidenceNote note={source.evidence_note} />}</li>)}</ul>;
}
function WorkBrowserContent({ render, onSelectWork, selectedID }: { render: (choose: (id: string) => void, selectedID?: string) => ReactNode; onSelectWork: (id: string) => void; selectedID?: string }) {
  return render(onSelectWork, selectedID);
}
function ArtistContext({ collapsed, children }: { collapsed: boolean; children: ReactNode }) {
  return collapsed ? <details className="chronology-biography"><summary>About the painter and influences</summary>{children}</details> : children;
}
export function ArtistRecord({ artist, essay, workId, onSelectWork, embedded = false, artworks, linkedWork, workBrowser, workMessage }: { artist: ArtistDetail; essay?: string | null; workId?: string | null; onSelectWork: (id: string) => void; embedded?: boolean; artworks?: Artwork[]; linkedWork?: Artwork; workBrowser?: (choose: (id: string) => void, selectedID?: string) => ReactNode; workMessage?: ReactNode }) {
  const works = artworks ?? artist.artworks;
  const collections = [...new Map(works.flatMap(work => work.holding ? [[work.holding.id, work.holding] as const] : [])).values()];
  const selectedIndex = workId ? works.findIndex((item) => item.id === workId) : 0;
  const work = workId ? works[selectedIndex] ?? (linkedWork?.id === workId ? linkedWork : undefined) : works[0];
  const [fullBiography, setFullBiography] = useState(false);
  const artworkPanel = useRef<HTMLElement>(null);
  const artworkHeading = useRef<HTMLHeadingElement>(null);
  const pendingWorkFocus = useRef(false);
  const selectedWorks = useRef<HTMLElement>(null);
  const shortBiography = artist.biography_md?.split(/(?<=\.)\s+/).slice(0, 2).join(" ") ?? "";
  function chooseWork(id: string) {
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
  return <div className="artist-record">
    <div className="artist-main">
      <header className="artist-heading">
        <div className="record-classification"><span><i style={{ background: artist.movement.color }} />{artist.movement.name}</span>{artist.countries.map(code => <span key={code}>{countryName(code)}</span>)}{artist.status !== "published" && <span className="review-label">{artist.status === "draft" ? "Draft" : "In review"}</span>}</div>
        <h1>{artist.display_name}</h1><p className="artist-dates">{artist.timeline_display}</p>
        {artist.aliases.length > 0 && <details className="artist-aliases"><summary>Other names ({artist.aliases.length})</summary><p>{artist.aliases.join(", ")}</p></details>}
      </header>
      <ArtistContext collapsed={Boolean(workBrowser)}><section className={`artist-context${!artist.influences.length ? " research-context" : ""}`} aria-label="Biography and influences">
        <div className="biography">{artist.biography_md ? <><ReactMarkdown remarkPlugins={[remarkGfm]}>{fullBiography ? artist.biography_md : shortBiography}</ReactMarkdown>{shortBiography !== artist.biography_md && <button className="biography-toggle" aria-expanded={fullBiography} onClick={() => setFullBiography(value => !value)}>{fullBiography ? "Show less" : "Read full biography"}</button>}</> : <p className="research-note">Biography and influences are still being researched. Explore the sourced artworks below.</p>}</div>
        {artist.influences.length > 0 ? (["incoming", "outgoing"] as const).map(direction => {
          const claims = artist.influences.filter(item => item.direction === direction);
          return <div key={direction} className={`influence-column ${direction}`}><h2>{direction === "incoming" ? "Influenced by" : "Later influence"}</h2>{claims.length ? <ul>{claims.map(claim => <li key={claim.id}>{claim.slug ? <Link href={`/artists/${claim.slug}`}>{claim.name}</Link> : claim.name}<small>{claim.evidence_level.replaceAll("_", " ")}</small><details><summary>Evidence</summary><p>{claim.evidence_note}</p><SourceList citations={claim.citations} /></details></li>)}</ul> : <p className="muted">Connections are still being researched.</p>}</div>;
        }) : artist.biography_md ? <p className="research-note influence-research">Influences are still being researched; no connections are asserted yet.</p> : null}
      </section></ArtistContext>
      {collections.length > 0 && <nav className="painter-collections" aria-label="Collections for these artworks"><h2>Explore these collections</h2><ul>{collections.map(collection => <li key={collection.id}><Link href={`/museums/${collection.slug}?artist=${artist.slug}`}>{collection.name}</Link></li>)}</ul><p>Holdings represented in this artwork selection; display is not confirmed.</p></nav>}
      <section ref={selectedWorks} className="selected-works" aria-labelledby={`works-${artist.id}`}>
        {workBrowser ? <WorkBrowserContent render={workBrowser} onSelectWork={chooseWork} selectedID={work?.id} /> : <><div className="section-heading"><h2 id={`works-${artist.id}`}>Selected works</h2><span>{works.length ? `${works.length} records · choose a work for details` : "Selection in progress"}</span></div>
        {works.length ? <div className={embedded ? "works-list" : "works-strip"} style={{ ["--work-columns" as string]: Math.min(5, works.length) }}>{works.map((item, index) => <button key={item.id} className={`work-card${embedded ? " work-row" : ""}${item.id === work?.id ? " is-selected" : ""}`} type="button" aria-pressed={item.id === work?.id} onClick={() => chooseWork(item.id)}><ArtworkImage work={item} number={embedded ? index + 1 : undefined} />{embedded ? <span className="work-row-copy"><span className="work-date">{item.date_display}</span><span className="work-title">{item.title}</span><span className="work-location">{item.creation_place_display ? `Made in ${item.creation_place_display}` : "Creation place not established"}</span><span className="work-location">{item.current_location_text ? `Held at ${item.current_location_text}` : "Current location under review"}</span></span> : <><span className="work-title">{item.title}</span><span className="work-date">{item.date_display}</span></>}</button>)}</div> : <div className="quiet-empty"><h3>A selection takes shape</h3><p>Works will appear here as dates, locations, and sources are reviewed.</p><Link href="/catalogue">Explore the catalogue</Link></div>}
        </>}
      </section>
      {essay && <details className="essay-section"><summary>Read the painter essay</summary><article className="essay"><ReactMarkdown remarkPlugins={[remarkGfm]}>{essay}</ReactMarkdown></article></details>}
      <details className="sources-section"><summary>Sources & research notes <span>{artist.citations.length}</span></summary><SourceList citations={artist.citations} /></details>
      {embedded && <Link className="text-link" href={work ? `/artists/${artist.slug}/works/${work.id}` : `/artists/${artist.slug}`}>Open full painter record</Link>}
    </div>
    {(!embedded || work || workMessage) && <aside ref={artworkPanel} className="artwork-panel" aria-labelledby="artwork-record-title">
      <div className="artwork-panel-actions">{embedded && <button type="button" onClick={returnToWorks}>{workBrowser ? "← Artworks by year" : "← Selected works"}</button>}{work && <ShareWorkLink key={work.id} path={`/artists/${artist.slug}/works/${work.id}`} />}</div>
      <div className="artwork-panel-heading"><h2 ref={artworkHeading} tabIndex={-1} id="artwork-record-title">Artwork record{work && <span className="sr-only">: {work.title}, {work.date_display}</span>}</h2>{work && selectedIndex>=0 && <span>{selectedIndex + 1} / {works.length}{workBrowser ? " on this page" : ""}</span>}</div>
      {works.length > 1 && selectedIndex>=0 && <nav className="artwork-navigation" aria-label="Browse selected works"><button type="button" disabled={selectedIndex === 0} onClick={() => chooseWork(works[selectedIndex - 1].id)}>Previous work</button><button type="button" disabled={selectedIndex === works.length - 1} onClick={() => chooseWork(works[selectedIndex + 1].id)}>Next work</button></nav>}
      {work ? <div key={work.id} className="artwork-details">
        <ArtworkViewer work={work} />
        <h3>{work.title}</h3>{work.alternate_title && <p>{work.alternate_title}</p>}<p className="artwork-date">{work.date_display}</p>
        <dl><div><dt>Dating</dt><dd>{({ exact: "Exact year", exact_year: "Exact year", circa: "Approximate", range: "Date range", circa_range: "Approximate date range", decade: "Within this decade", century: "Within this century", before: "Before this date", after: "After this date", unknown: "Uncertain" } as Record<string, string>)[work.date_precision] ?? work.date_precision.replaceAll("_", " ")}</dd></div><div><dt>Made in</dt><dd>{work.creation_place_display ?? "Not yet established"}{!work.creation_place_display && work.creation_place_unknown_reason && <small className="metadata-note">{work.creation_place_unknown_reason}</small>}</dd></div><div><dt>Held at</dt><dd>{work.current_location_text ?? "Location under review"}</dd></div><div><dt>Medium</dt><dd>{work.medium_text ?? work.work_type.replaceAll("_", " ")}</dd></div><div><dt>Dimensions</dt><dd>{work.dimensions_text ?? "Not recorded in this catalogue"}</dd></div>{work.accession_number && <div><dt>Collection no.</dt><dd>{work.accession_number}</dd></div>}<div><dt>Attribution</dt><dd>{({ primary: "By the artist", workshop: "Workshop", attributed_to: "Attributed to the artist", follower_of: "Follower of the artist", formerly_attributed_to: "Formerly attributed to the artist", circle_of: "Circle of the artist" } as Record<string, string>)[work.attribution_role] ?? work.attribution_role.replaceAll("_", " ")}</dd></div><div><dt>Image rights</dt><dd>{work.license_label ?? work.rights_status?.replaceAll("_", " ") ?? "Not reviewed"}{work.license_url && <a className="license-link" href={safeSourceURL(work.license_url)} target="_blank" rel="noreferrer">License details</a>}</dd></div></dl>
        {work.attribution_text && <p className="image-credit">{work.attribution_text}</p>}
        <ArtworkLocation work={work} />
        <ArtworkDescription key={work.id} work={work} detailPath={`artists/${artist.slug}/works/${work.id}`} />
        {work.location_checked_at && <p className="image-credit">Location checked {new Intl.DateTimeFormat("en", { dateStyle: "medium", timeZone: "UTC" }).format(new Date(work.location_checked_at))}. This does not indicate whether the work is on display.</p>}
        <details><summary>Artwork sources</summary><SourceList citations={work.citations} />{safeSourceURL(work.source_page_url) && <a href={safeSourceURL(work.source_page_url)} target="_blank" rel="noreferrer">Image source</a>}</details>
      </div> : workMessage ?? <div className="artwork-waiting"><span aria-hidden="true">▧</span><h3>A closer look</h3><p>Select an artwork to explore its date, origin, collection, and sources.</p></div>}
    </aside>}
  </div>;
}
