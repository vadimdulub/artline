"use client";
import { useEffect, useRef, useState } from "react";
import { ApiError, apiRequest, errorMessage } from "@/lib/api";

export function useCatalogueRequest<T>(path: string | null, revision = 0, initialData?: T, reuseInitial = false) {
  const key = `${path}|${revision}`;
  const seed = useRef({ key, reusable: reuseInitial && revision === 0 && Boolean(initialData) });
  const [result, setResult] = useState<{ key: string; data?: T; error?: string }>(() => initialData ? { key, data: initialData } : { key: "" });
  useEffect(() => {
    if (!path) return;
    if (seed.current.reusable && seed.current.key === key) return;
    seed.current.reusable = false;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      apiRequest<T>(path, { signal: controller.signal })
        .then(data => { if (!controller.signal.aborted) setResult({ key, data }); })
        .catch(error => {
          if (controller.signal.aborted) return;
          const transient = !(error instanceof ApiError) || error.status >= 500;
          setResult(previous => ({ key, data: transient ? previous.data : undefined, error: errorMessage(error) }));
        });
    }, 120);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [path, key]);
  // Keep previous data for loading context, without showing stale cards as current.
  return { data: result.key === key && !result.error ? result.data : undefined, previousData: result.data, error: result.key === key ? result.error : undefined, loading: Boolean(path) && result.key !== key };
}

export const useMuseumRequest = useCatalogueRequest;
