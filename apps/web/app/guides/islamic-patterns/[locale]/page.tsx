import { notFound, permanentRedirect } from "next/navigation";
import { IslamicPatternGuide } from "@/components/patterns/IslamicPatternGuide";
import { getPatternGuide, patternGuideMetadata } from "@/lib/pattern-guide";

type Props = { params: Promise<{ locale: string }> };
export async function generateMetadata({ params }: Props) {
  const copy = getPatternGuide((await params).locale);
  return copy ? patternGuideMetadata(copy) : {};
}
export default async function Page({ params }: Props) {
  const { locale } = await params;
  const copy = getPatternGuide(locale);
  if (!copy) notFound();
  if (locale === "en") permanentRedirect("/guides/islamic-patterns");
  return <IslamicPatternGuide copy={copy} />;
}
