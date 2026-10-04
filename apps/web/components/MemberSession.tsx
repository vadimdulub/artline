"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type Session = { enabled: boolean; local_debug?: boolean; all_features?: boolean; user: { id: string; name: string; email: string } | null };
type SessionState = { session: Session | null; failed: boolean };
const MemberSession = createContext<SessionState>({ session: null, failed: false });

export function MemberSessionProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<SessionState>({ session: null, failed: false });
  useEffect(() => {
    let controller: AbortController | null = null;
    function refresh() {
      controller?.abort();
      const request = new AbortController();
      controller = request;
      fetch("/api/auth/session", { cache: "no-store", signal: request.signal })
        .then(response => { if (!response.ok) throw new Error(); return response.json() as Promise<Session>; })
        .then(session => { if (!request.signal.aborted) setState({ session, failed: false }); })
        .catch(() => { if (!request.signal.aborted) setState({ session: null, failed: true }); });
    }
    function visible() { if (document.visibilityState === "visible") refresh(); }
    refresh();
    document.addEventListener("visibilitychange", visible);
    window.addEventListener("focus", refresh);
    return () => { controller?.abort(); document.removeEventListener("visibilitychange", visible); window.removeEventListener("focus", refresh); };
  }, []);
  return <MemberSession.Provider value={state}>{children}</MemberSession.Provider>;
}

export const useMemberSession = () => useContext(MemberSession);
