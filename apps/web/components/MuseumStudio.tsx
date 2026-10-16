"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { PreparedStudioGuides } from "./PreparedStudioGuides";
import { PublicationEditor } from "./MuseumPublicationEditor";
import { useMemberSession } from "./MemberSession";
import { contentLabels, contentSingular, publicationPath, studioRequest, type MuseumContentKind, type MuseumPublication, type MuseumPublicationPage, type StudioMuseum } from "@/lib/museum-studio";
import styles from "./MuseumStudio.module.css";

export function MuseumStudio({ slug, initialQuery = "" }: { slug?: string; initialQuery?: string }) {
  return <main id="main-content" className={styles.page}>{slug ? <MuseumWorkspace slug={slug} /> : <MuseumChooser initialQuery={initialQuery} />}</main>;
}
function MuseumChooser({ initialQuery }: { initialQuery: string }) {
  const router = useRouter();
  const [query, setQuery] = useState(initialQuery);
  const [result, setResult] = useState<{ items: StudioMuseum[]; local_debug: boolean; work_identity: boolean }>();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setLoading(true); setError("");
      studioRequest<typeof result>(`?${new URLSearchParams({ q: query })}`, { signal: controller.signal }).then(setResult).catch(e => { if (!controller.signal.aborted) setError(e.message); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    }, 250);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [query, revision]);
  async function claim(museum: StudioMuseum) {
    setBusy(museum.slug); setError("");
    try { await studioRequest(`/${museum.slug}/claim`, { method: "POST" }); router.push(`/account/museums/${museum.slug}`); }
    catch (e) { setError((e as Error).message); setBusy(""); }
  }
  return <>
    <Link className={styles.back} href="/account">Your account</Link>
    <header className={styles.intro}><h1>Museum studio</h1><p>Bring your collection to Artline. Share artworks, announce exhibitions, and help visitors look closer with your own guides.</p></header>
    <div className={styles.onboarding}><div><h2>Your museum, in focus.</h2><p>A public page for your collection and programme. Verified museum staff can save drafts and publish directly.</p><ul><li>Historical and contemporary artworks</li><li>Exhibitions, dates, and visiting details</li><li>Guides written by your museum</li></ul></div><div className={styles.claim}>
      <h2>Find your museum</h2><p>{result?.local_debug ? "Local preview: choose a museum to try the studio. Changes stay in memory until the API restarts." : "Sign in with your museum’s Google work account. Access is confirmed automatically when its verified domain matches an approved museum domain."}</p>
      <label className={styles.field}>Museum name<input type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search for your museum" maxLength={200} /></label>
      {error && <p role="alert">{error} <button onClick={() => setRevision(v => v + 1)}>Retry</button></p>}
      {loading ? <p role="status">Finding museums…</p> : <><ul className={styles.museumList}>{result?.items.map(museum => <li key={museum.id}><div><strong>{museum.name}</strong>{museum.website_url && <a href={museum.website_url} target="_blank" rel="noreferrer">Museum website</a>}</div>{museum.managed ? <Link className={styles.button} href={`/account/museums/${museum.slug}`}>Open studio</Link> : <button disabled={!museum.eligible || !!busy} onClick={() => claim(museum)}>{busy === museum.slug ? "Verifying…" : "Manage museum"}</button>}</li>)}</ul>
      {!result?.items.length && <p>{query ? "No matching museums. Try another name or the museum’s full name." : "Search to add your first museum, or open a museum you already manage."}</p>}
      {!!result?.items.some(m => !m.eligible) && <p className={styles.note}>Access is unavailable for this account or domain. Use the museum’s verified Google work account; its domain must be approved by Artline before it can receive publishing access.</p>}</>}
    </div></div>
  </>;
}
function MuseumWorkspace({ slug }: { slug: string }) {
  const { session } = useMemberSession();
  const [museum, setMuseum] = useState<StudioMuseum>();
  const [kind, setKind] = useState<MuseumContentKind>("artwork");
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState("");
  const [page, setPage] = useState<MuseumPublicationPage>();
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);
  const [editing, setEditing] = useState<MuseumPublication | "new" | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    studioRequest<StudioMuseum>(`/${slug}`, { signal: controller.signal }).then(setMuseum).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [slug, revision]);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setLoading(true); setError("");
      studioRequest<MuseumPublicationPage>(`/${slug}/content?${new URLSearchParams({ kind, q: query, cursor })}`, { signal: controller.signal }).then(setPage).catch(e => { if (!controller.signal.aborted) setError(e.message); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    }, query ? 250 : 0);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [slug, kind, query, cursor, revision]);
  function saved(action: string) { setEditing(null); setNotice(action === "publish" ? "Published. Your museum’s public page is updated." : action === "unpublish" ? "Unpublished. This record is now private." : "Draft saved. Your public page is unchanged."); setRevision(v => v + 1); }
  return <>
    <Link className={styles.back} href="/account/museums">Your museums</Link>
    <header className={styles.workspaceHeader}><div><p>Museum studio</p><h1>{museum?.name ?? "Your museum"}</h1></div><Link className={styles.button} href={`/museums/${slug}`} target="_blank">View public page</Link></header>
    <p className={styles.note}>{session?.local_debug ? "Local preview. Publications and access are temporary and are visible only through this local API." : "Museum staff can publish directly. Save changes as a draft when you’re not ready to share them."}</p>
    <nav className={styles.tabs} aria-label="Museum content">{Object.entries(contentLabels).map(([value, label]) => <button key={value} aria-pressed={kind === value} onClick={() => { setKind(value as MuseumContentKind); setQuery(""); setCursor(""); setPage(undefined); setNotice(""); }}>{label}</button>)}</nav>
    <div className={styles.toolbar}><div><h2>{contentLabels[kind]}</h2><p>{kind === "profile" ? "Introduce your museum and help visitors plan their visit." : kind === "artwork" ? "Add works from any period to your museum collection." : kind === "exhibition" ? "Share current, upcoming, and past exhibitions." : "Create reading and looking guides for your visitors."}</p></div>{museum && !loading && !error && (kind !== "profile" || !page?.items.length) && <button className={styles.primary} onClick={() => setEditing("new")}>{kind === "profile" ? "Edit museum page" : `Add ${contentSingular[kind]}`}</button>}</div>
    {kind !== "profile" && <label className={styles.search}>Search {contentLabels[kind].toLowerCase()}<input type="search" value={query} maxLength={200} onChange={e => { setQuery(e.target.value); setCursor(""); }} placeholder={kind === "guide" ? "Search your guides and Artline guides" : "Search by title"} /></label>}
    {kind === "guide" && <><PreparedStudioGuides slug={slug} query={query} /><h3>Your museum’s guides</h3></>}
    <p role="status" className={styles.notice}>{notice}</p>
    {error ? <div role="alert" className={styles.empty}><p>{error}</p><button onClick={() => setRevision(v => v + 1)}>Retry</button><Link href="/account/museums">Find your museum</Link></div> : loading ? <p role="status">Loading museum content…</p> : page?.items.length ? <ul className={styles.contentList}>{page.items.map(item => <li key={item.id}><div><span className={styles.status}>{item.published ? item.has_changes ? "Published · unpublished changes" : "Published" : "Draft"}</span><h3>{item.document.title}</h3><p>{item.document.creator || item.document.summary || item.document.start_date}</p></div><div className={styles.rowActions}>{item.published && <Link href={kind === "profile" ? `/museums/${slug}` : publicationPath(slug, item.id)} target="_blank">View</Link>}<button onClick={() => setEditing(item)}>Edit<span className="sr-only"> {item.document.title}</span></button></div></li>)}</ul> : <div className={styles.empty}><h3>{query ? "No matching content" : kind === "profile" ? "Make this page yours." : `Your first ${contentSingular[kind]} starts here.`}</h3><p>{query ? "Try another title or clear your search." : "Add the details, save a draft, and publish when it’s ready. Only published content is visible to visitors."}</p>{query && <button onClick={() => setQuery("")}>Clear search</button>}</div>}
    {(cursor || page?.next_cursor) && <div className={`${styles.pager} catalogue-pagination`}>{cursor && <button disabled={loading} onClick={() => setCursor("")}>First page</button>}{page?.next_cursor && <button disabled={loading} onClick={() => setCursor(page.next_cursor)}>Next page</button>}</div>}
    {editing && <PublicationEditor slug={slug} kind={kind} museumName={museum?.name ?? ""} item={editing === "new" ? undefined : editing} close={() => setEditing(null)} saved={saved} />}
  </>;
}