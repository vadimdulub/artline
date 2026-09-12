import { notFound } from "next/navigation";
import { MuseumDetail } from "@/components/MuseumDetail";
import { getMuseum, researchPreviewEnabled } from "@/lib/server-api";
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const museum = await getMuseum((await params).slug);
  return { title: museum ? `${museum.name} · Artline` : "Museum not found · Artline" };
}
export default async function MuseumPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || slug.length > 100) notFound();
  if (!await getMuseum(slug)) notFound();
  return <MuseumDetail slug={slug} preview={researchPreviewEnabled()} />;
}
