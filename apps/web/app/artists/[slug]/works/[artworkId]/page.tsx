import { notFound } from "next/navigation";
import { ArtistProfile } from "@/components/ArtistProfile";
import { getArtist, getArtistArtwork, researchPreviewEnabled } from "@/lib/server-api";
import { getPainterEssay } from "@/lib/content";
export default async function ArtworkPage({ params }: { params: Promise<{ slug: string; artworkId: string }> }) {
  const { slug, artworkId } = await params;
  const artist = await getArtist(slug);
  if (!artist) notFound();
  if (!artist.artworks.some(work => work.id === artworkId)) {
    const work = await getArtistArtwork(artist.slug, artworkId);
    if (!work) notFound();
    // A shared chronology link can point beyond the representative selection.
    return <ArtistProfile artist={artist} essay={getPainterEssay(artist.slug, researchPreviewEnabled())?.content ?? null} initialWorkId={artworkId} initialWork={work} />;
  }
  const essay = getPainterEssay(artist.slug, researchPreviewEnabled());
  return <ArtistProfile artist={artist} essay={essay?.content ?? null} initialWorkId={artworkId} />;
}
