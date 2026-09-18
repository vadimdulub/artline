import type { ReactNode, RefObject } from "react";

export function TimelineGrid({ stageRef, ticks, busy, children, selection }: {
  stageRef: RefObject<HTMLDivElement | null>; ticks: { key: number; label: string; position: number }[];
  busy?: boolean; children: ReactNode;
  selection?: { left: number; right: number };
}) {
  return <div className="timeline-stage" ref={stageRef} aria-busy={busy}>
    <div className="tick-row" aria-hidden="true">{ticks.map(tick => <span key={tick.key} style={{ left: `${tick.position}%` }}><i />{tick.label}</span>)}</div>
    {selection && (selection.left > 0 || selection.right < 100) && <div className="timeline-selected-years" aria-hidden="true" style={{ left: `${selection.left}%`, width: `${selection.right - selection.left}%` }} />}
    {children}
  </div>;
}

export function TimelineLanes({ label, descriptionId, height, loading, children }: {
  label: string; descriptionId: string; height: number; loading?: boolean; children: ReactNode;
}) {
  return <div className="timeline-lanes" role="region" aria-label={label} aria-describedby={descriptionId} tabIndex={0}>
    <div className={loading ? "artist-field is-loading" : "artist-field"} style={{ height }}>{children}</div>
  </div>;
}

export function TimelineMark({ label, name, date, context, color, left, top, width, labelOffset, labelWidth, selected, disabled, approximate, href, onSelect, title, hasPopup, className = "" }: {
  label: string; name: string; date: string; context?: string; color: string;
  left: number; top: number; width: number; labelOffset: number; labelWidth: number;
  selected?: boolean; disabled?: boolean; approximate?: boolean; href?: string;
  onSelect: () => void; title?: string; hasPopup?: "dialog"; className?: string;
}) {
  const props = {
    className: `timeline-mark ${context ? "has-context" : ""} ${className}`,
    style: { left: `${left}%`, top, width: `${width}%`, ["--movement-color" as string]: color, ["--label-offset" as string]: `${labelOffset}px`, ["--label-width" as string]: `${labelWidth}px` },
    "aria-label": label, title: title ?? label, "data-approximate": approximate, "aria-haspopup": hasPopup,
  };
  const contents = <><span>{name}</span><small>{context ?? date}</small>{context && <small className="marker-context">{date}</small>}<i /></>;
  return href ? <a {...props} href={href} aria-current={selected ? "true" : undefined} aria-disabled={disabled || undefined} onClick={event => { if (disabled) event.preventDefault(); else onSelect(); }}>{contents}</a> :
    <button {...props} type="button" disabled={disabled} aria-pressed={selected} onClick={onSelect}>{contents}</button>;
}
