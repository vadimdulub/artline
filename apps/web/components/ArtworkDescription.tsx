"use client";
import { displayMetadata } from "@/lib/display-metadata";
import ReactMarkdown from "react-markdown";
import { safeSourceURL } from "@/lib/api";
import type { Artwork } from "@/lib/types";
import { useMuseumRequest } from "./museum-state";

// Long catalogue text is fetched for one opened record, not every card/page.
export function ArtworkDescription({ work, detailPath }: { work: Artwork; detailPath: string }) {
  const request = useMuseumRequest<Artwork>(work.description_md === undefined ? detailPath : null, 0);
  const description = work.description_md ?? request.data?.description_md;
  if (!displayMetadata(description)) return null;
  return <details className="sources-section">
    <summary>About this artwork</summary>
    <div className="artwork-description"><ReactMarkdown skipHtml allowedElements={["p", "a", "strong", "em", "ul", "ol", "li", "blockquote", "br"]} unwrapDisallowed components={{ a: ({ href, children }) => safeSourceURL(href) ? <a href={safeSourceURL(href)} target="_blank" rel="noreferrer">{children}</a> : <span>{children}</span> }}>{description}</ReactMarkdown></div>
  </details>;
}
