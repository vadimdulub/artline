import Link from "@/components/MemberLink";
import styles from "./MuseumGuideCallout.module.css";

export type MuseumGuideLink = { href: string; title: string; count?: number; languages?: number };

export function MuseumGuideCallout({ guides }: { guides: MuseumGuideLink[] }) {
  if (!guides.length) return null;
  return <nav className={styles.guideCallout} aria-label="Museum guides">
    <h2>{guides.length === 1 ? "Explore with a guide" : "Explore with guides"}</h2>
    <ul>{guides.map(guide => <li key={guide.href}>
      <div><h3>{guide.title}</h3>{guide.count !== undefined && <p>{guide.count} artworks{guide.languages ? ` · ${guide.languages} languages` : ""}</p>}</div>
      <Link prefetch={false} href={guide.href} aria-label={`Read guide: ${guide.title}`}>Read guide</Link>
    </li>)}</ul>
  </nav>;
}
