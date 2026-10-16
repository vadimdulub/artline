"use client";
import { useEffect, useId, useRef, useState } from "react";
import { lockBodyScroll } from "@/lib/modal-scroll";
import { studioRequest, type MuseumArtworkChoice, type MuseumArtworkPage, type MuseumArtworkRef } from "@/lib/museum-studio";
import styles from "./MuseumStudio.module.css";
export function MuseumArtworkPicker({ slug, selected, add, close }: { slug: string; selected: MuseumArtworkRef[]; add: (item: MuseumArtworkChoice) => void; close: () => void }) {
  const ref = useRef<HTMLDialogElement>(null), title = useId();
  const [scope, setScope] = useState("collection"), [query, setQuery] = useState(""), [cursor, setCursor] = useState(""), [images, setImages] = useState(false);
  const [page, setPage] = useState<MuseumArtworkPage>(), [busy, setBusy] = useState(true), [error, setError] = useState(""), [revision, setRevision] = useState(0);
  useEffect(() => { const focus = document.activeElement as HTMLElement | null, dialog = ref.current; dialog?.showModal(); const unlock = lockBodyScroll(); return () => { dialog?.close(); unlock(); focus?.focus(); }; }, []);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setBusy(true); setError("");
      studioRequest<MuseumArtworkPage>(`/${slug}/artworks?${new URLSearchParams({ scope, q: query, cursor, images: images ? "1" : "" })}`, { signal: controller.signal }).then(setPage).catch(e => { if (!controller.signal.aborted) setError(e.message); }).finally(() => { if (!controller.signal.aborted) setBusy(false); });
    }, query ? 250 : 0);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [slug, scope, query, cursor, images, revision]);
  return <dialog ref={ref} className={`${styles.dialog} ${styles.picker}`} aria-labelledby={title} onCancel={e => { e.preventDefault(); close(); }}><div className={styles.pickerShell}>
    <header className={styles.dialogHeader}><div><h2 id={title}>Choose artworks</h2><p>{selected.length} of 48 selected</p></div><button type="button" onClick={close}>Done</button></header>
    <div className={styles.pickerFilters}><label className={styles.field}>Search artworks<input type="search" maxLength={200} value={query} placeholder="Title or artist" onChange={e => { setQuery(e.target.value); setCursor(""); }} /></label><label className={styles.field}>Collection<select value={scope} onChange={e => { setScope(e.target.value); setCursor(""); setImages(false); }}><option value="collection">This museum’s historical collection</option><option value="museum">Added by your museum</option><option value="all">All Artline artworks</option></select></label>{scope !== "museum" && <label className={styles.inlineCheck}><input type="checkbox" checked={images} onChange={e => { setImages(e.target.checked); setCursor(""); }} />With images</label>}</div>
    <div className={styles.pickerResults} aria-busy={busy}>{error ? <div role="alert"><p>{error}</p><button type="button" onClick={() => setRevision(v => v + 1)}>Retry</button></div> : busy ? <p role="status">Finding artworks…</p> : page?.items.length ? <ul className={styles.pickerGrid}>{page.items.map(item => {
      const picked = selected.some(ref => ref.id === item.id && ref.kind === item.kind);
      return <li key={item.kind + item.id}><div className={styles.pickerImage}>{item.image_url ? <PickerImage item={item} /> : <span>No image available</span>}</div><div><h3>{item.title}</h3><p>{[item.creator, item.date].filter(Boolean).join(" · ")}</p>{!item.published && <p className={styles.note}>Draft artwork</p>}<button type="button" disabled={picked || selected.length >= 48} onClick={() => add(item)}>{picked ? "Selected" : "Add artwork"}<span className="sr-only">: {item.title}</span></button></div></li>;
    })}</ul> : <p>No matching artworks. Try another title, artist, or collection.</p>}</div>
    <footer className={styles.dialogFooter}><p className={styles.note}>Selection adds a reference. It does not change the artwork’s recorded holding collection or display status.</p><div>{cursor && <button type="button" disabled={busy} onClick={() => setCursor("")}>First page</button>}{page?.next_cursor && <button type="button" disabled={busy} onClick={() => setCursor(page.next_cursor)}>Next page</button>}<button type="button" className={styles.primary} onClick={close}>Use selection ({selected.length})</button></div></footer>
  </div></dialog>;
}
export function PickerImage({ item }: { item: Pick<MuseumArtworkChoice, "image_url" | "image_alt" | "title"> }) {
  // The catalogue supplies existing approved paths; uploads use the permission-checked image route.
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={item.image_url} alt={item.image_alt || item.title} loading="lazy" referrerPolicy="no-referrer" />;
}
