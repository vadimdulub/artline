import type { Metadata } from "next";
import { MemberAccount } from "@/components/MemberAccount";
import { noIndex } from "@/lib/seo";
import { redirect } from "next/navigation";
import { getMemberSession } from "@/lib/member-session";
import { memberReturnTo } from "@/lib/member-return";
import "./account.css";

export const metadata: Metadata = { title: "Your account", robots: noIndex };
export default async function AccountPage({ searchParams }: { searchParams: Promise<{ error?: string; return_to?: string | string[] }> }) {
  const params = await searchParams;
  const returnTo = memberReturnTo(params.return_to);
  if (returnTo && (await getMemberSession()).user?.id) redirect(returnTo);
  return <main id="main-content" className="account-page"><section className="account-card"><MemberAccount signInError={params.error === "google_signin"} returnTo={returnTo} /></section></main>;
}
