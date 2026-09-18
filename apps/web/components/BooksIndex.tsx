"use client";

import { useEffect, useRef, useState } from "react";
import { type TimelineAuthor, type BooksResponse, type BooksFacets, bookYearLabel, authorLifespanLabel } from "@/lib/books";
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
  const selectionKey = new URLSearchParams([...params].filter(([key]) => ["women", "top100"].includes(key))).toString();
  const query = params.get("q") || "";
  const requestKey = new URLSearchParams([...params].filter(([key]) => ["q", "author", "start", "end", "after", "women", "top100", "language", "country", "region", "view"].includes(key))).toString();
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
  const error = current ? result?.error : undefined;
  const visibleBooks = data?.items ?? [];
  const selected = params.get("book") ?? "";
  const visibleAuthors = data?.authors ?? [];
  const noun = authorView ? "authors" : "books";

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
    updateQuery({ collection: null, ...values, after: null }, push);
  }

  function reset() {
    change({ ...clearChoices, top100: null, start: null, end: null, view: null });
    setSelectedAuthor(null);
    search.current?.focus();
  }

  function openBook(id: string) { updateQuery({ book: id }, true); }
  function closeBook() { updateQuery({ book: null }); }
  function changePage(after: string | null) {
    updateQuery({ after }, true);
    const heading = document.getElementById("shelf-title");
    heading?.scrollIntoView({ block: "start" });
    heading?.focus({ preventScroll: true });
  }

  const bounds = result?.data?.bounds ?? { start: -5000, end: 2000 };
  const readYear = (key: string, fallback: number) => {
    const raw = params.get(key); return raw && Number.isFinite(Number(raw)) ? Number(raw) : fallback;
  };
  const range = { start: readYear("start", bounds.start), end: readYear("end", bounds.end) };
  const activeFilters = [
    ...(query ? [{ key: "q", label: `Search: ${query}`, remove: () => change({ q: null }) }] : []),
    ...authors.map(value => ({ key: `author-${value}`, label: `Author: ${value}`, remove: () => change({ author: authors.filter(item => item !== value) }) })),
    ...(womenOnly ? [{ key: "women", label: "Women authors", remove: () => change({ women: null }) }] : []),
    ...(top100Only ? [{ key: "top100", label: "Top 100 books", remove: () => change({ top100: "false" }) }] : []),
    ...[{ key: "language", values: languages }, { key: "country", values: countries }, { key: "region", values: regions }].flatMap(group => group.values.map(value => ({ key: `${group.key}-${value}`, label: facetResult.labels[value] ?? value.replaceAll("-", " "), remove: () => change({ [group.key]: group.values.filter(item => item !== value) }) }))),
  ];

  return <div className={styles.page}>
    <section className="explorer books-explorer" aria-labelledby="books-timeline">
      {facetResult.error && <p className="save-message" role="status">Some filter choices could not be loaded. <button onClick={() => setRetry(value => value + 1)}>Retry filters</button></p>}
      <AtlasFilters searchRef={search} query={query} onQuery={value => change({ q: value }, false)} onReset={reset} searchLabel="Find a book or author" placeholder="Book, author, or idea" columns={4} activeCount={activeFilters.filter(f => f.key !== "q").length}>
        <BookFilterFields params={params} change={change} facets={facetResult.data} unavailable={Boolean(facetResult.error)} authorChoices={{options:(authorResult?.query===authorKey?authorResult.items:[]).map(name=>({slug:name,name})),remote:{search:authorSearch,onSearch:setAuthorSearch,loading:authorResult?.query!==authorKey,hasMore:Boolean(authorResult?.hasMore)},retry:()=>setAuthorRetry(v=>v+1),unavailable:Boolean(authorResult?.error)}} />
      </AtlasFilters>
      <ActiveFilters filters={activeFilters} onClear={() => change(clearChoices)} searchRef={search} />
      <BooksTimeline data={data} metadata={result?.data} range={range} loading={loading} error={error} selected={authorView ? selectedAuthor?.id ?? "" : selected}
        authorView={authorView} onAuthorView={checked => { setSelectedAuthor(null); change({ view: checked ? "authors" : null, book: null }); }}
        onSelect={id => { if (authorView) setSelectedAuthor(visibleAuthors.find(author => author.id === id) ?? null); else openBook(id); }} onRange={(start, end) => change({ start: String(start), end: String(end) }, false)}
        onRetry={() => setRetry(value => value + 1)} onReset={reset}
        onSuggestion={suggestion => change({ [suggestion.key]: suggestion.value })} onTop100={() => change({ top100: null })} />
    </section>
    <section className={styles.shelf} aria-labelledby="shelf-title" aria-busy={loading}>
      <div className={styles.shelfHeader}>
        <div><h2 id="shelf-title" tabIndex={-1}>{authorView ? "Author index" : "Book index"}</h2><p>Explore the stories, beliefs, and questions that connect literature, philosophy, religion, and art across time.</p><p>{data ? `${bookYearLabel(data.range.start)} – ${bookYearLabel(data.range.end)}` : ""}</p></div>
        <p className={styles.count} role="status">{data ? `${data.total.toLocaleString("en-GB")} of ${data.selectionTotal.toLocaleString("en-GB")} ${noun}` : ""}</p>
      </div>
      <ul className={styles.bookIndex} aria-label={authorView ? "Author index" : "Book index"}>
        {authorView && visibleAuthors.map(author => <li key={author.id} data-selected={selectedAuthor?.id === author.id}>
          <button type="button" aria-label={`Open author ${author.name}`} aria-haspopup="dialog" onClick={() => setSelectedAuthor(author)}>
            <strong>{author.name}</strong><span>{author.bookCount} {author.bookCount === 1 ? "book" : "books"} in this selection</span><time>{authorLifespanLabel(author)}</time>
          </button>
        </li>)}
        {!authorView && visibleBooks.map(book => <li key={book.id} id={`book-${book.id}`} data-selected={selected === book.id}>
          <button type="button" aria-label={`Open ${book.title} by ${book.author}`} aria-haspopup="dialog" onClick={() => openBook(book.id)}>
            <strong>{book.title}</strong><span>{book.author}</span><time>{book.years}</time>
          </button>
        </li>)}
      </ul>
      {data && (data.hasMore || params.has("after")) && <nav className={styles.pagination} aria-label={authorView ? "Author pages" : "Book pages"}>
        {params.has("after") && <button onClick={() => changePage(null)}>First page</button>}
        <span>{authorView ? visibleAuthors.length : visibleBooks.length} {noun} on this page</span>
        {data.hasMore && <button onClick={() => changePage(data.nextCursor)}>Next {noun}</button>}
      </nav>}
      <p className={styles.footerNote}>Explore widely documented works alongside our original editorial selection. Source-linked records are being reviewed; encyclopedia coverage is one indication of recognition, not a definitive ranking of importance. Unknown dates remain unplaced on the timeline.</p>
    </section>
    {authorView && selectedAuthor && <BookAuthorDrawer author={selectedAuthor} close={() => setSelectedAuthor(null)} onBooks={() => { change({ view: null, author: selectedAuthor.name, start: null, end: null, book: null }); setSelectedAuthor(null); }} />}
    {selected && <BookDrawer id={selected} items={visibleBooks} close={closeBook} select={id => updateQuery({ book: id })} />}
  </div>;
}
