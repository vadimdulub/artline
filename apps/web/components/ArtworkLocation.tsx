import Link from "next/link";
import { safeSourceURL } from "@/lib/api";
import type { Artwork } from "@/lib/types";

export function checkedDate(value: string) {
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeZone: "UTC" }).format(new Date(value));
}
export function ArtworkLocation({ work }: { work: Artwork }) {
  const display = work.display;
  if (!work.holding && !display) return null;
  return <section className="artwork-location" aria-label="Collection and display">
    {work.holding && <p>Collection: <Link href={`/museums/${work.holding.slug}`}>{work.holding.name}</Link></p>}
    {display && <p>{display.state === "on_view" ? "Reported on view" : display.state === "not_on_view" ? "Reported not on view" : display.state === "stale" ? "Display report is out of date" : "Display not verified"} at <Link href={`/museums/${display.slug}`}>{display.venue_name}</Link>{display.state === "on_view" && display.gallery ? `, gallery ${display.gallery}` : ""}. {display.context === "loan" && "On loan; the holding collection is unchanged. "}<a href={safeSourceURL(display.source_url)} target="_blank" rel="noreferrer">Checked {checkedDate(display.checked_at)}</a>.</p>}
  </section>;
}
