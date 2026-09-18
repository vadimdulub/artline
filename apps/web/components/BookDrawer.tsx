"use client";

import { useEffect, useState } from "react";
import { apiRequest, errorMessage } from "@/lib/api";
import type { Book } from "@/lib/books";
import { BookCover } from "./BookCover";
import { RecordDrawer } from "./RecordDrawer";
import { LoadingIndicator } from "./LoadingIndicator";
import styles from "./Books.module.css";

export function BookDrawer({ id, items, close, select, fallbackFocusId = "books-timeline" }: {
  id: string; items: Book[]; close: () => void; select: (id: string) => void; fallbackFocusId?: string;
}) {
  const cached = items.find(book => book.id === id);
  const index = items.findIndex(book => book.id === id);
  const [retry, setRetry] = useState(0);
  const [result, setResult] = useState<{ id: string; attempt: number; book?: Book; error?: string }>();
  useEffect(() => {
    if (cached) return;
    const controller = new AbortController();
    apiRequest<Book>(`books/${encodeURIComponent(id)}`, { signal: controller.signal })
      .then(book => { if (!controller.signal.aborted) setResult({ id, attempt: retry, book }); })
      .catch(error => { if (!controller.signal.aborted) setResult({ id, attempt: retry, error: errorMessage(error) }); });
    return () => controller.abort();
  }, [id, cached, retry]);
  const book = cached ?? (result?.id === id && result.attempt === retry ? result.book : undefined);
  const error = !cached && result?.id === id && result.attempt === retry ? result.error : undefined;
  const creator = book?.creators?.length === 1 ? book.creators[0] : undefined;
  const lifespan = creator?.birth && creator?.death ? `${creator.birth}–${creator.death}` : creator?.birth ? `born ${creator.birth}` : "";

  return <RecordDrawer label="Book details" closeLabel="Close book details" recordKey={id} close={close} fallbackFocusId={fallbackFocusId}
    title={index >= 0 ? `Book ${index + 1} of ${items.length}` : "Book record"}
    navigation={<nav className="painter-navigation" aria-label="Browse books">
      <button type="button" aria-label="Previous book" disabled={index <= 0} onClick={() => select(items[index - 1].id)}>←</button>
      <button type="button" aria-label="Next book" disabled={index < 0 || index >= items.length - 1} onClick={() => select(items[index + 1].id)}>→</button>
    </nav>}>
    {error ? <div className={styles.drawerState} role="alert"><h2>Book unavailable</h2><p>{error}</p><button type="button" onClick={() => setRetry(value => value + 1)}>Retry book</button></div> :
      !book ? <p className={styles.drawerState} role="status"><LoadingIndicator label="Opening book record…" /></p> : <div className={styles.drawerContent}>
        <header className={styles.bookHeading}><p>{book.author}{lifespan && lifespan.length < 40 && <> · {lifespan}</>}</p><h2 id="book-record-title">{book.title}</h2><p>{book.years}</p></header>
        <div className={styles.drawerCover}><BookCover book={book} /></div>
        <section className={styles.bookAbout} aria-labelledby="book-description-title"><h3 id="book-description-title">About this book</h3><p>{book.description}</p></section>
        <section className={styles.creators} aria-labelledby="book-creators-title">
          <h3 id="book-creators-title">{book.creators?.length === 1 ? "About the creator" : "About the creators"}</h3>
          {book.creators?.length ? book.creators.map(creator => <article key={creator.id}>
            <h4>{creator.name}</h4>
            {creator.credit && creator.credit !== "Author" && <p className={styles.lifespan}>{creator.credit}</p>}
            <p className={styles.lifespan}>{creator.kind === "collective" ? "Collective authorship · no single lifespan" : creator.kind === "unknown" && !creator.birth && !creator.death ? "Lifespan not established in the source record" : <>{creator.birth ? `Born ${creator.birth}` : "Birth date unknown"} · {creator.death ? `Died ${creator.death}` : "Death date not recorded"}</>}</p>
            <p>{creator.description || "A biography has not yet been established for this creator."}</p>
            <a href={creator.sourceUrl} target="_blank" rel="noreferrer">Creator source ↗</a>
          </article>) : <><h4>{book.author}</h4><p>Creator biographies and lifespan dates have not been established for this record.</p></>}
        </section>
        <div className={`artwork-details ${styles.bookFacts}`}><dl>
          <div><dt>Author</dt><dd>{book.author}</dd></div>
          <div><dt>Dates</dt><dd>{book.years}</dd></div>
          <div><dt>Collection</dt><dd>{book.era}</dd></div>
          <div><dt>Ideas and themes</dt><dd>{book.theme}</dd></div>
        </dl></div>
        <p className={styles.recordNote}>{book.dateBasis || "Dates may refer to composition or publication."} Approximate dates retain their original labels.</p>
        {book.sourceUrl && <p className={styles.recordNote}><a href={book.sourceUrl} target="_blank" rel="noreferrer">Book source ↗</a> · {book.status === "review" ? "Research record · awaiting review" : "Source record"}</p>}
      </div>}
  </RecordDrawer>;
}
