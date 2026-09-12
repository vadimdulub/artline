"use client";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { safeSourceURL } from "@/lib/api";
import type { Artwork } from "@/lib/types";
import { useMuseumRequest } from "./museum-state";

// Long catalogue text is fetched for one opened record, not every card/page.
export function ArtworkDescription({ work, detailPath, token = "" }: { work: Artwork; detailPath: string; token?: string }) {
  const [opened, setOpened] = useState(false), [retry, setRetry] = useState(0);
  const request = useMuseumRequest<Artwork>(opened && work.description_md === undefined ? detailPath : null, token, retry);
  const description = work.description_md ?? request.data?.description_md;
  return <details className="sources-section" onToggle={event => setOpened(event.currentTarget.open)}>
    <summary>About this artwork</summary>
    {opened && <div className="artwork-description">
      {description ? <ReactMarkdown skipHtml allowedElements={["p", "a", "strong", "em", "ul", "ol", "li", "blockquote", "br"]} unwrapDisallowed components={{ a: ({ href, children }) => safeSourceURL(href) ? <a href={safeSourceURL(href)} target="_blank" rel="noreferrer">{children}</a> : <span>{children}</span> }}>{description}</ReactMarkdown>
        : request.error ? <div role="alert"><p>{request.error}</p><button type="button" onClick={() => setRetry(value => value + 1)}>Retry description</button></div>
        : request.loading ? <p role="status">Loading catalogue description…</p>
        : <p>No catalogue description has been added yet.</p>}
    </div>}
  </details>;
}
