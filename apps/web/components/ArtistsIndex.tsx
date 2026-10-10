"use client";

import { BookmarkButton } from "./Bookmarks";
import Link from "next/link";
import { useRef, useState } from "react";
import { countryName } from "@/lib/api";
import type { ArtistBrowsePage } from "@/lib/types";
import { updateQuery, useQueryString } from "@/lib/url-state";
import { AtlasFilters, AtlasSelect, AtlasCheckbox, ActiveFilters } from "./AtlasFilters";
import { AtlasPageHeader } from "./AtlasPageHeader";
import { MultiSelectFilter } from "./MultiSelectFilter";
import { useCatalogueRequest } from "./museum-state";
import { formatCount } from "./use-cursor-paging";
import styles from "@/app/artists/directory.module.css";

export function ArtistsIndex({ initialPage, initialQuery }: { initialPage: ArtistBrowsePage; initialQuery: string }) {
  const params = new URLSearchParams(useQueryString(initialQuery ? `?${initialQuery}` : ""));
  const search = useRef<HTMLInputElement>(null);
  const [retry, setRetry] = useState(0);
  const request = new URLSearchParams();
  for (const key of ["q", "country", "movement", "sort", "popular", "women", "cursor"]) params.getAll(key).forEach(value => request.append(key, value));
  const { data, previousData, loading, error } = useCatalogueRequest<ArtistBrowsePage>(`artists?${request}`, retry, initialPage);
  const facets = data?.facets ?? previousData?.facets ?? initialPage.facets;
  const query = params.get("q") ?? "", countries = params.get("country") ? [params.get("country")!.toLowerCase()] : [], movements = params.get("movement") ? [params.get("movement")!] : [];
  const popular = params.get("popular") === "true", women = params.get("women") === "true", sort = params.get("sort") ?? "popular";
  const countryOptions = facets.countries.map(option => ({ ...option, slug: option.slug.toLowerCase() }));
  const change = (values: Record<string, string | string[] | null>, push = true) => updateQuery({ ...values, cursor: null }, push);
  const clear = () => change({ q: null, country: null, movement: null, popular: null, women: null, sort: null });
  const filters = [
    ...(query ? [{ key: "q", label: `Search: ${query}`, remove: () => change({ q: null }) }] : []),
    ...(popular ? [{ key: "popular", label: "Top 1,000 cohort", remove: () => change({ popular: null }) }] : []),
    ...(women ? [{ key: "women", label: "Women artists", remove: () => change({ women: null }) }] : []),
    ...countries.map(value => ({ key: `country-${value}`, label: countryOptions.find(option => option.slug === value)?.name ?? countryName(value.toUpperCase()), remove: () => change({ country: countries.filter(item => item !== value) }) })),
    ...movements.map(value => ({ key: `movement-${value}`, label: facets.movements.find(option => option.slug === value)?.name ?? value.replaceAll("-", " "), remove: () => change({ movement: movements.filter(item => item !== value) }) })),
  ];
  const next = new URLSearchParams(params); next.set("cursor", data?.next_cursor ?? "");
  const first = new URLSearchParams(params); first.delete("cursor");
  function go(cursor: string | null) { updateQuery({ cursor }, true); document.getElementById("artist-results-title")?.focus(); }
  return <main id="main-content" className={styles.page}>
    <AtlasPageHeader title="Artists"><Link href="/">Explore the timeline</Link></AtlasPageHeader>
    <AtlasFilters searchRef={search} query={query} onQuery={value => change({ q: value || null }, false)} onReset={clear} searchLabel="Search artists" placeholder="Artist name or alternative spelling" columns={3} activeCount={filters.filter(filter => filter.key !== "q").length}>
      <MultiSelectFilter label="Countries" allLabel="All countries" options={countryOptions} values={countries} single onChange={values => change({ country: values[0]?.toUpperCase() ?? null })} helpText="Choose an artist’s recorded country association." />
      <MultiSelectFilter label="Movements" allLabel="All movements" options={facets.movements} values={movements} single onChange={values => change({ movement: values[0] ?? null })} helpText="Choose an artistic movement." />
      <AtlasSelect label="Order" value={sort} onChange={value => change({ sort: value })} options={[{ value: "popular", label: "Popularity" }, { value: "name", label: "Name A–Z" }]} />
      <AtlasCheckbox label="Top 1,000 cohort" checked={popular} onChange={checked => change({ popular: checked ? "true" : null })} />
      <AtlasCheckbox label="Women artists" checked={women} onChange={checked => change({ women: checked ? "true" : null })} />
    </AtlasFilters>
    <ActiveFilters filters={filters} onClear={clear} searchRef={search} />
    <div className={styles.resultsHeading}><h2 id="artist-results-title" tabIndex={-1} aria-live="polite">{loading ? "Finding artists…" : error ? "Connection interrupted" : `${formatCount(data?.total ?? 0)} ${data?.total === 1 ? "artist" : "artists"}`}</h2><p>{sort === "name" ? "Alphabetical by catalogue name" : "Popularity uses the Pantheon cohort; it is not a ranking of artistic quality."}</p></div>
    <section aria-label="Artist results" aria-busy={loading}>
      {error ? <div className={styles.empty} role="alert"><h3>We couldn’t load this view</h3><p>{error}</p><button type="button" onClick={() => setRetry(value => value + 1)}>Try again</button></div> : loading ? <p className={styles.empty}>Finding artists…</p> : data?.items.length ? <ul className={styles.artists}>{data.items.map(artist => <li key={artist.id} className="bookmark-grid-item artist-bookmark-card"><Link href={`/artists/${artist.slug}`} prefetch={false}>
        <h3>{artist.name}</h3><p className={styles.dates}>{artist.date_display}</p>
        <p className={styles.context}>{artist.movement.name !== "Unclassified" && <span>{artist.movement.name}</span>}{artist.countries.length > 0 && <span>{artist.countries.map(countryName).join(", ")}</span>}</p>
        <span className={styles.works}>{formatCount(artist.artwork_count)} recorded {artist.artwork_count === 1 ? "work" : "works"}</span>
      </Link><BookmarkButton kind="artist" id={artist.id} title={artist.name} compact /></li>)}</ul> : <div className={styles.empty}><h3>No artists match these filters</h3><p>Try another spelling, or broaden the country and movement filters.</p><button type="button" onClick={clear}>Show all artists</button></div>}
    </section>
    {data && <nav className={styles.pagination} aria-label="Artist directory pages"><span>{data.items.length} shown on this page</span><div>{params.has("cursor") && <Link href={`/artists?${first}`} prefetch={false} onClick={event => { if (!event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey && event.button === 0) { event.preventDefault(); go(null); } }}>First artists</Link>}{data.next_cursor && <Link href={`/artists?${next}`} prefetch={false} onClick={event => { if (!event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey && event.button === 0) { event.preventDefault(); go(data.next_cursor); } }}>Next artists</Link>}</div></nav>}
  </main>;
}
