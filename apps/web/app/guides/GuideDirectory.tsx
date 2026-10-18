"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { AtlasSearchField } from "@/components/AtlasSearchField";
import { useCatalogueRequest } from "@/components/museum-state";
import { updateQuery, useQueryString } from "@/lib/url-state";
import type { GuideSearchPage } from "@/lib/guide-search";
import styles from "./guides.module.css";

const kinds = [{ value: "", label: "All guides" }, { value: "artist", label: "Artists" }, { value: "museum", label: "Museums" }, { value: "interactive", label: "Interactive" }, { value: "using", label: "Using Artline" }] as const;

export function GuideDirectory({ initialPage, initialQuery }: { initialPage?: GuideSearchPage; initialQuery: string }) {
  const params = new URLSearchParams(useQueryString(initialQuery ? `?${initialQuery}` : ""));
  const request = new URLSearchParams();
  for (const key of ["q", "kind", "cursor", "institution"]) params.getAll(key).forEach(value => request.append(key, value));
  const query = params.get("q") ?? "", kind = params.get("kind") ?? "";
  const [retry, setRetry] = useState(0);
  const search = useRef<HTMLInputElement>(null);
  const { data, loading, error } = useCatalogueRequest<GuideSearchPage>(`guides?${request}`, retry, initialPage, true);
  const change = (values: Record<string, string | null>, push = true) => updateQuery({ ...values, cursor: null }, push);
  const clear = () => { change({ q: null, kind: null, institution: null }); search.current?.focus(); };
  function go(cursor: string | null) {
    updateQuery({ cursor }, true);
    document.getElementById("guide-results-title")?.focus();
  }
  const next = new URLSearchParams(request); next.set("cursor", data?.next_cursor ?? "");
  const first = new URLSearchParams(request); first.delete("cursor");
  return <>
    <div className={styles.searchPanel}>
      <AtlasSearchField label="Search guides" placeholder="Search artists, museums, places or keywords…" value={query} onChange={value => change({ q: value || null }, false)} inputRef={search} />
      <p className={styles.searchHint}>{params.has("institution") ? "Showing Artline guides for this museum. Clear filters to explore all guides." : "Find a place to begin. Search by name, subject or location."}</p>
      <div className={`${styles.filters} catalogue-selection`} role="group" aria-label="Guide types">
        {kinds.map(option => <button key={option.value} type="button" aria-pressed={kind === option.value} onClick={() => change({ kind: option.value || null })}>{option.label}{data && <span>{data.counts[option.value || "all"]}</span>}</button>)}
      </div>
    </div>
    <div className={styles.resultsHeading}>
      <h2 id="guide-results-title" tabIndex={-1} aria-live="polite">{loading ? "Finding guides…" : error ? "Guides unavailable" : `${data?.matched ?? 0} ${data?.matched === 1 ? "guide" : "guides"}${query.trim() ? ` for “${query.trim()}”` : " to explore"}`}</h2>
      {(query || kind || params.has("institution")) && <button type="button" onClick={clear}>Clear filters</button>}
    </div>
    <section aria-label="Guide results" aria-busy={loading}>
      {error ? <div className={styles.empty} role="alert"><h3>We couldn’t load these guides</h3><p>{error}</p><button type="button" onClick={() => setRetry(value => value + 1)}>Try again</button><button type="button" onClick={clear}>Show all guides</button></div>
        : loading ? <p className={styles.empty}>Finding guides…</p>
        : data?.items.length ? <div className={styles.museumGrid}>{data.items.map(guide => <article key={guide.slug} className={styles.museum}>
          {guide.image && <Link href={guide.href} prefetch={false} className={styles.museumImage} tabIndex={-1} aria-hidden="true"><img src={guide.image} alt="" width="600" height="420" loading="lazy" /></Link>}
          <p className={styles.city}>{guide.kind === "artist" ? "Artist guide · " : guide.kind === "museum" ? "Museum guide · " : guide.kind === "interactive" ? "Interactive guide · " : ""}{guide.location}</p>
          <h3><Link href={guide.href} prefetch={false}>{guide.kind === "museum" ? guide.title : guide.label}</Link></h3>
          <p>{guide.subtitle}</p>
          {guide.kind === "interactive" ? <span className={styles.editions}>{guide.count} patterns · {guide.languages} languages</span> : guide.count > 0 ? <span className={styles.editions}>{guide.count} artworks · {guide.languages} languages · PDF</span> : <Link className={styles.read} href={guide.href}>Read the guide</Link>}
        </article>)}</div>
        : <div className={styles.empty}><h3>No guides found</h3><p>Try another name or place, or explore all the guides.</p><button type="button" onClick={clear}>Show all guides</button></div>}
    </section>
    {data && data.matched > 0 && <nav className={`${styles.pagination} catalogue-pagination`} aria-label="Guide directory pages"><span>{data.items.length} shown on this page</span><div>
      {params.has("cursor") && <Link href={`/guides?${first}`} prefetch={false} onClick={event => { if (!event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey && event.button === 0) { event.preventDefault(); go(null); } }}>First guides</Link>}
      {data.next_cursor && <Link href={`/guides?${next}`} prefetch={false} onClick={event => { if (!event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey && event.button === 0) { event.preventDefault(); go(data.next_cursor); } }}>Next guides <span aria-hidden="true">→</span></Link>}
    </div></nav>}
  </>;
}
