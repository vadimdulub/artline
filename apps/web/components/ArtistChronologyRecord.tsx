"use client";
import { useRef, useState } from "react";
import Link from "next/link";
import { artworkDate, displayMetadata } from "@/lib/display-metadata";
import type { ArtistDetail, ArtistWorksPage, Artwork } from "@/lib/types";
import { updateQuery, useQueryString } from "@/lib/url-state";
import { ArtistRecord } from "./ArtistRecord";
import { AtlasCheckbox, AtlasFilters, AtlasSelect } from "./AtlasFilters";
import { AtlasSearchField } from "./AtlasSearchField";
import { MultiSelectFilter } from "./MultiSelectFilter";
import { useRecordNavigation } from "./RecordNavigation";
import { ArtworkImage } from "./ArtworkViewer";
import { useMuseumRequest } from "./museum-state";
import { formatCount, useCursorPaging } from "./use-cursor-paging";
import styles from "./ArtistChronology.module.css";

export function ArtistChronologyRecord({ artist, workId, onSelectWork, embedded = true, essay, initialWork, defaultImageOnly = embedded }: { artist: ArtistDetail; workId: string | null; onSelectWork: (id: string) => void; embedded?: boolean; essay?: string | null; initialWork?: Artwork; defaultImageOnly?: boolean }) {
  const params = new URLSearchParams(useQueryString());
  const searchInput = useRef<HTMLInputElement>(null);
  const imageOnly = params.has("art_images") ? params.get("art_images") !== "false" : defaultImageOnly;
  const year = params.get("art_year") ?? "", cursor = params.get("art_cursor") ?? "";
  const search = params.get("art_q") ?? "", museum = params.get("art_museum") ?? "", workType = params.get("art_type") ?? "";
  const filtered = Boolean(search || museum || workType || year || imageOnly);
  const activeFilters = [search, museum, workType, year, imageOnly].filter(Boolean).length;
  const [filtersOpen, setFiltersOpen] = useState(false);
  const paging = useCursorPaging(`${artist.id}|${year}|${imageOnly}|${search}|${museum}|${workType}`, cursor, value => { updateQuery({ art_cursor: value, work: null }, true); document.getElementById(`works-${artist.id}`)?.focus(); });
  const [retry, setRetry] = useState(0), [help, setHelp] = useState(false);
  const query = new URLSearchParams({image_only:String(imageOnly)});
  if (year === "undated") query.set("undated", "1"); else if (year) query.set("year", year);
  if (cursor) query.set("cursor", cursor);
  if (search) query.set("q", search);
  if (museum) query.set("museum", museum);
  if (workType) query.set("work_type", workType);
  const request = useMuseumRequest<ArtistWorksPage>(`artists/${artist.slug}/works?${query}`, retry);
  const page = request.data, summary = page ?? request.previousData;
  const works = page?.items ?? [];
  // Opening a painter uses the saved selection. Explicit links and a filtered
  // chronology retain their own selection, including pages without the key work.
  const defaultWork = !workId && !search && !museum && !workType && !year && !cursor
    && (!imageOnly || artist.key_artwork?.media_url) ? artist.key_artwork ?? undefined : undefined;
  const [navigatedWork,setNavigatedWork] = useState<Artwork>();
  const knownWork = (navigatedWork?.id===workId?navigatedWork:undefined) ?? (initialWork?.id===workId?initialWork:undefined) ?? works.find(work => work.id === workId) ?? artist.artworks.find(work => work.id === workId);
  const linked = useMuseumRequest<Artwork>(workId && !knownWork ? `artists/${artist.slug}/works/${encodeURIComponent(workId)}` : null, retry);
  const selectedWork = knownWork ?? linked.data;
  const navigation = useRecordNavigation(`artists/${artist.slug}/works?${query}`, (workId || defaultWork?.id || (embedded ? works[0]?.id : "")) || "", (id,item) => { setNavigatedWork(item as Artwork); onSelectWork(id); });
  const displayWork = selectedWork ?? (linked.loading ? linked.previousData : undefined);
  const start = summary?.range_start ?? artist.timeline_start_year, end = summary?.range_end ?? artist.timeline_end_year;
  const span = Math.max(1, end - start);
  const unknown = summary?.undated_count ?? 0, empty = summary?.total === 0;
  const missingTip = empty && imageOnly ? "No works with an attached picture match this view. Switch off With pictures to see all recorded artworks." : empty ? "No artwork dates are recorded in this view. This marker is not a creation date." : `${unknown} ${unknown === 1 ? "artwork has" : "artworks have"} no recorded creation year. They are listed after the dated works; this marker is not a date.`;
  const fullViewQuery = new URLSearchParams({ art_images: String(imageOnly) });
  for (const key of ["art_q", "art_year", "art_museum", "art_type"]) {
    const value = params.get(key);
    if (value) fullViewQuery.set(key, value);
  }
  const yearOptions = [{ value: "", label: embedded ? "All years" : "All recorded years" }, ...(summary?.years ?? []).map(item => ({ value: String(item.year), label: `${item.year} · ${formatCount(item.count)}${embedded ? "" : item.count === 1 ? " work" : " works"}` })), { value: "undated", label: `Undated · ${formatCount(unknown)}${embedded ? "" : " works"}` }, ...(year && year !== "undated" && !summary?.years.some(item => String(item.year) === year) ? [{ value: year, label: `${year} · ${embedded ? "0" : "no recorded works"}` }] : [])];
  const yearFilter = <AtlasSelect label="Artwork year" value={year} onChange={changeYear} options={yearOptions} />;
  const imageFilter = <AtlasCheckbox label="With pictures" checked={imageOnly} onChange={checked => updateQuery({ art_images: String(checked), art_cursor: null, work: null }, true)} />;
  function changeSearch(value: string) { updateQuery({ art_q: value || null, art_cursor: null, work: null }); }
  function resetFilters() { updateQuery({ art_q: null, art_museum: null, art_type: null, art_year: null, art_cursor: null, art_images: "false", work: null }, true); }
  function changeYear(value: string) { updateQuery({ art_year: value || null, art_cursor: null, work: null }); }
  return <ArtistRecord artist={artist} embedded={embedded} gallery={!embedded} essay={essay} pageWork={initialWork ?? null} workId={workId} defaultWork={defaultWork} onSelectWork={onSelectWork} artworks={works} linkedWork={displayWork} navigation={{...navigation,busy:navigation.busy || linked.loading}}
    workMessage={workId && !knownWork && !linked.data ? linked.error ? <div role="alert"><p>{linked.error}</p><button onClick={() => setRetry(value => value + 1)}>Retry artwork</button></div> : <p>Opening linked artwork…</p> : undefined}
    workBrowser={(choose, selectedID) => <div className={styles.chronology}>
      <div className={styles.heading}>
        <div><h2 id={`works-${artist.id}`} tabIndex={-1}>Artworks by year</h2><span role="status">{request.loading ? "Loading chronology…" : request.error ? "Chronology unavailable" : `${formatCount(artist.artwork_count ?? summary?.total ?? 0)} recorded ${(artist.artwork_count ?? summary?.total ?? 0) === 1 ? "work" : "works"}`}</span></div>
        {embedded ? <button type="button" className={styles.filterToggle} aria-label="Artwork filters" aria-expanded={filtersOpen} aria-controls={`artwork-filters-${artist.id}`} onClick={() => setFiltersOpen(value => !value)}>Filters{activeFilters > 0 && ` (${activeFilters})`}</button> : null}
      </div>
      <div id={`artwork-filters-${artist.id}`} hidden={embedded && !filtersOpen} className={styles.controls}>
        {embedded ? <div className={styles.quickFilters}>
          <AtlasSearchField inputRef={searchInput} label="Search artworks" placeholder="Search artworks" value={search} onChange={changeSearch} />
          <div className={styles.quickFilterRow}>{yearFilter}{imageFilter}</div>
          {(museum || workType) && <div className={styles.carriedFilters} aria-label="Additional active artwork filters">
            {workType && <button type="button" aria-label="Remove work type filter" onClick={() => updateQuery({ art_type: null, art_cursor: null, work: null }, true)}>{artist.work_types?.find(item => item.slug === workType)?.name ?? workType.replaceAll("-", " ")}<span aria-hidden="true">×</span></button>}
            {museum && <button type="button" aria-label="Remove collection filter" onClick={() => updateQuery({ art_museum: null, art_cursor: null, work: null }, true)}>{artist.collections?.find(item => item.slug === museum)?.name ?? museum.replaceAll("-", " ")}<span aria-hidden="true">×</span></button>}
          </div>}
          <div className={styles.quickFilterActions}>
            <Link href={`/artists/${artist.slug}?${fullViewQuery}#works-${artist.id}`} prefetch={false}>All filters in full view <span aria-hidden="true">↗</span></Link>
            {filtered && <button type="button" onClick={resetFilters} aria-label="Clear artwork filters">Clear</button>}
          </div>
        </div> : <AtlasFilters searchRef={searchInput} query={search} onQuery={changeSearch} onReset={resetFilters} searchLabel="Search artworks" placeholder="Title or accession number" columns={3} activeCount={activeFilters - (search ? 1 : 0)}>
          {yearFilter}
          <AtlasSelect label="Work type" value={workType} onChange={value => updateQuery({ art_type: value || null, art_cursor: null, work: null }, true)} options={[{ value: "", label: "All work types" }, ...(artist.work_types ?? []).map(item => ({ value: item.slug, label: `${item.name} · ${formatCount(item.count)}` }))]} />
          <MultiSelectFilter label="Museum / collection" allLabel="All collections" single options={(artist.collections ?? []).map(item => ({ slug: item.slug, name: item.name, detail: `${formatCount(item.work_count)} works` }))} values={museum ? [museum] : []} onChange={values => updateQuery({ art_museum: values[0] ?? null, art_cursor: null, work: null }, true)} helpText="Choose a documented holding collection. Holdings do not imply current display." />
          {imageFilter}
        </AtlasFilters>}
      </div>
      {page && <p className={styles.matchingCount}>{formatCount(page.matching_total)} matching {page.matching_total === 1 ? "work" : "works"}{imageOnly ? " with pictures" : ""}. {page.items.length} shown on this page.</p>}
      <div aria-busy={request.loading}>
        {request.error ? <div role="alert" className={styles.empty}><h3>We couldn’t load the chronology</h3><p>{request.error}</p><button onClick={() => setRetry(value => value + 1)}>Retry chronology</button><button onClick={resetFilters}>Reset artwork filters</button></div> : !page ? <p className={styles.empty}>Finding recorded artworks…</p> : page.items.length ? <>
          {embedded ? page.groups.map(group => <section key={group.year ?? "undated"} className={styles.yearGroup} aria-label={group.year===null ? "Undated artworks" : `Artworks grouped at ${group.year}`}><h3>{group.year ?? "Undated"}{group.year!==null && group.has_uncertain_dates && <small>Recorded date or range boundary</small>}</h3><div className={`works-list ${styles.thumbnailGrid}`}>{works.slice(group.start_index,group.start_index+group.count).map(work => <button key={work.id} className={`work-card work-row${selectedID===work.id ? " is-selected" : ""}`} aria-pressed={selectedID===work.id} onClick={() => choose(work.id)}><ArtworkImage work={work} /><span className="work-row-copy">{artworkDate(work) && <span className="work-date">{artworkDate(work)}</span>}<span className="work-title">{work.title}</span>{displayMetadata(work.current_location_text) && <span className="work-location">Held at {work.current_location_text}</span>}</span></button>)}</div></section>) : <div className={styles.gallery}>{works.map(work => <button key={work.id} type="button" className={`work-card ${styles.galleryCard}${selectedID===work.id ? " is-selected" : ""}`} aria-label={`View ${work.title}`} aria-pressed={selectedID===work.id} onClick={() => choose(work.id)}><ArtworkImage work={work} /><span className="work-title">{work.title}</span>{artworkDate(work) && <span className="work-date">{artworkDate(work)}</span>}{work.holding && <span className={styles.holding}>{work.holding.name}</span>}{work.attribution_role !== "primary" && <span className={styles.holding}>{work.attribution_role.replaceAll("_", " ")}</span>}</button>)}</div>}
          {(cursor || page.next_cursor) && <nav className={styles.pagination} aria-label="Artwork chronology pages"><span>{paging.number ? `Page ${paging.number} · ` : ""}{page.items.length} of {formatCount(page.matching_total)} matching works</span><div>{cursor && <button onClick={paging.first}>First artworks</button>}<button disabled={!paging.canPrevious} onClick={paging.previous}>Previous artworks</button>{page.next_cursor && <button onClick={() => paging.next(page.next_cursor)}>Next artworks</button>}</div></nav>}
        </> : <div className={styles.empty}><h3>{filtered ? "No matching artworks" : "No artworks in this view"}</h3><p>{imageOnly ? "Try clearing the picture filter to see more artworks." : filtered ? embedded ? "Try another title or year, or clear the artwork filters." : "Try another title, year, work type or collection. " : "Browse another artist or adjust the artwork filters."}</p>{filtered && <button type="button" onClick={resetFilters}>Clear artwork filters</button>}</div>}

      </div>
      {summary && !empty && <div className={styles.dateSummary}>
        <p className={styles.interval}>{artist.timeline_basis === "life" ? "Life" : "Painter interval"}: {artist.timeline_display}</p>
        <div className={styles.chartRow}>
          <div className={styles.chart}>
            <svg viewBox="0 0 500 48" preserveAspectRatio="none" role="img" aria-label={`Recorded artwork dates across ${start} to ${end}. ${summary.years.length} date groups; ${unknown} undated works. Use the artwork year control to browse.`}>
              <line x1="10" y1="38" x2="490" y2="38" className={styles.baseline} />
              <line x1={10 + (artist.timeline_start_year-start)/span*480} y1="38" x2={10 + (artist.timeline_end_year-start)/span*480} y2="38" className={styles.lifeline} />
              {summary.years.map(item => <g key={item.year}><title>{item.year}: {item.count} recorded {item.count === 1 ? "work" : "works"}. Ranges are grouped at their starting boundary.</title><line x1={10+(item.year-start)/span*480} x2={10+(item.year-start)/span*480} y1={38-Math.min(28,8+Math.log2(item.count+1)*6)} y2="38" className={styles.yearMark} /></g>)}
            </svg>
            <div className={styles.axisLabels} aria-hidden="true"><span>{start}</span><span>{end}</span></div>
          </div>
          {(unknown > 0 || empty) && <button className={styles.missingMark} type="button" aria-expanded={help || empty} aria-controls={`chronology-help-${artist.id}`} title={missingTip} onClick={() => { setHelp(value => !value); if (unknown>0) changeYear("undated"); }}><i aria-hidden="true" /><span>{empty ? "No data" : `${unknown} undated`}</span><span className="sr-only">. Show missing-data information</span></button>}
        </div>
        {(help || empty) && <p id={`chronology-help-${artist.id}`} className={styles.missingHelp}>{missingTip}</p>}
        {!help && !empty && unknown>0 && <span id={`chronology-help-${artist.id}`} className="sr-only">{missingTip}</span>}
      </div>}
    </div>} />;
}
