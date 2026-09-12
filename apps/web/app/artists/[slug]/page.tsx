import type { Metadata } from "next";
import { notFound, permanentRedirect } from "next/navigation";
import { ArtistProfile } from "@/components/ArtistProfile";
import { getPainterEssay } from "@/lib/content";
import { getArtist, researchPreviewEnabled } from "@/lib/server-api";
type PageProps = { params: Promise<{ slug: string }> };
export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const artist = await getArtist(slug);
  return { title: artist?.display_name ?? "Painter not found", robots: artist?.status === "published" ? undefined : { index: false } };
}
export default async function ArtistPage({ params }: PageProps) {
  const { slug } = await params;
  const artist = await getArtist(slug);
  if (!artist) notFound();
  if (artist.slug !== slug) permanentRedirect(`/artists/${artist.slug}`);
  const essay = getPainterEssay(slug, researchPreviewEnabled());
  return <ArtistProfile artist={artist} essay={essay?.content ?? null} />;
}
