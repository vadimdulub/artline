/** Keep the announcement on the containing status region; the spinner is decorative. */
export function LoadingIndicator({ label = "Loading…" }: { label?: string }) {
  return <span className="loading-indicator"><span className="loading-spinner" aria-hidden="true" />{label}</span>;
}
