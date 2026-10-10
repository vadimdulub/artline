"use client";

import Link from "@/components/MemberLink";
import Image from "next/image";
import { useMemberSession } from "./MemberSession";

export function MemberAccount({ signInError, returnTo = null, dialog = false, bookmark = false }: { signInError: boolean; returnTo?: string | null; dialog?: boolean; bookmark?: boolean }) {
  const { session, failed } = useMemberSession();
  const Heading = dialog ? "h2" : "h1";
  const museum = returnTo?.startsWith("/museums");
  const saving = bookmark || returnTo?.startsWith("/bookmarks");

  if (failed) return <p role="alert">Your account is temporarily unavailable. Please reload this page to try again.</p>;
  if (!session) return <p role="status">Loading your account…</p>;
  if (session.local_debug && session.all_features) return <>
    <p className="eyebrow">Local workspace</p>
    <h1>Everything is open.</h1>
    <p>All member features are available here. Google sign-in and a subscription are not required for local development.</p>
    <div className="account-actions"><Link href="/bookmarks">Your bookmarks</Link><Link href="/membership-preview">Review membership ideas</Link><Link href="/all">Explore the atlas</Link></div>
  </>;
  if (session.user) return <>
    <p className="eyebrow">Your account</p>
    <h1>Welcome, {session.user.name || "art explorer"}.</h1>
    <p>Signed in as {session.user.email}</p>
    <p>You have a free Artline account. Explore art, literature and history at your own pace.</p>
    <div className="account-actions"><Link href="/bookmarks">Your bookmarks</Link><Link href="/all">Explore the atlas</Link><form action="/api/auth/logout" method="post"><button type="submit">Sign out</button></form></div>
  </>;
  return <>
    <p className="eyebrow">Your Artline account</p>
    <Heading>{saving ? "Keep the art you love." : returnTo ? museum ? "Sign in to explore museums." : "Sign in to Artline." : "A place for your curiosity."}</Heading>
    <p>{saving ? "Sign in for free to bookmark artists and artworks, and find them again in your collection." : returnTo ? "Continue with your Google account. It’s free, and we’ll take you back to the page you selected." : "Sign in to Artline with your Google account."}</p>
    {signInError && <p role="alert">Google sign-in wasn’t completed. Please try again.</p>}
    {session.enabled ? <form action={`/api/auth/google/start${returnTo ? `?${new URLSearchParams({ return_to: returnTo })}` : ""}`} method="post"><button className="google-signin" type="submit"><Image src="/google-signin.png" alt="Sign in with Google" width={180} height={40} unoptimized /></button></form> : <p role="status">Google sign-in is unavailable. You can explore the atlas without an account.</p>}
    <p className="account-note">Artline uses your name and email to create your account. <Link href="/privacy">Privacy</Link> · <Link href="/all">Continue exploring</Link></p>
  </>;
}
