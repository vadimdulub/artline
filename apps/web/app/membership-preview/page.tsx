import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { MembershipPreview } from "./MembershipPreview";
import "./preview.css";

export const metadata: Metadata = { title: "Membership ideas", robots: { index: false, follow: false } };
export const dynamic = "force-dynamic";

export default async function MembershipPreviewPage({ searchParams }: { searchParams: Promise<{ idea?: string }> }) {
  if (process.env.NODE_ENV !== "development" || process.env.K_SERVICE) notFound();
  const { idea } = await searchParams;
  return <MembershipPreview initialIdea={idea} />;
}
