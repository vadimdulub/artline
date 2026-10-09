import { notFound, permanentRedirect } from "next/navigation";
import { ArtistProfile } from "@/components/ArtistProfile";
import { getArtist, getArtistArtwork } from "@/lib/server-api";
import { getPainterEssay } from "@/lib/content";
import { artworkDescription, artworkStructuredData, breadcrumbs, pageMetadata, shareImage } from "@/lib/seo";
import { StructuredData } from "@/components/StructuredData";
import { painterRecordPath } from "@/lib/painter-return";
type Props = { params: Promise<{ slug: string; artworkId: string }>; searchParams: Promise<Record<string, string | string[] | undefined>> };
export async function generateMetadata({ params }: Props) {
  const { slug, artworkId } = await params;
  const artist = await getArtist(slug);
  if (!artist) notFound();
  const work = await getArtistArtwork(artist.slug, artworkId);
  if (!work) notFound();
  return pageMetadata(`${work.title} — ${artist.display_name}`, artworkDescription(work, artist), `/artists/${artist.slug}/works/${work.id}`, { index: true, image: shareImage(work) });
}
export default async function ArtworkPage({ params, searchParams }: Props) {
  const { slug, artworkId } = await params;
  const query = await searchParams;
  const artist = await getArtist(slug);
  if (!artist) notFound();
  // Always fetch this one record: the representative cards omit long text.
  const work = await getArtistArtwork(artist.slug, artworkId);
  if (!work) notFound();
  if (slug !== artist.slug || artworkId !== work.id || query.catalogue !== undefined || query.preview !== undefined) permanentRedirect(painterRecordPath(artist.slug, query, work.id));
  const essay = getPainterEssay(artist.slug);
  return <><StructuredData data={artworkStructuredData(work, artist)} /><StructuredData data={breadcrumbs([{ name: "Artline", path: "/" }, { name: artist.display_name, path: `/artists/${artist.slug}` }, { name: work.title, path: `/artists/${artist.slug}/works/${work.id}` }])} /><ArtistProfile artist={artist} essay={essay?.content ?? null} initialWorkId={work.id} initialWork={work} /></>;
}
