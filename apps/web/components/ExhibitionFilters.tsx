"use client";

import { useRef, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { ActiveFilters, AtlasFilters, AtlasSelect } from "./AtlasFilters";
import { exhibitionSource, exhibitionState } from "@/lib/exhibitions";

export function ExhibitionFilters({ initialQuery }: { initialQuery: string }) {
  const router = useRouter();
  const searchRef = useRef<HTMLInputElement>(null);
  const [draft, setDraft] = useState(() => new URLSearchParams(initialQuery));
  const [pending, startTransition] = useTransition();
  const applied = new URLSearchParams(initialQuery);
  const set = (key: string, value: string) => setDraft(previous => { const next = new URLSearchParams(previous); if (value) next.set(key, value); else next.delete(key); next.delete("after"); return next; });
  const navigate = (query: URLSearchParams) => startTransition(() => router.push(`/exhibitions${query.size ? `?${query}` : ""}`, { scroll: false }));
  const clear = () => { const next = new URLSearchParams(); setDraft(next); navigate(next); };
  const label = (key: string, value: string) => key === "theme" ? `Topic: ${value}` : key === "person" ? "Selected artist" : key === "source" ? exhibitionSource(value) : key === "state" ? exhibitionState(value) : key === "institution" ? "Selected museum" : key === "artist" ? "Selected artist" : key === "artwork" ? "Selected artwork" : `${key === "q" ? "Title" : key === "start" ? "From" : key === "end" ? "To" : key === "country" ? "Country" : key === "city" ? "City" : "Format"}: ${value}`;
  const filters = [...applied].filter(([key]) => key !== "after").map(([key, value]) => ({ key, label: label(key, value), remove: () => { const next = new URLSearchParams(applied); next.delete(key); next.delete("after"); setDraft(next); navigate(next); } }));
  return <form aria-label="Filter exhibitions" aria-busy={pending} onSubmit={event => { event.preventDefault(); const next = new URLSearchParams(draft); next.delete("after"); navigate(next); }}>
    <AtlasFilters searchRef={searchRef} query={draft.get("q") ?? ""} onQuery={value => set("q", value)} onReset={clear} placeholder="Search exhibition titles" searchLabel="Search exhibition titles" columns={6} activeCount={filters.filter(f => f.key !== "q").length} actions={<button className="reset-button" type="submit" disabled={pending}>{pending ? "Searching…" : "Search"}</button>}>
      <label className="atlas-select"><span>Country</span><input aria-label="Country" type="text" maxLength={200} value={draft.get("country") ?? ""} placeholder="Any country" onChange={event => set("country", event.target.value)} /></label>
      <label className="atlas-select"><span>City</span><input aria-label="City" type="text" maxLength={200} value={draft.get("city") ?? ""} placeholder="Any city" onChange={event => set("city", event.target.value)} /></label>
      <label className="atlas-select"><span>From year</span><input aria-label="From year" type="number" min={-12000} max={9999} value={draft.get("start") ?? ""} placeholder="Any year" onChange={event => set("start", event.target.value)} /></label>
      <label className="atlas-select"><span>To year</span><input aria-label="To year" type="number" min={-12000} max={9999} value={draft.get("end") ?? ""} placeholder="Any year" onChange={event => set("end", event.target.value)} /></label>
      <AtlasSelect label="Format" value={draft.get("format") ?? ""} onChange={value => set("format", value)} options={[{ value: "", label: "All formats" }, { value: "physical", label: "In person" }, { value: "online", label: "Online" }, { value: "hybrid", label: "Hybrid" }, { value: "unknown", label: "Not recorded" }]} />
      <AtlasSelect label="Event record" value={draft.get("state") ?? ""} onChange={value => set("state", value)} options={[{ value: "", label: "All records" }, ...["held", "uncertain", "announced", "cancelled"].map(value => ({ value, label: exhibitionState(value) }))]} />
    </AtlasFilters>
    <ActiveFilters filters={filters} onClear={clear} searchRef={searchRef} />
    <noscript><p>Interactive filters require JavaScript.</p></noscript>
  </form>;
}
