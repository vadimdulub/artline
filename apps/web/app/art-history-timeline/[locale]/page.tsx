import { notFound, permanentRedirect } from "next/navigation";
import { TimelineGuide, timelineGuideMetadata } from "@/components/TimelineGuide";
import { guideLanguages } from "@/lib/museum-guide-types";
import { getTimelineGuide } from "@/lib/timeline-guide";

export const dynamicParams = false;
export function generateStaticParams() {
  return Object.keys(guideLanguages).filter(locale => locale !== "en").map(locale => ({ locale }));
}
export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }) {
  const guide = getTimelineGuide((await params).locale);
  return guide ? timelineGuideMetadata(guide) : {};
}
export default async function TranslatedTimelineGuidePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (locale === "en") permanentRedirect("/art-history-timeline");
  const guide = getTimelineGuide(locale);
  if (!guide) notFound();
  return <TimelineGuide guide={guide} />;
}
