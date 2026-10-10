"use client";
import { BookmarkButton } from "./Bookmarks";

import { displayMetadata } from "@/lib/display-metadata";
import { useEffect, useState } from "react";
import { apiRequest, errorMessage, safeSourceURL } from "@/lib/api";
import type { Book, BookDetails } from "@/lib/books";
import { RecordArrows, type RecordNavigation } from "./RecordNavigation";
import { BookCover } from "./BookCover";
import { BookOverview } from "./BookOverview";
import { RecordDrawer } from "./RecordDrawer";
import { LoadingIndicator } from "./LoadingIndicator";
import styles from "./Books.module.css";

export function BookDrawer({ id, items, close, select, navigation, fallbackFocusId = "books-timeline" }: {
  id: string; items: Book[]; close: () => void; select: (id: string) => void; fallbackFocusId?: string; navigation?: RecordNavigation;
}) {
  const entry = items.find(book => book.id === id);
  const cached = entry && !entry.summary ? entry : undefined;
  const index = items.findIndex(book => book.id === id);
  const [retry, setRetry] = useState(0);
  const [result, setResult] = useState<{ id: string; attempt: number; book?: BookDetails; error?: string }>();
  useEffect(() => {
    if (cached) return;
    const controller = new AbortController();
    apiRequest<BookDetails>(`books/${encodeURIComponent(id)}`, { signal: controller.signal })
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
    navigation={navigation ? <RecordArrows navigation={navigation} noun="book" /> : <nav className="painter-navigation" aria-label="Browse books">
      <button type="button" aria-label="Previous book" disabled={index <= 0} onClick={() => select(items[index - 1].id)}>←</button>
      <button type="button" aria-label="Next book" disabled={index < 0 || index >= items.length - 1} onClick={() => select(items[index + 1].id)}>→</button>
    </nav>}>
    {error ? <div className={styles.drawerState} role="alert"><h2>Book unavailable</h2><p>{error}</p><button type="button" onClick={() => setRetry(value => value + 1)}>Retry book</button></div> :
      !book ? <p className={styles.drawerState} role="status"><LoadingIndicator label="Opening book record…" /></p> : <div className={styles.drawerContent}>
        <header className={styles.bookHeading}><p>{displayMetadata(book.author)}{lifespan && lifespan.length < 40 && <> · {lifespan}</>}</p><div className="bookmark-title"><h2 id="book-record-title">{book.title}</h2><BookmarkButton kind="book" id={book.id} title={book.title} /></div>{displayMetadata(book.years) && <p>{book.years}</p>}</header>
        <div className={styles.drawerCover}><BookCover book={book} /></div>
        {(book.overview || displayMetadata(book.description)) && <section className={styles.bookAbout} aria-labelledby="book-description-title"><h3 id="book-description-title">About this book</h3>{book.overview ? <BookOverview overview={book.overview} /> : <p>{book.description}</p>}</section>}
        {(book.creators?.length || displayMetadata(book.author)) ? <section className={styles.creators} aria-labelledby="book-creators-title">
          <h3 id="book-creators-title">{book.creators?.length === 1 ? "About the creator" : "About the creators"}</h3>
          {book.creators?.length ? book.creators.map(creator => <article key={creator.id}>
            <h4>{creator.name}</h4>
            {creator.credit && creator.credit !== "Author" && <p className={styles.lifespan}>{creator.credit}</p>}
            {(creator.birth || creator.death) && <p className={styles.lifespan}>{[displayMetadata(creator.birth) && `Born ${creator.birth}`, displayMetadata(creator.death) && `Died ${creator.death}`].filter(Boolean).join(" · ")}</p>}
            {creator.overview ? <BookOverview overview={creator.overview} /> : displayMetadata(creator.description) ? <p>{creator.description}</p> : null}
            <a href={creator.sourceUrl} target="_blank" rel="noreferrer">Creator source ↗</a>
          </article>) : <h4>{displayMetadata(book.author)}</h4>}
        </section> : null}
        <div className={`artwork-details ${styles.bookFacts}`}><dl>
          {displayMetadata(book.author) && <div><dt>Author</dt><dd>{book.author}</dd></div>}
          {displayMetadata(book.years) && <div><dt>Dates</dt><dd>{book.years}</dd></div>}
          {displayMetadata(book.era) && <div><dt>Collection</dt><dd>{book.era}</dd></div>}
          {displayMetadata(book.theme) && <div><dt>Ideas and themes</dt><dd>{book.theme}</dd></div>}
        </dl></div>
        {displayMetadata(book.dateBasis) && <p className={styles.recordNote}>{book.dateBasis}</p>}
        {book.dateSources?.map(source => <p key={source.url} className={styles.recordNote}><a href={safeSourceURL(source.url)} target="_blank" rel="noreferrer">Dating source: {source.name} ↗</a></p>)}
        {book.sourceUrl && <p className={styles.recordNote}><a href={book.sourceUrl} target="_blank" rel="noreferrer">Book source ↗</a></p>}
      </div>}
  </RecordDrawer>;
}
