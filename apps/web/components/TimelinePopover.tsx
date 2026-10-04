"use client";

import { useState, type ReactNode } from "react";
import "./TimelineHeader.css";

export function TimelinePopover({ label, children, className = "", defaultOpen = false }: {
  label: string; children: ReactNode; className?: string; defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return <details className={`timeline-popover ${className}`} open={open}
    onToggle={event => setOpen(event.currentTarget.open)}
    onKeyDown={event => { if (event.key === "Escape" && event.currentTarget.open) { event.preventDefault(); event.stopPropagation(); event.currentTarget.open = false; setOpen(false); event.currentTarget.querySelector("summary")?.focus(); } }}
    onBlur={event => { if (event.relatedTarget instanceof Node && !event.currentTarget.contains(event.relatedTarget)) setOpen(false); }}>
    <summary>{label}</summary>
    <div className="timeline-popover-panel">{children}</div>
  </details>;
}
