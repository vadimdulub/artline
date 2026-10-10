import "server-only";
import { cache } from "react";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { memberSignInPath } from "./member-return";
import { memberRequestHeaders } from "./session-cookies";

type MemberSession = { user: { id: string; name: string; email: string } | null };

// Go validates the real session (or its existing loopback-only debug mode).
// React cache deduplicates checks only within the current server render.
export const getMemberSession = cache(async (): Promise<MemberSession> => {
  const jar = await cookies();
  const headers = memberRequestHeaders(jar);
  const url = new URL("/api/v1/auth/session", process.env.API_INTERNAL_URL ?? "http://localhost:8080");
  const response = await fetch(url, { headers, cache: "no-store", redirect: "error", signal: AbortSignal.timeout(12000) });
  if (!response.ok) throw new Error("Sign-in is temporarily unavailable. Please try again.");
  return response.json();
});

export async function requireMemberSession(destination: string) {
  const session = await getMemberSession();
  if (!session.user?.id) redirect(memberSignInPath(destination));
}
