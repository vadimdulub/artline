"use client";
import Link from "@/components/MemberLink";
import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemberSession } from "@/components/MemberSession";
import { MemberAccount } from "@/components/MemberAccount";
import { AtlasSearchField } from "@/components/AtlasSearchField";
import { StudyDialog } from "./StudyDialog";
import { studyRequest, type StudyListPage, type StudySummary } from "@/lib/studies";
import styles from "./Studies.module.css";

export function StudyCollection() {
  const { session } = useMemberSession();
  return <StudyCollectionContent key={session?.user?.id ?? "signed-out"} />;
}

function StudyCollectionContent() {
  const { session, failed } = useMemberSession(); const router = useRouter(); const searchParams = useSearchParams();
  const [data, setData] = useState<StudyListPage | null>(null), [error, setError] = useState(""), [retry, setRetry] = useState(0), [loading, setLoading] = useState(true);
  const [query, setQuery] = useState(searchParams.get("q") ?? ""), [sort, setSort] = useState(searchParams.get("sort") === "title" ? "title" : "recent");
  const [cursor, setCursor] = useState(""), [pages, setPages] = useState<string[]>([]);
  const [creating, setCreating] = useState(false), [title, setTitle] = useState(""), [busy, setBusy] = useState(false), [saveError, setSaveError] = useState("");
  const owner = session?.user?.id;
  const library = useRef<HTMLElement>(null), scrollOnPage = useRef(false);
  useEffect(() => {
    if (!owner) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      const params = new URLSearchParams({ q: query, sort, cursor });
      studyRequest<StudyListPage>(`?${params}`, { signal: controller.signal }).then(result => { setData(result); setError(""); setLoading(false); if (scrollOnPage.current) { scrollOnPage.current = false; requestAnimationFrame(() => library.current?.scrollIntoView({ block: "start" })); } }).catch(error => { if (!controller.signal.aborted) { setError(error.message); setLoading(false); } });
    }, 220);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [owner, query, sort, cursor, retry]);
  useEffect(() => {
    if (!owner) return;
    const params = new URLSearchParams(); if (query) params.set("q", query); if (sort !== "recent") params.set("sort", sort);
    window.history.replaceState(null, "", `/studies${params.size ? `?${params}` : ""}`);
  }, [owner, query, sort]);
  function firstPage() { scrollOnPage.current = false; setCursor(""); setPages([]); setLoading(true); }
  function openCreate() { setTitle(""); setSaveError(""); setCreating(true); }
  async function create(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setSaveError("");
    try { const study = await studyRequest<StudySummary>("", { method: "POST", body: JSON.stringify({ title }) }); router.push(`/studies/${study.id}`); }
    catch (error) { setSaveError(error instanceof Error ? error.message : "Couldn’t create your study."); setBusy(false); }
  }
  if (!owner) return <main id="main-content" className={styles.page}>{failed ? <p role="alert">Your account is unavailable. Reload to try again.</p> : <MemberAccount signInError={false} returnTo="/studies" />}</main>;
  return <main id="main-content" className={styles.page}>
    <header className={styles.collectionHeader}><div><h1>Your studies</h1><p>Your research, organised by question, artist or period.</p></div><button className={styles.primary} onClick={openCreate}>+ New study</button></header>
    <div className={styles.collectionTools}><AtlasSearchField label="Search your studies" placeholder="Search your studies…" value={query} onChange={value => { setQuery(value); firstPage(); }} /><label>Sort by<select aria-label="Sort by" value={sort} onChange={event => { setSort(event.target.value); firstPage(); }}><option value="recent">Recently updated</option><option value="title">Title A–Z</option></select></label></div>
    <section ref={library} className={styles.library} aria-label="Your research studies" aria-busy={loading}>
      <div className={styles.collectionCount}><p role="status">{loading ? "Loading studies…" : data ? query.trim() ? `${data.matched} of ${data.total} studies` : `${data.total} ${data.total === 1 ? "study" : "studies"}` : ""}</p>{query && <button className={styles.textButton} onClick={() => { setQuery(""); firstPage(); }}>Clear search</button>}</div>
      {error ? <div className={styles.empty} role="alert"><p>{error}</p><button onClick={() => { firstPage(); setRetry(value => value + 1); }}>Try again</button></div> : !data ? null : !data.total ? <section className={styles.empty}><span className={styles.emptyMark} aria-hidden>＋</span><h2>A place to follow an idea.</h2><p>Create a study for each research question. Gather artworks, books and events, compare the works, and keep your notes and sources together.</p><button className={styles.primary} onClick={openCreate}>Create your first study</button></section> : !data.items.length ? <section className={styles.empty}><h2>No studies found.</h2><p>Try another title or clear your search.</p><button onClick={() => { setQuery(""); firstPage(); }}>Show all studies</button></section> : <>
        <div className={styles.studyColumns} aria-hidden><span>Study</span><span>Records</span><span>Last updated</span><span /></div>
        <ul className={styles.studyList}>{data.items.map(study => <li key={study.id}><Link href={`/studies/${study.id}`} className={styles.studyRow}><div className={styles.studyIdentity}><h2>{study.title}</h2><small className={styles.libraryVisibility}>{study.public ? "Public" : "Private"}</small></div><span className={styles.studyRecordCount}>{study.count} <span>{study.count === 1 ? "record" : "records"}</span></span><time dateTime={study.updated_at}>{new Date(study.updated_at).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}</time><span className={styles.openStudy} aria-hidden>→</span></Link></li>)}</ul>
      </>}
      {data && !error && (pages.length > 0 || data.next_cursor) && <nav className={styles.paging} aria-label="Studies pages"><button disabled={loading || !pages.length} onClick={() => { setLoading(true); scrollOnPage.current = true; const previous = [...pages]; setCursor(previous.pop() ?? ""); setPages(previous); }}>← Previous</button><span>Page {pages.length + 1}</span><button disabled={loading || !data.next_cursor} onClick={() => { setLoading(true); scrollOnPage.current = true; setPages(previous => [...previous, cursor]); setCursor(data.next_cursor); }}>Next →</button></nav>}
    </section>
    {creating && <StudyDialog title="New study" subtitle="Start with a question, an artist or a period." close={() => { if (!busy) setCreating(false); }} footer={<><button disabled={busy} onClick={() => setCreating(false)}>Cancel</button><button type="submit" form="create-study" className={styles.primary} disabled={busy || !title.trim()}>{busy ? "Creating…" : "Create study"}</button></>}><form id="create-study" onSubmit={create} className={styles.form}><label>Study title<input autoFocus required maxLength={180} value={title} onChange={event => setTitle(event.target.value)} placeholder="e.g. Paris and the modern city" /></label><p className={styles.help}>Each study has its own records, comparisons and notes. Private by default. You can share a read-only public link later.</p>{saveError && <p role="alert" className={styles.error}>{saveError}</p>}</form></StudyDialog>}
  </main>;
}
