"use client";
import { ExplorerFrame } from "./ExplorerFrame";
import { useFitYears } from "./use-fit-years";
import { timelineRequestKey } from "@/lib/timeline-request";
import { discoveryChanges } from "@/lib/discovery";

import { useEffect, useRef, useState } from "react";
import { type Book, type TimelineAuthor, type BooksResponse, type BooksFacets } from "@/lib/books";
import { apiRequest, errorMessage } from "@/lib/api";
import { updateQuery, useQueryString } from "@/lib/url-state";
import { BooksTimeline } from "./BooksTimeline";
import { AtlasFilters, ActiveFilters } from "./AtlasFilters";
import { BookFilterFields } from "./EntityFilterFields";
import { BookDrawer } from "./BookDrawer";
import { BookAuthorDrawer } from "./BookAuthorDrawer";
import styles from "./Books.module.css";

export function BooksIndex() {
  const queryString = useQueryString();
  const params = new URLSearchParams(queryString);
  if (!params.has("top100")) params.set("top100", "true");
  const authors = [...new Set(params.getAll("author"))];
  const languages = [...new Set(params.getAll("language"))];
  const countries = [...new Set(params.getAll("country"))];
  const regions = [...new Set(params.getAll("region"))];
  const authorView = params.get("view") === "authors";
  const [selectedAuthor, setSelectedAuthor] = useState<TimelineAuthor | null>(null);
  const womenOnly = params.get("women") === "true";
  const top100Only = params.get("top100") === "true";
  const selectionKey = `top100=false&${new URLSearchParams([...params].filter(([key]) => key === "women"))}`;
  const query = params.get("q") || "";
  const requestParams = new URLSearchParams([...params].filter(([key]) => ["fit", "q", "author", "start", "end", "after", "women", "top100", "language", "country", "region", "view"].includes(key)));
  requestParams.set("limit", top100Only ? "500" : "150");
  const requestKey = timelineRequestKey(requestParams, { start: -5000, end: 2000 });
  const [result, setResult] = useState<{ key: string; data?: BooksResponse; error?: string }>();
  const [retry, setRetry] = useState(0);
  const [authorSearch, setAuthorSearch] = useState("");
  const authorKey = `${selectionKey}&q=${encodeURIComponent(authorSearch)}`;
  const [authorRetry, setAuthorRetry] = useState(0);
  const [authorResult, setAuthorResult] = useState<{ query: string; items: string[]; hasMore: boolean; error?: string }>();
  const [facetResult, setFacetResult] = useState<{ data?: BooksFacets; labels: Record<string, string>; error?: string }>({ labels: {} });
  const search = useRef<HTMLInputElement>(null);
  const current = result?.key === requestKey;
  const data = current && !result?.error ? result?.data : undefined;
  const loading = !current;
  useFitYears(params.get("fit") === "true", !!data && current, data?.matchedRange, data?.undatedTotal);
  const error = current ? result?.error : undefined;
  const visibleBooks = data?.items ?? [];
  const selected = params.get("book") ?? "";
  const [drawerBooks, setDrawerBooks] = useState<{ key: string; items: Book[] }>();

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      apiRequest<BooksResponse>(`books?${requestKey}`, { signal: controller.signal })
        .then(data => { if (!controller.signal.aborted) setResult({ key: requestKey, data }); })
        .catch(error => { if (!controller.signal.aborted) setResult(previous => ({ key: requestKey, data: previous?.data, error: errorMessage(error) })); });
    }, 160);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [requestKey, retry]);

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      apiRequest<{ items: string[]; hasMore: boolean }>(`books/authors?${authorKey}`, { signal: controller.signal })
        .then(result => { if (!controller.signal.aborted) setAuthorResult({ query: authorKey, ...result }); })
        .catch(error => { if (!controller.signal.aborted) setAuthorResult({ query: authorKey, items: [], hasMore: false, error: errorMessage(error) }); });
    }, 160);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [authorKey, authorRetry]);

  useEffect(() => {
    const controller = new AbortController();
    apiRequest<BooksFacets>(`books/facets?${selectionKey}`, { signal: controller.signal })
      .then(data => { if (!controller.signal.aborted) setFacetResult(previous => ({ data, labels: { ...previous.labels, ...Object.fromEntries([...data.languages, ...data.countries, ...data.regions].map(option => [option.slug, option.name])) } })); })
      .catch(error => { if (!controller.signal.aborted) setFacetResult(previous => ({ ...previous, error: errorMessage(error) })); });
    return () => controller.abort();
  }, [selectionKey, retry]);

  const clearChoices = { collection: null, author: null, q: null, language: null, country: null, region: null, women: null, top100: "false" };

  function change(values: Record<string, string | string[] | null>, push = true) {
    updateQuery({ collection: null, fit: null, ...discoveryChanges(values, "top100"), after: null }, push);
  }

  function reset() {
    change({ ...clearChoices, top100: null, start: null, end: null, view: null });
    setSelectedAuthor(null);
    search.current?.focus();
  }

  function closeBook() { updateQuery({ book: null }); }

  const bounds = result?.data?.bounds ?? { start: -5000, end: 2000 };
  const readYear = (key: string, fallback: number) => {
    const raw = params.get(key); return raw && Number.isFinite(Number(raw)) ? Number(raw) : fallback;
  };
  const range = { start: readYear("start", bounds.start), end: readYear("end", bounds.end) };
  const activeFilters = [
    ...(query ? [{ key: "q", label: `Search: ${query}`, remove: () => change({ q: null }) }] : []),
    ...authors.map(value => ({ key: `author-${value}`, label: `Author: ${value}`, remove: () => change({ author: authors.filter(item => item !== value) }) })),
    ...(womenOnly ? [{ key: "women", label: "Women authors", remove: () => change({ women: null }) }] : []),
    ...(top100Only ? [{ key: "top100", label: "Book highlights", remove: () => change({ top100: "false" }) }] : []),
    ...[{ key: "language", values: languages }, { key: "country", values: countries }, { key: "region", values: regions }].flatMap(group => group.values.map(value => ({ key: `${group.key}-${value}`, label: facetResult.labels[value] ?? value.replaceAll("-", " "), remove: () => change({ [group.key]: group.values.filter(item => item !== value) }) }))),
  ];

  return <div className={`${styles.page} books-page`}>
    <ExplorerFrame className="explorer books-explorer" aria-labelledby="books-timeline">
      {facetResult.error && <p className="save-message" role="status">Some filter choices could not be loaded. <button onClick={() => setRetry(value => value + 1)}>Retry filters</button></p>}
      <AtlasFilters searchRef={search} query={query} onQuery={value => change({ q: value }, false)} onReset={reset} searchLabel="Find a book or author" placeholder="Book, author, or idea" columns={4} activeCount={activeFilters.filter(f => f.key !== "q").length}>
        <BookFilterFields params={params} change={change} facets={facetResult.data} unavailable={Boolean(facetResult.error)} authorChoices={{options:(authorResult?.query===authorKey?authorResult.items:[]).map(name=>({slug:name,name})),remote:{search:authorSearch,onSearch:setAuthorSearch,loading:authorResult?.query!==authorKey,hasMore:Boolean(authorResult?.hasMore)},retry:()=>setAuthorRetry(v=>v+1),unavailable:Boolean(authorResult?.error)}} />
      </AtlasFilters>
      <ActiveFilters filters={activeFilters} onClear={() => change(clearChoices)} searchRef={search} />
      <BooksTimeline data={data} metadata={result?.data} range={range} loading={loading} error={error} selected={authorView ? selectedAuthor?.id ?? "" : selected}
        authorView={authorView} onAuthorView={checked => { setSelectedAuthor(null); change({ view: checked ? "authors" : null, book: null }); }}
        query={requestKey} onAuthor={setSelectedAuthor} onBook={(book, items) => { setDrawerBooks({ key: requestKey, items }); updateQuery({ book: book.id }, true); }} onRange={(start, end) => change({ start: String(start), end: String(end) }, false)}
        onZoomOut={() => change({ start: null, end: null })} onRetry={() => setRetry(value => value + 1)} onReset={reset} />
    </ExplorerFrame>
    {authorView && selectedAuthor && <BookAuthorDrawer author={selectedAuthor} close={() => setSelectedAuthor(null)} onBooks={() => { change({ view: null, author: selectedAuthor.name, start: null, end: null, book: null }); setSelectedAuthor(null); }} />}
    {selected && <BookDrawer id={selected} items={drawerBooks?.key === requestKey ? drawerBooks.items : visibleBooks} close={closeBook} select={id => updateQuery({ book: id })} />}
  </div>;
}
