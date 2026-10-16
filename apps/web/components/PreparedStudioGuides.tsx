"use client";
import { useState } from "react";
import { useCatalogueRequest } from "./museum-state";
import { PreparedMuseumGuides } from "./PreparedMuseumGuides";
import type { GuideSearchPage } from "@/lib/guide-search";

export function PreparedStudioGuides({ slug, query }: { slug: string; query: string }) {
  const [retry, setRetry] = useState(0);
  const { data, loading, error } = useCatalogueRequest<GuideSearchPage>(`guides?${new URLSearchParams({ institution: slug, q: query })}`, retry, undefined, true);
  if (loading) return <p role="status">Finding Artline guides…</p>;
  if (error) return <div role="alert"><p>Artline guides could not be loaded.</p><button onClick={() => setRetry(v => v + 1)}>Retry Artline guides</button></div>;
  return data ? <PreparedMuseumGuides page={data} slug={slug} query={query} /> : null;
}
