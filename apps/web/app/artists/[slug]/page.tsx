import type { Metadata } from "next";
import { notFound, permanentRedirect } from "next/navigation";
import { ArtistProfile } from "@/components/ArtistProfile";
import { getPainterEssay } from "@/lib/content";
import { getArtist, researchPreviewEnabled } from "@/lib/server-api";
import { absoluteURL, artistDescription, breadcrumbs, pageMetadata } from "@/lib/seo";
import { StructuredData } from "@/components/StructuredData";
type PageProps = { params: Promise<{ slug: string }>; searchParams: Promise<Record<string, string | string[] | undefined>> };
export async function generateMetadata({ params, searchParams }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const fullCatalogue = (await searchParams).catalogue === "all" && researchPreviewEnabled();
  const artist = await getArtist(slug, fullCatalogue);
  if (!artist) notFound();
  return pageMetadata(artist.display_name, artistDescription(artist), `/artists/${artist.slug}`, { index: !fullCatalogue && artist.status === "published" });
}
export default async function ArtistPage({ params, searchParams }: PageProps) {
  const { slug } = await params;
  const fullCatalogue = (await searchParams).catalogue === "all" && researchPreviewEnabled();
  const artist = await getArtist(slug, fullCatalogue);
  if (!artist) notFound();
  const query = await searchParams;
  const work = query.work;
  if (typeof work === "string" && /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i.test(work)) {
    const filters = new URLSearchParams();
    for (const key of ["art_images", "art_year", "art_cursor", "art_q", "art_museum", "art_type", "catalogue"]) if (typeof query[key] === "string") filters.set(key, query[key]);
    permanentRedirect(`/artists/${artist.slug}/works/${work.toLowerCase()}${filters.size ? `?${filters}` : ""}`);
  }
  if (artist.slug !== slug) permanentRedirect(`/artists/${artist.slug}${fullCatalogue ? "?catalogue=all" : ""}`);
  const essay = getPainterEssay(slug, artist.status !== "published" && researchPreviewEnabled());
  const index = !fullCatalogue && artist.status === "published";
  return <>{index && <><StructuredData data={{ "@context": "https://schema.org", "@type": "ProfilePage", url: absoluteURL(`/artists/${artist.slug}`), mainEntity: { "@type": artist.entity_type === "person" ? "Person" : "Thing", name: artist.display_name, alternateName: artist.aliases, description: artistDescription(artist) } }} /><StructuredData data={breadcrumbs([{ name: "Artline", path: "/" }, { name: "Artists", path: "/artists" }, { name: artist.display_name, path: `/artists/${artist.slug}` }])} /></>}<ArtistProfile fullCatalogue={fullCatalogue} fullCatalogueAvailable={researchPreviewEnabled()} artist={artist} essay={essay?.content ?? null} /></>;
}
