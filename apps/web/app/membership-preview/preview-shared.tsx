import Image from "next/image";
import type { CSSProperties, ReactNode } from "react";

export type Feature = { id: string; title: string; short: string; promise: string; free: string; paid: string; phase: string };

export const works = [
  { id: "wave", title: "Under the Wave off Kanagawa", artist: "Katsushika Hokusai", date: "c. 1830–1832", year: 1831, image: "hokusai-wave.jpg", medium: "Woodblock print; ink and colour on paper", collection: "The Metropolitan Museum of Art", source: "https://www.metmuseum.org/art/collection/search/45434", credit: "The Metropolitan Museum of Art, CC0", description: "A curling blue wave above boats and distant Mount Fuji." },
  { id: "bridge", title: "Bridge over a Pond of Water Lilies", artist: "Claude Monet", date: "1899", year: 1899, image: "monet-bridge.jpg", medium: "Oil on canvas", collection: "The Metropolitan Museum of Art", source: "https://www.metmuseum.org/art/collection/search/437127", credit: "Daniel Schwen / Wikimedia Commons, public domain", description: "A green arched bridge above a pond of water lilies." },
  { id: "evening", title: "Summer Evening on Skagen Sønderstrand", artist: "P. S. Krøyer", date: "1893", year: 1893, image: "kroyer-evening.jpg", medium: "Oil on canvas", collection: "Skagens Museum", source: "https://commons.wikimedia.org/wiki/File:P.S._Kr%C3%B8yer_-_Summer_evening_on_Skagen%27s_Beach._Anna_Ancher_and_Marie_Kr%C3%B8yer_walking_together._-_Google_Art_Project.jpg", credit: "Wikimedia Commons, public domain", description: "Two women walking beside a blue sea in the evening." },
  { id: "room", title: "Sunlight in the Blue Room", artist: "Anna Ancher", date: "1891", year: 1891, image: "anna-blue.jpg", medium: "Oil on canvas", collection: "Skagens Museum", source: "https://commons.wikimedia.org/wiki/File:Anna_Ancher_-_Sunlight_in_the_blue_room_-_Google_Art_Project.jpg", credit: "Wikimedia Commons, public domain", description: "A child in a blue room with sunlight across the wall." },
];
export type Work = typeof works[number];

export function Art({ work, className = "", style }: { work: Work; className?: string; style?: CSSProperties }) {
  return <Image className={`mp-art ${className}`} src={`/assets/artworks/${work.image}`} width={720} height={720} alt={work.description} loading="eager" unoptimized style={style} />;
}
export function Action({ children, onClick, secondary = false, disabled = false }: { children: ReactNode; onClick?: () => void; secondary?: boolean; disabled?: boolean }) {
  return <button className={`mp-button${secondary ? " mp-button-secondary" : ""}`} type="button" onClick={onClick} disabled={disabled}>{children}</button>;
}
export function WorkCaption({ work }: { work: Work }) {
  return <figcaption><span>{work.artist}, {work.date}</span><h3>{work.title}</h3></figcaption>;
}
export function Source({ work }: { work: Work }) {
  return <a className="mp-source" href={work.source} target="_blank" rel="noreferrer">Image &amp; source: {work.credit}</a>;
}
export function StageHeading({ title, description, children }: { title: string; description: string; children?: ReactNode }) {
  return <div className="mp-stage-heading"><div><h2>{title}</h2><p>{description}</p></div>{children}</div>;
}

