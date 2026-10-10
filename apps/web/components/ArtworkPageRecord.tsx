import { BookmarkButton } from "./Bookmarks";
import Link from "next/link";
import { ArtworkViewer, ShareWorkLink } from "./ArtworkViewer";
import { PainterArtworkDetails } from "./PainterArtworkDetails";
import { artworkDate } from "@/lib/display-metadata";
import type { ArtistIdentity, Artwork } from "@/lib/types";
import styles from "./ArtworkPageRecord.module.css";

export function ArtworkPageRecord({ artist, work, browsePath }: { artist: ArtistIdentity; work: Artwork; browsePath: string }) {
  const creator = <><Link href={`/artists/${artist.slug}`} prefetch={false}>{artist.display_name}</Link>{work.attribution_role !== "primary" && <small className="artwork-creator-role">{work.attribution_role.replaceAll("_", " ")}</small>}</>;
  return <main id="main-content" className="record-page">
    <nav className="record-toolbar" aria-label="Artwork navigation"><Link href={browsePath} prefetch={false}>Browse {artist.display_name} artworks</Link><Link href="/artists">All artists</Link></nav>
    <article className={`standalone-artwork-page ${styles.record}`}>
      <div className={styles.image}><ArtworkViewer work={work} creator={creator} /></div>
      <div className={`artwork-details ${styles.details}`}>
        <p className="artwork-creator">{creator} <BookmarkButton kind="artist" id={artist.id} title={artist.display_name} compact /></p>
        <h1>{work.title}</h1>
        <div className="bookmark-record-actions"><BookmarkButton kind="artwork" id={work.id} title={work.title} /></div>
        {work.alternate_title && <p>{work.alternate_title}</p>}
        {artworkDate(work) && <p className="artwork-date">{artworkDate(work)}</p>}
        <PainterArtworkDetails artist={artist} work={work} />
        <ShareWorkLink path={`/artists/${artist.slug}/works/${work.id}`} />
      </div>
    </article>
  </main>;
}
