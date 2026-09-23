"use client";
import { useRef } from "react";
import type { AtlasItem, AtlasLane } from "@/lib/atlas";
import { ArtworkImage } from "./ArtworkViewer";

export function AllArtworkGallery({ lane, busy, selected, select, next, first, hasCursor }: { lane: AtlasLane; busy: boolean; selected: string; select: (item: AtlasItem) => void; next: () => void; first: () => void; hasCursor: boolean }) {
  const strip = useRef<HTMLUListElement>(null);
  return <div className="all-gallery">
    <div className="all-gallery-caption"><p>{lane.items.length.toLocaleString("en-GB")} of {lane.total.toLocaleString("en-GB")} artworks · ordered by creation date</p><div><button disabled={busy} aria-label="Scroll artworks left" onClick={() => strip.current?.scrollBy({ left: -strip.current.clientWidth * .8, behavior: "smooth" })}>←</button><button disabled={busy} aria-label="Scroll artworks right" onClick={() => strip.current?.scrollBy({ left: strip.current.clientWidth * .8, behavior: "smooth" })}>→</button></div></div>
    <ul ref={strip} className="all-artwork-strip" aria-label="Artworks in this view" tabIndex={0}>{lane.items.map(item => <li key={item.id}><button className="all-artwork-card" aria-label={`${item.title}, ${item.context}, ${item.years}. Open artwork details`} aria-haspopup="dialog" aria-current={selected === item.id ? "true" : undefined} disabled={busy} onClick={() => select(item)}><span className="all-artwork-image"><ArtworkImage work={{ ...item, media_url: item.media_url ?? null, alt_text: item.alt_text ?? null, rights_status: item.rights_status ?? null }} /></span><strong>{item.title}</strong><span>{item.context}</span><time>{item.years}</time>{item.relation === "context" && <small>Historical context</small>}</button></li>)}</ul>
    {(hasCursor || lane.nextCursor) && <nav className="all-gallery-pages" aria-label="Artwork pages">{hasCursor && <button disabled={busy} onClick={first}>Back to first artworks</button>}<button disabled={busy || !lane.nextCursor} onClick={next}>Next {Math.min(60, lane.total)} artworks →</button></nav>}
  </div>;
}
