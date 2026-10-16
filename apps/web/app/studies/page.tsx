import type { Metadata } from "next";
import { memberReturnTo } from "@/lib/member-return";
import { requireMemberSession } from "@/lib/member-session";
import { StudyCollection } from "@/components/studies/StudyCollection";
export const metadata: Metadata = { title: "Your studies", robots: { index: false, follow: false } };
export default async function StudiesPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const values = await searchParams; const query = new URLSearchParams();
  for (const key of ["q", "sort"]) if (typeof values[key] === "string") query.set(key, values[key]);
  await requireMemberSession(memberReturnTo(`/studies${query.size ? `?${query}` : ""}`) ?? "/studies");
  return <StudyCollection />;
}
