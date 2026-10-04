"use client";
import { useRef, type CSSProperties, type RefObject } from "react";
import type { AtlasItem, AtlasLane } from "@/lib/atlas";
import { ArtworkImage } from "./ArtworkViewer";
import { LoadingIndicator } from "./LoadingIndicator";
import { useAtlasGalleryScroll } from "./use-atlas-gallery-scroll";

export function GalleryScrollButtons({ strip, disabled, noun = "artworks" }: { strip: RefObject<HTMLUListElement | null>; disabled: boolean; noun?: string }) {
  return <div className="all-gallery-scroll"><button type="button" disabled={disabled} aria-label={`Scroll ${noun} left`} onClick={() => strip.current?.scrollBy({ left: -strip.current.clientWidth * .8, behavior: "smooth" })}>←</button><button type="button" disabled={disabled} aria-label={`Scroll ${noun} right`} onClick={() => strip.current?.scrollBy({ left: strip.current.clientWidth * .8, behavior: "smooth" })}>→</button></div>;
}

export function AllArtworkGallery({ lane, query, busy, selected, select, stripRef, inlineControls = true, showDetails = true }: { lane: AtlasLane; query: string; busy: boolean; selected: string; select: (item: AtlasItem) => void; stripRef?: RefObject<HTMLUListElement | null>; inlineControls?: boolean; showDetails?: boolean }) {
  const ownStrip = useRef<HTMLUListElement>(null);
  const strip = stripRef ?? ownStrip;
  const window = useAtlasGalleryScroll(strip, lane, query, busy);
  const spacer = (count: number) => <li className="all-artwork-spacer" role="presentation" aria-hidden="true" style={{ "--skipped-artworks": count } as CSSProperties} />;
  return <div className="all-gallery">
    <div className={`all-gallery-caption${inlineControls ? "" : " all-gallery-status"}`}><div role="status">{window.loading ? <LoadingIndicator label="Loading artworks…" /> : window.failed ? <><span>Couldn’t load more artworks.</span> <button className="all-gallery-retry" onClick={window.retry}>Try again</button></> : <span className="sr-only">{window.complete ? "All artworks loaded" : "More artworks load as you scroll"}</span>}</div>{inlineControls && <GalleryScrollButtons strip={strip} disabled={busy} />}</div>
    <ul ref={strip} className="all-artwork-strip" aria-label="Artworks in this view" aria-busy={window.loading || busy} tabIndex={0}>
      {window.before > 0 && spacer(window.before)}
      {window.items.map((item, index) => <li key={item.id} aria-posinset={window.before + index + 1} aria-setsize={lane.total}><button className="all-artwork-card all-gallery-card" data-artwork-id={item.id} title={item.title} aria-label={`${item.title}, ${item.context}${showDetails ? `, ${item.years}` : ""}. Open artwork details`} aria-haspopup="dialog" aria-current={selected === item.id ? "true" : undefined} disabled={busy} onClick={() => select(item)}><span className="all-artwork-image"><ArtworkImage work={{ ...item, media_url: item.media_url ?? null, alt_text: item.alt_text ?? null, rights_status: item.rights_status ?? null }} /></span><strong>{item.title}</strong><span title={item.context}>{item.context}</span>{showDetails && <><time>{item.years}</time>{item.relation === "context" && <small>Historical context</small>}</>}</button></li>)}
      {window.after > 0 && spacer(window.after)}
    </ul>
  </div>;
}
