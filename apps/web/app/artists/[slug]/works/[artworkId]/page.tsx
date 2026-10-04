import { notFound, permanentRedirect } from "next/navigation";
import { ArtistProfile } from "@/components/ArtistProfile";
import { getArtist, getArtistArtwork, researchPreviewEnabled } from "@/lib/server-api";
import { getPainterEssay } from "@/lib/content";
import { artworkDescription, artworkStructuredData, breadcrumbs, pageMetadata, shareImage } from "@/lib/seo";
import { StructuredData } from "@/components/StructuredData";
type Props = { params: Promise<{ slug: string; artworkId: string }>; searchParams: Promise<{ catalogue?: string | string[] }> };
export async function generateMetadata({ params, searchParams }: Props) {
  const { slug, artworkId } = await params;
  const fullCatalogue = (await searchParams).catalogue === "all" && researchPreviewEnabled();
  const artist = await getArtist(slug, fullCatalogue);
  if (!artist) notFound();
  const work = await getArtistArtwork(artist.slug, artworkId, fullCatalogue);
  if (!work) notFound();
  return pageMetadata(`${work.title} — ${artist.display_name}`, artworkDescription(work, artist), `/artists/${artist.slug}/works/${work.id}`, { index: !fullCatalogue && artist.status === "published" && work.status === "published", image: shareImage(work) });
}
export default async function ArtworkPage({ params, searchParams }: Props) {
  const { slug, artworkId } = await params;
  const fullCatalogue = (await searchParams).catalogue === "all" && researchPreviewEnabled();
  const artist = await getArtist(slug, fullCatalogue);
  if (!artist) notFound();
  // Always fetch this one record: the representative cards omit long text.
  const work = await getArtistArtwork(artist.slug, artworkId, fullCatalogue);
  if (!work) notFound();
  if (slug !== artist.slug || artworkId !== work.id) permanentRedirect(`/artists/${artist.slug}/works/${work.id}${fullCatalogue ? "?catalogue=all" : ""}`);
  const essay = getPainterEssay(artist.slug, artist.status !== "published" && researchPreviewEnabled());
  const index = !fullCatalogue && artist.status === "published" && work.status === "published";
  return <>{index && <><StructuredData data={artworkStructuredData(work, artist)} /><StructuredData data={breadcrumbs([{ name: "Artline", path: "/" }, { name: artist.display_name, path: `/artists/${artist.slug}` }, { name: work.title, path: `/artists/${artist.slug}/works/${work.id}` }])} /></>}<ArtistProfile fullCatalogue={fullCatalogue} fullCatalogueAvailable={researchPreviewEnabled()} artist={artist} essay={essay?.content ?? null} initialWorkId={work.id} initialWork={work} /></>;
}
