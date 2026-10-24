"use client";
import { useEffect, useRef, useState } from "react";
import { ApiError, apiRequest, errorMessage } from "@/lib/api";
import { cachedMuseumPage, clearMuseumPageCache, rememberMuseumPage } from "@/lib/museum-page-cache";

export function useCatalogueRequest<T>(path: string | null, revision = 0, initialData?: T, reuseInitial = false, cacheDirectory = false) {
  const key = `${path}|${revision}`;
  const seed = useRef({ key, reusable: reuseInitial && revision === 0 && Boolean(initialData) });
  const [result, setResult] = useState<{ key: string; data?: T; error?: string }>(() => initialData ? { key, data: initialData } : { key: "" });
  const cached = cacheDirectory && revision === 0 ? cachedMuseumPage<T>(path) : undefined;
  // Adjust only when the request key changes, before committing a loading frame.
  if (cached && result.key !== key) setResult({ key, data: cached });
  useEffect(() => {
    if (!path) return;
    if (seed.current.reusable && seed.current.key === key) {
      if (cacheDirectory) rememberMuseumPage(path, initialData);
      return;
    }
    seed.current.reusable = false;
    const saved = cacheDirectory && revision === 0 ? cachedMuseumPage<T>(path) : undefined;
    if (saved) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      apiRequest<T>(path, { signal: controller.signal })
        .then(data => {
          if (controller.signal.aborted) return;
          if (cacheDirectory) rememberMuseumPage(path, data);
          setResult({ key, data });
        })
        .catch(error => {
          if (controller.signal.aborted) return;
          const transient = !(error instanceof ApiError) || error.status >= 500;
          if (!transient && cacheDirectory) clearMuseumPageCache();
          setResult(previous => ({ key, data: transient ? previous.data : undefined, error: errorMessage(error) }));
        });
    }, 120);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [path, key, cacheDirectory, revision, initialData]);
  // Keep previous data for loading context, without showing stale cards as current.
  return { data: result.key === key ? (!result.error ? result.data : undefined) : cached, previousData: result.data, error: result.key === key ? result.error : undefined, loading: Boolean(path) && result.key !== key && !cached };
}

export const useMuseumRequest = useCatalogueRequest;
