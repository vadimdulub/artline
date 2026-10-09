"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { apiRequest, errorMessage } from "@/lib/api";
import { AtlasFilters, AtlasSelect, ActiveFilters } from "./AtlasFilters";
import { AtlasPageHeader } from "./AtlasPageHeader";
import { updateQuery, useQueryString } from "@/lib/url-state";
import type { CatalogueArtist } from "@/lib/types";

export function CatalogueClient() {
  const [artists, setArtists] = useState<CatalogueArtist[]>([]);
  const parameters = new URLSearchParams(useQueryString());
  const query = parameters.get("q") ?? "";
  const searchRef = useRef<HTMLInputElement>(null);
  const setQuery = (value: string) => updateQuery({ q: value || null, page: null }, false);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true), [refresh, setRefresh] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const rawPage = Number(parameters.get("page") ?? "1");
  const page = Number.isSafeInteger(rawPage) && rawPage >= 1 && rawPage <= 10000 ? rawPage - 1 : 0;
  const setPage = (next: number) => updateQuery({ page: next ? String(next + 1) : null }, true);
  const rawSort = parameters.get("sort") ?? "name";
  const sort = ["name", "date", "updated"].includes(rawSort) ? rawSort : "name";
  const setSort = (value: string) => updateQuery({ sort: value === "name" ? null : value, page: null }, true);
  const clearFilters = () => updateQuery({ q: null, status: null, page: null }, true);
  const resetView = () => updateQuery({ q: null, status: null, sort: null, page: null }, true);
  const activeFilters = [
    ...(query ? [{ key: "q", label: `Search: ${query}`, remove: () => setQuery("") }] : []),
  ];
  const requestVersion = JSON.stringify([query, refresh, page, sort]);
  const [settledRequest, setSettledRequest] = useState("");
  const pending = loading || settledRequest !== requestVersion;
  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoading(true); setLoadError("");
      const parameters = new URLSearchParams({ limit: "50", offset: String(page * 50), sort });
      if (query.trim()) parameters.set("q", query.trim());
      apiRequest<{ items: CatalogueArtist[]; has_more: boolean }>(`catalogue/artists?${parameters}`, { signal: controller.signal })
        .then(body => { setArtists(body.items); setHasMore(body.has_more); })
        .catch(error => { if (!controller.signal.aborted) { setLoadError(errorMessage(error)); setArtists([]); } })
        .finally(() => { if (!controller.signal.aborted) { setLoading(false); setSettledRequest(requestVersion); } });
    }, 180);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [query, refresh, page, sort, requestVersion]);

  return <main id="main-content" className="admin-page">
    <AtlasPageHeader title="Catalogue" description="Browse painters and explore their artworks." />
    <AtlasFilters searchRef={searchRef} query={query} onQuery={setQuery} onReset={resetView} searchLabel="Search painters" placeholder="Painter name" columns={1} activeCount={0}>
      <AtlasSelect label="Sort by" value={sort} onChange={setSort} options={[{ value: "name", label: "Name" }, { value: "date", label: "Date" }, { value: "updated", label: "Recently updated" }]} />
    </AtlasFilters>
    <ActiveFilters filters={activeFilters} onClear={clearFilters} searchRef={searchRef} />
    {loadError && <p className="save-message" role="alert">{loadError} <button onClick={() => setRefresh(value => value + 1)}>Try again</button></p>}
    <p className="table-scroll-hint" id="catalogue-scroll-help">Scroll the table sideways to see all details. With the table focused, use the arrow keys.</p>
    <div className="table-shell" tabIndex={0} role="region" aria-label="Painter catalogue" aria-describedby="catalogue-scroll-help" aria-busy={pending}><table><caption className="sr-only">Painter records</caption><thead><tr><th scope="col">Name</th><th scope="col">Dates</th><th scope="col">Updated</th></tr></thead><tbody>{artists.map(artist => <tr key={artist.id}><td><Link href={`/artists/${artist.slug}`}>{artist.display_name}</Link></td><td>{artist.timeline_display}</td><td>{new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(artist.updated_at))}</td></tr>)}</tbody></table>{!artists.length && <div className="table-empty">{pending ? "Loading the catalogue…" : loadError ? "Catalogue unavailable" : "No painters match these filters."}</div>}</div>
    <div className="catalogue-pagination"><button disabled={page === 0 || pending} onClick={() => setPage(page - 1)}>Previous page</button><span role="status">{pending ? "Updating catalogue…" : `Page ${page + 1} · ${artists.length} records`}</span><button disabled={!hasMore || pending} onClick={() => setPage(page + 1)}>Next page</button></div>
  </main>;
}
