"use client";

import { BookmarkButton } from "./Bookmarks";
import Link from "@/components/MemberLink";
import { artworkDate } from "@/lib/display-metadata";
import { useRef, useState } from "react";
import { updateQuery, useQueryString } from "@/lib/url-state";
import { AtlasFilters, AtlasCheckbox } from "./AtlasFilters";
import { AtlasPageHeader } from "./AtlasPageHeader";
import { ArtworkImage } from "./ArtworkViewer";
import { AllArtworkDrawer } from "./AllArtworkDrawer";
import { useMuseumRequest } from "./museum-state";
import { MuseumError } from "./MuseumFilters";
import { CursorPager } from "./CursorPager";
import { formatCount, useCursorPaging } from "./use-cursor-paging";
import styles from "./Museums.module.css";
import recordStyles from "./ArtworksIndex.module.css";

type Item = { id: string; title: string; creator: string; date_display: string; status: string; media_url: string | null; alt_text: string | null; rights_status: string | null; museum: { id: string; slug: string; name: string } | null };
type Page = { items: Item[]; total: number; next_cursor: string };

export function ArtworksIndex() {
  const search = useRef<HTMLInputElement>(null);
  const params = new URLSearchParams(useQueryString());
  const query = params.get("q") ?? "", status = params.get("status") ?? "";
  const undated = params.get("undated") === "true", pictures = params.get("image_only") === "true";
  const cursor = params.get("cursor") ?? "", selected = params.get("work") ?? "";
  const [retry, setRetry] = useState(0);
  const request = new URLSearchParams({ limit: "24" });
  for (const key of ["q", "status", "undated", "image_only"]) if (params.get(key)) request.set(key, params.get(key)!);
  const paging = useCursorPaging(request.toString(), cursor, value => { updateQuery({ cursor: value, work: null }, true); document.getElementById("artwork-results-title")?.focus(); });
  if (cursor) request.set("cursor", cursor);
  const result = useMuseumRequest<Page>(`artworks?${request}`, retry);
  const change = (values: Record<string, string | null>) => updateQuery({ ...values, cursor: null, work: null });
  const reset = () => change({ q: null, status: null, undated: null, image_only: null });
  return <main id="main-content" className={styles.page}>
    <AtlasPageHeader title="Artworks" description="Explore artworks across the catalogue."><Link href="/museums">Museums and collections</Link></AtlasPageHeader>
    <AtlasFilters searchRef={search} query={query} onQuery={value => change({ q: value || null })} onReset={reset} placeholder="Artwork title" searchLabel="Search artworks" columns={2} activeCount={Number(Boolean(status)) + Number(undated) + Number(pictures)}>
      <AtlasCheckbox label="Undated works" checked={undated} onChange={value => change({ undated: value ? "true" : null })} />
      <AtlasCheckbox label="With pictures" checked={pictures} onChange={value => change({ image_only: value ? "true" : null })} />
    </AtlasFilters>
    <div className={styles.resultsHeading}><h2 id="artwork-results-title" tabIndex={-1}>Explore the catalogue</h2><p role="status">{result.loading ? "Finding artworks…" : result.error ? "Connection interrupted" : `${formatCount(result.data?.total ?? 0)} artworks`}</p></div>
    <section aria-label="Artwork results" aria-busy={result.loading}>
      {result.error ? <MuseumError message={result.error} retry={() => setRetry(value => value + 1)} /> : result.loading ? <p className={styles.loading}>Opening artworks…</p> : result.data?.items.length ? <ul className={styles.worksGrid}>{result.data.items.map(work => <li key={work.id} className="bookmark-grid-item">
        <button className={`${styles.workCard} ${recordStyles.card}`} aria-label={`Open ${work.title}`} aria-haspopup="dialog" onClick={() => updateQuery({ work: work.id }, true)}>
          {work.media_url && <span className={styles.workImage}><ArtworkImage work={work} /></span>}
          <span className={styles.workCopy}>{work.creator && <span className={styles.place}>{work.creator}</span>}<strong>{work.title}</strong>{artworkDate(work) && <span>{artworkDate(work)}</span>}{work.museum && <span>{work.museum.name}</span>}</span>
        </button><BookmarkButton kind="artwork" id={work.id} title={work.title} />
      </li>)}</ul> : <div className={styles.empty}><h3>No artworks match these filters</h3><button onClick={reset}>Show all artworks</button></div>}
    </section>
    {result.data && <CursorPager paging={paging} next={result.data.next_cursor} busy={result.loading} total={result.data.total} shown={result.data.items.length} label="Artwork pages" noun="artworks" />}
    {selected && <AllArtworkDrawer id={selected} close={() => updateQuery({ work: null }, true)} fallbackFocusId="artwork-results-title" />}
  </main>;
}
