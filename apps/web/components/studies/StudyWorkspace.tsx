"use client";
import { useEffect, useId, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemberSession } from "@/components/MemberSession";
import { MemberAccount } from "@/components/MemberAccount";
import { AtlasSearchField } from "@/components/AtlasSearchField";
import { kindLabels, recordKey, studyKinds, readStudy, studyRequest, studyYearError, yearLabel, type StudyKind, type StudyRecord, type StudyView } from "@/lib/studies";
import { AddStudyRecords } from "./AddStudyRecords";
import { RecordInspector, StudyImage } from "./StudyRecord";
import { StudyDialog } from "./StudyDialog";
import { StudyTimeline } from "./StudyTimeline";
import { ShareStudy } from "./ShareStudy";
import { StudyCompare } from "./StudyCompare";
import styles from "./Studies.module.css";

export function StudyWorkspace({ id, shared = false }: { id: string; shared?: boolean }) {
  const { session } = useMemberSession();
  return <StudyWorkspaceContent key={`${id}:${shared ? "public" : session?.user?.id ?? "signed-out"}`} id={id} shared={shared} />;
}

function StudyWorkspaceContent({ id, shared }: { id: string; shared: boolean }) {
  const { session, failed } = useMemberSession(); const owner = session?.user?.id; const readable = shared || !!owner; const router = useRouter(); const searchParams = useSearchParams();
  const [data, setData] = useState<StudyView | null>(null), [error, setError] = useState(""), [loading, setLoading] = useState(true), [revision, setRevision] = useState(0);
  const [query, setQuery] = useState(searchParams.get("q") ?? ""), [from, setFrom] = useState(searchParams.get("from") ?? ""), [to, setTo] = useState(searchParams.get("to") ?? "");
  const [kinds, setKinds] = useState<StudyKind[]>(() => searchParams.has("kind") ? studyKinds.filter(kind => searchParams.getAll("kind").includes(kind)) : [...studyKinds]);
  const [view, setView] = useState<"timeline" | "gallery">(searchParams.get("view") === "gallery" ? "gallery" : "timeline"), [compact, setCompact] = useState(false), [filtersOpen, setFiltersOpen] = useState(false);
  const [cursor, setCursor] = useState(""), [pages, setPages] = useState<string[]>([]), [selected, setSelected] = useState<StudyRecord | null>(null), [adding, setAdding] = useState(false), [compare, setCompare] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [settings, setSettings] = useState(false), [newTitle, setNewTitle] = useState(""), [deleteConfirm, setDeleteConfirm] = useState(false), [busy, setBusy] = useState(false), [actionError, setActionError] = useState("");
  const [viewReady, setViewReady] = useState(false);
  const initialView = useRef(searchParams.get("view"));
  const [notice, setNotice] = useState(""); const search = useRef<HTMLInputElement>(null); const yearError = studyYearError(from, to); const yearErrorId = useId();
  const filterQuery = new URLSearchParams({ q: query, cursor, view }); if (from) filterQuery.set("from", from); if (to) filterQuery.set("to", to); for (const kind of kinds.length ? kinds : ["none"]) filterQuery.append("kind", kind);
  const filterString = filterQuery.toString();
  useEffect(() => {
    if (!readable) return;
    const media = window.matchMedia("(max-width: 1279px)"); const listener = () => setCompact(media.matches); media.addEventListener("change", listener);
    const hasView = !!initialView.current;
    const frame = requestAnimationFrame(() => { listener();
    if (!hasView) { try { const remembered = sessionStorage.getItem("artline-study-view"); if (remembered === "gallery" || remembered === "timeline") setView(remembered); else if (window.matchMedia("(max-width: 767px)").matches) setView("gallery"); } catch { if (window.matchMedia("(max-width: 767px)").matches) setView("gallery"); } }
    setViewReady(true);
    });
    return () => { cancelAnimationFrame(frame); media.removeEventListener("change", listener); };
  }, [readable]);
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => { if (event.key === "/" && !document.querySelector("dialog[open]") && !(event.target instanceof HTMLElement && (event.target.matches("input,textarea,select") || event.target.isContentEditable))) { event.preventDefault(); search.current?.focus(); } };
    window.addEventListener("keydown", onKey); return () => window.removeEventListener("keydown", onKey);
  }, []);
  useEffect(() => {
    if (!readable || yearError) return;
    const controller = new AbortController(); const timer = setTimeout(() => {
      setLoading(true); setError(""); readStudy(id, filterString, controller.signal, shared).then(result => { setData(result); setLoading(false); }).catch(error => { if (!controller.signal.aborted) { setError(error.message); setLoading(false); if (shared) { setData(null); setSelected(null); setCompare(false); } } });
    }, 260);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [id, readable, filterString, revision, yearError, shared]);
  useEffect(() => { if (!readable || !viewReady) return; const params = new URLSearchParams(filterString); params.delete("cursor"); if (!query) params.delete("q"); params.set("view", view); window.history.replaceState(null, "", `/${shared ? "shared/studies" : "studies"}/${id}?${params}`); }, [id, filterString, view, query, readable, viewReady, shared]);
  useEffect(() => {
    if (!shared) return;
    const refresh = () => { if (document.visibilityState === "visible") setRevision(value => value + 1); };
    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", refresh);
    const timer = setInterval(refresh, 30000);
    return () => { clearInterval(timer); window.removeEventListener("focus", refresh); document.removeEventListener("visibilitychange", refresh); };
  }, [shared]);
  function changeView(value: "timeline" | "gallery") { resetPage(); setView(value); try { sessionStorage.setItem("artline-study-view", value); } catch { /* View still works when storage is unavailable. */ } }
  function resetPage() { setCursor(""); setPages([]); }
  function resetFilters() { setQuery(""); setFrom(""); setTo(""); setKinds([...studyKinds]); resetPage(); }
  const refresh = () => setRevision(value => value + 1);
  async function saveNote(note: string) { if (shared || !selected) return; setBusy(true); try { await studyRequest(`/${id}/records/${selected.kind}/${selected.id}`, { method: "PUT", body: JSON.stringify({ note }) }); setSelected(record => record ? { ...record, note } : null); refresh(); } finally { setBusy(false); } }
  async function removeRecord() { if (shared || !selected) return; setBusy(true); try { await studyRequest(`/${id}/records/${selected.kind}/${selected.id}`, { method: "DELETE" }); setSelected(null); resetPage(); refresh(); setNotice("Record removed from this study."); } finally { setBusy(false); } }
  async function exportStudy(format: "csv" | "references") {
    if (shared) return;
    setActionError(""); setBusy(true); try { const response = await fetch(`/api/studies/${id}/export?format=${format}`, { cache: "no-store" }); if (!response.ok) { if (response.status === 401) window.dispatchEvent(new Event("artline:session-expired")); const body = await response.json(); throw new Error(body.error?.message ?? "Couldn’t export this study."); } const blob = await response.blob(); const url = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = url; a.download = `artline-study.${format === "csv" ? "csv" : "txt"}`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); setNotice("Exported all study references and notes. Images are not included."); } catch (error) { setActionError(error instanceof Error ? error.message : "Couldn’t export this study."); } finally { setBusy(false); }
  }
  const selectedKey = selected ? recordKey(selected) : undefined;
  if (!readable) return <main id="main-content" className={styles.page}>{failed ? <p role="alert">Your account is unavailable. Reload to try again.</p> : <MemberAccount signInError={false} returnTo={`/studies/${id}`} />}</main>;
  if (!data) return <main id="main-content" className={styles.page}>{error || yearError ? <div className={styles.empty} role="alert"><h1>{yearError ? "Check the study filters" : "Study unavailable"}</h1><p>{yearError || error}</p><button onClick={() => { resetFilters(); refresh(); }}>Reset and try again</button></div> : <p role="status">Loading study…</p>}</main>;
  const inspector = selected && <RecordInspector key={recordKey(selected)} record={selected} readOnly={shared} saveNote={saveNote} remove={removeRecord} busy={busy} close={() => setSelected(null)} />;
  const filters = <><AtlasSearchField label="Search this study" placeholder="Search this study…" value={query} inputRef={search} shortcut onChange={value => { setQuery(value); resetPage(); }} /><div className={styles.yearFields}><label>From<input type="number" value={from} placeholder={data.range ? String(data.range.start) : "Any year"} aria-invalid={!!yearError} aria-describedby={yearError ? yearErrorId : undefined} onChange={event => { setFrom(event.target.value); resetPage(); }} /></label><span aria-hidden>—</span><label>To<input type="number" value={to} placeholder={data.range ? String(data.range.end) : "Any year"} aria-invalid={!!yearError} aria-describedby={yearError ? yearErrorId : undefined} onChange={event => { setTo(event.target.value); resetPage(); }} /></label></div><button className={styles.textButton} onClick={resetFilters}>Reset filters</button>{yearError && <p className={styles.error} id={yearErrorId} role="alert">{yearError}</p>}</>;
  return <main id="main-content" className={`${styles.page} ${styles.workspace}`}>
    <header className={styles.workspaceHeader}><div><span className={styles.sharingStatus}>{shared ? "Public study · Read only" : data.public ? "Public · Anyone with the link can read" : "Private study"}</span><h1>{data.title}</h1><p>Follow a question through artworks, books and events.</p></div><div className={styles.headerActions}><button disabled={data.artworks.length < 2} onClick={() => setCompare(true)}>Compare artworks</button>{!shared && <><button onClick={() => setSharing(true)}>Share</button><details className={styles.export}><summary>Export</summary><div><button disabled={!data.count || busy} onClick={() => void exportStudy("references")}>Download references</button><button disabled={!data.count || busy} onClick={() => void exportStudy("csv")}>Download CSV</button><p>All study records and notes. No images.</p></div></details><button onClick={() => { setSettings(true); setNewTitle(data.title); setDeleteConfirm(false); setActionError(""); }}>Study settings</button><button id="study-add" className={styles.primary} onClick={() => setAdding(true)}>+ Add records</button></>}</div></header>
    {actionError && !settings && <p role="alert" className={styles.error}>{actionError}</p>}<p className={styles.notice} role="status">{notice}</p>
    <div className={styles.desktopFilters}>{!filtersOpen && filters}</div><div className={styles.mobileFilters}><button onClick={() => setFiltersOpen(true)}>Search & filters{query || from || to ? " · Applied" : ""}</button><span>{from || (data.range ? yearLabel(data.range.start) : "Any year")} — {to || (data.range ? yearLabel(data.range.end) : "Any year")}</span></div>
    <div className={styles.workspaceToolbar}><div className={styles.kindFilters} role="group" aria-label="Record types">{studyKinds.map(kind => <label className={styles.check} key={kind}><input type="checkbox" checked={kinds.includes(kind)} onChange={() => { setKinds(current => current.includes(kind) ? current.filter(value => value !== kind) : [...current, kind]); resetPage(); }} /><i className={styles.typeDot} data-kind={kind} aria-hidden />{kindLabels[kind]} <span>{data.counts[kind]}</span></label>)}</div><div className={styles.viewSwitch} role="group" aria-label="Study view"><button aria-pressed={view === "timeline"} onClick={() => changeView("timeline")}>Timeline</button><button aria-pressed={view === "gallery"} onClick={() => changeView("gallery")}>Gallery</button></div></div>
    <div className={styles.workArea} data-inspecting={!!selected && !compact}><section className={styles.results} aria-label="Study records"><div className={styles.resultHeading}><p role="status">{loading ? "Updating…" : `${data.matched} of ${data.count} records`}</p>{view === "timeline" && <span>┄ Date range &nbsp; · Single year</span>}</div>
      {error ? <div className={styles.empty} role="alert"><p>{error}</p><button onClick={refresh}>Try again</button><button onClick={resetFilters}>Reset filters</button></div> : !data.count ? <section className={styles.empty}><h2>{shared ? "No records yet." : "Start with a work. Follow the connections."}</h2><p>{shared ? "The owner hasn’t added any records to this study yet." : "Add artworks, books and events from the catalogue, or add a record of your own."}</p>{!shared && <button className={styles.primary} onClick={() => setAdding(true)}>Add your first records</button>}</section> : !data.matched ? <div className={styles.empty}><h2>No records match these filters.</h2><p>Broaden your dates, search or selected record types.</p><button onClick={resetFilters}>Reset filters</button></div> : view === "timeline" ? <StudyTimeline readOnly={shared} records={data.items} range={data.range} selected={selectedKey} select={setSelected} /> : <div className={styles.gallery}>{data.items.map(record => <button className={styles.galleryCard} key={recordKey(record)} aria-pressed={selectedKey === recordKey(record)} onClick={() => setSelected(record)}><StudyImage readOnly={shared} record={record} /><span className={styles.galleryCaption}><small>{record.personal ? shared ? "Personal record" : "Your own" : record.kind === "artwork" ? "Artwork" : record.kind === "book" ? "Book" : "Event"}</small><strong>{record.title}</strong><span>{record.creator || "Creator not recorded"}</span><span>{record.date || "Date not recorded"}</span>{record.note && <small>Note saved</small>}</span></button>)}</div>}
      {(pages.length > 0 || data.next_cursor) && <nav className={styles.paging} aria-label="Study records pages"><button disabled={loading || !pages.length} onClick={() => { setLoading(true); const previous = [...pages]; setCursor(previous.pop() ?? ""); setPages(previous); }}>← Previous</button><span>Page {pages.length + 1}</span><button disabled={loading || !data.next_cursor} onClick={() => { setLoading(true); setPages(previous => [...previous, cursor]); setCursor(data.next_cursor); }}>Next →</button></nav>}
    </section>{!compact && inspector}</div>
    {selected && compact && <StudyDialog title="Record inspection" close={() => setSelected(null)}>{inspector}</StudyDialog>}
    {!shared && adding && <AddStudyRecords studyId={id} existing={data.keys ?? []} close={() => setAdding(false)} added={() => { resetPage(); refresh(); setNotice("Records added to your study."); }} />}
    {compare && data.artworks.length >= 2 && <StudyCompare shared={shared} id={id} options={data.artworks} initial={selectedKey} close={() => setCompare(false)} />}
    {filtersOpen && <StudyDialog title="Study filters" close={() => setFiltersOpen(false)} footer={<button disabled={!!yearError} className={styles.primary} onClick={() => setFiltersOpen(false)}>Show records</button>}><div className={styles.mobileFilterForm}>{filters}</div></StudyDialog>}
    {!shared && sharing && <ShareStudy id={id} close={() => setSharing(false)} changed={refresh} />}
    {!shared && settings && <StudyDialog title="Study settings" close={() => { if (!busy) setSettings(false); }} footer={<><button onClick={() => setSettings(false)} disabled={busy}>Cancel</button><button className={styles.primary} form="rename-study" type="submit" disabled={busy || !newTitle.trim()}>Save changes</button></>}><form id="rename-study" className={styles.form} onSubmit={async event => { event.preventDefault(); setBusy(true); setActionError(""); try { await studyRequest(`/${id}`, { method: "PATCH", body: JSON.stringify({ title: newTitle }) }); setSettings(false); refresh(); } catch (error) { setActionError(error instanceof Error ? error.message : "Couldn’t save study."); } finally { setBusy(false); } }}><label>Study title<input required maxLength={180} autoFocus value={newTitle} onChange={event => setNewTitle(event.target.value)} /></label><p className={styles.help}>Catalogue details are captured when you add a record. Source links stay with your references. Up to 200 records per study.</p></form>{actionError && <p role="alert" className={styles.error}>{actionError}</p>}{deleteConfirm ? <div className={styles.removeConfirm}><p>Delete this study and all its notes? This cannot be undone.</p><button disabled={busy} onClick={async () => { setBusy(true); try { await studyRequest(`/${id}`, { method: "DELETE" }); router.push("/studies"); } catch (error) { setActionError(error instanceof Error ? error.message : "Couldn’t delete study."); setBusy(false); } }}>Delete study permanently</button><button onClick={() => setDeleteConfirm(false)}>Keep study</button></div> : <button className={styles.textButton} onClick={() => setDeleteConfirm(true)}>Delete study</button>}</StudyDialog>}
  </main>;
}
