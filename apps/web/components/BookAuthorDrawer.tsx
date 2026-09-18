"use client";

import { authorLifespanLabel, type TimelineAuthor } from "@/lib/books";
import { RecordDrawer } from "./RecordDrawer";
import styles from "./Books.module.css";

export function BookAuthorDrawer({ author, close, onBooks }: { author: TimelineAuthor; close: () => void; onBooks: () => void }) {
  return <RecordDrawer label="Book author details" closeLabel="Close author details" recordKey={author.id} title="Book author" close={close} fallbackFocusId="books-timeline">
    <div className={styles.drawerContent}>
      <header className={styles.bookHeading}><p>Author</p><h2>{author.name}</h2><p>{authorLifespanLabel(author)}</p></header>
      <section className={styles.bookAbout} aria-labelledby="author-about"><h3 id="author-about">About the author</h3><p>{author.description || "A biography has not yet been established for this creator."}</p></section>
      <div className={`artwork-details ${styles.bookFacts}`}><dl>
        <div><dt>Born</dt><dd>{author.birth || "Not recorded"}</dd></div>
        <div><dt>Died</dt><dd>{author.death || "Not recorded"}</dd></div>
      </dl></div>
      {author.credits.filter(credit => credit !== "Author").map(credit => <p key={credit} className={styles.recordNote}>{credit}</p>)}
      <p className={styles.recordNote}>Life dates are shown as recorded, including approximate ranges.</p>
      <p><button type="button" className={styles.authorBooksButton} onClick={onBooks}>Show books by this author</button></p>
      {author.sourceUrl && <p className={styles.recordNote}><a href={author.sourceUrl} target="_blank" rel="noreferrer">Creator source ↗</a></p>}
    </div>
  </RecordDrawer>;
}
