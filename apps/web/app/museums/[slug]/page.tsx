import { notFound } from "next/navigation";
import { MuseumDetail } from "@/components/MuseumDetail";
import { getMuseum } from "@/lib/server-api";
import { absoluteURL, breadcrumbs, pageMetadata, plainDescription, noIndex } from "@/lib/seo";
import { StructuredData } from "@/components/StructuredData";
import { getMemberSession, requireMemberSession } from "@/lib/member-session";
import { museumRecordPath } from "@/lib/member-return";
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  if (!(await getMemberSession()).user?.id) return { title: "Sign in to explore museums", robots: noIndex };
  const museum = await getMuseum((await params).slug);
  if (!museum) notFound();
  return pageMetadata(museum.name, plainDescription(museum.description ? `${museum.name}. ${museum.description}` : null, `Explore ${museum.name}, its documented art collection and sources in Artline.`), `/museums/${museum.slug}`, { index: false });
}
export default async function MuseumPage({ params, searchParams }: { params: Promise<{ slug: string }>; searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { slug } = await params;
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || slug.length > 100) notFound();
  await requireMemberSession(museumRecordPath(slug, await searchParams));
  const museum = await getMuseum(slug);
  if (!museum) notFound();
  return <><StructuredData data={{ "@context": "https://schema.org", "@type": "CollectionPage", name: museum.name, description: museum.description || undefined, url: absoluteURL(`/museums/${museum.slug}`) }} /><StructuredData data={breadcrumbs([{ name: "Artline", path: "/" }, { name: "Museums", path: "/museums" }, { name: museum.name, path: `/museums/${museum.slug}` }])} /><MuseumDetail key={slug} slug={slug} initialMuseum={museum} /></>;
}
