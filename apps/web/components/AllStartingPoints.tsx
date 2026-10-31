"use client";
import { useState } from "react";
import type { AtlasMetadata, AtlasPreset } from "@/lib/atlas";
import { bookYearLabel } from "@/lib/books";
import { ArtworkImage } from "./ArtworkViewer";
import "./AllStoryCards.css";

const featured = ["womens-rights", "first-world-war", "second-world-war", "second-world-war-asia-africa", "renaissance", "silk-roads"];
const years = (p: AtlasPreset) => `${bookYearLabel(p.period.start)}–${bookYearLabel(p.period.end)}`;
function Cover({ preset, eager }: { preset: AtlasPreset; eager: boolean }) {
  return preset.cover ? <ArtworkImage eager={eager} work={{ ...preset.cover, media_url: preset.cover.media_url ?? null, alt_text: preset.cover.alt_text ?? null, rights_status: preset.cover.rights_status ?? null }} sizes="(max-width: 600px) 90vw, (max-width: 1100px) 45vw, 23vw" /> : <span className="all-start-image-date">{years(preset)}</span>;
}

export function AllStartingPoints({ metadata, select }: { metadata: AtlasMetadata; select: (id: string) => void }) {
  const [query, setQuery] = useState("");
  const [group, setGroup] = useState("");
  const groups = [...new Set(metadata.presets.map(p => p.group))];
  const terms = query.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
  const filtered = metadata.presets.filter(p => (!group || p.group === group) && terms.every(term => `${p.name} ${p.group} ${p.description} ${p.startingScope} ${p.overview ?? ""} ${years(p)} ${p.id}`.toLocaleLowerCase().includes(term)));
  const stories = [...featured.flatMap(id => filtered.find(p => p.id === id) ?? []), ...filtered.filter(p => !featured.includes(p.id))];
  return <div className="all-start">
    <header className="all-start-heading"><h1 id="all-timeline-title" tabIndex={-1}>Explore a moment in history</h1><p>Art, books and the events that connect them.<br />Find a moment. See what changed, and how people responded.</p></header>
    <section aria-labelledby="all-featured-title" className="all-stories">
      <div className="all-other-heading"><h2 id="all-featured-title">Start with a story</h2><p>Rights, war, exchange and changing ways of seeing.</p></div>
      <div className="all-moments-tools"><label htmlFor="all-moments-search">Find a moment<input id="all-moments-search" type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Try war, Japan or printing" /></label><div className="all-moment-groups" role="group" aria-label="Browse historical eras"><button type="button" aria-pressed={!group} onClick={() => setGroup("")}>All eras</button>{groups.map(value => <button type="button" key={value} aria-pressed={group === value} onClick={() => setGroup(value)}>{value}</button>)}</div></div>
      <p className="all-moment-results" role="status">{query || group ? `${stories.length} ${stories.length === 1 ? "moment" : "moments"} found` : `${metadata.presets.length} stories to explore, from early cities to the digital world.`}</p>
      <div className="all-featured all-story-grid">{stories.map((p, index) => <button key={p.id} className="all-start-card" aria-label={p.name} aria-describedby={`start-description-${p.id} start-geography-${p.id}`} onClick={() => select(p.id)}>
        <span className="all-start-image"><Cover preset={p} eager={index < 4} /></span>
        <span className="all-start-card-copy"><span className="all-start-date">{years(p)}</span><strong>{p.name}</strong><span className="all-start-description" id={`start-description-${p.id}`}>{p.description}</span><span className="all-start-geography" id={`start-geography-${p.id}`}>{p.startingScope}</span></span>
      </button>)}</div>
      {!filtered.length && <div className="all-moments-empty"><p>No moments match this search.</p><button onClick={() => { setQuery(""); setGroup(""); }}>Show all moments</button></div>}
    </section>
  </div>;
}
