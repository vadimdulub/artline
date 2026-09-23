export function TimelineZoomOut({ disabled, onClick, title = "Show all years and keep filters" }: {
  disabled: boolean; onClick: () => void; title?: string;
}) {
  return <button type="button" className="timeline-zoom-out" disabled={disabled} aria-label="Zoom out to all years" title={title} onClick={onClick}>
    <span aria-hidden="true">−</span> Zoom out
  </button>;
}
