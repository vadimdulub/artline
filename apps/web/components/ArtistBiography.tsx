"use client";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { safeSourceURL } from "@/lib/api";
import type { ArtistDetail, ReferenceBiography } from "@/lib/types";

function Credit({ source }: { source: ReferenceBiography }) {
  return <p className="biography-credit"><a href={safeSourceURL(source.source_url)} target="_blank" rel="noreferrer">{source.attribution}</a>. Opening excerpt, formatted for reading. <a href={safeSourceURL(source.license_url)} target="_blank" rel="noreferrer">CC BY-SA 4.0</a>. <a href={safeSourceURL(source.revision_url)} target="_blank" rel="noreferrer">Source revision</a>.</p>;
}
export function ArtistBiography({ artist, embedded }: { artist: ArtistDetail; embedded: boolean }) {
  const source = artist.reference_biography;
  // Keep substantial existing editorial biographies. The reference source supplies
  // fuller reading where the catalogue has only a short authority description.
  const useReference = Boolean(source && (artist.biography_md?.trim().length ?? 0) < 400);
  const text = (useReference ? source?.text : artist.biography_md) ?? "";
  const [expanded, setExpanded] = useState(!embedded && !useReference);
  const short = text.split(/(?<=[.!?])\s+/).slice(0, 2).join(" ");
  const shown = expanded ? text : short;
  return <div className="biography" id={`biography-${artist.id}`}>
    <h2>Biography</h2>
    {text ? <>{useReference ? shown.split(/\n\n+/).map((paragraph, index) => <p key={index}>{paragraph}</p>) : <ReactMarkdown remarkPlugins={[remarkGfm]}>{shown}</ReactMarkdown>}
      {short !== text && <button className="biography-toggle" aria-expanded={expanded} onClick={() => setExpanded(value => !value)}>{expanded ? "Show less" : "Read full biography"}</button>}
      {useReference && source && <Credit source={source} />}
      {!useReference && source && <details className="reference-biography"><summary>Reference biography</summary>{source.text.split(/\n\n+/).map((paragraph, index) => <p key={index}>{paragraph}</p>)}<Credit source={source} /></details>}
    </> : <p className="research-note">A sourced biography is not available yet.</p>}
  </div>;
}
