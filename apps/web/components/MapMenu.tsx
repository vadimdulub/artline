"use client";
import { useEffect, useRef, type ReactNode } from "react";

export function MapMenu({ className, label, children }: { className: string; label: ReactNode; children: ReactNode }) {
  const menu = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    function dismiss(event: PointerEvent) {
      if (menu.current?.open && event.target instanceof Node && !menu.current.contains(event.target)) menu.current.open = false;
    }
    document.addEventListener("pointerdown", dismiss, true);
    return () => document.removeEventListener("pointerdown", dismiss, true);
  }, []);
  return <details ref={menu} className={className}
    onKeyDown={event => { if (event.key === "Escape" && event.currentTarget.open) { event.preventDefault(); event.stopPropagation(); event.currentTarget.open = false; event.currentTarget.querySelector("summary")?.focus(); } }}
    onBlur={event => { if (event.relatedTarget instanceof Node && !event.currentTarget.contains(event.relatedTarget)) event.currentTarget.open = false; }}>
    <summary>{label}</summary>{children}
  </details>;
}
