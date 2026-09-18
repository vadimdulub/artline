"use client";
import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";
import { apiRequest, ApiError, editorHeaders, errorMessage } from "@/lib/api";
import { useEditorToken, EditorAccess } from "./EditorAccess";
import { EditorNav } from "./EditorNav";
import { AtlasFilters, AtlasSelect, ActiveFilters } from "./AtlasFilters";
import { AtlasPageHeader } from "./AtlasPageHeader";
import { updateQuery, useQueryString } from "@/lib/url-state";
import type { ArtistDetail, CatalogueArtist, PublicationValidation } from "@/lib/types";
type Draft = { slug: string; display_name: string; sort_name: string; entity_type: string; timeline_start_year: number; timeline_end_year: number; timeline_display: string; timeline_basis: string; biography_md: string; status: string; expected_revision?: number };
const blank: Draft = { slug: "", display_name: "", sort_name: "", entity_type: "person", timeline_start_year: 1800, timeline_end_year: 1900, timeline_display: "", timeline_basis: "life", biography_md: "", status: "draft" };

export function CatalogueClient({ preview = false }: { preview?: boolean }) {
  const [token, setToken] = useEditorToken();
  const [artists, setArtists] = useState<CatalogueArtist[]>([]);
  const parameters = new URLSearchParams(useQueryString());
  const query = parameters.get("q") ?? "";
  const searchRef = useRef<HTMLInputElement>(null);
  const editorAccessRef = useRef<HTMLDetailsElement>(null);
  const setQuery = (value: string) => updateQuery({ q: value || null, page: null }, false);
  const rawStatus = parameters.get("status") ?? "";
  const statuses = token ? ["draft", "review", "published", "archived"] : preview ? ["draft", "review", "published"] : ["published"];
  const status = statuses.includes(rawStatus) ? rawStatus : "";
  const setStatus = (value: string) => updateQuery({ status: value || null, page: null }, true);
  const [form, setForm] = useState<Draft | null>(null), [editing, setEditing] = useState<string | null>(null);
  const [message, setMessage] = useState(""), [loadError, setLoadError] = useState("");
  const [busy, setBusy] = useState(false), [loading, setLoading] = useState(true), [refresh, setRefresh] = useState(0);
  const [validation, setValidation] = useState<{ artistName: string; report: PublicationValidation } | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const rawPage = Number(parameters.get("page") ?? "1");
  const page = Number.isSafeInteger(rawPage) && rawPage >= 1 && rawPage <= 10000 ? rawPage - 1 : 0;
  const setPage = (next: number) => updateQuery({ page: next ? String(next + 1) : null }, true);
  const rawSort = parameters.get("sort") ?? "name";
  const sort = ["name", "date", "updated"].includes(rawSort) ? rawSort : "name";
  const setSort = (value: string) => updateQuery({ sort: value === "name" ? null : value, page: null }, true);
  const clearFilters = () => updateQuery({ q: null, status: null, page: null }, true);
  const resetView = () => updateQuery({ q: null, status: null, sort: null, page: null }, true);
  const activeFilters = [
    ...(query ? [{ key: "q", label: `Search: ${query}`, remove: () => setQuery("") }] : []),
    ...(status ? [{ key: "status", label: status === "review" ? "In review" : status[0].toUpperCase() + status.slice(1), remove: () => setStatus("") }] : []),
  ];
  const requestVersion = JSON.stringify([query, status, token, refresh, page, sort]);
  const [settledRequest, setSettledRequest] = useState("");
  const pending = loading || settledRequest !== requestVersion;
  const [baseline, setBaseline] = useState("");
  const [isError, setIsError] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);
  const validationRef = useRef<HTMLElement>(null);
  const formOpen = Boolean(form);
  const dirty = Boolean(form && JSON.stringify(form) !== baseline);
  const wordCount = form?.biography_md.trim().split(/\s+/).filter(Boolean).length ?? 0;
  useEffect(() => {
    if (!formOpen) return;
    formRef.current?.scrollIntoView({ block: "start", behavior: "instant" });
    formRef.current?.querySelector<HTMLInputElement>("input")?.focus({ preventScroll: true });
  }, [formOpen, editing]);
  useEffect(() => {
    if (validation) { validationRef.current?.scrollIntoView({ block: "center", behavior: "instant" }); validationRef.current?.focus({ preventScroll: true }); }
  }, [validation]);
  useEffect(() => {
    if (!dirty) return;
    function unload(event: BeforeUnloadEvent) { event.preventDefault(); event.returnValue = ""; }
    function navigate(event: MouseEvent) {
      if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      const link = event.target instanceof Element ? event.target.closest<HTMLAnchorElement>("a[href]") : null;
      if (link && link.target !== "_blank" && !link.hasAttribute("download") && !link.getAttribute("href")?.startsWith("#") && !window.confirm("Leave this page and discard your unsaved painter changes?")) { event.preventDefault(); event.stopPropagation(); }
    }
    window.addEventListener("beforeunload", unload);
    document.addEventListener("click", navigate, true);
    return () => { window.removeEventListener("beforeunload", unload); document.removeEventListener("click", navigate, true); };
  }, [dirty]);
  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoading(true); setLoadError("");
      const parameters = new URLSearchParams({ limit: "50", offset: String(page * 50), sort });
      if (status) parameters.set("status", status);
      if (query.trim()) parameters.set("q", query.trim());
      apiRequest<{ items: CatalogueArtist[]; has_more: boolean }>(`catalogue/artists?${parameters}`, { signal: controller.signal, headers: editorHeaders(token) })
        .then(body => { setArtists(body.items); setHasMore(body.has_more); })
        .catch(error => { if (!controller.signal.aborted) { setLoadError(errorMessage(error)); setArtists([]); } })
        .finally(() => { if (!controller.signal.aborted) { setLoading(false); setSettledRequest(requestVersion); } });
    }, 180);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [query, status, token, refresh, page, sort, requestVersion]);

  async function action(work: () => Promise<void>) {
    if (busy) return;
    setBusy(true); setMessage(""); setIsError(false);
    try { await work(); } catch (error) { setIsError(true); setMessage(errorMessage(error)); } finally { setBusy(false); }
  }
  async function save(event: FormEvent) {
    event.preventDefault();
    if (!form) return;
    await action(async () => {
      await apiRequest(editing ? `catalogue/artists/${editing}` : "catalogue/artists", { method: editing ? "PATCH" : "POST", headers: editorHeaders(token), body: JSON.stringify({ ...form, sort_name: form.sort_name || form.display_name, biography_md: form.biography_md.trim() || null }) });
      setForm(null); setEditing(null); setValidation(null); setMessage("Painter saved."); setRefresh(value => value + 1);
    });
  }
  async function edit(artist: CatalogueArtist, duplicate = false) {
    await action(async () => {
      if (dirty && !window.confirm("Discard the unsaved form and open this painter?")) return;
      const record = await apiRequest<ArtistDetail>(`catalogue/artists/${artist.id}`, { headers: editorHeaders(token) });
      setEditing(duplicate ? null : record.id);
      const next: Draft = { slug: duplicate ? `${record.slug}-copy` : record.slug, display_name: duplicate ? `${record.display_name} (copy)` : record.display_name, sort_name: record.sort_name, entity_type: record.entity_type, timeline_start_year: record.timeline_start_year, timeline_end_year: record.timeline_end_year, timeline_display: record.timeline_display, timeline_basis: record.timeline_basis, biography_md: record.biography_md ?? "", status: record.status === "draft" || duplicate ? "draft" : "review", expected_revision: duplicate ? undefined : record.revision };
      setForm(next); setBaseline(duplicate ? "" : JSON.stringify(next));
      if (record.status === "published" && !duplicate) setMessage("Saving this edit returns the painter to review.");
    });
  }
  async function archive(artist: CatalogueArtist, restore = false) {
    if (!restore && !window.confirm(`Archive ${artist.display_name}? You can restore it from the archived view.`)) return;
    await action(async () => {
      await apiRequest(`catalogue/artists/${artist.id}${restore ? "/restore" : ""}`, { method: restore ? "POST" : "DELETE", headers: editorHeaders(token), body: JSON.stringify({ expected_revision: artist.revision }) });
      setValidation(null); setMessage(restore ? "Painter restored as a draft." : "Painter archived. It can be restored from the archived view."); setRefresh(value => value + 1);
    });
  }
  async function validate(artist: CatalogueArtist) {
    await action(async () => {
      const report = await apiRequest<PublicationValidation>("publish/validate", { method: "POST", headers: editorHeaders(token), body: JSON.stringify({ artist_id: artist.id }) });
      setValidation({ artistName: artist.display_name, report });
      setMessage(report.ready ? "All publication checks passed." : "Review the publication checks below.");
    });
  }
  async function publish(id: string, revision: number, publish: boolean) {
    await action(async () => {
      try { await apiRequest(`${publish ? "publish" : "unpublish"}/artists/${id}`, { method: "POST", headers: editorHeaders(token), body: JSON.stringify({ expected_revision: revision }) }); }
      catch (error) {
        if (error instanceof ApiError && error.status === 422) {
          const report = error.details as PublicationValidation;
          if (report.issues) setValidation({ artistName: artists.find(item => item.id === id)?.display_name ?? "Painter", report });
        }
        throw error;
      }
      setValidation(null); setMessage(publish ? "Painter published." : "Painter returned to review."); setRefresh(value => value + 1);
    });
  }
  function change<K extends keyof Draft>(key: K, value: Draft[K]) { if (form) setForm({ ...form, [key]: value }); }
  return <main id="main-content" className="admin-page">
    <EditorNav />
    <AtlasPageHeader title="Catalogue" description="A working collection. Add, revise, and follow the evidence."><button className="primary-button" disabled={busy} onClick={() => { if (dirty && !window.confirm("Discard your unsaved changes?")) return; setEditing(null); setForm({ ...blank }); setBaseline(JSON.stringify(blank)); setMessage(""); if (!token && editorAccessRef.current) editorAccessRef.current.open = true; }}>Add painter</button></AtlasPageHeader>
    <details ref={editorAccessRef} className="catalogue-access"><summary>Editor access<span>{token ? "Enabled" : "Read-only preview"}</span></summary><EditorAccess token={token} onChange={setToken} /></details>
    {form && <form ref={formRef} className="artist-form" onSubmit={save} aria-label={editing ? "Edit painter" : "New painter"}>
      <fieldset disabled={busy} className="form-fields">
      <div className="form-heading"><h2>{editing ? "Edit painter" : "New painter"}</h2><span>{dirty ? "Unsaved changes" : "No unsaved changes"}</span></div>
      <label><span>Display name</span><input required maxLength={200} value={form.display_name} onChange={event => change("display_name", event.target.value)} /></label>
      <label><span>Stable slug</span><input required maxLength={100} pattern="[a-z0-9]+(-[a-z0-9]+)*" value={form.slug} onChange={event => change("slug", event.target.value)} placeholder="painter-name" /></label>
      <label><span>Sort name</span><input value={form.sort_name} onChange={event => change("sort_name", event.target.value)} placeholder="Surname, given name" /></label>
      <label><span>Entity type</span><select value={form.entity_type} onChange={event => change("entity_type", event.target.value)}>{["person", "anonymous_master", "workshop", "collective"].map(value => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</select></label>
      <label><span>Start year</span><input required type="number" min={1} max={2000} value={form.timeline_start_year} onChange={event => change("timeline_start_year", Number(event.target.value))} /></label>
      <label><span>End year</span><input required type="number" min={1100} max={2100} value={form.timeline_end_year} onChange={event => change("timeline_end_year", Number(event.target.value))} /></label>
      <label><span>Dates as shown to readers</span><input required value={form.timeline_display} onChange={event => change("timeline_display", event.target.value)} placeholder="c. 1495–1540" /></label>
      <label><span>Date basis</span><select value={form.timeline_basis} onChange={event => change("timeline_basis", event.target.value)}>{["life", "activity", "mixed", "estimated"].map(value => <option key={value}>{value}</option>)}</select></label>
      <label className="wide-field"><span>Short biography (Markdown)</span><textarea aria-describedby="biography-count" value={form.biography_md} onChange={event => change("biography_md", event.target.value)} /><small id="biography-count">{wordCount} words · 80–300 required for publication. A draft can be saved at any length.</small></label>
      <label><span>Save as</span><select value={form.status} onChange={event => change("status", event.target.value)}><option value="draft">Draft</option><option value="review">In review</option></select></label>
      {message && <p className={`form-feedback${isError ? " is-error" : ""}`} role={isError ? "alert" : "status"}>{message}</p>}
      <div className="form-actions"><button className="primary-button" disabled={!token || busy} type="submit">{busy ? "Saving…" : "Save painter"}</button><button type="button" disabled={busy} onClick={() => { if (!dirty || window.confirm("Discard the unsaved form?")) { setForm(null); setEditing(null); setMessage(""); } }}>Cancel</button></div>
      </fieldset>
    </form>}
    <AtlasFilters searchRef={searchRef} query={query} onQuery={setQuery} onReset={resetView} searchLabel="Search painters" placeholder="Painter name" columns={2} activeCount={status ? 1 : 0}>
      <AtlasSelect label="Status" value={status} onChange={setStatus} options={[{ value: "", label: "All records" }, ...statuses.map(value => ({ value, label: value === "review" ? "In review" : value[0].toUpperCase() + value.slice(1) }))]} />
      <AtlasSelect label="Sort by" value={sort} onChange={setSort} options={[{ value: "name", label: "Name" }, { value: "date", label: "Date" }, { value: "updated", label: "Recently updated" }]} />
    </AtlasFilters>
    <ActiveFilters filters={activeFilters} onClear={clearFilters} searchRef={searchRef} />
    {message && !form && <p className={`save-message${isError ? " is-error" : ""}`} role={isError ? "alert" : "status"}>{message}</p>}
    {loadError && <p className="save-message" role="alert">{loadError} <button onClick={() => setRefresh(value => value + 1)}>Try again</button></p>}
    {validation && <section ref={validationRef} tabIndex={-1} className={`validation-panel ${validation.report.ready ? "is-ready" : ""}`} aria-labelledby="validation-title"><div><span className="validation-kicker">Publication checks</span><h2 id="validation-title">{validation.artistName}</h2><p>{validation.report.ready ? "This record is ready for publication." : `${validation.report.issues.length} items need attention.`}</p></div>{validation.report.ready ? <button className="primary-button" disabled={!token || busy} onClick={() => void publish(validation.report.artist_id, validation.report.revision, true)}>Publish record</button> : <ol>{validation.report.issues.map((issue, i) => <li key={i}><code>{issue.path}</code>{issue.message}</li>)}</ol>}</section>}
    <p className="table-scroll-hint" id="catalogue-scroll-help">Scroll the table sideways for dates and editing actions. With the table focused, use the arrow keys.</p>
    <div className="table-shell" tabIndex={0} role="region" aria-label="Painter catalogue" aria-describedby="catalogue-scroll-help" aria-busy={pending}><table><caption className="sr-only">Painter records and editorial actions</caption><thead><tr><th scope="col">Name</th><th scope="col">Dates</th><th scope="col">Status</th><th scope="col">Revision</th><th scope="col">Updated</th><th scope="col">Actions</th></tr></thead><tbody>{artists.map(artist => <tr key={artist.id}><td><Link href={`/artists/${artist.slug}`}>{artist.display_name}</Link><small>{artist.slug}</small></td><td>{artist.timeline_display}</td><td><span className={`table-status status-${artist.status}`}>{artist.status === "review" ? "In review" : artist.status[0].toUpperCase() + artist.status.slice(1)}</span></td><td>{artist.revision}</td><td>{new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(artist.updated_at))}</td><td><div className="row-actions">{artist.status === "archived" ? <button disabled={!token || busy || pending} onClick={() => void archive(artist, true)}>Restore</button> : <><button disabled={!token || busy || pending} onClick={() => void edit(artist)}>Edit</button><button disabled={!token || busy || pending} onClick={() => void edit(artist, true)}>Duplicate</button><button disabled={!token || busy || pending} onClick={() => void validate(artist)}>Check</button>{artist.status === "published" && <button disabled={!token || busy || pending} onClick={() => void publish(artist.id, artist.revision, false)}>Unpublish</button>}<button disabled={!token || busy || pending} onClick={() => void archive(artist)}>Archive</button></>}</div></td></tr>)}</tbody></table>{!artists.length && <div className="table-empty">{pending ? "Loading the catalogue…" : loadError ? "Catalogue unavailable" : "No painters match these filters."}</div>}</div>
    <div className="catalogue-pagination"><button disabled={page === 0 || pending} onClick={() => setPage(page - 1)}>Previous page</button><span role="status">{pending ? "Updating catalogue…" : `Page ${page + 1} · ${artists.length} records`}</span><button disabled={!hasMore || pending} onClick={() => setPage(page + 1)}>Next page</button></div>
  </main>;
}
