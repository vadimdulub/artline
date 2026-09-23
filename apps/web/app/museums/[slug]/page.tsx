import { notFound } from "next/navigation";
import { MuseumDetail } from "@/components/MuseumDetail";
import { getMuseum, researchPreviewEnabled } from "@/lib/server-api";
import { absoluteURL, breadcrumbs, pageMetadata, plainDescription } from "@/lib/seo";
import { StructuredData } from "@/components/StructuredData";
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const museum = await getMuseum((await params).slug);
  if (!museum) notFound();
  return pageMetadata(museum.name, plainDescription(museum.description ? `${museum.name}. ${museum.description}` : null, `Explore ${museum.name}, its documented art collection and sources in Artline.`), `/museums/${museum.slug}`, { index: museum.status === "published" && !researchPreviewEnabled() });
}
export default async function MuseumPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || slug.length > 100) notFound();
  const museum = await getMuseum(slug);
  if (!museum) notFound();
  const index = museum.status === "published" && !researchPreviewEnabled();
  return <>{index && <><StructuredData data={{ "@context": "https://schema.org", "@type": "CollectionPage", name: museum.name, description: museum.description || undefined, url: absoluteURL(`/museums/${museum.slug}`) }} /><StructuredData data={breadcrumbs([{ name: "Artline", path: "/" }, { name: "Museums", path: "/museums" }, { name: museum.name, path: `/museums/${museum.slug}` }])} /></>}<MuseumDetail slug={slug} preview={researchPreviewEnabled()} initialMuseum={museum} /></>;
}
