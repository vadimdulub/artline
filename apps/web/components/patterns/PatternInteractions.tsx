"use client";

import { useEffect, useRef, type ReactNode } from "react";
import type { PatternInteractiveCopy } from "@/lib/pattern-guide";
import { mountPatternGuide } from "./pattern-interactions";

export function PatternInteractions({ copy, children, className, locale }: { copy: PatternInteractiveCopy; children: ReactNode; className: string; locale: string }) {
  const root = useRef<HTMLElement>(null);
  useEffect(() => {
    if (root.current) return mountPatternGuide(root.current, copy);
  }, [copy]);
  return <article ref={root} className={className} lang={locale} dir={locale === "ar" ? "rtl" : "ltr"}>{children}</article>;
}
