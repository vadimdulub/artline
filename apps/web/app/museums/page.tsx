import { MuseumsIndex } from "@/components/MuseumsIndex";
import { pageMetadata } from "@/lib/seo";
import { requireMemberSession } from "@/lib/member-session";
import { museumRecordPath } from "@/lib/member-return";
import { getMuseumDirectory } from "@/lib/server-api";
export function generateMetadata() { return pageMetadata("Museums & art collections", "Sign in to explore museums and their documented art collections.", "/museums", { index: false }); }
export default async function MuseumsPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const search = await searchParams;
  const query = new URLSearchParams();
  for (const key of ["q", "region", "country", "artist", "movement", "selection", "display", "cursor"]) {
    const value = search[key];
    for (const item of Array.isArray(value) ? value : value === undefined ? [] : [value]) query.append(key, item);
  }
  if (query.has("selection") && query.get("selection") !== "museum") { query.delete("selection"); query.delete("cursor"); }
  // Render the first bounded page on the server; do not wait for hydration and
  // repeat the same collection request in the browser.
  const [, page] = await Promise.all([
    requireMemberSession(museumRecordPath(null, search)),
    getMuseumDirectory(query).catch(() => null),
  ]);
  return <MuseumsIndex initialPage={page ?? undefined} initialQuery={query.toString()} />;
}
