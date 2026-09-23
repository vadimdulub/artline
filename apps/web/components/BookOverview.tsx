import { safeSourceURL } from "@/lib/api";
import type { BookOverview as Overview } from "@/lib/books";
import styles from "./Books.module.css";

export function BookOverview({ overview }: { overview: Overview }) {
  return <div className={styles.overviewText}>
    {overview.paragraphs.map((paragraph, index) => <p key={index}>{paragraph.replace(/\(\s*,\s*(?:US also\s*)?;\s*/g, "(")}</p>)}
    <p className={styles.overviewCredit}>
      Excerpt from <a href={safeSourceURL(overview.sourceUrl)} target="_blank" rel="noreferrer">Wikipedia ↗</a>
      {" · "}<a href={safeSourceURL(overview.licenseUrl)} target="_blank" rel="noreferrer">CC BY-SA 4.0</a>
    </p>
  </div>;
}
