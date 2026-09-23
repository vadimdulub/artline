"use client";
import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import type { FilterOption } from "./MultiSelectFilter";

type Choices = { items: FilterOption[]; selected: FilterOption[]; has_more: boolean };
export function useAtlasCreators(values: string[]) {
  const [search, setSearch] = useState("");
  const [revision, setRevision] = useState(0);
  const params = new URLSearchParams({ q: search });
  values.forEach(value => params.append("selected", value));
  const key = params.toString();
  const [result, setResult] = useState<{ key: string; data?: Choices; error?: boolean }>({ key: "" });
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      apiRequest<Choices>(`atlas/creators?${key}`, { signal: controller.signal })
        .then(data => { if (!controller.signal.aborted) setResult({ key, data }); })
        .catch(() => { if (!controller.signal.aborted) setResult({ key, error: true }); });
    }, 160);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [key, revision]);
  const options = [...new Map([...(result.data?.selected ?? []), ...(result.data?.items ?? [])].map(item => [item.slug, item])).values()];
  return { options, unavailable: result.key === key && !!result.error, retry: () => setRevision(value => value + 1), remote: { search, onSearch: setSearch, loading: result.key !== key, hasMore: result.data?.has_more ?? false } };
}
