import { ArtworkFacts } from "./ArtworkFacts";
import { ArtworkLocation } from "./ArtworkLocation";
import { ArtworkDescription } from "./ArtworkDescription";
import { safeSourceURL } from "@/lib/api";
import type { ArtistIdentity, Artwork, Citation } from "@/lib/types";

export function SourceList({ citations }: { citations: Citation[] }) {
  return <ul className="source-list">{citations.map((source, index) => <li key={index}><a href={safeSourceURL(source.source_url)} target="_blank" rel="noreferrer">{source.source_name}</a></li>)}</ul>;
}
export function PainterArtworkDetails({ artist, work }: { artist: Pick<ArtistIdentity, "slug">; work: Artwork }) {
  return <>
        <ArtworkFacts work={work} attribution />
        {work.attribution_text && <p className="image-credit">{work.attribution_text}</p>}
        <ArtworkLocation work={work} />
        <ArtworkDescription key={work.id} work={work} detailPath={`artists/${artist.slug}/works/${work.id}`} />
        {work.location_checked_at && <p className="image-credit">Location checked {new Intl.DateTimeFormat("en", { dateStyle: "medium", timeZone: "UTC" }).format(new Date(work.location_checked_at))}. This does not indicate whether the work is on display.</p>}
        {(work.citations.length > 0 || safeSourceURL(work.source_page_url)) && <details><summary>Artwork sources</summary><SourceList citations={work.citations} />{safeSourceURL(work.source_page_url) && <a href={safeSourceURL(work.source_page_url)} target="_blank" rel="noreferrer">Image source</a>}</details>}
  </>;
}
