import { notFound } from "next/navigation";
import { requireMemberSession } from "@/lib/member-session";
import { MuseumStudio } from "@/components/MuseumStudio";
import { noIndex } from "@/lib/seo";
export const metadata = { title: "Museum studio", robots: noIndex };
export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  if (!/^[a-z0-9]+(?:[-_][a-z0-9]+)*$/.test(slug) || slug.length > 100) notFound();
  await requireMemberSession(`/account/museums/${slug}`);
  return <MuseumStudio key={slug} slug={slug} />;
}
