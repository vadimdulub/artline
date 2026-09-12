"use client";
import Link from "next/link";
import { ArtistRecord } from "./ArtistRecord";
import { updateQuery, useQueryString } from "@/lib/url-state";
import type { ArtistDetail, Artwork } from "@/lib/types";
export function ArtistProfile({ artist, essay, initialWorkId, initialWork }: { artist: ArtistDetail; essay: string | null; initialWorkId?: string; initialWork?: Artwork }) {
  const parameters = new URLSearchParams(useQueryString());
  return <main id="main-content" className="record-page"><div className="record-toolbar"><Link href={`/?artist=${artist.slug}`}>Back to timeline</Link><span>{artist.status === "published" ? "Published painter" : "Research record · in review"}</span></div><ArtistRecord artist={artist} essay={essay} workId={parameters.get("work") ?? initialWorkId} linkedWork={initialWork} onSelectWork={id => updateQuery({ work: id }, true)} /></main>;
}
