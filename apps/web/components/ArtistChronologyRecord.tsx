"use client";
import { useState } from "react";
import type { ArtistDetail, ArtistWorksPage, Artwork } from "@/lib/types";
import { updateQuery, useQueryString } from "@/lib/url-state";
import { ArtistRecord } from "./ArtistRecord";
import { ArtworkImage } from "./ArtworkViewer";
import { useMuseumRequest } from "./museum-state";
import { formatCount, useCursorPaging } from "./use-cursor-paging";
import styles from "./ArtistChronology.module.css";

export function ArtistChronologyRecord({ artist, workId, onSelectWork }: { artist: ArtistDetail; workId: string | null; onSelectWork: (id: string) => void }) {
  const params = new URLSearchParams(useQueryString());
  const year = params.get("art_year") ?? "", cursor = params.get("art_cursor") ?? "";
  const paging = useCursorPaging(`${artist.id}|${year}`, cursor, value => { updateQuery({ art_cursor: value, work: null }, true); document.getElementById(`works-${artist.id}`)?.focus(); });
  const [retry, setRetry] = useState(0), [help, setHelp] = useState(false);
  const query = new URLSearchParams();
  if (year === "undated") query.set("undated", "1"); else if (year) query.set("year", year);
  if (cursor) query.set("cursor", cursor);
  const request = useMuseumRequest<ArtistWorksPage>(`artists/${artist.slug}/works?${query}`, "", retry);
  const page = request.data, summary = page ?? request.previousData;
  const works = page?.items ?? [];
  const knownWork = works.find(work => work.id === workId) ?? artist.artworks.find(work => work.id === workId);
  const linked = useMuseumRequest<Artwork>(workId && !knownWork ? `artists/${artist.slug}/works/${encodeURIComponent(workId)}` : null, "", retry);
  const start = summary?.range_start ?? artist.timeline_start_year, end = summary?.range_end ?? artist.timeline_end_year;
  const span = Math.max(1, end - start);
  const unknown = summary?.undated_count ?? 0, empty = summary?.total === 0;
  const missingTip = empty ? "We don’t have artwork data for this painter yet. This marker is not a creation date." : `${unknown} ${unknown === 1 ? "artwork has" : "artworks have"} no recorded creation year. They are listed after the dated works; this marker is not a date.`;
  function changeYear(value: string) { updateQuery({ art_year: value || null, art_cursor: null, work: null }); }
  return <ArtistRecord artist={artist} embedded workId={workId} onSelectWork={onSelectWork} artworks={works} linkedWork={knownWork ?? linked.data}
    workMessage={workId && !knownWork && !linked.data ? linked.error ? <div role="alert"><p>{linked.error}</p><button onClick={() => setRetry(value => value + 1)}>Retry artwork</button></div> : <p>Opening linked artwork…</p> : undefined}
    workBrowser={(choose, selectedID) => <div className={styles.chronology}>
      <div className="section-heading"><h2 id={`works-${artist.id}`} tabIndex={-1}>Artworks by year</h2><span role="status">{request.loading ? "Loading chronology…" : request.error ? "Chronology unavailable" : `${formatCount(summary?.total ?? 0)} recorded ${(summary?.total ?? 0) === 1 ? "work" : "works"}`}</span></div>
      {summary && <>
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
        <p className={styles.note}>Recorded works, not a complete lifetime output. Ranges use their first recorded year; approximate and before/after dates keep their original labels.</p>
        {summary.total>0 && <div className={styles.controls}><label><span>Artwork year</span><select value={year} onChange={event => changeYear(event.target.value)}><option value="">All recorded years</option>{summary.years.map(item => <option key={item.year} value={item.year}>{item.year} · {item.count} {item.count === 1 ? "work" : "works"}</option>)}<option value="undated">Undated · {unknown} works</option>{year && year!=="undated" && !summary.years.some(item => String(item.year)===year) && <option value={year}>{year} · no recorded works</option>}</select></label>{year && <button type="button" onClick={() => changeYear("")}>All years</button>}</div>}
      </>}
      <div aria-busy={request.loading}>
        {request.error ? <div role="alert" className={styles.empty}><h3>We couldn’t load the chronology</h3><p>{request.error}</p><button onClick={() => setRetry(value => value + 1)}>Retry chronology</button><button onClick={() => changeYear("")}>Reset artwork filters</button></div> : !page ? <p className={styles.empty}>Finding recorded artworks…</p> : page.items.length ? <>
          {page.groups.map(group => <section key={group.year ?? "undated"} className={styles.yearGroup} aria-label={group.year===null ? "Undated artworks" : `Artworks grouped at ${group.year}`}><h3>{group.year ?? "Undated"}{group.year!==null && group.has_uncertain_dates && <small>Recorded date or range boundary</small>}</h3><div className="works-list">{works.slice(group.start_index,group.start_index+group.count).map(work => <button key={work.id} className={`work-card work-row${selectedID===work.id ? " is-selected" : ""}`} aria-pressed={selectedID===work.id} onClick={() => choose(work.id)}><ArtworkImage work={work} /><span className="work-row-copy"><span className="work-date">{work.date_display}</span><span className="work-title">{work.title}</span><span className="work-location">{work.creation_place_display ? `Made in ${work.creation_place_display}` : "Creation place not established"}</span><span className="work-location">{work.current_location_text ? `Held at ${work.current_location_text}` : "Current location under review"}</span></span></button>)}</div></section>)}
          {(cursor || page.next_cursor) && <nav className={styles.pagination} aria-label="Artwork chronology pages"><span>{paging.number ? `Page ${paging.number} · ` : ""}{page.items.length} of {formatCount(page.matching_total)} matching works</span><div>{cursor && <button onClick={paging.first}>First artworks</button>}<button disabled={!paging.canPrevious} onClick={paging.previous}>Previous artworks</button>{page.next_cursor && <button onClick={() => paging.next(page.next_cursor)}>Next artworks</button>}</div></nav>}
        </> : <div className={styles.empty}><h3>{empty ? "No artworks recorded yet" : year === "undated" ? "No undated works in this catalogue" : `No works recorded for ${year || "this page"}`}</h3><p>{empty ? "The end marker identifies missing catalogue data, not a period when the painter stopped working." : "Missing records do not mean the painter created no artworks during this time."}</p>{!empty && <button onClick={() => changeYear("")}>Show all recorded years</button>}</div>}
      </div>
    </div>} />;
}
