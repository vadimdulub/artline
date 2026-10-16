"use client";
import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { lockBodyScroll } from "@/lib/modal-scroll";
import { contentSingular, emptyMuseumDocument, museumImageURL, publicationPath, studioRequest, type MuseumArtworkChoice, type MuseumContentKind, type MuseumDocument, type MuseumPublication } from "@/lib/museum-studio";
import { MuseumArtworkPicker, PickerImage } from "./MuseumArtworkPicker";
import { MuseumImageField } from "./MuseumImageField";
import { MuseumRichText } from "./MuseumRichText";
import styles from "./MuseumStudio.module.css";
type TextField = Exclude<keyof MuseumDocument, "artworks" | "body_format">;
export function PublicationEditor({ slug, kind, item, museumName, close, saved }: { slug: string; kind: MuseumContentKind; item?: MuseumPublication; museumName: string; close: () => void; saved: (action: string, record: MuseumPublication) => void }) {
  const ref = useRef<HTMLDialogElement>(null), titleID = useId();
  const [draft, setDraft] = useState<MuseumDocument>(() => ({ ...emptyMuseumDocument(), ...(item?.document ?? { title: kind === "profile" ? museumName : "" }), artworks: item?.document.artworks ?? [] }));
  const [busy, setBusy] = useState(false), [uploading, setUploading] = useState(false), [error, setError] = useState("");
  const [picker, setPicker] = useState(false), [newArtwork, setNewArtwork] = useState<MuseumPublication | "new" | null>(null);
  const [choices, setChoices] = useState<Record<string, MuseumArtworkChoice>>({}), [resolving, setResolving] = useState(false), [resolveError, setResolveError] = useState("");
  const dirty = useRef(false);
  useEffect(() => { const focus = document.activeElement as HTMLElement | null, dialog = ref.current; dialog?.showModal(); const unlock = lockBodyScroll(); return () => { dialog?.close(); unlock(); focus?.focus(); }; }, []);
  const selectionKey = draft.artworks.map(work => work.kind + ":" + work.id).join(",");
  useEffect(() => {
    if (!selectionKey) return;
    const controller = new AbortController();
    const refs = selectionKey.split(",").map(key => { const [kind, id] = key.split(":"); return { kind, id, note: "" }; });
    let active = true;
    Promise.resolve().then(() => { if (active) { setResolving(true); setResolveError(""); } });
    studioRequest<{ items: MuseumArtworkChoice[] }>(`/${slug}/artworks/resolve`, { method: "POST", body: JSON.stringify(refs), signal: controller.signal }).then(page => { if (active) setChoices(Object.fromEntries(page.items.map(work => [work.kind + ":" + work.id, work]))); }).catch(e => { if (active) setResolveError(e.message); }).finally(() => { if (active) setResolving(false); });
    return () => { active = false; controller.abort(); };
  }, [slug, selectionKey]);
  function dismiss() { if (!busy && !uploading && (!dirty.current || window.confirm("Discard your unsaved changes?"))) close(); }
  function change<K extends keyof MuseumDocument>(key: K, value: MuseumDocument[K]) { dirty.current = true; setDraft(d => ({ ...d, [key]: value })); }
  function patch(fields: Partial<MuseumDocument>) { dirty.current = true; setDraft(d => ({ ...d, ...fields })); }
  function addArtwork(work: MuseumArtworkChoice) {
    const key = work.kind + ":" + work.id;
    setChoices(current => ({ ...current, [key]: work }));
    dirty.current = true;
    setDraft(current => current.artworks.some(ref => ref.kind === work.kind && ref.id === work.id) ? current : { ...current, artworks: [...current.artworks, { kind: work.kind, id: work.id, note: "" }].slice(0, 48) });
  }
  function move(index: number, offset: number) { const next = [...draft.artworks]; [next[index], next[index + offset]] = [next[index + offset], next[index]]; change("artworks", next); }
  async function editArtwork(id: string) {
    setError(""); try { setNewArtwork(await studioRequest<MuseumPublication>(`/${slug}/content/${id}`)); } catch (e) { setError((e as Error).message); }
  }
  function artworkSaved(_action: string, record: MuseumPublication) {
    setNewArtwork(null);
    addArtwork({ kind: "museum", id: record.id, note: "", title: record.document.title, creator: record.document.creator, date: record.document.date_label, image_url: museumImageURL(slug, record.document), image_alt: record.document.image_alt, credit: record.document.image_credit, href: publicationPath(slug, record.id), available: true, published: record.published });
  }
  const field = (key: TextField, label: string, type = "text", required = false, max = 1000) => <label className={styles.field}><span>{label} <span className={styles.requirement}>{required ? "Required" : "Optional"}</span></span><input type={type} required={required} maxLength={max} value={draft[key] ?? ""} min={type === "number" ? -10000 : undefined} max={type === "number" ? 3000 : undefined} onChange={e => change(key, type === "number" ? e.target.value === "" ? null : Number(e.target.value) : e.target.value)} /></label>;
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); if (busy || uploading) return;
    const action = ((e.nativeEvent as SubmitEvent).submitter as HTMLButtonElement)?.value || "save";
    setBusy(true); setError("");
    try { const record = await studioRequest<MuseumPublication>(`/${slug}/content${item ? `/${item.id}` : ""}`, { method: item ? "PUT" : "POST", body: JSON.stringify({ kind, document: draft, version: item?.version ?? 0, action }) }); saved(action, record); }
    catch (err) { setError((err as Error).message); setBusy(false); }
  }
  const composer = kind === "guide" || kind === "exhibition";
  return <><dialog ref={ref} className={styles.dialog} aria-labelledby={titleID} onCancel={e => { e.preventDefault(); dismiss(); }}><form onSubmit={submit}>
    <header className={styles.dialogHeader}><div><p>{museumName}</p><h2 id={titleID}>{item ? "Edit" : "Add"} {contentSingular[kind]}</h2></div><button type="button" disabled={busy || uploading} onClick={dismiss} aria-label="Close editor">Close</button></header>
    <div className={styles.editorBody}><fieldset disabled={busy}>
      <p className={styles.formHelp}>{kind === "artwork" ? "Title and recorded date are required. Add other details when you know them." : "Required fields are marked. Add images and artworks when they help tell the story."}</p>
      {field("title", kind === "profile" ? "Page title" : "Title", "text", true, 240)}
      {kind === "artwork" && <><div className={styles.fields}>{field("creator", "Artist or recorded attribution")}{field("date_label", "Recorded date", "text", true)}</div><p className={styles.note}>Keep the source’s wording, such as “c. 1920”, “2020–2024”, or “Date unknown”.</p><details className={styles.optionalDetails}><summary>Additional artwork details <span className={styles.requirement}>Optional</span></summary><div className={styles.fields}>{field("year_start", "Start year", "number")}{field("year_end", "End year", "number")}{field("medium", "Medium")}{field("dimensions", "Dimensions")}{field("inventory", "Accession or inventory number")}</div></details></>}
      {kind === "exhibition" && <><div className={styles.fields}>{field("start_date", "Opening date", "date", true)}{field("end_date", "Closing date", "date")}</div>{field("venue", "Venue")}</>}
      {kind === "guide" && field("language", "Language")}
      <label className={styles.field}><span>{kind === "profile" ? "Introduction" : "Short introduction"} <span className={styles.requirement}>Optional</span></span><textarea rows={3} maxLength={1000} value={draft.summary} onChange={e => change("summary", e.target.value)} /></label>
      {composer ? <MuseumRichText label={kind === "guide" ? "Guide text" : "Exhibition text"} value={draft.body} onChange={body => patch({ body, body_format: "markdown" })} disabled={busy} /> : <label className={styles.field}><span>{kind === "profile" ? "About your museum" : "Description"} <span className={styles.requirement}>Optional</span></span><textarea rows={5} maxLength={20000} value={draft.body} onChange={e => change("body", e.target.value)} /></label>}
      {composer && <section className={styles.composer} aria-label="Selected artworks"><div className={styles.composerHeader}><h3>Artworks <span className={styles.requirement}>Optional</span></h3><span>{draft.artworks.length} / 48</span></div><p className={styles.note}>Choose works from the collection or add a new artwork. Arrange them in reading order and write notes beside each one.</p><div className={styles.composerActions}><button type="button" disabled={draft.artworks.length >= 48} onClick={() => setPicker(true)}>Choose from collection</button><button type="button" disabled={draft.artworks.length >= 48} onClick={() => setNewArtwork("new")}>Add new artwork</button></div>
        {draft.artworks.length > 0 && resolving && <p role="status">Loading selected artworks…</p>}{resolveError && <p role="alert">{resolveError}</p>}
        <ol className={styles.selectedArtworks}>{draft.artworks.map((entry, index) => {
          const work = choices[entry.kind + ":" + entry.id];
          return <li key={entry.kind + entry.id}><div className={styles.selectedHeading}><div className={styles.selectedImage}>{work?.image_url && <PickerImage item={work} />}</div><div><h4>{work?.title || "Loading artwork…"}</h4><p>{[work?.creator, work?.date].filter(Boolean).join(" · ")}</p>{work && !work.published && <p className={styles.note}>Draft: publish this artwork before publishing the {contentSingular[kind]}.</p>}</div></div><div className={styles.orderActions}><button type="button" disabled={index === 0} aria-label={`Move ${work?.title || "artwork"} earlier`} onClick={() => move(index, -1)}>Move up</button><button type="button" disabled={index === draft.artworks.length - 1} aria-label={`Move ${work?.title || "artwork"} later`} onClick={() => move(index, 1)}>Move down</button>{entry.kind === "museum" && <button type="button" onClick={() => editArtwork(entry.id)}>Edit artwork</button>}<button type="button" onClick={() => change("artworks", draft.artworks.filter((_, position) => position !== index))}>Remove<span className="sr-only"> {work?.title}</span></button></div><label className={styles.field}>Notes beside {work?.title || "this artwork"} <span className={styles.requirement}>Optional</span><textarea rows={3} maxLength={1000} value={entry.note} onChange={e => change("artworks", draft.artworks.map((ref, position) => position === index ? { ...ref, note: e.target.value } : ref))} /></label></li>;
        })}</ol>
      </section>}
      {kind === "profile" && <div className={styles.fields}>{field("visit_url", "Plan a visit / tickets URL", "url", false, 2048)}{field("address", "Visitor address")}{field("hours", "Opening hours")}</div>}
      <MuseumImageField slug={slug} document={draft} change={patch} busy={busy} onBusy={setUploading} />
      {field("source_url", kind === "profile" ? "Official museum URL" : "Source or further information URL", "url", false, 2048)}
    </fieldset></div>
    <footer className={styles.dialogFooter}>{error && <p role="alert">{error}</p>}<p className={styles.note}>Save a draft to keep changes private. Publish to update your public page.</p><div>{item?.published && <button type="submit" value="unpublish" disabled={busy || uploading}>Unpublish</button>}<button type="submit" value="save" disabled={busy || uploading}>{busy ? "Saving…" : "Save draft"}</button><button className={styles.primary} type="submit" value="publish" disabled={busy || uploading}>Publish</button></div></footer>
  </form></dialog>{picker && <MuseumArtworkPicker slug={slug} selected={draft.artworks} add={addArtwork} close={() => setPicker(false)} />}{newArtwork && <PublicationEditor slug={slug} kind="artwork" museumName={museumName} item={newArtwork === "new" ? undefined : newArtwork} close={() => setNewArtwork(null)} saved={artworkSaved} />}</>;
}
