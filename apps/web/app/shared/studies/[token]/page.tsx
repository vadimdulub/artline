import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { StudyWorkspace } from "@/components/studies/StudyWorkspace";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Shared study", robots: { index: false, follow: false }, referrer: "no-referrer" };

export default async function SharedStudyPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  if (!/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(token)) notFound();
  return <StudyWorkspace id={token} shared />;
}
