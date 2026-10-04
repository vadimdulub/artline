"use client";

import { createContext, useContext, useEffect, useRef, useState, type ComponentPropsWithRef } from "react";
import { lockBodyScroll } from "@/lib/modal-scroll";
import "./ExplorerFrame.css";

const ExplorerView = createContext<{ fullView: boolean; setFullView: (value: boolean) => void } | null>(null);
export const useExplorerView = () => useContext(ExplorerView);

export function ExplorerFrame({ ref, children, ...props }: ComponentPropsWithRef<"section">) {
  const root = useRef<HTMLElement>(null);
  const indexTarget = useRef<HTMLElement | null>(null);
  const [fullView, setFullView] = useState(false);

  useEffect(() => {
    if (!fullView || !root.current) return;
    const element = root.current;
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const unlock = lockBodyScroll();
    const background: { element: HTMLElement; inert: boolean }[] = [];
    // Keep sibling native record dialogs available above the expanded canvas.
    for (let branch: HTMLElement = element; branch.parentElement; branch = branch.parentElement) {
      for (const sibling of branch.parentElement.children) {
        if (!(sibling instanceof HTMLElement) || sibling === branch || sibling.matches("dialog,script,style") || sibling.querySelector("dialog")) continue;
        background.push({ element: sibling, inert: sibling.inert });
        sibling.inert = true;
      }
      if (branch.parentElement === document.body) break;
    }
    function keyboard(event: KeyboardEvent) {
      if (event.defaultPrevented || document.querySelector("dialog[open]")) return;
      if (event.key === "Escape") { event.preventDefault(); setFullView(false); }
      if (event.key !== "Tab") return;
      const controls = [...element.querySelectorAll<HTMLElement>('button,a[href],input,select,textarea,summary,[tabindex]')]
        .filter(control => control.tabIndex >= 0 && !control.matches(":disabled") && control.getClientRects().length && getComputedStyle(control).visibility !== "hidden");
      const first = controls[0], last = controls.at(-1);
      if (!first) { event.preventDefault(); element.focus(); }
      else if (event.shiftKey && (document.activeElement === first || !element.contains(document.activeElement))) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && (document.activeElement === last || !element.contains(document.activeElement))) { event.preventDefault(); first.focus(); }
    }
    document.addEventListener("keydown", keyboard);
    return () => {
      document.removeEventListener("keydown", keyboard);
      background.forEach(item => { item.element.inert = item.inert; });
      unlock();
      if (indexTarget.current?.isConnected) indexTarget.current.focus({ preventScroll: true });
      else if (previousFocus?.isConnected && previousFocus.getClientRects().length) previousFocus.focus({ preventScroll: true });
      else if (element.isConnected) element.focus({ preventScroll: true });
      indexTarget.current = null;
    };
  }, [fullView]);

  return <ExplorerView.Provider value={{ fullView, setFullView }}>
    <section {...props} ref={element => { root.current = element; if (typeof ref === "function") return ref(element); else if (ref) ref.current = element; }}
      data-full-view={fullView} role={fullView ? "dialog" : props.role} aria-modal={fullView || undefined} tabIndex={-1}
      onClick={event => {
        props.onClick?.(event);
        if (!fullView || event.defaultPrevented || !(event.target instanceof Element)) return;
        const href = event.target.closest('a[href^="#"]')?.getAttribute("href");
        const target = href ? document.getElementById(href.slice(1)) : null;
        if (target && !root.current?.contains(target)) { indexTarget.current = target; setFullView(false); }
      }}>
      {children}
    </section>
  </ExplorerView.Provider>;
}
