import Link from "next/link";
import type { GuideSearchPage } from "@/lib/guide-search";
import styles from "./PreparedMuseumGuides.module.css";

export function PreparedMuseumGuides({ page, slug, query = "" }: { page: GuideSearchPage; slug: string; query?: string }) {
  if (!page.items.length) return null;
  const more = new URLSearchParams({ institution: slug, ...(query ? { q: query } : {}) });
  return <section className={styles.section} aria-label="Artline guides">
    <h3>Artline guides</h3>
    <p className={styles.note}>Prepared by Artline and available to read in full. These guides are read-only.</p>
    <ul className={styles.list}>{page.items.map(guide => <li key={guide.slug}>
      {guide.image && <div className={styles.cover}>{/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={guide.image} alt="" loading="lazy" width="120" height="120" />
      </div>}
      <div className={styles.copy}><span className={styles.note}>Read-only</span><h4><Link href={guide.href}>{guide.title}</Link></h4><p>{guide.subtitle}</p><p className={styles.note}>{guide.count} artworks · {guide.languages} languages · PDF</p></div>
      <Link className={styles.read} href={guide.href}>Read guide<span className="sr-only">: {guide.title}</span></Link>
    </li>)}</ul>
    {page.next_cursor && <Link className={styles.read} href={`/guides?${more}`}>See all Artline guides for this museum</Link>}
  </section>;
}
