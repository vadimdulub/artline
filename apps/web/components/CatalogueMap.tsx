"use client";
import { useEffect, useState, type ReactNode } from "react";
import { apiRequest, errorMessage } from "@/lib/api";
import type { MapItem, MapKind, MapRecord } from "@/lib/map";
import { MapWorkspace } from "./MapWorkspace";

export type CatalogueMapProps = {
  items: MapItem[]; total: number; loading: boolean; error?: string; onRetry: () => void;
  range: { start: number; end: number }; onOpen: (item: MapItem) => void;
  children?: ReactNode; layerPicker?: ReactNode; layerPickers?: Partial<Record<MapKind, ReactNode>>; relations?: string[]; headingId?: string;
};

export function CatalogueMap(props: CatalogueMapProps) {
  const { items, range, relations, loading, error, onRetry } = props;
  const relationKey = relations ? [...relations].sort().join(",") : "all";
  const identities = JSON.stringify(items.map(({ id, kind }) => ({ id, kind })));
  const key = `${range.start}:${range.end}:${relationKey}:${identities}`;
  const [result, setResult] = useState<{ key: string; records: Record<string, MapRecord>; error?: string }>();
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    if (loading || error) return;
    const controller = new AbortController();
    async function load() {
      const ids = JSON.parse(identities) as Pick<MapItem, "id" | "kind">[];
      const records: Record<string, MapRecord> = {};
      // Keep the established serial batches and source/date semantics.
      for (const kind of ["artist", "artwork", "book", "event"] as MapKind[]) {
        if (relationKey === "") continue;
        const selected = [...new Set(ids.filter(item => item.kind === kind).map(item => item.id))];
        for (let offset = 0; offset < selected.length; offset += 80) {
          const query = new URLSearchParams({ kind, start: String(kind === "artist" ? -12000 : range.start), end: String(kind === "artist" ? 2100 : range.end) });
          if (relationKey !== "all" && (kind === "artist" || kind === "artwork")) relationKey.split(",").forEach(value => query.append("relation", value));
          selected.slice(offset, offset + 80).forEach(id => query.append("id", id));
          const data = await apiRequest<{ records: MapRecord[] }>(`map/locations?${query}`, { signal: controller.signal });
          data.records.forEach(record => { records[`${kind}:${record.id}`] = record; });
        }
      }
      if (!controller.signal.aborted) setResult({ key, records });
    }
    load().catch(cause => { if (!controller.signal.aborted) setResult({ key, records: {}, error: errorMessage(cause) }); });
    return () => controller.abort();
  }, [identities, relationKey, key, range.start, range.end, retry, loading, error]);
  const failure = error ?? (result?.key === key ? result.error : undefined);
  const busy = !failure && (loading || result?.key !== key);
  return <MapWorkspace {...props} busy={busy} failure={failure}
    records={!busy && !failure ? result?.records ?? {} : {}}
    retryLocations={() => { setResult(undefined); setRetry(value => value + 1); onRetry(); }} />;
}
