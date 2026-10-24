"use client";

import { useRef, useState, useSyncExternalStore } from "react";
import { NavigationIcon } from "./MemberNavigation";
import { timelineIntroductionCopy, type TimelineIntroductionKind } from "@/lib/timeline-introduction";
import type { GuideLocale } from "@/lib/museum-guide-types";
import styles from "./TimelineIntroduction.module.css";

const preferenceChanged = "artline:timeline-introduction";

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  window.addEventListener(preferenceChanged, callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(preferenceChanged, callback);
  };
}

function wasDismissed(key: string) {
  try { return window.localStorage.getItem(key) === "1"; } catch { return false; }
}

export function TimelineIntroduction({ kind, locale = "en", fromGuide = false }: {
  kind: TimelineIntroductionKind;
  locale?: GuideLocale;
  fromGuide?: boolean;
}) {
  const key = `artline:timeline-introduction:v1:${kind}`;
  // SSR is a small, usable disclosure; hydration reads this browser’s preference.
  const dismissed = useSyncExternalStore(subscribe, () => wasDismissed(key), () => true);
  const [sessionDismissed, setSessionDismissed] = useState(false);
  const [reopened, setReopened] = useState(false);
  const summary = useRef<HTMLElement>(null);
  const open = reopened || (!dismissed && !sessionDismissed);
  const copy = timelineIntroductionCopy[locale];
  const title = kind === "artworks" ? copy.artworksTitle : copy.lifespansTitle;

  function dismiss() {
    // Still dismiss for this visit when storage is blocked (for example, privacy mode).
    setSessionDismissed(true);
    setReopened(false);
    try { window.localStorage.setItem(key, "1"); } catch { /* No account or network fallback. */ }
    window.dispatchEvent(new Event(preferenceChanged));
  }

  return <aside className={styles.note} lang={locale} dir={locale === "ar" ? "rtl" : "ltr"} aria-label={title}>
    <details open={open} data-timeline-introduction={kind}>
      <summary ref={summary} onClick={event => {
        event.preventDefault();
        if (open) dismiss();
        else setReopened(true);
      }}>
        <NavigationIcon kind="about" />
        <span>{open ? title : copy.help}</span>
        <span className={styles.toggle} aria-hidden="true">{open ? "−" : "+"}</span>
      </summary>
      <div className={styles.body}>
        <p>{kind === "artworks" ? copy.artworks : <>{fromGuide && <>{copy.guideArtists} </>}{copy.lifespans}</>}</p>
        <div className={styles.foot}>
          <p>{kind === "artworks" ? copy.contextNote : copy.overlapNote}</p>
          <button type="button" onClick={() => {
            dismiss();
            summary.current?.focus({ preventScroll: true });
          }}>{copy.dismiss}</button>
        </div>
      </div>
    </details>
  </aside>;
}
