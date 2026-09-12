"use client";
import { useEffect, useState } from "react";
import { apiRequest, editorHeaders, errorMessage } from "@/lib/api";

export function useMuseumRequest<T>(path: string | null, token = "", revision = 0) {
  const key = `${path}|${token}|${revision}`;
  const [result, setResult] = useState<{ key: string; token?: string; data?: T; error?: string }>({ key: "" });
  useEffect(() => {
    if (!path) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      const target = token ? `${path}${path.includes("?") ? "&" : "?"}preview=1` : path;
      apiRequest<T>(target, { signal: controller.signal, headers: token ? editorHeaders(token) : undefined })
        .then(data => { if (!controller.signal.aborted) setResult({ key, token, data }); })
        .catch(error => { if (!controller.signal.aborted) setResult(previous => ({ key, token, data: previous.token === token ? previous.data : undefined, error: errorMessage(error) })); });
    }, 120);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [path, token, key]);
  // Never retain data across a visibility/token change, or show stale cards as current.
  return { data: result.key === key && !result.error ? result.data : undefined, previousData: result.token === token ? result.data : undefined, error: result.key === key ? result.error : undefined, loading: Boolean(path) && result.key !== key };
}
