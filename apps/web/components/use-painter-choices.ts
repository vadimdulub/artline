"use client";
import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import type { FilterOption } from "./MultiSelectFilter";

type Choices = { items: FilterOption[]; selected: FilterOption[]; has_more: boolean };
export function usePainterChoices(values: string[], popular = false, museum = "", token = "", women = false) {
  const [search, setSearch] = useState("");
  const [revision, setRevision] = useState(0);
  const params = new URLSearchParams({ q: search, popular: String(popular), women: String(women) });
  if (museum) params.set("museum", museum);
  values.forEach(value => params.append("selected", value));
  const key = params.toString();
  const [result, setResult] = useState<{ key: string; token: string; data?: Choices; error?: boolean }>({ key: "", token });
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      apiRequest<Choices>(`painters/options?${key}`, { signal: controller.signal, ...(token ? { headers: { Authorization: `Bearer ${token}` } } : {}) })
        .then(data => setResult({ key, token, data }))
        .catch(() => { if (!controller.signal.aborted) setResult({ key, token, error: true }); });
    }, 160);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [key, token, revision]);
  const data = result.token === token ? result.data : undefined;
  // Keep selected names visible when another painter is searched. The server
  // resolves these identities independently of the search, without a full list.
  const options = [...new Map([...(data?.selected ?? []), ...(data?.items ?? [])].map(item => [item.slug, item])).values()];
  return { options, unavailable: result.key === key && !!result.error, retry: () => setRevision(value => value + 1), remote: { search, onSearch: setSearch, loading: result.key !== key, hasMore: data?.has_more ?? false } };
}

export const workTypeOptions = ["painting", "fresco", "manuscript_illumination", "drawing", "watercolor", "print"].map(slug => ({ slug, name: slug.replaceAll("_", " ") }));
