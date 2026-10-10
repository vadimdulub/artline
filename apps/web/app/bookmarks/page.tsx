import type { Metadata } from "next";
import { BookmarkCollection } from "@/components/BookmarkCollection";
import { requireMemberSession } from "@/lib/member-session";
import { noIndex } from "@/lib/seo";
export const metadata: Metadata = { title: "Your bookmarks", robots: noIndex };
export default async function BookmarksPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams;
  const query = new URLSearchParams();
  for (const key of ["kind", "cursor"]) if (typeof params[key] === "string") query.set(key, params[key]);
  await requireMemberSession(`/bookmarks${query.size ? `?${query}` : ""}`);
  return <BookmarkCollection />;
}
