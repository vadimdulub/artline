"use client";

import { useEffect, useId, useRef, useState } from "react";
import Link from "@/components/MemberLink";
import { apiRequest } from "@/lib/api";
import type { ArtistConnection, ArtistConnections, ArtistConnectionsPage, ArtistDetail, Influence } from "@/lib/types";
import { SourceList } from "./PainterArtworkDetails";
import { RecordDrawer } from "./RecordDrawer";
import styles from "./ArtisticConnections.module.css";

type Direction = "incoming" | "outgoing";
const directions: Direction[] = ["incoming", "outgoing"];
const titles = { incoming: "Teachers & influences", outgoing: "Influence & legacy" };
const INITIAL_COUNT = 3;
function relationship(claim: Influence, direction: Direction) {
  if (claim.relationship_type === "teacher_of") return direction === "incoming" ? "Teacher" : "Student";
  return ({ influenced: "Influence", documented_admiration: "Admiration", workshop_of: "Workshop relationship", collaborated_with: "Collaboration", responded_to_work_of: "Response to work" } as Record<string, string>)[claim.relationship_type] ?? claim.relationship_type.replaceAll("_", " ");
}
function supported(claim: Influence) {
  return ["documented", "scholarly_consensus", "scholarly_interpretation"].includes(claim.evidence_level);
}
function EvidenceLevel({ claim }: { claim: Influence }) {
  return <span className={`${styles.level} ${supported(claim) ? styles.supported : ""}`}>{claim.evidence_level.replaceAll("_", " ")}</span>;
}

