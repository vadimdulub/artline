import type { ReactNode } from "react";
import "./TimelineHeader.css";

export function TimelineHeader({ children, controls, legend, status, className = "" }: {
  children: ReactNode; controls?: ReactNode; legend?: ReactNode; status?: ReactNode; className?: string;
}) {
  return <div className={`timeline-heading-row timeline-compact-heading ${className}`}>
    <div className="timeline-heading-title">{children}</div>
    {controls && <div className="timeline-heading-controls">{controls}</div>}
    {legend && <div className="timeline-heading-key">{legend}</div>}
    {status && <div className="timeline-counter sr-only" role="status">{status}</div>}
  </div>;
}
