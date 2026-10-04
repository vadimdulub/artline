import type { Metadata } from "next";
import { MemberAccount } from "@/components/MemberAccount";
import { noIndex } from "@/lib/seo";
import "./account.css";

export const metadata: Metadata = { title: "Your account", robots: noIndex };
export default async function AccountPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const params = await searchParams;
  return <main id="main-content" className="account-page"><section className="account-card"><MemberAccount signInError={params.error === "google_signin"} /></section></main>;
}
