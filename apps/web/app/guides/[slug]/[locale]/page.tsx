import { notFound, permanentRedirect } from "next/navigation";
import { getMuseumGuide } from "@/lib/museum-guides";
import { MuseumGuide, museumGuideMetadata } from "@/components/MuseumGuide";
export async function generateMetadata({ params }: { params: Promise<{ slug: string; locale: string }> }) {
  const { slug, locale } = await params; const guide = getMuseumGuide(slug, locale); return guide ? museumGuideMetadata(guide) : {};
}
export default async function TranslatedGuidePage({ params }: { params: Promise<{ slug: string; locale: string }> }) {
  const { slug, locale } = await params; const guide = getMuseumGuide(slug, locale); if (!guide) notFound();
  if (locale === "en") permanentRedirect(`/guides/${slug}`);
  return <MuseumGuide guide={guide} />;
}
