import { MuseumsIndex } from "@/components/MuseumsIndex";
import { pageMetadata } from "@/lib/seo";
import { requireMemberSession } from "@/lib/member-session";
import { museumRecordPath } from "@/lib/member-return";
export function generateMetadata() { return pageMetadata("Museums & art collections", "Sign in to explore museums and their documented art collections.", "/museums", { index: false }); }
export default async function MuseumsPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  await requireMemberSession(museumRecordPath(null, await searchParams));
  return <MuseumsIndex />;
}
