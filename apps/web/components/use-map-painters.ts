"use client";
import { useEffect, useState } from "react";
import { apiRequest, errorMessage } from "@/lib/api";
import type { MapItem } from "@/lib/map";
import type { ArtistDetail, TimelineResponse } from "@/lib/types";

export function useMapPainters(values: string[], enabled: boolean) {
  const key = JSON.stringify([...new Set(values)].sort());
  const [retry, setRetry] = useState(0);
  const [result, setResult] = useState<{ key: string; retry: number; items: MapItem[]; error?: string }>();
  useEffect(() => {
    if (!enabled || key === "[]") return;
    const controller = new AbortController();
    async function load() {
      const selected = JSON.parse(key) as string[];
      const query = new URLSearchParams({ start: "1100", end: "2000", popular: "false" });
      selected.forEach(slug => query.append("painter", slug));
      const timeline = await apiRequest<TimelineResponse>(`timeline?${query}`, { signal: controller.signal });
      const items: MapItem[] = timeline.items.map(artist => ({ id: artist.id, slug: artist.slug, kind: "artist", title: artist.name, years: artist.date_display, context: artist.movement.name }));
      // Pre-1100 and undated painters are not in the timeline's date window.
      // Resolve their native records directly, retaining the recorded lifespan.
      for (const slug of selected.filter(slug => !items.some(item => item.slug === slug))) {
        const artist = await apiRequest<ArtistDetail>(`artists/${encodeURIComponent(slug)}`, { signal: controller.signal });
        items.push({ id: artist.id, slug: artist.slug, kind: "artist", title: artist.display_name, years: artist.timeline_display, context: artist.movement?.name });
      }
      if (!controller.signal.aborted) setResult({ key, retry, items });
    }
    load().catch(cause => { if (!controller.signal.aborted) setResult({ key, retry, items: [], error: errorMessage(cause) }); });
    return () => controller.abort();
  }, [enabled, key, retry]);
  const loading = enabled && key !== "[]" && (result?.key !== key || result.retry !== retry);
  return { items: enabled && key !== "[]" && result?.key === key ? result.items : [], loading, error: !loading && enabled && result?.key === key ? result.error : undefined, retry: () => setRetry(value => value + 1) };
}
