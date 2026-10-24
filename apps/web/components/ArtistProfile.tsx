"use client";
import Link from "next/link";
import { ArtistChronologyRecord } from "./ArtistChronologyRecord";
import { updateQuery, useQueryString } from "@/lib/url-state";
import type { ArtistDetail, Artwork } from "@/lib/types";
export function ArtistProfile({ artist, essay, initialWorkId, initialWork }: { artist: ArtistDetail; essay: string | null; initialWorkId?: string; initialWork?: Artwork }) {
  const params = new URLSearchParams(useQueryString());
  const workId = params.get("work") ?? initialWorkId ?? null;
  return <main id="main-content" className="record-page" data-return-label={artist.display_name} data-return-path={`/artists/${artist.slug}`}><div className="record-toolbar"><Link href={`/?artist=${artist.slug}`}>View on timeline</Link><Link href={`/exhibitions?artist=${artist.id}`} prefetch={false}>Exhibition records</Link></div><ArtistChronologyRecord artist={artist} essay={essay} embedded={false} workId={workId} initialWork={initialWork} onSelectWork={id => updateQuery({ work: id }, true)} /></main>;
}
