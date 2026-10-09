"use client";

import Link from "next/link";
import { displayMetadata } from "@/lib/display-metadata";
import { useEffect, useState } from "react";
import { apiRequest, errorMessage, safeSourceURL } from "@/lib/api";
import type { HistoricalEvent } from "@/lib/events";
import { RecordArrows, type RecordNavigation } from "./RecordNavigation";
import { RecordDrawer } from "./RecordDrawer";
import { LoadingIndicator } from "./LoadingIndicator";
import styles from "./Books.module.css";

export function EventDrawer({ id, close, navigation, fallbackFocusId = "events-timeline" }: { id: string; close: () => void; fallbackFocusId?: string; navigation?: RecordNavigation }) {
  const [result, setResult] = useState<{ id: string; attempt: number; data?: HistoricalEvent; error?: string }>();
  const [retry, setRetry] = useState(0);
  const [failedImage, setFailedImage] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    apiRequest<HistoricalEvent>(`events/${encodeURIComponent(id)}`, { signal: controller.signal })
      .then(data => { if (!controller.signal.aborted) setResult({ id, attempt: retry, data }); })
      .catch(error => { if (!controller.signal.aborted) setResult({ id, attempt: retry, error: errorMessage(error) }); });
    return () => controller.abort();
  }, [id, retry]);
  const event = result?.id === id && result.attempt === retry ? result.data : undefined;
  const error = result?.id === id && result.attempt === retry ? result.error : undefined;
  const contextualRange = (min: number, max: number) => {
    if (!event || event.startYear === null || event.endYear === null || event.endYear < min || event.startYear > max) return null;
    let start = Math.max(min, event.startYear), end = Math.min(max, event.endYear);
    if (start === end) { if (end < max) end += end === -1 ? 2 : 1; else start -= start === 1 ? 2 : 1; }
    return new URLSearchParams({ start: String(start), end: String(end), top100: "false" }).toString();
  };
  const books = contextualRange(-5000, 2026), art = contextualRange(1100, 2000);
  return <RecordDrawer label="Event details" closeLabel="Close event details" recordKey={id} title={event?.kind ?? "Event"} navigation={navigation && <RecordArrows navigation={navigation} noun="event" />} close={close} fallbackFocusId={fallbackFocusId}>
    {event ? <div className={`${styles.drawerContent} ${styles.eventContent}`}>
      <header className={styles.bookHeading}><p>{event.kind} · {event.topics.join(" · ")}</p><h2>{event.title}</h2>{displayMetadata(event.years) && <p>{event.years}</p>}</header>
      {event.image && <figure className={styles.eventIllustration}>
        {failedImage !== event.image.imageUrl &&
          // eslint-disable-next-line @next/next/no-img-element
          <img className={styles.coverImage} src={event.image.imageUrl} alt={event.image.label} decoding="async" onError={() => setFailedImage(event.image!.imageUrl)} />}
        <figcaption className={styles.coverNote}>
          <a href={safeSourceURL(event.image.sourceUrl)} target="_blank" rel="noreferrer">{event.image.label}</a><br />
          {event.image.credit} · <a href={safeSourceURL(event.image.licenseUrl)} target="_blank" rel="noreferrer">{event.image.license}</a>
        </figcaption>
      </figure>}
      {event.description && <section className={styles.bookAbout} aria-labelledby="event-about"><h3 id="event-about">About this {event.kind.toLowerCase()}</h3><p>{event.description}</p></section>}
      {event.descriptionSource && <p className={styles.recordNote}>
        {event.descriptionSource.kind === "wikipedia" ? "From " : "Source: "}<a href={safeSourceURL(event.descriptionSource.url)} target="_blank" rel="noreferrer">{event.descriptionSource.name}</a>
        {event.descriptionSource.kind === "wikipedia" && (event.descriptionSource.language && event.descriptionSource.language !== "en" ? " contributors · English summary" : " contributors · Shortened excerpt")}
        {event.descriptionSource.kind === "wikidata" && event.descriptionSource.notice.includes("assembled") && " · Based on recorded classification and dates"}
        {event.descriptionSource.licenseUrl && <> · <a href={safeSourceURL(event.descriptionSource.licenseUrl)} target="_blank" rel="noreferrer">{event.descriptionSource.license}</a></>}
      </p>}
      {event.significance && <section className={styles.creators}><h3>Why it matters</h3><p>{event.significance}</p></section>}
      <div className={`artwork-details ${styles.bookFacts}`}><dl>
        {displayMetadata(event.years) && <div><dt>Dates</dt><dd>{event.years}</dd></div>}
        {event.countries.length > 0 && <div><dt>Countries and states</dt><dd>{event.countries.join(", ")}</dd></div>}
        {event.regions.length > 0 && <div><dt>Regions</dt><dd>{event.regions.join(", ")}</dd></div>}
      </dl></div>
      {displayMetadata(event.dateBasis) && <p className={styles.recordNote}>{event.dateBasis}</p>}
      {event.geographyBasis && <p className={styles.recordNote}>{event.geographyBasis}</p>}
      {event.locations.length > 0 && <section className={styles.creators}><h3>Recorded places</h3><p>{event.locations.map((place, i) => <span key={place.url}>{i > 0 && ", "}<a href={safeSourceURL(place.url)} target="_blank" rel="noreferrer">{place.name}</a></span>)}</p></section>}
      {event.people.length > 0 && <section className={styles.creators}><h3>People and participants</h3><p>{event.people.map((person, i) => <span key={person.url}>{i > 0 && ", "}<a href={safeSourceURL(person.url)} target="_blank" rel="noreferrer">{person.name}</a></span>)}</p></section>}
      {(books || art) && <section className={styles.creators}><h3>Explore these years</h3>{books && <p><Link href={`/books?${books}`}>Books from this period</Link></p>}{art && <p><Link href={`/?${art.replace("top100=false", "popular=false")}`}>ArtWorks from this period</Link></p>}</section>}
      <section className={styles.creators}><h3>Sources</h3>{event.sources.map(source => <p key={source.url}><a href={safeSourceURL(source.url)} target="_blank" rel="noreferrer">{source.name} ↗</a></p>)}{event.sourceUrl && !event.sources.some(source => source.url === event.sourceUrl) && <p><a href={safeSourceURL(event.sourceUrl)} target="_blank" rel="noreferrer">{/^https:\/\/www\.wikidata\.org\/wiki\/Q\d+$/.test(event.sourceUrl) ? "Wikidata record" : "Source record"} ↗</a></p>}</section>
      <p className={styles.recordNote}>{event.selectionBasis}</p>
    </div> : <div className={styles.drawerState} role={error ? "alert" : "status"}>{error ? <><h2>This event could not be loaded</h2><p>{error}</p><button onClick={() => setRetry(value => value + 1)}>Retry event</button></> : <LoadingIndicator label="Opening event…" />}</div>}
  </RecordDrawer>;
}
