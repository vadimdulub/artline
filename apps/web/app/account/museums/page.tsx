import { requireMemberSession } from "@/lib/member-session";
import { MuseumStudio } from "@/components/MuseumStudio";
import { noIndex } from "@/lib/seo";
export const metadata = { title: "Museum studio", robots: noIndex };
export default async function Page({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const query = (await searchParams).q;
  await requireMemberSession("/account/museums");
  return <MuseumStudio initialQuery={typeof query === "string" ? query.slice(0, 200) : ""} />;
}
