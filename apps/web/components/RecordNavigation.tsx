"use client";
import { useEffect, useState } from "react";
import { apiRequest, errorMessage } from "@/lib/api";
import type { AtlasResponse, AtlasItem } from "@/lib/atlas";
import type { ArtistWorksPage, Artwork } from "@/lib/types";

export type RecordNavigation = {
  previous?: () => void;
  next?: () => void;
  busy?: boolean;
  error?: string;
  retry?: () => void;
};

// Fetch only the two adjacent keys in the server's current filtered sequence.
// This works for direct links and across pages without accumulating records.
export function useRecordNavigation(path: string | null, id: string, select: (id: string, item: AtlasItem | Artwork) => void): RecordNavigation {
  const [attempt, setAttempt] = useState(0);
  const key = `${path}|${id}|${attempt}`;
  const [result, setResult] = useState<{ key: string; previous?: AtlasItem | Artwork; next?: AtlasItem | Artwork; error?: string }>();
  useEffect(() => {
    if (!path || !id) return;
    const controller = new AbortController();
    async function neighbor(direction: string) {
      const [route, raw] = path!.split("?");
      const query = new URLSearchParams(raw);
      for (const field of ["cursor", "after_artwork", "after_book", "after_event"]) query.delete(field);
      query.set("neighbor_of", id);
      query.set("direction", direction);
      query.set("limit", "1");
      const page = await apiRequest<AtlasResponse | ArtistWorksPage>(`${route}?${query}`, { signal: controller.signal });
      return ("lanes" in page ? page.lanes[0]?.items : page.items)?.[0];
    }
    Promise.all([neighbor("previous"), neighbor("next")])
      .then(([previous, next]) => { if (!controller.signal.aborted) setResult({ key, previous, next }); })
      .catch(error => { if (!controller.signal.aborted) setResult({ key, error: errorMessage(error) }); });
    return () => controller.abort();
  }, [path, id, key]);
  const current = result?.key === key ? result : undefined;
  return {
    busy: Boolean(path && id && !current),
    previous: current?.previous ? () => select(current.previous!.id,current.previous!) : undefined,
    next: current?.next ? () => select(current.next!.id,current.next!) : undefined,
    error: current?.error,
    retry: () => setAttempt(value => value + 1),
  };
}

export function RecordArrows({ navigation, noun }: { navigation: RecordNavigation; noun: string }) {
  return <div className="record-navigation">
    <nav className="painter-navigation" aria-label={`Browse ${noun}s`} aria-busy={navigation.busy}>
      <button type="button" aria-label={`Previous ${noun}`} title={`Previous ${noun}`} disabled={navigation.busy || !navigation.previous} onClick={navigation.previous}>←</button>
      <button type="button" aria-label={`Next ${noun}`} title={`Next ${noun}`} disabled={navigation.busy || !navigation.next} onClick={navigation.next}>→</button>
    </nav>
    {navigation.error && <p role="alert">Navigation unavailable. <button onClick={navigation.retry}>Retry navigation</button></p>}
  </div>;
}
