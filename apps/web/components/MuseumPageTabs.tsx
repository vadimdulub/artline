"use client";

import { useEffect, useRef, useState, useSyncExternalStore, type KeyboardEvent, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import Link from "./MemberLink";
import { useMemberSession } from "./MemberSession";
import { PublicationEditor } from "./MuseumPublicationEditor";
import { studioRequest, type MuseumContentKind, type MuseumPublication, type MuseumPublicationPage } from "@/lib/museum-studio";
import styles from "./MuseumPublic.module.css";

const tabs = [
  { id: "collection", label: "Collection", heading: "The collection", kind: "artwork", add: "Add artwork" },
  { id: "exhibitions", label: "Exhibitions", heading: "Exhibitions", kind: "exhibition", add: "Add exhibition" },
  { id: "guides", label: "Guides", heading: "Guides", kind: "guide", add: "Add guide" },
  { id: "visit", label: "Visit & about", heading: "Visit & about", kind: "profile", add: "Add details" },
] as const;
export type MuseumTab = typeof tabs[number]["id"];

function subscribe(callback: () => void) {
  for (const event of ["popstate", "hashchange", "artline:navigate"]) window.addEventListener(event, callback);
  return () => { for (const event of ["popstate", "hashchange", "artline:navigate"]) window.removeEventListener(event, callback); };
}
function tabFromLocation(location: string): MuseumTab {
  const url = new URL(location, "https://artline.invalid");
  // Keep links shared before the tab redesign working, including artwork links.
  const hash = url.hash.slice(1), query = url.searchParams.get("tab");
  return tabs.find(tab => tab.id === hash)?.id ?? tabs.find(tab => tab.id === query)?.id ?? "collection";
}

export function MuseumPageTabs({ slug, museumName, initialSearch, hasProfile, panels }: { slug: string; museumName: string; initialSearch: string; hasProfile: boolean; panels: Record<MuseumTab, ReactNode> }) {
  const location = useSyncExternalStore(subscribe, () => window.location.search + window.location.hash, () => initialSearch);
  const active = tabFromLocation(location), selected = tabs.find(tab => tab.id === active)!;
  const links = useRef<(HTMLAnchorElement | null)[]>([]);
  const { session } = useMemberSession();
  const member = session?.user?.id ?? "", accessKey = `${slug}:${member}`;
  const [access, setAccess] = useState<{ key: string; allowed: boolean }>();
  useEffect(() => {
    if (!member) return;
    const controller = new AbortController();
    studioRequest(`/${slug}`, { signal: controller.signal }).then(() => {
      if (!controller.signal.aborted) setAccess({ key: accessKey, allowed: true });
    }).catch(() => { if (!controller.signal.aborted) setAccess({ key: accessKey, allowed: false }); });
    return () => controller.abort();
  }, [member, slug, accessKey]);
  const canManage = !!member && access?.key === accessKey && access.allowed;
  function href(id: MuseumTab) {
    const url = new URL(location, "https://artline.invalid");
    url.searchParams.set("tab", id); url.hash = id;
    return `/museums/${slug}${url.search}${url.hash}`;
  }
  function activate(id: MuseumTab) {
    if (id === active) return;
    window.history.pushState(null, "", href(id));
    window.dispatchEvent(new Event("artline:navigate"));
  }
  function keyDown(event: KeyboardEvent<HTMLAnchorElement>, index: number) {
    if (event.key === " ") { event.preventDefault(); activate(tabs[index].id); return; }
    const next = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : event.key === "ArrowRight" ? (index + 1) % tabs.length : event.key === "ArrowLeft" ? (index + tabs.length - 1) % tabs.length : -1;
    if (next < 0) return;
    event.preventDefault(); activate(tabs[next].id); links.current[next]?.focus();
  }
  return <div className={styles.tabArea}>
    <nav className={styles.navigation} role="tablist" aria-label="Museum sections">{tabs.map((tab, index) => <a key={tab.id} ref={element => { links.current[index] = element; }} id={`museum-tab-${tab.id}`} href={href(tab.id)} role="tab" aria-selected={tab.id === active} aria-controls={tab.id} tabIndex={tab.id === active ? 0 : -1} onKeyDown={event => keyDown(event, index)} onClick={event => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault(); activate(tab.id);
    }}>{tab.label}</a>)}</nav>
    {tabs.map(tab => <section key={tab.id} id={tab.id} role="tabpanel" aria-labelledby={`museum-tab-${tab.id}`} tabIndex={0} hidden={tab.id !== active} className={styles.tabPanel}>
      {tab.id === active && <><div className={styles.tabHeading}><h2>{tab.heading}</h2>{canManage && <MuseumAddAction key={tab.kind} slug={slug} museumName={museumName} kind={selected.kind} label={tab.id === "visit" && hasProfile ? "Edit details" : tab.add} />}</div>{panels[tab.id]}</>}
    </section>)}
  </div>;
}

function MuseumAddAction({ slug, museumName, kind, label }: { slug: string; museumName: string; kind: MuseumContentKind; label: string }) {
  const router = useRouter();
  const [editing, setEditing] = useState<MuseumPublication | "new" | null>(null);
  const [loading, setLoading] = useState(false), [error, setError] = useState(""), [notice, setNotice] = useState("");
  const pending = useRef<AbortController | null>(null);
  const trigger = useRef<HTMLButtonElement>(null), wasEditing = useRef(false);
  useEffect(() => () => pending.current?.abort(), []);
  useEffect(() => {
    // Loading the profile disables its trigger before the editor captures focus.
    if (wasEditing.current && !editing) trigger.current?.focus();
    wasEditing.current = !!editing;
  }, [editing]);
  async function open() {
    setError(""); setNotice("");
    if (kind !== "profile") { setEditing("new"); return; }
    // Use the existing private draft when one exists, even if never published.
    const controller = new AbortController(); pending.current = controller; setLoading(true);
    try {
      const page = await studioRequest<MuseumPublicationPage>(`/${slug}/content?kind=profile`, { signal: controller.signal });
      if (!controller.signal.aborted) setEditing(page.items[0] ?? "new");
    } catch (e) { if (!controller.signal.aborted) setError((e as Error).message); }
    finally { if (!controller.signal.aborted) setLoading(false); }
  }
  function saved(action: string) {
    setEditing(null);
    setNotice(action === "publish" ? "Published. This page is updated." : action === "unpublish" ? "Unpublished. The details are now private." : "Draft saved in your museum studio.");
    if (action !== "save") router.refresh();
  }
  return <div className={styles.tabAction}>
    <button ref={trigger} type="button" className={styles.addButton} disabled={loading} onClick={open}>{loading ? "Opening…" : label}</button>
    {error && <p role="alert">{error}</p>}
    {notice && <p role="status">{notice} <Link href={`/account/museums/${slug}`}>Open studio</Link></p>}
    {editing && <PublicationEditor slug={slug} kind={kind} museumName={museumName} item={editing === "new" ? undefined : editing} close={() => setEditing(null)} saved={saved} />}
  </div>;
}
