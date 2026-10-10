"use client";
import { BookmarkButton } from "./Bookmarks";
import { displayMetadata } from "@/lib/display-metadata";

import { useState, type CSSProperties, type RefObject } from "react";
import type { AtlasItem, AtlasLane } from "@/lib/atlas";
import { LoadingIndicator } from "./LoadingIndicator";
import { useAtlasGalleryScroll } from "./use-atlas-gallery-scroll";

function Cover({ item }: { item: AtlasItem }) {
  const [failedImage, setFailedImage] = useState("");
  const cover = item.cover;
  return <span className="all-book-cover">
    {cover && failedImage !== cover.imageUrl ?
      // Covers are selected by the server. Full edition/source credits are in the book drawer.
      // eslint-disable-next-line @next/next/no-img-element
      <img src={cover.imageUrl} alt="" loading="lazy" decoding="async" referrerPolicy="no-referrer" onError={() => setFailedImage(cover.imageUrl)} /> :
      <span className="all-book-cover-placeholder" aria-hidden="true">
        <svg viewBox="0 0 48 60" fill="none" aria-hidden="true"><path d="M10 5h30v46H10a5 5 0 0 0 0 10M10 5a5 5 0 0 0-5 5v46a5 5 0 0 0 5 5h30M12 5v46M19 19h14M19 25h10" /></svg>
      </span>}
  </span>;
}

export function AllBookGallery({ lane, query, busy, selected, select, stripRef }: {
  lane: AtlasLane; query: string; busy: boolean; selected: string;
  select: (item: AtlasItem) => void; stripRef: RefObject<HTMLUListElement | null>;
}) {
  const window = useAtlasGalleryScroll(stripRef, lane, query, busy);
  const spacer = (count: number) => <li className="all-book-spacer" role="presentation" aria-hidden="true" style={{ "--skipped-books": count } as CSSProperties} />;
  return <div className="all-gallery all-book-gallery">
    <div className="all-gallery-caption all-gallery-status" role="status">
      {window.loading ? <LoadingIndicator label="Loading books…" /> : window.failed ? <><span>Couldn’t load more books.</span><button className="all-gallery-retry" onClick={window.retry}>Try again</button></> : <span className="sr-only">{window.complete ? "All books loaded" : "More books load as you scroll"}</span>}
    </div>
    <ul ref={stripRef} className="all-book-strip" aria-label="Books in this view" aria-busy={window.loading || busy} tabIndex={0}>
      {window.before > 0 && spacer(window.before)}
      {window.items.map((item, index) => <li key={item.id} className="bookmark-grid-item" aria-posinset={window.before + index + 1} aria-setsize={lane.total}>
        <button type="button" className="all-book-card all-gallery-card" data-book-id={item.id} title={item.title} aria-label={`${item.title}${displayMetadata(item.years) ? `, ${item.years}` : ""}. Open book details`} aria-haspopup="dialog" aria-current={selected === item.id ? "true" : undefined} disabled={busy} onClick={() => select(item)}>
          <Cover item={item} />
          <strong>{item.title}</strong>
          {displayMetadata(item.years) && <time title={item.years}>{item.years}</time>}
        </button>
        <BookmarkButton kind="book" id={item.id} title={item.title} />
      </li>)}
      {window.after > 0 && spacer(window.after)}
    </ul>
  </div>;
}
