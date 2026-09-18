"use client";

import { useState } from "react";
import type { Book } from "@/lib/books";
import styles from "./Books.module.css";

export function BookCover({ book }: { book: Book }) {
  const [failedImage, setFailedImage] = useState("");
  const cover = book.cover;
  if (cover && failedImage !== cover.imageUrl) return <figure className={styles.editionCover}>
    {/* One verified edition image, requested only when the details drawer opens. */}
    {/* eslint-disable-next-line @next/next/no-img-element */}
    <img className={styles.coverImage} src={cover.imageUrl} alt={`${book.title} · ${cover.label}`} decoding="async" referrerPolicy="no-referrer" onError={() => setFailedImage(cover.imageUrl)} />
    <figcaption className={styles.coverNote}>{cover.label}<br />{cover.credit}<br /><a href={cover.sourceUrl} target="_blank" rel="noreferrer">Image source</a> · <a href={cover.licenseUrl} target="_blank" rel="noreferrer">{cover.license}</a></figcaption>
  </figure>;
  return <><span className={styles.cover} style={{ backgroundColor: book.coverTone, color: book.coverInk }} aria-hidden="true">
    <span className={styles.coverRule} />
    <span className={styles.coverEra}>{book.era}</span>
    <span className={styles.coverTitle}>{book.title}</span>
    <span className={styles.coverMark}>{book.coverMark}</span>
    <span className={styles.coverAuthor}>{book.author}</span>
  </span><p className={styles.coverNote}>Original Artline text cover · not a historical edition</p></>;
}
