"use client";
import Link from "next/link";
import { ArtistRecord } from "./ArtistRecord";
import { ArtistChronologyRecord } from "./ArtistChronologyRecord";
import { updateQuery, useQueryString } from "@/lib/url-state";
import type { ArtistDetail, Artwork } from "@/lib/types";
export function ArtistProfile({ artist, essay, initialWorkId, initialWork }: { artist: ArtistDetail; essay: string | null; initialWorkId?: string; initialWork?: Artwork }) {
  const params = new URLSearchParams(useQueryString());
  const workId = params.get("work") ?? initialWorkId ?? null;
  return <main id="main-content" className="record-page"><div className="record-toolbar"><Link href={`/?artist=${artist.slug}`}>Back to timeline</Link></div>{artist.status === "published" ? <ArtistRecord artist={artist} essay={essay} embedded={false} workId={workId} linkedWork={initialWork} pageWork={initialWork ?? null} onSelectWork={id => updateQuery({ work: id }, true)} /> : <ArtistChronologyRecord artist={artist} essay={essay} embedded={false} defaultImageOnly={false} workId={workId} initialWork={initialWork} onSelectWork={id => updateQuery({ work: id }, true)} />}</main>;
}
