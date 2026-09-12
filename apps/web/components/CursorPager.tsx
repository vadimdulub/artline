"use client";
import { formatCount, useCursorPaging } from "./use-cursor-paging";
import styles from "./Museums.module.css";

export function CursorPager({ paging, next, busy, total, shown, label, compact = false, noun = "works" }: {
  paging: ReturnType<typeof useCursorPaging>; next: string; busy: boolean;
  total: number; shown: number; label: string; compact?: boolean; noun?: string;
}) {
  if (!next && !paging.hasCursor && !busy) return null;
  return <nav className={styles.cursorPager} aria-label={label}>
    {!compact && <span>{paging.number ? `Page ${paging.number} · ` : ""}{formatCount(shown)} of {formatCount(total)} {noun}</span>}
    <div>
      {!compact && paging.hasCursor && <button disabled={busy} onClick={paging.first}>First page</button>}
      <button disabled={busy || !paging.canPrevious} onClick={paging.previous}>Previous page</button>
      <button disabled={busy || !next} onClick={() => paging.next(next)}>Next page</button>
    </div>
  </nav>;
}
