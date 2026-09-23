import type { AtlasMetadata, AtlasPreset } from "@/lib/atlas";
import { bookYearLabel } from "@/lib/books";
import { ArtworkImage } from "./ArtworkViewer";

const featured = ["renaissance", "edo", "romanticism", "second-world-war"];
const years = (p: AtlasPreset) => `${bookYearLabel(p.context.start)}–${bookYearLabel(p.context.end)}`;
export function AllStartingPoints({ metadata, select }: { metadata: AtlasMetadata; select: (id: string) => void }) {
  const main = featured.flatMap(id => metadata.presets.find(p => p.id === id) ?? []);
  const groups = [...new Set(metadata.presets.map(p => p.group))];
  return <div className="all-start">
    <header className="all-start-heading"><span className="all-eyebrow">Art · Literature · History</span><h1 id="all-timeline-title" tabIndex={-1}>Explore a moment in history</h1><p>See the pictures, read the books, follow the events.<br />Choose a starting point, then make it your own.</p></header>
    <div className="all-featured" role="group" aria-label="Featured starting points">{main.map(p => <button key={p.id} className="all-start-card" aria-label={p.name} aria-describedby={`start-description-${p.id} start-geography-${p.id}`} onClick={() => select(p.id)}>
      <span className="all-start-image">{p.cover ? <ArtworkImage work={{ ...p.cover, media_url: p.cover.media_url ?? null, alt_text: p.cover.alt_text ?? null, rights_status: p.cover.rights_status ?? null }} /> : <span className="all-start-image-date">{years(p)}</span>}</span>
      <span className="all-start-card-copy"><span className="all-eyebrow">{years(p)} <span aria-hidden="true">↗</span></span><strong>{p.name}</strong><span className="all-start-description" id={`start-description-${p.id}`}>{p.description}</span><span className="all-start-geography" id={`start-geography-${p.id}`}>{p.startingScope}{p.startingCountries?.length ? <small>Artwork focus: {p.startingCountries.map(name => name.replace(/\b\w/g, c => c.toUpperCase())).join(", ")} · editable</small> : null}</span></span>
    </button>)}</div>
    <div className="all-other-heading"><h2>More starting points</h2><p>Different places. Connected histories.</p></div>
    <div className="all-period-groups">{groups.map(group => <section key={group} className="all-period-group"><h3>{group}</h3>{metadata.presets.filter(p => p.group === group && !featured.includes(p.id)).map(p => <button key={p.id} aria-label={p.name} aria-describedby={`start-description-${p.id} start-geography-${p.id}`} onClick={() => select(p.id)}><span><strong>{p.name}</strong><time>{years(p)}</time></span><span className="all-period-description" id={`start-description-${p.id}`}>{p.description}</span><span className="all-start-geography" id={`start-geography-${p.id}`}>{p.startingScope}{p.startingCountries?.length ? <small>Artwork focus: {p.startingCountries.map(name => name.replace(/\b\w/g, c => c.toUpperCase())).join(", ")} · editable</small> : null}</span></button>)}</section>)}</div>
  </div>;
}
