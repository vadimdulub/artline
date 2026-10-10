import Link from "next/link";
import { StructuredData } from "@/components/StructuredData";
import { breadcrumbs, pageMetadata } from "@/lib/seo";
import styles from "./guides.module.css";

export function generateMetadata() {
  return pageMetadata("Guides to exploring art, literature & history", "Find a starting point for exploring Artline. Learn to compare artists, follow artwork dates, and connect art with books and historical events.", "/guides");
}

export default function GuidesPage() {
  return <main id="main-content" className={styles.page}>
    <StructuredData data={breadcrumbs([{ name: "Artline", path: "/" }, { name: "Guides", path: "/guides" }])} />
    <header className={styles.heading}>
      <div><h1>Guides</h1><p>Look closely. Follow a connection. Explore art, literature and history.</p></div>
      <Link href="/">Explore the timeline</Link>
    </header>
    <article className={styles.feature} aria-labelledby="timeline-guide-title">
      <div className={styles.summary}>
        <p className={styles.topic}>Using Artline</p>
        <h2 id="timeline-guide-title"><Link href="/art-history-timeline">Explore art history through time</Link></h2>
        <p>Begin with a question and a date range. Compare artists’ lives, follow the dates of their works, and bring books and historical events into the picture.</p>
        <Link className={styles.read} href="/art-history-timeline">Read the guide</Link>
      </div>
      <div className={styles.contents}>
        <h3>Inside the guide</h3>
        <ul>
          <li>Choose a period and narrow your exploration</li>
          <li>Compare an artist’s life with the dates of their work</li>
          <li>Connect art with books and historical events</li>
          <li>Follow museum holdings and check the sources</li>
        </ul>
      </div>
    </article>
  </main>;
}
