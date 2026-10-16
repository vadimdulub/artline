import { notFound } from "next/navigation";
import { getMuseumGuide } from "@/lib/museum-guides";
import { MuseumGuide, museumGuideMetadata } from "@/components/MuseumGuide";
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const guide = getMuseumGuide((await params).slug); return guide ? museumGuideMetadata(guide) : {};
}
export default async function GuidePage({ params }: { params: Promise<{ slug: string }> }) {
  const guide = getMuseumGuide((await params).slug); if (!guide) notFound();
  return <MuseumGuide guide={guide} />;
}
