"use client";
import Link from "next/link";
import { ArtistChronologyRecord } from "./ArtistChronologyRecord";
import { updateQuery, useQueryString } from "@/lib/url-state";
import type { ArtistDetail, Artwork } from "@/lib/types";
export function ArtistProfile({ artist, essay, initialWorkId, initialWork, fullCatalogue = false, fullCatalogueAvailable = false }: { artist: ArtistDetail; fullCatalogue?: boolean; fullCatalogueAvailable?: boolean; essay: string | null; initialWorkId?: string; initialWork?: Artwork }) {
  const params = new URLSearchParams(useQueryString());
  const workId = params.get("work") ?? initialWorkId ?? null;
  return <main id="main-content" className="record-page"><div className="record-toolbar"><Link href="/artists">All artists</Link>{!fullCatalogue && fullCatalogueAvailable && artist.status === "published" && <Link className="full-catalogue-link" href={`/artists/${artist.slug}?catalogue=all`}>Browse the full recorded catalogue</Link>}<Link href={`/?artist=${artist.slug}`}>View on timeline</Link></div><ArtistChronologyRecord artist={artist} essay={essay} embedded={false} defaultImageOnly={false} publishedOnly={!fullCatalogue && artist.status === "published"} workId={workId} initialWork={initialWork} onSelectWork={id => updateQuery({ work: id }, true)} /></main>;
}
