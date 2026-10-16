"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import styles from "./about.module.css";

export function PreviewScroller({ id, label, previousLabel, nextLabel, heading, action, children, dark = false }: {
  id: string; label: string; previousLabel: string; nextLabel: string;
  heading: ReactNode; action: ReactNode; children: ReactNode; dark?: boolean;
}) {
  const viewport = useRef<HTMLDivElement>(null);
  const [edges, setEdges] = useState({ ready: false, start: true, end: true });
  const measure = useCallback(() => {
    const element = viewport.current;
    if (!element) return;
    const next = { ready: true, start: element.scrollLeft < 2, end: element.scrollLeft + element.clientWidth >= element.scrollWidth - 2 };
    setEdges(current => current.ready === next.ready && current.start === next.start && current.end === next.end ? current : next);
  }, []);

  useEffect(() => {
    const element = viewport.current;
    if (!element) return;
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    // Observe the content too: responsive card sizes can change the scroll span.
    for (const child of element.children) observer.observe(child);
    return () => observer.disconnect();
  }, [measure]);

  function move(direction: number | "start" | "end") {
    const element = viewport.current;
    if (!element) return;
    const left = direction === "start" ? 0 : direction === "end" ? element.scrollWidth : element.scrollLeft + direction * element.clientWidth * .8;
    element.scrollTo({ left, behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth" });
  }

  return <div>
    <div className={styles.scrollerHeading}>
      <div className={styles.sectionHeading}>{heading}</div>
      <div className={styles.scrollerActions}>
        {action}
        <div className={styles.scrollControls} hidden={edges.ready && edges.start && edges.end} style={{ visibility: edges.ready ? "visible" : "hidden" }}>
          <button type="button" aria-label={previousLabel} aria-controls={id} disabled={edges.start} onClick={() => move(-1)}>←</button>
          <button type="button" aria-label={nextLabel} aria-controls={id} disabled={edges.end} onClick={() => move(1)}>→</button>
        </div>
      </div>
    </div>
    <div id={id} ref={viewport} role="region" aria-label={label} tabIndex={0}
      className={`${styles.scroller}${dark ? ` ${styles.darkScroller}` : ""}`} onScroll={measure}
      onKeyDown={event => {
        if (event.target !== event.currentTarget) return;
        const direction = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : event.key === "Home" ? "start" : event.key === "End" ? "end" : null;
        if (direction !== null) { event.preventDefault(); move(direction); }
      }}>{children}</div>
  </div>;
}
