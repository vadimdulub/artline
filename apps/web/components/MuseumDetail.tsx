"use client";
import { BookmarkButton } from "./Bookmarks";
import { artworkDate, museumDescription } from "@/lib/display-metadata";
import Link from "@/components/MemberLink";
import { useRef, useState } from "react";
import { queryValues, updateQuery, useQueryString } from "@/lib/url-state";
import { MultiSelectFilter } from "./MultiSelectFilter";
import { usePainterChoices, workTypeOptions } from "./use-painter-choices";
import { countryName, safeSourceURL } from "@/lib/api";
import type { Museum, MuseumWorksPage } from "@/lib/types";
import { ArtworkImage } from "./ArtworkViewer";
import { MuseumDrawer } from "./MuseumDrawer";
import { useMuseumRequest } from "./museum-state";
import { MuseumError, setMuseumFilters } from "./MuseumFilters";
import { AtlasFilters, AtlasSelect, AtlasCheckbox, ActiveFilters } from "./AtlasFilters";
import { CursorPager } from "./CursorPager";
import { formatCount, useCursorPaging } from "./use-cursor-paging";
import styles from "./Museums.module.css";

export function MuseumDetail({ slug, initialMuseum }: { slug: string; initialMuseum?: Museum }) {
  const params = new URLSearchParams(useQueryString());
  if (params.has("selection") && params.get("selection") !== "museum") { params.delete("selection"); params.delete("cursor"); }
  const search = useRef<HTMLInputElement>(null);
  const painters = queryValues(params, "artist"), movements = queryValues(params, "movement"), venues = queryValues(params, "venue"), workTypes = queryValues(params, "work_type");
  const painterChoices = usePainterChoices(painters, false, slug);
  const [revision, setRevision] = useState(0);
  const museumRequest = useMuseumRequest<Museum>(`museums/${slug}`, revision, initialMuseum?.slug === slug ? initialMuseum : undefined, true);
  const museum = museumRequest.data ?? (museumRequest.previousData?.slug === slug ? museumRequest.previousData : undefined);
  const request = new URLSearchParams();
  for (const key of ["q", "artist", "movement", "selection", "display", "venue", "work_type", "start", "end", "unknown_date", "image_only", "sort", "limit"]) params.getAll(key).forEach(value => request.append(key, value));
  const scope = `${slug}|${request}`;
  const paging = useCursorPaging(scope, params.get("cursor") ?? "", cursor => { updateQuery({ cursor, work: null }, true); document.getElementById("museum-results-title")?.focus(); });
  if (params.get("cursor")) request.set("cursor", params.get("cursor")!);
  const view = params.get("view") === "list" ? "list" : "grid";
  const works = useMuseumRequest<MuseumWorksPage>(`museums/${slug}/works?${request}`, revision);
  const facets = works.data?.facets ?? works.previousData?.facets;
  const query = params.get("q") ?? "", selection = params.get("selection") ?? "", display = params.get("display") ?? "", workID = params.get("work");
  const filterLabels: Record<string, string> = {
    q: `Search: ${query}`, selection: "Museum highlights", display: "Confirmed on view",
    start: `From ${params.get("start")}`, end: `To ${params.get("end")}`,
    unknown_date: "Unknown creation dates", image_only: "With an image",
  };
  const filters = Object.entries(filterLabels).filter(([key]) => params.has(key) && params.get(key) && params.get(key) !== "0").map(([key, label]) => ({ key, label, remove: () => setMuseumFilters({ [key]: null }) }));
  const venueOptions = museum?.venues.map(item => ({ slug: item.id, name: item.name })) ?? [];
  for (const group of [{ key: "artist", values: painters, options: painterChoices.options }, { key: "movement", values: movements, options: facets?.movements ?? [] }, { key: "venue", values: venues, options: venueOptions }, { key: "work_type", values: workTypes, options: workTypeOptions }]) {
    for (const value of group.values) filters.push({ key: `${group.key}-${value}`, label: group.options.find(item => item.slug === value)?.name ?? value.replaceAll("-", " "), remove: () => setMuseumFilters({ [group.key]: group.values.filter(item => item !== value) }) });
  }
  const clear = () => setMuseumFilters(Object.fromEntries([...Object.keys(filterLabels), "artist", "movement", "venue", "work_type", "sort"].map(key => [key, null])));
  return <main id="main-content" className={`${styles.page} ${styles.collectionPage}`}>
    <Link className={styles.back} href="/museums">All museums and collections</Link>
    {museumRequest.error && !museum ? <MuseumError message={museumRequest.error} retry={() => setRevision(value => value + 1)} /> : !museum ? <p className={styles.loading}>Opening collection…</p> : <>
      {museumRequest.error && <p role="status" className={styles.note}>Collection information could not be refreshed. <button type="button" onClick={() => setRevision(value => value + 1)}>Retry</button></p>}
      <header className={styles.museumIntro}><div>{museum.venues.length > 0 && <p className={styles.place}>{ [...new Set(museum.venues.map(venue => `${venue.city}, ${countryName(venue.country)}`))].join(" / ") }</p>}<h1>{museum.name}</h1>{museumDescription(museum.description) && <details className={styles.aboutMuseum}><summary>About this collection</summary><p>{museumDescription(museum.description)}</p></details>}</div>
        <details className={styles.visit}><summary>{museum.venues.length ? "Visiting information" : "Exhibition information"}</summary>{museum.venues.length ? <ul>{museum.venues.map(venue => <li key={venue.id}><a href={safeSourceURL(venue.visit_url)} target="_blank" rel="noreferrer">{venue.name} <span aria-hidden="true">↗</span></a></li>)}</ul> : <p><a href={safeSourceURL(museum.website_url)} target="_blank" rel="noreferrer">Check the collection’s website</a>.</p>}<p>Use the official site for access, opening hours and exhibition changes. A collection record does not guarantee display.</p></details>
      </header>
      <div className={styles.selectionTabs} role="group" aria-label="Artwork selection">{[["", "All catalogued works"], ["museum", "Museum highlights"]].map(([value, label]) => <button key={value} aria-pressed={selection === value} onClick={() => setMuseumFilters({ selection: value, sort: value ? "curated" : "images" })}>{label}<span>{formatCount(value === "museum" ? museum.highlight_count : museum.work_count)}</span></button>)}</div>
      <AtlasFilters searchRef={search} query={query} onQuery={value => setMuseumFilters({ q: value })} onReset={clear} searchLabel="Search artworks" placeholder="Artwork or painter" columns={2} activeCount={filters.filter(filter => filter.key !== "q").length}>
        <MultiSelectFilter label="Painters" allLabel="All painters" {...painterChoices} values={painters} onChange={values => setMuseumFilters({ artist: values })} />
        <MultiSelectFilter label="Movements" allLabel="All movements" options={facets?.movements ?? []} values={movements} onChange={values => setMuseumFilters({ movement: values })} />
        <AtlasCheckbox label="With pictures" checked={params.get("image_only") === "1"} onChange={checked => setMuseumFilters({ image_only: checked ? "1" : null })} />
      </AtlasFilters>
      <details className={styles.more}><summary>More artwork filters</summary><div className={styles.secondaryFilters}>
        <AtlasSelect label="Display" value={display} onChange={value => setMuseumFilters({ display: value })} options={[{ value: "", label: "Any display status" }, { value: "on_view", label: "Confirmed on view" }]} />
        <MultiSelectFilter label="Confirmed at venues" allLabel="Any venue" options={venueOptions} values={venues} onChange={values => setMuseumFilters({ venue: values })} />
        <MultiSelectFilter label="Work types" allLabel="All types" options={workTypeOptions} values={workTypes} onChange={values => setMuseumFilters({ work_type: values })} />
        <label><span>Created from</span><input type="number" aria-label="Creation start year" min={-10000} max={3000} step={1} value={params.get("start") ?? ""} onChange={event => setMuseumFilters({ start: event.target.value, unknown_date: null })} /></label>
        <label><span>Created through</span><input type="number" aria-label="Creation end year" min={-10000} max={3000} step={1} value={params.get("end") ?? ""} onChange={event => setMuseumFilters({ end: event.target.value, unknown_date: null })} /></label>
        <label className={styles.check}><input type="checkbox" checked={params.get("unknown_date") === "1"} onChange={event => setMuseumFilters({ unknown_date: event.target.checked ? "1" : null, start: null, end: null })} /><span>Only unknown creation dates</span></label>
      </div><p className={styles.note}>Dates refer to artwork creation. Values within a filter combine with “or”; groups combine with “and”. Venue filters require current, confirmed display evidence.</p></details>
      <ActiveFilters filters={filters} onClear={clear} searchRef={search} />
      <div className={`${styles.resultsHeading} ${styles.resultsToolbar}`}><div><h2 id="museum-results-title" tabIndex={-1}>{selection === "museum" ? "Museum highlights" : "Works in this collection"}</h2><p role="status">{works.loading ? "Finding artworks…" : works.error ? "Connection interrupted" : `${formatCount(works.data?.total ?? 0)} ${(works.data?.total ?? 0) === 1 ? "work" : "works"} in this view${works.data?.image_count === undefined ? "" : ` · ${formatCount(works.data.image_count)} with images`}`}</p></div>
        <div className={styles.resultControls}><div className={styles.viewToggle} role="group" aria-label="Artwork layout"><button aria-pressed={view === "grid"} onClick={() => updateQuery({ view: null })}>Grid</button><button aria-pressed={view === "list"} onClick={() => updateQuery({ view: "list" })}>List</button></div><label><span className="sr-only">Sort artworks</span><select value={params.get("sort") ?? "images"} onChange={event => setMuseumFilters({ sort: event.target.value })}><option value="images">Images first</option><option value="year">Creation date</option><option value="title">Title</option>{selection && <option value="curated">Selection order</option>}</select></label><label><span className="sr-only">Artworks per page</span><select value={params.get("limit") ?? "24"} onChange={event => setMuseumFilters({ limit: event.target.value })}><option value="24">24 per page</option><option value="48">48 per page</option></select></label></div>
        <CursorPager compact paging={paging} next={works.data?.next_cursor ?? ""} busy={works.loading} total={works.data?.total ?? 0} shown={works.data?.items.length ?? 0} label="Artwork pages above results" />
      </div>
      <p className={styles.note}>Explore artworks from this collection.</p>
      <section aria-label="Museum artwork results" aria-busy={works.loading}>
        {works.error ? <MuseumError message={works.error} retry={() => setRevision(value => value + 1)} /> : works.loading ? <div className={styles.resultsLoading}><p>Loading artworks…</p><div aria-hidden="true" className={styles.skeletonGrid}>{Array.from({ length: 8 }, (_, i) => <span key={i} />)}</div></div> : works.data?.items.length ? <ul className={`${styles.worksGrid} ${view === "list" ? styles.worksList : ""}`} data-layout={view}>{works.data.items.map(work => <li key={work.id} className="bookmark-grid-item"><button className={styles.workCard} aria-label={`Open ${work.title}`} onClick={() => updateQuery({ work: work.id }, true)}><div className={styles.workImage}><ArtworkImage work={work} /></div><span className={styles.workCopy}><span className={styles.place}>{work.artists.map(artist => artist.name).join(", ") || work.unlinked_creator_label}</span><strong title={work.title}>{work.title}</strong>{artworkDate(work) && <span>{artworkDate(work)}</span>}{work.selections.some(selection => selection.kind === "museum") && <span className={styles.badges}>{work.selections.filter(selection => selection.kind === "museum").map(item => <span key={item.kind}>Museum highlight</span>)}</span>}{work.display && work.display.state !== "unknown" && <span className={styles.displayNote}>{work.display.state === "on_view" ? `Reported on view: ${work.display.venue_name}` : work.display.state === "stale" ? "Display report is out of date" : "Reported not on view"}</span>}</span></button><BookmarkButton kind="artwork" id={work.id} title={work.title} /></li>)}</ul> : <div className={styles.empty}><h3>{display || params.get("venue") ? "No matching works are confirmed on view" : selection === "museum" ? "No museum highlights are recorded for this view" : "No artworks match these filters"}</h3><p>{display || params.get("venue") ? "Display information is missing or out of date. Check the museum’s official site before visiting." : "Try clearing a filter to see more artworks."}</p><button onClick={clear}>Show all catalogued works</button></div>}
      </section>
      {works.data && <CursorPager paging={paging} next={works.data.next_cursor} busy={works.loading} total={works.data.total} shown={works.data.items.length} label="Museum catalogue pages" />}
      {workID && <MuseumDrawer key={workID} museum={museum} workID={workID} close={() => updateQuery({ work: null }, true)} />}
    </>}
  </main>;
}
