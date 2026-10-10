"use client";

import Link from "next/link";
import { createContext, useContext, useEffect, useRef, useState, type ComponentProps, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { memberReturnTo, requiresMember } from "@/lib/member-return";
import { lockBodyScroll } from "@/lib/modal-scroll";
import { useMemberSession } from "./MemberSession";
import { MemberAccount } from "./MemberAccount";

type SignInOptions = { bookmark?: boolean; onDismiss?: () => void };
const SignIn = createContext<((destination: string, trigger: HTMLElement, options?: SignInOptions) => void) | null>(null);
export const useRequestSignIn = () => useContext(SignIn);

function SignInDialog({ destination, trigger, options, close }: { destination: string; trigger: HTMLElement; options?: SignInOptions; close: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const { session } = useMemberSession();
  const router = useRouter();
  useEffect(() => {
    const element = dialog.current!;
    const unlock = lockBodyScroll();
    element.showModal();
    return () => {
      element.close();
      unlock();
      if (trigger.isConnected) trigger.focus({ preventScroll: true });
    };
  }, [trigger]);
  useEffect(() => {
    if (session?.user?.id) { close(); router.push(destination); }
  }, [session, destination, close, router]);
  function dismiss() { options?.onDismiss?.(); close(); }
  return <dialog ref={dialog} className="signin-dialog account-card" aria-label="Sign in to Artline" onCancel={event => { event.preventDefault(); event.stopPropagation(); dismiss(); }} onClick={event => {
    if (event.target !== event.currentTarget) return;
    const box = event.currentTarget.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dismiss();
  }}>
    <button type="button" className="signin-close" onClick={dismiss} autoFocus aria-label="Close sign-in window">×</button>
    <MemberAccount signInError={false} returnTo={destination} dialog bookmark={options?.bookmark} />
  </dialog>;
}

export function MemberAccessProvider({ children }: { children: ReactNode }) {
  const [request, setRequest] = useState<{ destination: string; trigger: HTMLElement; options?: SignInOptions } | null>(null);
  return <SignIn.Provider value={(destination, trigger, options) => setRequest({ destination, trigger, options })}>{children}{request && <SignInDialog {...request} close={() => setRequest(null)} />}</SignIn.Provider>;
}

export default function MemberLink({ href, onClick, prefetch, ...props }: ComponentProps<typeof Link>) {
  const { session } = useMemberSession();
  const signIn = useContext(SignIn);
  const destination = typeof href === "string" && requiresMember(href) ? memberReturnTo(href) : null;
  return <Link {...props} href={href} prefetch={destination ? false : prefetch} onClick={event => {
    onClick?.(event);
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || props.target === "_blank" || props.download) return;
    if (destination && !session?.user?.id && signIn) { event.preventDefault(); signIn(destination, event.currentTarget); }
  }} />;
}
