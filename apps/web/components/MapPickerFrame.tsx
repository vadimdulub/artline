"use client";
import { createContext, useContext, useEffect, useRef, type Dispatch, type ReactNode, type SetStateAction } from "react";

export function isMapPickerControl(target: Node) { return target instanceof Element && !!target.closest(".map-picker-visibility"); }

export type ActiveMapPicker = { name: string; element: HTMLDetailsElement; close: (restoreFocus?: boolean) => void };
export const MapPickerContext = createContext<Dispatch<SetStateAction<ActiveMapPicker | undefined>> | null>(null);

export function MapPickerFrame({ children, name, className = "" }: { children: ReactNode; name: string; className?: string }) {
  const picker = useRef<HTMLDivElement>(null), setActivePicker = useContext(MapPickerContext);
  useEffect(() => {
    const host = picker.current;
    if (!host) return;
    let frame = 0;
    function toggle(event: Event) {
      if (!(event.target instanceof HTMLDetailsElement)) return;
      const details = event.target;
      cancelAnimationFrame(frame);
      const summary = details.querySelector<HTMLElement>("summary");
      if (details.open) summary?.setAttribute("aria-hidden", "true"); else summary?.removeAttribute("aria-hidden");
      if (!details.open) {
        const restoreFocus = host?.contains(document.activeElement);
        setActivePicker?.(current => current?.element === details ? undefined : current);
        if (restoreFocus) frame = requestAnimationFrame(() => { if (!host?.closest("[hidden]")) details.querySelector<HTMLElement>("summary")?.focus({ preventScroll: true }); });
        return;
      }
      setActivePicker?.({ name, element: details, close: (restoreFocus = false) => { details.open = false; if (restoreFocus) requestAnimationFrame(() => summary?.focus({ preventScroll: true })); } });
      frame = requestAnimationFrame(() => {
        if (!details.open) return;
        const search = details.querySelector<HTMLInputElement>('input[type="search"]'), active = document.activeElement;
        if (active instanceof HTMLElement && details.contains(active) && active !== search && !active.matches("summary")) return;
        search?.focus({ preventScroll: true });
      });
    }
    host.addEventListener("toggle", toggle, true);
    return () => {
      cancelAnimationFrame(frame); host.removeEventListener("toggle", toggle, true);
      setActivePicker?.(current => host.contains(current?.element ?? null) ? undefined : current);
    };
  }, [name, setActivePicker]);
  return <div ref={picker} className={`map-selection-picker ${className}`.trim()}>{children}</div>;
}
