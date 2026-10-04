import type { ReactNode } from "react";
import "./TimelineHeader.css";

export function TimelineHeader({ children, controls, zoom, status, className = "" }: {
  children: ReactNode; controls?: ReactNode; zoom: ReactNode; status?: ReactNode; className?: string;
}) {
  return <div className={`timeline-heading-row timeline-compact-heading ${className}`}>
    <div className="timeline-heading-title">{children}</div>
    {controls && <div className="timeline-heading-controls">{controls}</div>}
    <div className="timeline-heading-zoom">{zoom}</div>
    {status && <div className="timeline-counter sr-only" role="status">{status}</div>}
  </div>;
}
