import type { Metadata } from "next";
import { notFound, permanentRedirect } from "next/navigation";
import { ArtistProfile } from "@/components/ArtistProfile";
import { getPainterEssay } from "@/lib/content";
import { getArtist } from "@/lib/server-api";
import { absoluteURL, artistDescription, breadcrumbs, pageMetadata } from "@/lib/seo";
import { StructuredData } from "@/components/StructuredData";
import { painterRecordPath } from "@/lib/painter-return";
type PageProps = { params: Promise<{ slug: string }>; searchParams: Promise<Record<string, string | string[] | undefined>> };
export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const artist = await getArtist(slug);
  if (!artist) notFound();
  return pageMetadata(artist.display_name, artistDescription(artist), `/artists/${artist.slug}`, { index: true });
}
export default async function ArtistPage({ params, searchParams }: PageProps) {
  const { slug } = await params;
  const query = await searchParams;
  const artist = await getArtist(slug);
  if (!artist) notFound();
  const work = query.work;
  if (typeof work === "string" && /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i.test(work)) {
    permanentRedirect(painterRecordPath(artist.slug, { ...query, work: undefined }, work.toLowerCase()));
  }
  if (artist.slug !== slug || query.catalogue !== undefined || query.preview !== undefined) permanentRedirect(painterRecordPath(artist.slug, query));
  const essay = getPainterEssay(artist.slug);
  return <><StructuredData data={{ "@context": "https://schema.org", "@type": "ProfilePage", url: absoluteURL(`/artists/${artist.slug}`), mainEntity: { "@type": artist.entity_type === "person" ? "Person" : "Thing", name: artist.display_name, alternateName: artist.aliases, description: artistDescription(artist) } }} /><StructuredData data={breadcrumbs([{ name: "Artline", path: "/" }, { name: "Artists", path: "/artists" }, { name: artist.display_name, path: `/artists/${artist.slug}` }])} /><ArtistProfile artist={artist} essay={essay?.content ?? null} /></>;
}
