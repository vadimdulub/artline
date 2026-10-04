"use client";
import { useState } from "react";
import type { ArtistDetail, ArtistWorksPage, Artwork } from "@/lib/types";
import { updateQuery, useQueryString } from "@/lib/url-state";
import { ArtistRecord } from "./ArtistRecord";
import { AtlasCheckbox } from "./AtlasFilters";
import { useRecordNavigation } from "./RecordNavigation";
import { ArtworkImage } from "./ArtworkViewer";
import { useMuseumRequest } from "./museum-state";
import { formatCount, useCursorPaging } from "./use-cursor-paging";
import styles from "./ArtistChronology.module.css";

export function ArtistChronologyRecord({ artist, workId, onSelectWork, embedded = true, essay, initialWork, defaultImageOnly = false, publishedOnly = false }: { artist: ArtistDetail; workId: string | null; onSelectWork: (id: string) => void; embedded?: boolean; essay?: string | null; initialWork?: Artwork; defaultImageOnly?: boolean; publishedOnly?: boolean }) {
  const params = new URLSearchParams(useQueryString());
  const imageOnly = params.has("art_images") ? params.get("art_images") !== "false" : defaultImageOnly;
  const year = params.get("art_year") ?? "", cursor = params.get("art_cursor") ?? "";
  const search = params.get("art_q") ?? "", museum = params.get("art_museum") ?? "", workType = params.get("art_type") ?? "";
  const filtered = Boolean(search || museum || workType || year || imageOnly);
  const paging = useCursorPaging(`${artist.id}|${year}|${imageOnly}|${search}|${museum}|${workType}`, cursor, value => { updateQuery({ art_cursor: value, work: null }, true); document.getElementById(`works-${artist.id}`)?.focus(); });
  const [retry, setRetry] = useState(0), [help, setHelp] = useState(false);
  const query = new URLSearchParams({image_only:String(imageOnly)});
  if (publishedOnly) query.set("preview", "0");
  if (year === "undated") query.set("undated", "1"); else if (year) query.set("year", year);
  if (cursor) query.set("cursor", cursor);
  if (search) query.set("q", search);
  if (museum) query.set("museum", museum);
  if (workType) query.set("work_type", workType);
  const request = useMuseumRequest<ArtistWorksPage>(`artists/${artist.slug}/works?${query}`, "", retry);
  const page = request.data, summary = page ?? request.previousData;
  const works = page?.items ?? [];
  const [navigatedWork,setNavigatedWork] = useState<Artwork>();
  const knownWork = (navigatedWork?.id===workId?navigatedWork:undefined) ?? (initialWork?.id===workId?initialWork:undefined) ?? works.find(work => work.id === workId) ?? artist.artworks.find(work => work.id === workId);
  const linked = useMuseumRequest<Artwork>(workId && !knownWork ? `artists/${artist.slug}/works/${encodeURIComponent(workId)}${publishedOnly ? "?preview=0" : ""}` : null, "", retry);
  const selectedWork = knownWork ?? linked.data;
  const navigation = useRecordNavigation(`artists/${artist.slug}/works?${query}`, (embedded ? workId || works[0]?.id : workId) || "", (id,item) => { setNavigatedWork(item as Artwork); onSelectWork(id); });
  const displayWork = selectedWork ?? (linked.loading ? linked.previousData : undefined);
  const start = summary?.range_start ?? artist.timeline_start_year, end = summary?.range_end ?? artist.timeline_end_year;
  const span = Math.max(1, end - start);
  const unknown = summary?.undated_count ?? 0, empty = summary?.total === 0;
  const missingTip = empty && imageOnly ? "No works with an attached picture match this view. Switch off With pictures to see all recorded artworks." : empty ? "We don’t have artwork data for this painter yet. This marker is not a creation date." : `${unknown} ${unknown === 1 ? "artwork has" : "artworks have"} no recorded creation year. They are listed after the dated works; this marker is not a date.`;
  function resetFilters() { updateQuery({ art_q: null, art_museum: null, art_type: null, art_year: null, art_cursor: null, art_images: "false", work: null }, true); }
  function changeYear(value: string) { updateQuery({ art_year: value || null, art_cursor: null, work: null }); }
  return <ArtistRecord artist={artist} embedded={embedded} gallery={!embedded} fullCatalogue={!publishedOnly && artist.status === "published"} essay={essay} pageWork={initialWork ?? null} workId={workId} onSelectWork={onSelectWork} artworks={works} linkedWork={displayWork} navigation={{...navigation,busy:navigation.busy || linked.loading}}
    workMessage={workId && !knownWork && !linked.data ? linked.error ? <div role="alert"><p>{linked.error}</p><button onClick={() => setRetry(value => value + 1)}>Retry artwork</button></div> : <p>Opening linked artwork…</p> : undefined}
    workBrowser={(choose, selectedID) => <div className={styles.chronology}>
      <div className={styles.heading}>
        <div><h2 id={`works-${artist.id}`} tabIndex={-1}>Artworks by year</h2><span role="status">{request.loading ? "Loading chronology…" : request.error ? "Chronology unavailable" : `${formatCount(artist.artwork_count ?? summary?.total ?? 0)} recorded ${(artist.artwork_count ?? summary?.total ?? 0) === 1 ? "work" : "works"}`}</span></div>
        <AtlasCheckbox label="With pictures" checked={imageOnly} onChange={checked => updateQuery({art_images:String(checked),art_cursor:null,work:null},true)} />
      </div>
      <form className={styles.controls} onSubmit={event => { event.preventDefault(); const value = new FormData(event.currentTarget).get("artwork-search"); updateQuery({ art_q: String(value ?? "").trim() || null, art_cursor: null, work: null }, true); }}>
        <label className={styles.search}><span>Search artworks</span><input key={search} type="search" name="artwork-search" aria-label="Search artworks" defaultValue={search} maxLength={200} placeholder="Title or accession number" /></label><button type="submit">Search works</button>
        <label><span>Artwork year</span><select value={year} onChange={event => changeYear(event.target.value)}><option value="">All recorded years</option>{summary?.years.map(item => <option key={item.year} value={item.year}>{item.year} · {item.count} {item.count === 1 ? "work" : "works"}</option>)}<option value="undated">Undated · {unknown} works</option>{year && year!=="undated" && !summary?.years.some(item => String(item.year)===year) && <option value={year}>{year} · no recorded works</option>}</select></label>
        <label><span>Work type</span><select value={workType} onChange={event => updateQuery({ art_type: event.target.value || null, art_cursor: null, work: null }, true)}><option value="">All work types</option>{artist.work_types?.map(item => <option key={item.slug} value={item.slug}>{item.name} · {formatCount(item.count)}</option>)}</select></label>
        <label><span>Museum / collection</span><select value={museum} onChange={event => updateQuery({ art_museum: event.target.value || null, art_cursor: null, work: null }, true)}><option value="">All collections</option>{artist.collections?.map(item => <option key={item.id} value={item.slug}>{item.name} · {formatCount(item.work_count)}</option>)}{museum && !artist.collections?.some(item => item.slug === museum) && <option value={museum}>{museum}</option>}</select></label>
        {filtered && <button type="button" onClick={resetFilters}>Clear artwork filters</button>}
      </form>
      {page && <p className={styles.matchingCount}>{formatCount(page.matching_total)} matching {page.matching_total === 1 ? "work" : "works"}{imageOnly ? " with pictures" : ""}. {page.items.length} shown on this page.</p>}
      <div aria-busy={request.loading}>
        {request.error ? <div role="alert" className={styles.empty}><h3>We couldn’t load the chronology</h3><p>{request.error}</p><button onClick={() => setRetry(value => value + 1)}>Retry chronology</button><button onClick={resetFilters}>Reset artwork filters</button></div> : !page ? <p className={styles.empty}>Finding recorded artworks…</p> : page.items.length ? <>
          {embedded ? page.groups.map(group => <section key={group.year ?? "undated"} className={styles.yearGroup} aria-label={group.year===null ? "Undated artworks" : `Artworks grouped at ${group.year}`}><h3>{group.year ?? "Undated"}{group.year!==null && group.has_uncertain_dates && <small>Recorded date or range boundary</small>}</h3><div className="works-list">{works.slice(group.start_index,group.start_index+group.count).map(work => <button key={work.id} className={`work-card work-row${selectedID===work.id ? " is-selected" : ""}`} aria-pressed={selectedID===work.id} onClick={() => choose(work.id)}><ArtworkImage work={work} /><span className="work-row-copy"><span className="work-date">{work.date_display}</span><span className="work-title">{work.title}</span><span className="work-location">{work.creation_place_display ? `Made in ${work.creation_place_display}` : "Creation place not established"}</span><span className="work-location">{work.current_location_text ? `Held at ${work.current_location_text}` : "Current location not recorded"}</span></span></button>)}</div></section>) : <div className={styles.gallery}>{works.map(work => <button key={work.id} type="button" className={`work-card ${styles.galleryCard}${selectedID===work.id ? " is-selected" : ""}`} aria-label={`View ${work.title}`} aria-pressed={selectedID===work.id} onClick={() => choose(work.id)}><ArtworkImage work={work} /><span className="work-title">{work.title}</span><span className="work-date">{work.date_display}</span>{work.holding && <span className={styles.holding}>{work.holding.name}</span>}{work.attribution_role !== "primary" && <span className={styles.holding}>{work.attribution_role.replaceAll("_", " ")}</span>}</button>)}</div>}
          {(cursor || page.next_cursor) && <nav className={styles.pagination} aria-label="Artwork chronology pages"><span>{paging.number ? `Page ${paging.number} · ` : ""}{page.items.length} of {formatCount(page.matching_total)} matching works</span><div>{cursor && <button onClick={paging.first}>First artworks</button>}<button disabled={!paging.canPrevious} onClick={paging.previous}>Previous artworks</button>{page.next_cursor && <button onClick={() => paging.next(page.next_cursor)}>Next artworks</button>}</div></nav>}
        </> : <div className={styles.empty}><h3>{filtered ? "No matching artworks" : "No artworks recorded yet"}</h3><p>{filtered ? "Try another title, year, work type or collection. Missing catalogue records do not imply the artist made no works in that period." : "Artworks will appear as they are documented in the catalogue."}</p>{filtered && <button type="button" onClick={resetFilters}>Clear artwork filters</button>}</div>}

      </div>
      {summary && (!empty || !filtered) && <div className={styles.dateSummary}>
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
