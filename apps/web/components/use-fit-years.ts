"use client";

import { useEffect } from "react";
import { updateQuery } from "@/lib/url-state";

export function useFitYears(enabled: boolean, ready: boolean, range?: { start: number; end: number } | null, undated = 0) {
  const start = range?.start, end = range?.end;
  useEffect(() => {
    if (!enabled || !ready) return;
    // Undated entries remain reachable in the full view. Empty results leave
    // the requested years unchanged; only a successful current response fits.
    updateQuery({ fit: null, ...(undated === 0 && start !== undefined && end !== undefined ? { start: String(start), end: String(end) } : {}) });
  }, [enabled, ready, start, end, undated]);
}
