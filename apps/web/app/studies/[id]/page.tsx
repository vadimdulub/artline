import type { Metadata } from "next";
import { memberReturnTo } from "@/lib/member-return";
import { notFound } from "next/navigation";
import { requireMemberSession } from "@/lib/member-session";
import { StudyWorkspace } from "@/components/studies/StudyWorkspace";
export const metadata: Metadata = { title: "Study workspace", robots: { index: false, follow: false } };
export default async function StudyPage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { id } = await params;
  if (!/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(id)) notFound();
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(await searchParams)) if (["q", "from", "to", "kind", "view"].includes(key)) for (const item of Array.isArray(value) ? value : value === undefined ? [] : [value]) query.append(key, item);
  await requireMemberSession(memberReturnTo(`/studies/${id}${query.size ? `?${query}` : ""}`) ?? `/studies/${id}`);
  return <StudyWorkspace key={id} id={id} />;
}
