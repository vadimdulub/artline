"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { lockBodyScroll } from "@/lib/modal-scroll";

export function RecordDrawer({ label, closeLabel, recordKey, title, navigation, close, fallbackFocusId, children }: {
  label: string; closeLabel: string; recordKey: string; title: ReactNode; navigation?: ReactNode;
  close: () => void; fallbackFocusId: string; children: ReactNode;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    const focused = document.activeElement as HTMLElement | null;
    const unlock = lockBodyScroll();
    element.showModal();
    return () => {
      element.close(); unlock();
      if (focused?.isConnected && focused !== document.body) focused.focus({ preventScroll: true });
      else document.getElementById(fallbackFocusId)?.focus({ preventScroll: true });
    };
  }, [fallbackFocusId]);
  useEffect(() => { dialog.current?.scrollTo({ top: 0, behavior: "instant" }); }, [recordKey]);

  return <dialog ref={dialog} className="painter-dialog" aria-label={label} onKeyDown={event => {
    if (event.key !== "Tab" || !(event.target instanceof Element) || event.target.closest("dialog") !== event.currentTarget) return;
    const elements = [...event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),summary,[tabindex]:not([tabindex="-1"])')]
      .filter(element => element.tabIndex >= 0 && element.getClientRects().length > 0 && getComputedStyle(element).visibility !== "hidden" && element.closest("dialog") === event.currentTarget);
    const first = elements[0], last = elements.at(-1);
    if (!first || !last) return;
    if (event.shiftKey && (document.activeElement === first || document.activeElement === event.currentTarget)) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }} onCancel={event => { event.preventDefault(); close(); }} onClick={event => {
    if (event.target !== event.currentTarget) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) close();
  }}>
    <div className="dialog-toolbar"><span role="status">{title}</span>{navigation}<button className="close-painter" autoFocus type="button" onClick={close} aria-label={closeLabel}><span aria-hidden="true">×</span></button></div>
    {children}
  </dialog>;
}
