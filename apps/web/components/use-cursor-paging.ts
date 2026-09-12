"use client";
import { useState } from "react";

type Entry = { cursor: string; number: number | null };
// Navigation state only: never retain artwork pages. A deep link has an unknown
// ordinal until First is used; do not invent an offset from an opaque cursor.
export function useCursorPaging(scope: string, cursor: string, change: (cursor: string | null) => void) {
  const [trail, setTrail] = useState<{ scope: string; entries: Entry[] }>({ scope: "", entries: [] });
  const entries = trail.scope === scope ? trail.entries : [];
  const index = entries.findIndex(entry => entry.cursor === cursor);
  const number = index >= 0 ? entries[index].number : cursor ? null : 1;
  function next(value: string) {
    if (!value) return;
    const prefix = index >= 0 ? entries.slice(0, index + 1) : [{ cursor, number }];
    setTrail({ scope, entries: [...prefix, { cursor: value, number: number === null ? null : number + 1 }].slice(-50) });
    change(value);
  }
  function previous() { if (index > 0) change(entries[index - 1].cursor || null); }
  function first() { setTrail({ scope, entries: [{ cursor: "", number: 1 }] }); change(null); }
  return { number, canPrevious: index > 0, hasCursor: Boolean(cursor), next, previous, first };
}

export const formatCount = (value: number) => new Intl.NumberFormat("en-GB").format(value);
