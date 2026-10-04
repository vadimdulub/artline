"use client";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { safeSourceURL } from "@/lib/api";
import { cleanEditorialBiography, referenceParagraphs, remarkBiographyParagraphs } from "@/lib/biography";
import type { ArtistDetail, ReferenceBiography } from "@/lib/types";

function Credit({ source }: { source: ReferenceBiography }) {
  return <p className="biography-credit"><a href={safeSourceURL(source.source_url)} target="_blank" rel="noreferrer">{source.attribution}</a>. Opening excerpt, formatted for reading. <a href={safeSourceURL(source.license_url)} target="_blank" rel="noreferrer">CC BY-SA 4.0</a>. <a href={safeSourceURL(source.revision_url)} target="_blank" rel="noreferrer">Source revision</a>.</p>;
}
export function ArtistBiography({ artist, embedded }: { artist: ArtistDetail; embedded: boolean }) {
  const source = artist.reference_biography;
  const editorial = cleanEditorialBiography(artist.biography_md ?? "");
  // Substantial editorial biographies stay primary; source excerpts fill short records.
  const useReference = Boolean(source && editorial.length < 400);
  const text = (useReference ? source?.text : editorial) ?? "";
  const [expanded, setExpanded] = useState(!embedded);
  const paragraphs = referenceParagraphs(text);
  const short = useReference ? paragraphs[0] : text.split(/\n\s*\n/)[0];
  const canExpand = useReference ? paragraphs.length > 1 : short !== text.trim();
  if (!text.trim()) return null;
  return <section className="biography" id={`biography-${artist.id}`} aria-labelledby={`biography-title-${artist.id}`}>
    <h2 id={`biography-title-${artist.id}`}>Biography</h2>
    <div className="biography-copy">{useReference ? (expanded ? paragraphs : paragraphs.slice(0, 1)).map((paragraph, index) => <p key={index}>{paragraph}</p>) : <ReactMarkdown remarkPlugins={[remarkGfm, remarkBiographyParagraphs]}>{expanded ? text : short}</ReactMarkdown>}</div>
    {canExpand && <button className="biography-toggle" aria-expanded={expanded} onClick={() => setExpanded(value => !value)}>{expanded ? "Show less" : "Read full biography"}</button>}
    {useReference && source && <Credit source={source} />}
    {!useReference && source && <details className="reference-biography"><summary>Reference biography</summary><div className="biography-copy">{referenceParagraphs(source.text).map((paragraph, index) => <p key={index}>{paragraph}</p>)}</div><Credit source={source} /></details>}
  </section>;
}
