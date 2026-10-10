"use client";
import Link from "next/link";
import { useEffect, useState, useSyncExternalStore } from "react";
import { bookmarkRequest, type BookmarkPage } from "@/lib/bookmarks";
import { useQueryString, updateQuery } from "@/lib/url-state";
import { BookmarkButton, StarIcon, useBookmarks } from "./Bookmarks";
import { LibraryImage } from "./BooksGallery";
import { ArtworkImage } from "./ArtworkViewer";
import { useMemberSession } from "./MemberSession";
import { MemberAccount } from "./MemberAccount";

const kinds = [{ value: "", label: "All bookmarks" }, { value: "artist", label: "Artists" }, { value: "artwork", label: "Artworks" }, { value: "book", label: "Books" }, { value: "event", label: "Events" }];
const labels = { artist: "Artist", artwork: "Artwork", book: "Book", event: "Event" };

export function BookmarkCollection() {
  const { session } = useMemberSession();
  const client = useBookmarks();
  const revision = useSyncExternalStore(client.subscribeChanges, client.getRevision, () => 0);
  const params = new URLSearchParams(useQueryString());
  const kind = ["artist", "artwork", "book", "event"].includes(params.get("kind") ?? "") ? params.get("kind")! : "";
  const cursor = params.get("cursor") ?? "";
  const [retry, setRetry] = useState(0);
  const key = `${client.owner}:${kind}:${cursor}:${revision}:${retry}`;
  const [result, setResult] = useState<{ key: string; data?: BookmarkPage; error?: string }>();
  useEffect(() => {
    if (!client.owner) return;
    const controller = new AbortController();
    const query = new URLSearchParams();
    if (kind) query.set("kind", kind);
    if (cursor) query.set("cursor", cursor);
    bookmarkRequest<BookmarkPage>(`?${query}`, { signal: controller.signal }).then(data => {
      if (!controller.signal.aborted) { client.seedSaved(data.items); setResult({ key, data }); }
    }).catch(error => { if (!controller.signal.aborted) setResult({ key, error: error instanceof Error ? error.message : "Couldn’t load bookmarks." }); });
    return () => controller.abort();
  }, [key, client, kind, cursor]);
  const loading = result?.key !== key;
  const data = !loading ? result?.data : undefined;
  const error = !loading ? result?.error : undefined;
  if (!session?.user) return <main id="main-content" className="account-page"><section className="account-card"><MemberAccount signInError={false} returnTo="/bookmarks" bookmark /></section></main>;
  return <main id="main-content" className="bookmarks-page">
    <header className="bookmarks-heading"><p className="eyebrow">Your collection</p><h1>Bookmarks</h1><p>Artists, artworks, books, and events you want to return to. Only you can see this collection.</p></header>
    <nav className="bookmark-tabs" aria-label="Bookmark type">{kinds.map(tab => <button key={tab.value} type="button" aria-pressed={kind === tab.value} onClick={() => updateQuery({ kind: tab.value || null, cursor: null })}>{tab.label}</button>)}</nav>
    {session.local_debug && <p className="bookmark-note">Local preview: bookmarks last until the local API restarts.</p>}
    <section aria-label="Your saved collection" aria-busy={loading}>
      {loading ? <p role="status">Opening your bookmarks…</p> : error ? <div className="bookmarks-empty" role="alert"><p>{error}</p><button type="button" onClick={() => setRetry(value => value + 1)}>Try again</button></div> : data?.items.length ? <ul className="bookmark-grid">{data.items.map(item => <li key={`${item.kind}:${item.id}`} className="bookmark-card">
        <Link href={item.href} prefetch={false} className="bookmark-card-link">{item.kind === "artwork" && <div className="bookmark-image"><ArtworkImage work={item} /></div>}{item.image && <div className="bookmark-image"><LibraryImage image={item.image} name={item.title} /></div>}<div className="bookmark-card-copy"><span className="eyebrow">{labels[item.kind]}</span><h2>{item.title}</h2><p>{item.subtitle}</p></div></Link>
        {item.image && <p className="bookmark-image-credit">{item.image.credit} · <a href={item.image.sourceUrl} target="_blank" rel="noreferrer">Image source</a> · <a href={item.image.licenseUrl} target="_blank" rel="noreferrer">{item.image.license}</a></p>}
        <BookmarkButton kind={item.kind} id={item.id} title={item.title} />
      </li>)}</ul> : <div className="bookmarks-empty"><StarIcon /><h2>{cursor ? "You’ve reached the end" : kind ? `No ${kinds.find(item => item.value === kind)?.label.toLowerCase()} saved yet` : "Start a collection of your own"}</h2><p>Tap the star beside an artist, artwork, book, or event to keep it here.</p><div><Link href="/artists">Explore artists</Link><Link href="/artworks">Explore artworks</Link><Link href="/books">Explore books</Link><Link href="/events">Explore events</Link></div></div>}
    </section>
    {(cursor || data?.next_cursor) && <nav className="bookmark-pagination" aria-label="Bookmark pages">{cursor && <button type="button" onClick={() => updateQuery({ cursor: null })}>Newest bookmarks</button>}{data?.next_cursor && <button type="button" onClick={() => updateQuery({ cursor: data.next_cursor })}>Older bookmarks</button>}</nav>}
  </main>;
}
