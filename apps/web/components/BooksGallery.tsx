"use client";
import { displayMetadata } from "@/lib/display-metadata";

import { useState, type CSSProperties, type RefObject } from "react";
import { authorLifespanLabel, type Book, type BooksResponse, type TimelineAuthor } from "@/lib/books";
import { LoadingIndicator } from "./LoadingIndicator";
import { useGalleryScroll } from "./use-gallery-scroll";
import "./BooksGallery.css";

type Entry = Book | TimelineAuthor;
const isAuthor = (entry: Entry): entry is TimelineAuthor => "bookCount" in entry;
const readBooks = (response: BooksResponse) => ({ items: response.items as Entry[], nextCursor: response.nextCursor });
const readAuthors = (response: BooksResponse) => ({ items: (response.authors ?? []) as Entry[], nextCursor: response.nextCursor });

export function LibraryImage({ image, name, portrait = false }: { image?: Book["cover"]; name: string; portrait?: boolean }) {
  const [failed, setFailed] = useState("");
  return <span className={`library-image${portrait ? " library-portrait" : ""}`}>
    {image && failed !== image.imageUrl ?
      // Only selected, attributed reproductions are supplied by the API.
      // eslint-disable-next-line @next/next/no-img-element
      <img src={image.imageUrl} alt={image.label} loading="lazy" decoding="async" referrerPolicy="no-referrer" onError={() => setFailed(image.imageUrl)} /> :
      <span className="library-image-placeholder" aria-hidden="true">
        {portrait ? <span className="library-initials" aria-hidden="true">{name.split(/\s+/).filter(Boolean).slice(0, 2).map(word => word[0]).join("")}</span> : <svg viewBox="0 0 48 60" fill="none" aria-hidden="true"><path d="M10 5h30v46H10a5 5 0 0 0 0 10M10 5a5 5 0 0 0-5 5v46a5 5 0 0 0 5 5h30M12 5v46M19 19h14M19 25h10" /></svg>}
      </span>}
  </span>;
}

export function BooksGallery({ data, query, authorView, selected, strip, onBook, onAuthor }: {
  data: BooksResponse; query: string; authorView: boolean; selected: string; strip: RefObject<HTMLUListElement | null>;
  onBook: (book: Book, page: Book[]) => void; onAuthor: (author: TimelineAuthor) => void;
}) {
  const readPage = authorView ? readAuthors : readBooks;
  const window = useGalleryScroll(strip, readPage(data), query, false, "books", "after", readPage);
  const noun = authorView ? "authors" : "books";
  const spacer = (count: number) => <li className="library-spacer" role="presentation" aria-hidden="true" style={{ "--skipped": count } as CSSProperties} />;
  return <div className="books-visual-gallery">
    <ul ref={strip} className="library-strip" aria-label={authorView ? "Authors in this view" : "Books in this view"} aria-busy={window.loading} tabIndex={0}>
      {window.before > 0 && spacer(window.before)}
      {window.items.map((entry, index) => {
        const author = isAuthor(entry);
        const title = author ? entry.name : entry.title;
        const dates = author ? authorLifespanLabel(entry) : entry.years;
        return <li key={entry.id} aria-posinset={window.before + index + 1} aria-setsize={data.total}>
          <button type="button" className="library-card all-gallery-card" data-entry-id={entry.id} aria-label={`${title}${displayMetadata(dates) ? `, ${dates}` : ""}. Open ${author ? "author" : "book"} details`} aria-haspopup="dialog" aria-current={selected === entry.id ? "true" : undefined}
            onClick={() => author ? onAuthor(entry) : onBook(entry, window.items.filter((item): item is Book => !isAuthor(item)))}>
            <LibraryImage image={author ? entry.portrait : entry.cover} name={title} portrait={author} />
            <strong>{title}</strong>
            <span>{author ? `${entry.bookCount.toLocaleString("en-GB")} ${entry.bookCount === 1 ? "book" : "books"}` : displayMetadata(entry.author)}</span>
            {displayMetadata(dates) && <time>{dates}</time>}
          </button>
        </li>;
      })}
      {window.after > 0 && spacer(window.after)}
    </ul>
    <div className="library-status" role="status">
      {window.loading ? <LoadingIndicator label={`Loading ${noun}…`} /> : window.failed ? <><span>Couldn’t load more {noun}.</span> <button onClick={window.retry}>Try again</button></> : <span className="sr-only">{window.complete ? `All ${noun} loaded` : `More ${noun} load as you scroll`}</span>}
    </div>
  </div>;
}
