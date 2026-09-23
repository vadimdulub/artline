import { notFound, permanentRedirect } from "next/navigation";
import { ArtistProfile } from "@/components/ArtistProfile";
import { getArtist, getArtistArtwork, researchPreviewEnabled } from "@/lib/server-api";
import { getPainterEssay } from "@/lib/content";
import { artworkDescription, artworkStructuredData, breadcrumbs, pageMetadata, shareImage } from "@/lib/seo";
import { StructuredData } from "@/components/StructuredData";
type Props = { params: Promise<{ slug: string; artworkId: string }> };
export async function generateMetadata({ params }: Props) {
  const { slug, artworkId } = await params;
  const artist = await getArtist(slug);
  if (!artist) notFound();
  const work = await getArtistArtwork(artist.slug, artworkId);
  if (!work) notFound();
  return pageMetadata(`${work.title} — ${artist.display_name}`, artworkDescription(work, artist), `/artists/${artist.slug}/works/${work.id}`, { index: artist.status === "published" && work.status === "published" && !researchPreviewEnabled(), image: shareImage(work) });
}
export default async function ArtworkPage({ params }: Props) {
  const { slug, artworkId } = await params;
  const artist = await getArtist(slug);
  if (!artist) notFound();
  // Always fetch this one record: the representative cards omit long text.
  const work = await getArtistArtwork(artist.slug, artworkId);
  if (!work) notFound();
  if (slug !== artist.slug || artworkId !== work.id) permanentRedirect(`/artists/${artist.slug}/works/${work.id}`);
  const essay = getPainterEssay(artist.slug, researchPreviewEnabled());
  const index = artist.status === "published" && work.status === "published" && !researchPreviewEnabled();
  return <>{index && <><StructuredData data={artworkStructuredData(work, artist)} /><StructuredData data={breadcrumbs([{ name: "Artline", path: "/" }, { name: artist.display_name, path: `/artists/${artist.slug}` }, { name: work.title, path: `/artists/${artist.slug}/works/${work.id}` }])} /></>}<ArtistProfile artist={artist} essay={essay?.content ?? null} initialWorkId={work.id} initialWork={work} /></>;
}
