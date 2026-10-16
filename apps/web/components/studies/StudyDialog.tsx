"use client";
import { useEffect, useId, useRef, type ReactNode } from "react";
import { lockBodyScroll } from "@/lib/modal-scroll";
import styles from "./Studies.module.css";

export function StudyDialog({ title, subtitle, close, children, footer, wide = false }: { title: string; subtitle?: string; close: () => void; children: ReactNode; footer?: ReactNode; wide?: boolean }) {
  const dialog = useRef<HTMLDialogElement>(null); const titleId = useId();
  useEffect(() => {
    const element = dialog.current!; const focused = document.activeElement as HTMLElement | null;
    const unlock = lockBodyScroll(); element.showModal();
    return () => { element.close(); unlock(); if (focused?.isConnected) focused.focus({ preventScroll: true }); };
  }, []);
  return <dialog ref={dialog} className={`${styles.dialog} ${wide ? styles.wideDialog : ""}`} aria-labelledby={titleId} onCancel={event => { event.preventDefault(); close(); }} onKeyDown={event => {
    if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); close(); return; }
    if (event.key !== "Tab") return;
    const elements = [...event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),summary,[tabindex="0"]')].filter(element => element.getClientRects().length > 0);
    const first = elements[0], last = elements.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
    if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
  }}>
    <header className={styles.dialogHeader}><div><h2 id={titleId}>{title}</h2>{subtitle && <p>{subtitle}</p>}</div><button type="button" className={styles.iconButton} onClick={close} aria-label={`Close ${title.toLowerCase()}`}>×</button></header>
    <div className={styles.dialogBody}>{children}</div>
    {footer && <footer className={styles.dialogFooter}>{footer}</footer>}
  </dialog>;
}
