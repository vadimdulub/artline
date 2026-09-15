"use client";
import { useSyncExternalStore } from "react";
const changed = "artline:navigate";
function subscribe(callback: () => void) {
  window.addEventListener("popstate", callback);
  window.addEventListener(changed, callback);
  return () => { window.removeEventListener("popstate", callback); window.removeEventListener(changed, callback); };
}
export function useQueryString() {
  return useSyncExternalStore(subscribe, () => window.location.search, () => "");
}
export function queryValues(params: URLSearchParams, key: string): string[] {
  return [...new Set(params.getAll(key).flatMap(value => value.split(",")).map(value => value.trim().toLowerCase()).filter(Boolean))].sort();
}
export function popularPaintersOnly(params: URLSearchParams): boolean {
  return params.get("popular") !== "false";
}
export function womenArtistsOnly(params: URLSearchParams): boolean {
  return params.get("women") === "true";
}
export function updateQuery(values: Record<string, string | string[] | null>, push = false) {
  const url = new URL(window.location.href);
  for (const [key, value] of Object.entries(values)) {
    url.searchParams.delete(key);
    if (Array.isArray(value)) [...new Set(value)].sort().forEach(item => { if (item) url.searchParams.append(key, item); });
    else if (value !== null && value !== "") url.searchParams.set(key, value);
  }
  if (push) window.history.pushState(null, "", url); else window.history.replaceState(null, "", url);
  window.dispatchEvent(new Event(changed));
}
