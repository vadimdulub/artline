import Link from "next/link";
import { museumImageURL, publicationPath, type MuseumPublication } from "@/lib/museum-studio";
import styles from "./MuseumPublic.module.css";
export function MuseumPublicationCards({ slug, items }: { slug: string; items: MuseumPublication[] }) {
  return <ul className={styles.cards}>{items.map(item => <li key={item.id}><Link href={publicationPath(slug, item.id)}>{museumImageURL(slug, item.document) && <div className={styles.cardImage}><PublicationImage item={item} slug={slug} /></div>}<div className={styles.cardCopy}><p>{item.kind === "exhibition" ? [item.document.start_date, item.document.end_date].filter(Boolean).join(" — ") : item.kind === "artwork" ? item.document.creator : item.document.language}</p><h3>{item.document.title}</h3>{item.document.date_label && <p>{item.document.date_label}</p>}{item.document.summary && <p>{item.document.summary}</p>}</div></Link></li>)}</ul>;
}
export function PublicationImage({ item, slug }: { item: MuseumPublication; slug: string }) {
  // Museum URLs are validated by Go. Loading directly avoids a server-side image fetcher.
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={museumImageURL(slug, item.document)} alt={item.document.image_alt || item.document.title} loading="lazy" referrerPolicy="no-referrer" />;
}
