"use client";

import { displayMetadata } from "@/lib/display-metadata";
import { authorLifespanLabel, type TimelineAuthor } from "@/lib/books";
import { RecordDrawer } from "./RecordDrawer";
import { LibraryImage } from "./BooksGallery";
import { BookOverview } from "./BookOverview";
import styles from "./Books.module.css";

export function BookAuthorDrawer({ author, close, onBooks }: { author: TimelineAuthor; close: () => void; onBooks: () => void }) {
  return <RecordDrawer label="Book author details" closeLabel="Close author details" recordKey={author.id} title="Book author" close={close} fallbackFocusId="books-timeline">
    <div className={styles.drawerContent}>
      <header className={styles.bookHeading}><p>Author</p><h2>{author.name}</h2><p>{authorLifespanLabel(author)}</p></header>
      {author.portrait && <figure className="author-portrait"><LibraryImage image={author.portrait} name={author.name} portrait /><figcaption>{author.portrait.credit} · <a href={author.portrait.sourceUrl} target="_blank" rel="noreferrer">Image source ↗</a> · <a href={author.portrait.licenseUrl} target="_blank" rel="noreferrer">{author.portrait.license}</a></figcaption></figure>}
      {(author.overview || displayMetadata(author.description)) && <section className={styles.bookAbout} aria-labelledby="author-about"><h3 id="author-about">About the author</h3>{author.overview ? <BookOverview overview={author.overview} /> : <p>{author.description}</p>}</section>}
      <div className={`artwork-details ${styles.bookFacts}`}><dl>
        {displayMetadata(author.birth) && <div><dt>Born</dt><dd>{author.birth}</dd></div>}
        {displayMetadata(author.death) && <div><dt>Died</dt><dd>{author.death}</dd></div>}
      </dl></div>
      {author.credits.filter(credit => credit !== "Author").map(credit => <p key={credit} className={styles.recordNote}>{credit}</p>)}
      <p><button type="button" className={styles.authorBooksButton} onClick={onBooks}>Show books by this author</button></p>
      {author.sourceUrl && <p className={styles.recordNote}><a href={author.sourceUrl} target="_blank" rel="noreferrer">Creator source ↗</a></p>}
    </div>
  </RecordDrawer>;
}
