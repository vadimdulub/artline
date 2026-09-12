"use client";
import Link from "next/link";
import { useRef, useState } from "react";
import { queryValues, updateQuery, useQueryString } from "@/lib/url-state";
import { MultiSelectFilter } from "./MultiSelectFilter";
import { usePainterChoices, workTypeOptions } from "./use-painter-choices";
import { countryName, safeSourceURL } from "@/lib/api";
import type { Museum, MuseumWorksPage } from "@/lib/types";
import { ArtworkImage } from "./ArtworkViewer";
import { EditorAccess, useEditorToken } from "./EditorAccess";
import { MuseumDrawer } from "./MuseumDrawer";
import { useMuseumRequest } from "./museum-state";
import { MuseumChips, MuseumError, setMuseumFilters } from "./MuseumFilters";
import { CursorPager } from "./CursorPager";
import { formatCount, useCursorPaging } from "./use-cursor-paging";
import styles from "./Museums.module.css";

export function MuseumDetail({ slug, preview }: { slug: string; preview: boolean }) {
  const params = new URLSearchParams(useQueryString());
  const [token, setToken] = useEditorToken();
  const painters = queryValues(params, "artist"), movements = queryValues(params, "movement"), venues = queryValues(params, "venue"), workTypes = queryValues(params, "work_type");
  const painterChoices = usePainterChoices(painters, false, slug, token);
  const [revision, setRevision] = useState(0), [message, setMessage] = useState("");
  const editor = useRef<HTMLDetailsElement>(null);
  const museumRequest = useMuseumRequest<Museum>(`museums/${slug}`, token, revision);
  const museum = museumRequest.data ?? (museumRequest.previousData?.slug === slug ? museumRequest.previousData : undefined);
  const request = new URLSearchParams();
  for (const key of ["q", "artist", "movement", "selection", "display", "venue", "work_type", "start", "end", "unknown_date", "image_only", "sort", "limit"]) params.getAll(key).forEach(value => request.append(key, value));
  const scope = `${slug}|${request}|${token}`;
  const paging = useCursorPaging(scope, params.get("cursor") ?? "", cursor => { updateQuery({ cursor, work: null }, true); document.getElementById("museum-results-title")?.focus(); });
  if (params.get("cursor")) request.set("cursor", params.get("cursor")!);
  const view = params.get("view") === "list" ? "list" : "grid";
  const works = useMuseumRequest<MuseumWorksPage>(`museums/${slug}/works?${request}`, token, revision);
  const facets = works.data?.facets ?? works.previousData?.facets;
  const query = params.get("q") ?? "", selection = params.get("selection") ?? "", display = params.get("display") ?? "", workID = params.get("work");
  const filterLabels: Record<string, string> = {
    q: `Search: ${query}`, selection: selection === "owner" ? "My must-see works" : "Museum highlights", display: "Confirmed on view",
    start: `From ${params.get("start")}`, end: `To ${params.get("end")}`,
    unknown_date: "Unknown creation dates", image_only: "With an image",
  };
  const filters = Object.entries(filterLabels).filter(([key]) => params.has(key) && params.get(key) && params.get(key) !== "0").map(([key, label]) => ({ key, label, remove: () => setMuseumFilters({ [key]: null }) }));
  const venueOptions = museum?.venues.map(item => ({ slug: item.id, name: item.name })) ?? [];
  for (const group of [{ key: "artist", values: painters, options: painterChoices.options }, { key: "movement", values: movements, options: facets?.movements ?? [] }, { key: "venue", values: venues, options: venueOptions }, { key: "work_type", values: workTypes, options: workTypeOptions }]) {
    for (const value of group.values) filters.push({ key: `${group.key}-${value}`, label: group.options.find(item => item.slug === value)?.name ?? value.replaceAll("-", " "), remove: () => setMuseumFilters({ [group.key]: group.values.filter(item => item !== value) }) });
  }
  const clear = () => setMuseumFilters(Object.fromEntries([...Object.keys(filterLabels), "artist", "movement", "venue", "work_type", "sort"].map(key => [key, null])));
  function saved() { setMessage("Your must-see selection was saved in review."); setRevision(value => value + 1); }
  function editAccess() { updateQuery({ work: null }); if (editor.current) { editor.current.open = true; setTimeout(() => { editor.current?.scrollIntoView({ block: "center" }); editor.current?.querySelector("input")?.focus(); }, 0); } }
  return <main id="main-content" className={`${styles.page} ${styles.collectionPage}`}>
    <Link className={styles.back} href="/museums">All museums and collections</Link>
    {museumRequest.error ? <MuseumError message={museumRequest.error} retry={() => setRevision(value => value + 1)} /> : !museum ? <p className={styles.loading}>Opening collection…</p> : <>
      <header className={styles.museumIntro}><div><p className={styles.place}>{museum.venues.length ? [...new Set(museum.venues.map(venue => `${venue.city}, ${countryName(venue.country)}`))].join(" / ") : "Holding collection · no verified public venue"}</p><h1>{museum.name}</h1><p className={styles.preview}>{preview || token ? "Research preview · records are still in review" : "Published catalogue"}</p>{museum.description && <details className={styles.aboutMuseum}><summary>About this collection</summary><p>{museum.description}</p></details>}</div>
        <details className={styles.visit}><summary>{museum.venues.length ? "Visiting information" : "Exhibition information"}</summary>{museum.venues.length ? <ul>{museum.venues.map(venue => <li key={venue.id}><a href={safeSourceURL(venue.visit_url)} target="_blank" rel="noreferrer">{venue.name} <span aria-hidden="true">↗</span></a></li>)}</ul> : <p>No permanent public venue is verified here. <a href={safeSourceURL(museum.website_url)} target="_blank" rel="noreferrer">Check the collection’s website</a>.</p>}<p>Use the official site for access, opening hours and exhibition changes. A collection record does not guarantee display.</p></details>
      </header>
      <div className={styles.selectionTabs} role="group" aria-label="Artwork selection">{[["", "All catalogued works"], ["owner", "My must-see works"], ["museum", "Museum highlights"]].map(([value, label]) => <button key={value} aria-pressed={selection === value} onClick={() => setMuseumFilters({ selection: value, sort: value ? "curated" : "year" })}>{label}<span>{formatCount(value === "owner" ? museum.must_see_count : value === "museum" ? museum.highlight_count : museum.work_count)}</span></button>)}</div>
      <div className={styles.workFilters}>
        <label className={styles.search}><span>Search artworks</span><input type="search" placeholder="Artwork or painter" value={query} onChange={event => setMuseumFilters({ q: event.target.value })} /></label>
        <MultiSelectFilter label="Painters" allLabel="All painters" {...painterChoices} values={painters} onChange={values => setMuseumFilters({ artist: values })} />
        <MultiSelectFilter label="Movements" allLabel="All movements" options={facets?.movements ?? []} values={movements} onChange={values => setMuseumFilters({ movement: values })} />
        <label className={styles.check}><input type="checkbox" checked={params.get("image_only") === "1"} onChange={event => setMuseumFilters({ image_only: event.target.checked ? "1" : null })} /><span>With an available image</span></label>
      </div>
      <details className={styles.more}><summary>More artwork filters</summary><div className={styles.secondaryFilters}>
        <label><span>Display</span><select value={display} onChange={event => setMuseumFilters({ display: event.target.value })}><option value="">Any display status</option><option value="on_view">Confirmed on view</option></select></label>
        <MultiSelectFilter label="Confirmed at venues" allLabel="Any venue" options={venueOptions} values={venues} onChange={values => setMuseumFilters({ venue: values })} />
        <MultiSelectFilter label="Work types" allLabel="All types" options={workTypeOptions} values={workTypes} onChange={values => setMuseumFilters({ work_type: values })} />
        <label><span>Created from</span><input type="number" aria-label="Creation start year" min={-10000} max={3000} step={1} value={params.get("start") ?? ""} onChange={event => setMuseumFilters({ start: event.target.value, unknown_date: null })} /></label>
        <label><span>Created through</span><input type="number" aria-label="Creation end year" min={-10000} max={3000} step={1} value={params.get("end") ?? ""} onChange={event => setMuseumFilters({ end: event.target.value, unknown_date: null })} /></label>
        <label className={styles.check}><input type="checkbox" checked={params.get("unknown_date") === "1"} onChange={event => setMuseumFilters({ unknown_date: event.target.checked ? "1" : null, start: null, end: null })} /><span>Only unknown creation dates</span></label>
      </div><p className={styles.note}>Dates refer to artwork creation. Values within a filter combine with “or”; groups combine with “and”. Venue filters require current, confirmed display evidence.</p></details>
      <MuseumChips filters={filters} clear={clear} />
      <div className={`${styles.resultsHeading} ${styles.resultsToolbar}`}><div><h2 id="museum-results-title" tabIndex={-1}>{selection === "owner" ? "My must-see works" : selection === "museum" ? "Museum highlights" : "Works in this collection"}</h2><p role="status">{works.loading ? "Finding artworks…" : works.error ? "Connection interrupted" : `${formatCount(works.data?.total ?? 0)} ${(works.data?.total ?? 0) === 1 ? "work" : "works"} in this view`}</p></div>
        <div className={styles.resultControls}><div className={styles.viewToggle} role="group" aria-label="Artwork layout"><button aria-pressed={view === "grid"} onClick={() => updateQuery({ view: null })}>Grid</button><button aria-pressed={view === "list"} onClick={() => updateQuery({ view: "list" })}>List</button></div><label><span className="sr-only">Sort artworks</span><select value={params.get("sort") ?? "year"} onChange={event => setMuseumFilters({ sort: event.target.value })}><option value="year">Creation date</option><option value="title">Title</option>{selection && <option value="curated">Selection order</option>}</select></label><label><span className="sr-only">Artworks per page</span><select value={params.get("limit") ?? "24"} onChange={event => setMuseumFilters({ limit: event.target.value })}><option value="24">24 per page</option><option value="48">48 per page</option></select></label></div>
        <CursorPager compact paging={paging} next={works.data?.next_cursor ?? ""} busy={works.loading} total={works.data?.total ?? 0} shown={works.data?.items.length ?? 0} label="Artwork pages above results" />
      </div>
      <p className={styles.note}>Artline catalogue records, not the museum’s complete holdings. Display is unverified unless explicitly noted.</p>
      <section aria-label="Museum artwork results" aria-busy={works.loading}>
        {works.error ? <MuseumError message={works.error} retry={() => setRevision(value => value + 1)} /> : works.loading ? <div className={styles.resultsLoading}><p>Loading artworks…</p><div aria-hidden="true" className={styles.skeletonGrid}>{Array.from({ length: 8 }, (_, i) => <span key={i} />)}</div></div> : works.data?.items.length ? <ul className={`${styles.worksGrid} ${view === "list" ? styles.worksList : ""}`} data-layout={view}>{works.data.items.map(work => <li key={work.id}><button className={styles.workCard} aria-label={`Open ${work.title}`} onClick={() => updateQuery({ work: work.id }, true)}><div className={styles.workImage}><ArtworkImage work={work} /></div><span className={styles.workCopy}><span className={styles.place}>{work.artists.map(artist => artist.name).join(", ") || work.unlinked_creator_label || "Creator not recorded"}</span><strong title={work.title}>{work.title}</strong><span>{work.date_display}</span>{work.selections.length > 0 && <span className={styles.badges}>{work.selections.map(item => <span key={item.kind}>{item.kind === "owner" ? "My must-see work" : "Museum highlight"}</span>)}</span>}{work.display && work.display.state !== "unknown" && <span className={styles.displayNote}>{work.display.state === "on_view" ? `Reported on view: ${work.display.venue_name}` : work.display.state === "stale" ? "Display report is out of date" : "Reported not on view"}</span>}</span></button></li>)}</ul> : <div className={styles.empty}><h3>{selection === "owner" ? "Your must-see list starts here" : display || params.get("venue") ? "No matching works are confirmed on view" : selection === "museum" ? "No museum highlights are recorded for this view" : "No artworks match these filters"}</h3><p>{selection === "owner" ? "Browse all works, open an artwork and save it to your selection with editor access." : display || params.get("venue") ? "Display information is missing or out of date. Check the museum’s official site before visiting." : "Try clearing a filter. Unverified designations are never inferred from an artwork’s popularity."}</p><button onClick={clear}>Show all catalogued works</button></div>}
      </section>
      {works.data && <CursorPager paging={paging} next={works.data.next_cursor} busy={works.loading} total={works.data.total} shown={works.data.items.length} label="Museum catalogue pages" />}
      <p role="status" className={styles.note}>{message}</p>
      {workID && <MuseumDrawer museum={museum} workID={workID} token={token} revision={revision} close={() => updateQuery({ work: null }, true)} saved={saved} reload={() => { setMessage(""); setRevision(value => value + 1); }} editAccess={editAccess} />}
    </>}
    <details ref={editor} id="museum-editor" className={styles.editor}><summary>Edit my must-see list</summary><EditorAccess token={token} onChange={setToken} /><p>Open an artwork to add, remove, annotate or order your personal picks. No record is published automatically.</p></details>
  </main>;
}