export function ArtisticConnections({ artist, initial }: { artist: Pick<ArtistDetail, "id" | "slug" | "display_name" | "timeline_display">; initial: ArtistConnections }) {
  const uid = useId().replaceAll(":", "");
  const headingID = `connections-${uid}`;
  const [pages, setPages] = useState(initial);
  const [loading, setLoading] = useState<Partial<Record<Direction, boolean>>>({});
  const [errors, setErrors] = useState<Partial<Record<Direction, string>>>({});
  const [selected, setSelected] = useState<{ item: ArtistConnection; direction: Direction } | null>(null);
  const [announcement, setAnnouncement] = useState("");
  const [lines, setLines] = useState<{ d: string; supported: boolean }[]>([]);
  const grid = useRef<HTMLDivElement>(null);
  const center = useRef<HTMLDivElement>(null);
  const requests = useRef<Partial<Record<Direction, AbortController>>>({});
  const focusTarget = useRef<{ direction: Direction; index?: number } | null>(null);

  useEffect(() => {
    const active = requests.current;
    return () => { directions.forEach(direction => active[direction]?.abort()); };
  }, []);
  useEffect(() => {
    const target = focusTarget.current;
    if (!target) return;
    focusTarget.current = null;
    const selector = target.index === undefined ? `[data-more="${target.direction}"]` : `[data-direction="${target.direction}"][data-index="${target.index}"]`;
    grid.current?.querySelector<HTMLButtonElement>(selector)?.focus({ preventScroll: true });
  }, [pages]);

  useEffect(() => {
    const element = grid.current, focal = center.current;
    if (!element || !focal) return;
    let frame = 0;
    const draw = () => {
      const bounds = element.getBoundingClientRect();
      if (bounds.width <= 700) { focal.style.marginTop = ""; setLines([]); return; }
      const nodes = [...element.querySelectorAll<HTMLButtonElement>("[data-index]")];
      const first = nodes.filter(node => Number(node.dataset.index) < INITIAL_COUNT);
      if (!first.length) return;
      const top = Math.min(...first.map(node => node.getBoundingClientRect().top));
      const bottom = Math.max(...first.map(node => node.getBoundingClientRect().bottom));
      focal.style.marginTop = `${Math.max(40, (top + bottom) / 2 - bounds.top - focal.offsetHeight / 2)}px`;
      const mid = focal.getBoundingClientRect(), cy = mid.top - bounds.top + mid.height / 2;
      setLines(nodes.flatMap(node => {
        const direction = node.dataset.direction as Direction, index = Number(node.dataset.index);
        const item = pages[direction].items[index], rect = node.parentElement!.getBoundingClientRect();
        const kinds = [...new Set(item.claims.map(supported))];
        return kinds.map((solid, i) => {
          const offset = (i - (kinds.length - 1) / 2) * 7;
          const x1 = (direction === "incoming" ? rect.right : mid.right) - bounds.left;
          const x2 = (direction === "incoming" ? mid.left : rect.left) - bounds.left;
          const y1 = (direction === "incoming" ? rect.top - bounds.top + rect.height / 2 : cy) + offset;
          const y2 = (direction === "incoming" ? cy : rect.top - bounds.top + rect.height / 2) + offset;
          return { d: `M${x1},${y1} C${(x1 + x2) / 2},${y1} ${(x1 + x2) / 2},${y2} ${x2},${y2}`, supported: solid };
        });
      }));
    };
    const schedule = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(draw); };
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(schedule);
    observer?.observe(element);
    schedule();
    return () => { observer?.disconnect(); cancelAnimationFrame(frame); };
  }, [pages]);

  async function showMore(direction: Direction) {
    if (requests.current[direction] || !pages[direction].next_cursor) return;
    const controller = new AbortController(); requests.current[direction] = controller;
    setLoading(value => ({ ...value, [direction]: true }));
    setErrors(value => ({ ...value, [direction]: "" }));
    const previous = pages[direction].items.length;
    try {
      const query = new URLSearchParams({ direction, cursor: pages[direction].next_cursor });
      const page = await apiRequest<ArtistConnectionsPage>(`artists/${encodeURIComponent(artist.slug)}/connections?${query}`, { signal: controller.signal });
      if (controller.signal.aborted) return;
      focusTarget.current = { direction, index: previous };
      setPages(value => ({ ...value, [direction]: { ...page, items: [...value[direction].items, ...page.items] } }));
      setAnnouncement(`${Math.min(previous + page.items.length, page.total)} of ${page.total} connections shown in ${titles[direction]}.`);
    } catch {
      if (!controller.signal.aborted) setErrors(value => ({ ...value, [direction]: "Connections could not be loaded. Please try again." }));
    } finally {
      if (requests.current[direction] === controller) { delete requests.current[direction]; setLoading(value => ({ ...value, [direction]: false })); }
    }
  }
  function showLess(direction: Direction) {
    requests.current[direction]?.abort(); delete requests.current[direction];
    focusTarget.current = { direction };
    setPages(value => ({ ...value, [direction]: initial[direction] }));
    setLoading(value => ({ ...value, [direction]: false }));
    setErrors(value => ({ ...value, [direction]: "" }));
    setAnnouncement(`${titles[direction]} returned to the first three connections.`);
  }
  if (!initial.incoming.total && !initial.outgoing.total) return null;
  const side = (direction: Direction) => {
    const page = pages[direction];
    return <section className={styles.side} aria-labelledby={`${uid}-${direction}-heading`} key={direction}>
      <header className={styles.sideHeading}><h3 id={`${uid}-${direction}-heading`}>{titles[direction]}</h3><span>{page.items.length < page.total ? `${page.items.length} of ${page.total}` : page.total}</span></header>
      <div className={styles.nodes} id={`${uid}-${direction}-nodes`} aria-busy={loading[direction] || undefined}>
        {page.items.map((item, index) => <div className={styles.node} key={item.id}>
          <div className={styles.nodeCopy}>{item.slug ? <Link className={styles.name} href={`/artists/${item.slug}`} prefetch={false}>{item.name}</Link> : <span className={styles.name}>{item.name}</span>}
            {item.claims.map(claim => <span key={claim.id} className={styles.claimLabel}><span>{relationship(claim, direction)}</span><span aria-hidden="true">·</span><EvidenceLevel claim={claim} /></span>)}
          </div>
          <button type="button" className={styles.evidenceButton} data-direction={direction} data-index={index} aria-label={`Evidence for ${item.name}`} onClick={() => setSelected({ item, direction })}><span aria-hidden="true">›</span></button>
        </div>)}
        {!page.total && <p className={styles.empty}>No connections recorded.</p>}
      </div>
      {errors[direction] && <p className={styles.error} role="alert">{errors[direction]}</p>}
      {page.next_cursor && <button type="button" className={styles.more} data-more={direction} aria-controls={`${uid}-${direction}-nodes`} aria-expanded={page.items.length > INITIAL_COUNT} disabled={loading[direction]} onClick={() => showMore(direction)}><span>{loading[direction] ? "Loading…" : "Show more"}</span><span>{Math.max(0, page.total - page.items.length)} remaining <span aria-hidden="true">+</span></span></button>}
      {page.items.length > INITIAL_COUNT && <button type="button" className={styles.less} aria-controls={`${uid}-${direction}-nodes`} onClick={() => showLess(direction)}>Show less</button>}
    </section>;
  };
  return <section className={styles.section} aria-labelledby={headingID}>
    <header className={styles.heading}><h2 id={headingID} tabIndex={-1}>Artistic connections</h2><p>Explore the people and evidence around {artist.display_name}.</p></header>
    <div className={styles.grid} ref={grid}>
      <svg className={styles.lines} aria-hidden="true"><defs>{[false, true].map(solid => <marker key={String(solid)} id={`${uid}-arrow-${solid}`} markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0L7 3.5L0 7" fill="none" className={solid ? styles.solidStroke : styles.dashedStroke} /></marker>)}</defs>{lines.map((line, index) => <path key={index} d={line.d} fill="none" className={line.supported ? styles.solidStroke : styles.dashedStroke} strokeDasharray={line.supported ? undefined : "4 4"} markerEnd={`url(#${uid}-arrow-${line.supported})`} />)}</svg>
      {side("incoming")}
      <div className={styles.center} ref={center}><p>You are exploring</p><h3>{artist.display_name}</h3><span>{artist.timeline_display}</span></div>
      {side("outgoing")}
    </div>
    <div className={styles.legend}><span><i />Editorial inference or contested claim</span><span><i className={styles.solidLegend} />Documented or scholarly evidence</span></div>
    <p className="sr-only" role="status">{announcement}</p>
    {selected && <RecordDrawer label={`Connection with ${selected.item.name}`} closeLabel="Close connection evidence" recordKey={`${selected.direction}-${selected.item.id}`} title="Connection evidence" close={() => setSelected(null)} fallbackFocusId={headingID}>
      <div className={styles.detail}><h2>{selected.item.name}</h2><p className={styles.detailContext}>{selected.direction === "incoming" ? `${selected.item.name} → ${artist.display_name}` : `${artist.display_name} → ${selected.item.name}`}</p>
        {selected.item.claims.map(claim => <section key={claim.id} className={styles.claimDetail}><h3>{relationship(claim, selected.direction)}</h3><EvidenceLevel claim={claim} /><p>{claim.evidence_note}</p><SourceList citations={claim.citations} /></section>)}
        {selected.item.slug && <Link className={styles.profileLink} href={`/artists/${selected.item.slug}`} prefetch={false}>Explore {selected.item.name}</Link>}
      </div>
    </RecordDrawer>}
  </section>;
}
